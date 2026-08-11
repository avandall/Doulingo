# Spec Kỹ Thuật Chi Tiết — 6 Task Rủi Ro Cao Nhất

> Mục đích: đủ chi tiết để một AI coding assistant khác viết boilerplate + unit test bám sát, không tự "đoán mò" magic numbers hay tự thiết kế lại thuật toán.
>
> Đã thêm **SPEC 0** — task tiền đề bị thiếu trong bản kế hoạch gốc: hiệu chỉnh anchor points từ dữ liệu thật *trước khi* Tier 1/Tier 2 dùng chúng, thay vì để việc calibration xuống tận Phase 5 (đã sửa thứ tự này trong `Tasks_list_v2.md`).

---

## SPEC 0 — TASK-010 (mới): Scoring Threshold Bootstrap & Calibration Config

### 0.1 Vấn đề đang giải quyết

Toàn bộ anchor points ở Spec 1 (mục 1.4: `WPM_ANCHORS`, `PAUSE_RATIO_ANCHORS`, `FILLER_ANCHORS`, `MTLD_ANCHORS`) hiện là **số đoán dựa trên tài liệu tham khảo**, không phải số đo từ dữ liệu thật. Nếu để nguyên đến Phase 5 mới chạy `TASK-022` (benchmark) để kiểm tra, hệ thống đã chạy production hàng tháng trời với ngưỡng sai mà không biết. Task này tách phần "khởi tạo ngưỡng ban đầu" ra làm tiền đề bắt buộc trước `TASK-011` (Tier 1), việc "giám sát trôi lệch định kỳ" (drift monitoring) mới để lại ở cuối (nay là `TASK-024`).

### 0.2 Nguồn dữ liệu để hiệu chỉnh (public corpus)

IELTS không công khai dữ liệu audio đã chấm điểm chính thức. Phương án thực dụng:

| Nguồn | Loại nhãn | Ghi chú |
|---|---|---|
| **ICNALE Spoken Monologue/Dialogue Corpus** | CEFR (A2-C1) | Corpus học thuật công khai cho nghiên cứu, có transcript + audio người học châu Á nói tiếng Anh — gần với đối tượng user của bạn |
| **NICT JLE Corpus** | SST score (Standard Speaking Test), map được sang CEFR | Có transcript chi tiết, phù hợp để trích đặc trưng văn bản (MTLD, filler) dù audio hạn chế hơn |
| Video mẫu IELTS Speaking gắn band trên các kênh luyện thi công khai | Band tự gắn bởi người đăng (không chính thức) | Chỉ dùng làm tập validate bổ sung, KHÔNG dùng làm nguồn hiệu chỉnh chính vì nhãn không đáng tin cậy |

**Bước bắt buộc:** vì các corpus trên gắn nhãn CEFR chứ không phải band IELTS trực tiếp, cần áp dụng **bảng quy đổi CEFR↔IELTS** đã công bố (Cambridge/British Council) để map nhãn trước khi fit:

```python
CEFR_TO_IELTS_BAND = {
    "A2": 3.5, "B1": 4.5, "B2": 6.0, "C1": 7.5, "C2": 8.5,
}
```

**Giới hạn cần ghi rõ trong báo cáo hiệu chỉnh:** đây là proxy, không phải nhãn IELTS thật — độ chính xác sẽ được tinh chỉnh tiếp bằng dữ liệu production thật (qua `TASK-024`) sau khi có đủ lượt hội thoại đã được người review chấm tay (khuyến nghị ≥500 lượt trước khi recalibrate lần 2).

### 0.3 Nguyên tắc bắt buộc: dùng chung code trích đặc trưng với production

**Sai lầm kinh điển cần tránh:** viết code tính WPM/pause_ratio/MTLD riêng cho script calibration, khác với code Tier 1 thật dùng khi chạy production → hiệu chỉnh xong nhưng số không khớp vì 2 nơi tính khác công thức.

```
app/scoring/features.py     <- module DUY NHẤT chứa compute_wpm(), compute_pause_ratio(),
                                compute_filler_density(), compute_mtld()
                                (chính là các hàm ở Spec 1 mục 1.3)

scripts/calibrate_thresholds.py   <- import từ app/scoring/features.py, KHÔNG viết lại
app/scoring/tier1_realtime.py     <- import từ app/scoring/features.py, KHÔNG viết lại
```

### 0.4 Pipeline hiệu chỉnh

```python
# scripts/calibrate_thresholds.py — pseudocode luồng chính

def calibrate():
    dataset = load_labeled_corpus()   # mỗi item: {audio, transcript, word_timestamps, cefr_label}
    dataset = [d for d in dataset if d.cefr_label in CEFR_TO_IELTS_BAND]
    for d in dataset:
        d.ielts_band_proxy = CEFR_TO_IELTS_BAND[d.cefr_label]
        d.features = {
            "wpm": compute_wpm(d.word_timestamps),
            "pause_ratio": compute_pause_ratio(d.word_timestamps),
            "filler_density": compute_filler_density(d.words),
            "mtld": compute_mtld(d.tokens),
        }

    train, val = train_test_split(dataset, test_size=0.2, stratify_by="ielts_band_proxy")

    anchors = {}
    for feature_name in ["wpm", "pause_ratio", "filler_density", "mtld"]:
        X = [d.features[feature_name] for d in train]
        y = [d.ielts_band_proxy for d in train]
        iso = IsotonicRegression(increasing=is_increasing_relationship(feature_name))  # WPM/MTLD tăng, pause/filler giảm
        iso.fit(X, y)
        # Lấy mẫu tại đúng 5 mốc band để khớp format piecewise-linear đang dùng ở Spec 1 (interpolate_band)
        anchors[feature_name] = [(b, float(iso.predict([sample_x_for_band(iso, b)])[0])) for b in [4.0, 5.5, 6.5, 7.5, 9.0]]

    mae = validate_on_holdout(anchors, val)
    write_config(anchors, mae, sample_size=len(dataset))
    write_report(mae, len(train), len(val))
```

### 0.5 Output artifact — config versioned, KHÔNG hardcode trong code

```json
// config/scoring_anchors.v1.json
{
  "version": "v1",
  "calibrated_from": "ICNALE Spoken + NICT JLE, mapped CEFR->IELTS proxy",
  "calibration_date": "2026-08-20",
  "sample_size": 842,
  "holdout_mae": 0.61,
  "status": "active",
  "anchors": {
    "wpm": [[4.0, 68.2], [5.5, 91.4], [6.5, 112.0], [7.5, 138.7], [9.0, 165.3]],
    "pause_ratio": [[4.0, 0.33], [5.5, 0.24], [6.5, 0.17], [7.5, 0.11], [9.0, 0.06]],
    "filler_density": [[4.0, 7.1], [5.5, 4.6], [6.5, 2.9], [7.5, 1.4], [9.0, 0.4]],
    "mtld": [[4.0, 33.5], [5.5, 52.0], [6.5, 68.9], [7.5, 87.2], [9.0, 108.6]]
  }
}
```

`app/scoring/tier1_realtime.py` (Spec 1) load anchors từ config này ở startup (hoặc hot-reload), **không import trực tiếp `WPM_ANCHORS = [...]` hardcode trong file .py nữa** — dòng code mẫu ở Spec 1 mục 1.4 chỉ là placeholder minh hoạ định dạng, thực tế phải đọc từ `config/scoring_anchors.v{active}.json`.

### 0.6 Kịch bản dự phòng nếu chưa kiếm được dữ liệu thật kịp deadline

Việc quan trọng nhất của task này **không phải là có ngay số liệu hoàn hảo**, mà là **dựng xong hạ tầng config versioned + hot-reload**. Nếu không kịp chạy calibration thật:

- Ship `config/scoring_anchors.v0.json` với `"calibrated_from": "expert_estimate_uncalibrated"` (dùng đúng số ở Spec 1 mục 1.4 làm giá trị tạm)
- Đảm bảo pipeline production đọc số từ file config này (không phải hardcode trong `.py`)
- Khi có dữ liệu thật, chỉ cần chạy lại `calibrate_thresholds.py`, sinh `v1.json`, đổi `"status": "active"` — **không redeploy code**

### 0.7 Acceptance Criteria

- [ ] `scripts/calibrate_thresholds.py` chạy được, import 100% hàm tính đặc trưng từ `app/scoring/features.py` (không viết lại riêng)
- [ ] Output đúng schema JSON versioned ở mục 0.5, kèm `calibration_report.md` có MAE trên tập validation
- [ ] `app/scoring/tier1_realtime.py` và `app/scoring/tier2_deep.py` đọc anchor points từ config, không hardcode
- [ ] Có cơ chế version + `"status": "active"` để chuyển đổi bộ config không cần redeploy
- [ ] Nếu ship `v0` (chưa hiệu chỉnh thật), phải gắn rõ `"calibrated_from": "expert_estimate_uncalibrated"` để không ai nhầm là số đã kiểm chứng

### 0.8 Test case biên bắt buộc

- [ ] Dataset input thiếu nhãn CEFR ở 1 số record → phải tự động loại bỏ record đó khỏi tập fit, không crash
- [ ] `IsotonicRegression` fit trên dữ liệu có tương quan NGƯỢC hướng kỳ vọng (vd do lỗi nhãn) → phải log cảnh báo rõ ràng thay vì âm thầm sinh anchor points vô nghĩa (band giảm khi WPM tăng)
- [ ] Load 2 file config cùng lúc (`v0` và `v1`) → hệ thống phải chỉ dùng đúng 1 bản có `"status": "active"`, không trộn lẫn
- [ ] Test round-trip: anchors sinh ra từ `calibrate_thresholds.py` phải load lại đúng bằng `interpolate_band()` ở Spec 1 mà không cần transform thêm — đảm bảo 2 bên khớp format tuyệt đối

---

## SPEC 1 — TASK-011: Tier 1 Real-Time Scorer

### 1.1 Làm rõ kiến trúc trước (điểm hay bị hiểu sai)

**Tier 1 KHÔNG tính `raw_score` đầy đủ 4 trục.** Vì Grammar (GRA) cần spaCy parser + Pronunciation (PRON) cần GOP score — cả hai đều quá chậm cho ngân sách <300ms. Tier 1 chỉ tính **2 trục proxy nhẹ** (Fluency, Lexical) để đưa ra tín hiệu tạm thời `difficulty_adjustment`, **không ghi đè `band_estimate_overall` chính thức trong DB**. Band chính thức chỉ được cập nhật bởi Tier 2 (xem Spec 4).

```
Tier 1 output = ephemeral signal, sống trong session cache (Redis/in-memory), KHÔNG persist vào user_profile
Tier 2 output = raw_score 4 trục đầy đủ → mới gọi EMA update vào user_profile (persist)
```

### 1.2 Input contract (precondition bắt buộc từ TASK-004)

```python
class WordTimestamp:
    word: str
    start_time: float   # giây, TÍNH TỪ ĐẦU AUDIO STREAM (session-relative), KHÔNG phải wall-clock nhận chunk
    end_time: float
    confidence: float   # 0.0-1.0, do ASR trả về

class TurnInput:
    words: list[WordTimestamp]   # đã sắp xếp theo thời gian, liên tục qua các chunk
    transcript: str
```

**Assertion bắt buộc ở đầu hàm** — nếu vi phạm, coi turn này là "insufficient_data", không tính điểm:
```python
assert all(words[i].end_time <= words[i+1].start_time for i in range(len(words)-1)), \
    "Timestamps không đơn điệu tăng — nghi ngờ lỗi offset giữa các chunk (xem TASK-004)"
```

### 1.3 Công thức từng tín hiệu

**(a) WPM (Words Per Minute)**
```
speech_duration_sec = words[-1].end_time - words[0].start_time
if speech_duration_sec <= 0: return INSUFFICIENT_DATA
wpm = (len(words) / speech_duration_sec) * 60
```

**(b) Pause ratio**
```
total_pause = sum(
    max(0, words[i+1].start_time - words[i].end_time)
    for i in range(len(words)-1)
    if (words[i+1].start_time - words[i].end_time) > 0.5   # ngưỡng pause đáng kể
)
pause_ratio = total_pause / speech_duration_sec
```

**(c) Filler density** — dùng lexicon cố định, KHÔNG heuristic tự do:
```python
FILLER_LEXICON = {"um", "uh", "umm", "erm", "hmm"}
# "well", "like", "you know" CHỦ Ý KHÔNG đưa vào — dễ false positive vì có nghĩa hợp lệ trong câu
filler_count = sum(1 for w in words if w.word.lower().strip(".,!?") in FILLER_LEXICON)
filler_density = (filler_count / len(words)) * 100   # trên 100 từ
```

**(d) Self-correction** — 2 tín hiệu độc lập, cộng dồn có trần:
```python
REPAIR_MARKERS = {"i mean", "sorry", "what i meant", "or rather", "actually no"}
repair_marker_hits = đếm số lần transcript chứa các cụm trên (case-insensitive substring match)

immediate_repetition_hits = đếm số cặp (words[i], words[i+1]) có words[i].word.lower() == words[i+1].word.lower()

self_correction_score = min(1.0, 0.5*repair_marker_hits + 0.3*immediate_repetition_hits)  # trần 1.0
```

**(e) MTLD (Measure of Textual Lexical Diversity)** — thuật toán đúng chuẩn, KHÔNG dùng TTR thô:

```python
def mtld(tokens: list[str], ttr_threshold: float = 0.72) -> float:
    """
    Thuật toán MTLD chuẩn (McCarthy & Jarvis 2010).
    Chạy 2 chiều (forward + backward) rồi lấy trung bình — bù trừ hiệu ứng vị trí.
    """
    def _mtld_one_direction(tokens):
        factor_count = 0
        types = set()
        token_count_in_factor = 0
        for token in tokens:
            types.add(token.lower())
            token_count_in_factor += 1
            ttr = len(types) / token_count_in_factor
            if ttr <= ttr_threshold:
                factor_count += 1
                types = set()
                token_count_in_factor = 0
        # phần dư cuối câu chưa đạt ngưỡng — tính factor riêng phần theo tỷ lệ
        if token_count_in_factor > 0:
            remaining_ttr = len(types) / token_count_in_factor
            partial_factor = (1 - remaining_ttr) / (1 - ttr_threshold) if remaining_ttr < 1 else 0
            factor_count += partial_factor
        return len(tokens) / factor_count if factor_count > 0 else len(tokens)  # tránh chia 0

    if len(tokens) < 10:
        return None  # MTLD không đáng tin với câu quá ngắn — trả None, không ép tính
    forward = _mtld_one_direction(tokens)
    backward = _mtld_one_direction(list(reversed(tokens)))
    return (forward + backward) / 2
```

**Unit test bắt buộc cho hàm này:** câu lặp toàn bộ 1 từ ("the the the the...") phải cho MTLD thấp gần với độ dài tối thiểu; câu không lặp từ nào (mọi từ unique) phải cho MTLD ≈ độ dài câu (vì không bao giờ đạt ngưỡng TTR 0.72 để cắt factor) — đây là 2 test case biên quan trọng nhất.

### 1.4 Map tín hiệu → band-equivalent proxy (nội suy tuyến tính, KHÔNG bucket rời rạc)

Lý do dùng nội suy thay vì if/elif cứng: khi có dữ liệu hiệu chỉnh thật từ TASK-010, chỉ cần sửa **anchor points**, không phải viết lại logic.

```python
# Anchor points mặc định — PHẢI được thay bằng giá trị thật sau khi chạy TASK-010 (calibration bootstrap)
# Đây là giá trị khởi tạo tạm, lấy tham khảo từ band_ladder trong Template A (Unit 1, Improve Your Skills IELTS)
WPM_ANCHORS = [(4.0, 70), (5.5, 95), (6.5, 115), (7.5, 140), (9.0, 170)]
PAUSE_RATIO_ANCHORS = [(4.0, 0.35), (5.5, 0.25), (6.5, 0.18), (7.5, 0.10), (9.0, 0.05)]  # tỷ lệ NGHỊCH: pause cao -> band thấp
FILLER_ANCHORS = [(4.0, 8.0), (5.5, 5.0), (6.5, 3.0), (7.5, 1.5), (9.0, 0.5)]  # per 100 từ, nghịch
MTLD_ANCHORS = [(4.0, 35), (5.5, 55), (6.5, 70), (7.5, 90), (9.0, 110)]

def interpolate_band(value: float, anchors: list[tuple[float, float]], inverse: bool = False) -> float:
    """anchors: [(band, metric_value), ...] tăng dần theo band.
    inverse=True nghĩa là metric càng THẤP thì band càng CAO (vd pause_ratio, filler)."""
    points = sorted(anchors, key=lambda x: x[1], reverse=inverse)
    bands = [p[0] for p in points]
    metrics = [p[1] for p in points]
    if inverse:
        metrics, bands = metrics[::-1], bands[::-1]
    if value <= metrics[0]:
        return bands[0]
    if value >= metrics[-1]:
        return bands[-1]
    for i in range(len(metrics) - 1):
        if metrics[i] <= value <= metrics[i+1]:
            ratio = (value - metrics[i]) / (metrics[i+1] - metrics[i])
            return bands[i] + ratio * (bands[i+1] - bands[i])
    return bands[-1]

fluency_proxy = (
    0.4 * interpolate_band(wpm, WPM_ANCHORS)
    + 0.3 * interpolate_band(pause_ratio, PAUSE_RATIO_ANCHORS, inverse=True)
    + 0.2 * interpolate_band(filler_density, FILLER_ANCHORS, inverse=True)
    + 0.1 * min(9.0, 6.0 + self_correction_score * 3.0)   # self-correction chỉ CỘNG điểm nhẹ, không phải trục chính
)

lexical_proxy = interpolate_band(mtld_value, MTLD_ANCHORS) if mtld_value is not None else fluency_proxy  # fallback nếu câu quá ngắn để tính MTLD

combined_proxy = 0.5 * fluency_proxy + 0.5 * lexical_proxy
```

### 1.5 Quyết định `difficulty_adjustment`

```python
def get_difficulty_signal(combined_proxy: float, current_official_band: float,
                           word_count: int, avg_asr_confidence: float) -> str:
    if word_count < 5 or avg_asr_confidence < 0.6:
        return "hold"   # không đủ tín hiệu — KHÔNG đoán, giữ nguyên

    delta = combined_proxy - current_official_band
    if delta >= 0.75:
        return "increase"
    if delta <= -0.75:
        return "decrease"
    return "hold"
```

Ngưỡng `0.75` là điểm khởi tạo tạm — cần backtest bằng dữ liệu thật (TASK-010/TASK-024) để xem có gây dao động quá nhạy (nhảy increase/decrease liên tục) hay quá trơ (không bao giờ đổi) không. **Test case bắt buộc:** giả lập 1 chuỗi 10 lượt dao động nhẹ quanh ngưỡng — đảm bảo không bị "flapping" (increase→decrease→increase liên tục), nếu có nên thêm hysteresis (băng đệm) — ví dụ cần vượt ngưỡng 2 lượt liên tiếp mới đổi signal.

### 1.6 Test case biên bắt buộc (checklist cho AI viết unit test)

- [ ] `words = []` (không nói gì) → phải trả `INSUFFICIENT_DATA`, không crash
- [ ] `words` chỉ có 1 từ → `speech_duration_sec = 0` → xử lý chia 0 an toàn
- [ ] Timestamps không đơn điệu (giả lập lỗi offset chunk) → raise/flag rõ ràng, không âm thầm tính sai
- [ ] Toàn bộ từ là filler ("um uh um uh") → filler_density phải ra đúng 100%, không tràn số
- [ ] `avg_asr_confidence = 0.59` (ngay dưới ngưỡng 0.6) → phải trả "hold"
- [ ] `avg_asr_confidence = 0.61` (ngay trên ngưỡng) + đủ điều kiện khác → phải tính bình thường
- [ ] Toàn bộ audio là pause > 0.5s (user im lặng giữa chừng rất lâu) → pause_ratio phải cap ở 1.0, không âm hoặc >1

---

## SPEC 2 — TASK-005 & TASK-015: RAG Retrieval Layer

### 2.1 Nguyên tắc bắt buộc: filter trong 1 câu SQL, KHÔNG lọc 2 pha ở Python

**Anti-pattern tuyệt đối tránh** (nguyên nhân gây trả về rỗng):
```python
# SAI — KHÔNG làm thế này
top_k = vector_search(query_embedding, k=10)          # lấy trước theo vector
filtered = [x for x in top_k if x.band in range and x.id not in exposed]  # lọc sau bằng Python
# Nếu top 10 vector đều trùng exposed history -> filtered = [] dù DB còn hàng nghìn record hợp lệ khác
```

**Đúng — 1 câu SQL duy nhất, filter trước, rank sau, trong cùng query:**

```sql
SELECT sd.id, sd.ai_line, sd.user_model_answer, sd.band_level,
       sd.embedding <-> %(query_embedding)s AS distance
FROM sample_dialogues sd
JOIN content_units cu ON sd.content_unit_id = cu.id
WHERE cu.topic_tags && %(topic_tags)s::text[]
  AND sd.band_level BETWEEN %(band_min)s AND %(band_max)s
  AND sd.id NOT IN (
      SELECT sample_dialogue_id FROM user_content_exposure
      WHERE user_id = %(user_id)s AND exposed_at > now() - interval '30 days'
  )
ORDER BY distance
LIMIT %(limit)s;
```

### 2.2 Cơ chế fallback cascade (bắt buộc — xử lý case query strict trả về quá ít)

```python
def retrieve_dialogues(user_id, topic_tags, band_min, band_max, query_embedding, limit=4) -> list:
    """Trả về tối thiểu 2 items nếu có thể. Nới lỏng điều kiện theo từng bậc, LOG mỗi lần nới lỏng."""

    stages = [
        {"exposure_days": 30, "band_pad": 0.0, "use_topic": True},
        {"exposure_days": 7,  "band_pad": 0.0, "use_topic": True},   # nới cửa sổ chống lặp trước
        {"exposure_days": 7,  "band_pad": 0.5, "use_topic": True},   # rồi mới nới band
        {"exposure_days": 0,  "band_pad": 0.5, "use_topic": False},  # cuối cùng bỏ topic filter, chỉ còn band + vector
    ]

    for i, stage in enumerate(stages):
        results = _run_query(
            user_id=user_id,
            topic_tags=topic_tags if stage["use_topic"] else None,
            band_min=band_min - stage["band_pad"],
            band_max=band_max + stage["band_pad"],
            exposure_window_days=stage["exposure_days"],
            query_embedding=query_embedding,
            limit=limit,
        )
        if len(results) >= 2:
            if i > 0:
                log.warning(f"Retrieval fallback stage {i} triggered — nội dung mỏng cho topic={topic_tags}, band={band_min}-{band_max}. Cần bổ sung content_units.")
            return results

    log.error(f"Retrieval fallback cạn kiệt — trả về rỗng cho user={user_id}, topic={topic_tags}")
    return []   # caller (prompt_constructor) PHẢI xử lý case rỗng — không giả định luôn có data
```

**Quan trọng:** log cảnh báo ở mỗi stage fallback không chỉ để debug — đây chính là **tín hiệu vận hành** cho biết Template DB đang thiếu nội dung ở band/topic nào, dùng để ưu tiên việc điền thêm template (liên hệ ngược lại TASK-003 admin CLI).

### 2.3 Lưu ý kỹ thuật pgvector (nguyên nhân latency >500ms hay gặp)

- Với pgvector bản cũ, filter WHERE (topic/band/NOT IN) có thể khiến planner **bỏ qua HNSW index** và full-scan nếu selectivity của filter quá cao/thấp không cân đối — luôn chạy `EXPLAIN ANALYZE` trên câu query thật với dữ liệu production-scale trước khi merge.
- Nếu dùng pgvector >= 0.7, có hỗ trợ iterative index scan cho trường hợp kết hợp WHERE + vector ORDER BY — cần set `SET hnsw.iterative_scan = relaxed_order;` ở session hoặc connection pool config, nếu không mặc định có thể fallback về exact scan chậm.
- Composite index bổ sung nên cân nhắc: `CREATE INDEX ON sample_dialogues (band_level) INCLUDE (content_unit_id);` để tăng tốc bước lọc band trước khi vào vector rank.

### 2.4 Điều chỉnh band window theo `difficulty_adjustment` (TASK-015)

```python
def compute_band_window(base_band: float, difficulty_signal: str) -> tuple[float, float]:
    if difficulty_signal == "increase":
        return (base_band, base_band + 1.5)      # chỉ lấy nội dung khó hơn hiện tại
    if difficulty_signal == "decrease":
        return (base_band - 1.5, base_band)       # chỉ lấy nội dung dễ hơn
    return (base_band - 0.5, base_band + 1.0)      # hold — cửa sổ mặc định, hơi lệch lên để khuyến khích thử thách nhẹ
```

### 2.5 Test case biên bắt buộc

- [ ] Topic hoàn toàn không có content_unit nào trong DB → phải rơi vào fallback stage cuối, không throw exception
- [ ] User đã "dùng hết" mọi sample_dialogue trong 30 ngày qua ở band/topic đó → phải tự nới exposure_days xuống 7 rồi 0
- [ ] `query_embedding` là vector toàn số 0 (edge case lỗi embedding upstream) → không crash, vẫn trả kết quả theo filter cứng (band/topic), chỉ ranking ngẫu nhiên/không đáng tin — nên log warning riêng
- [ ] Đo latency với >100k rows trong `sample_dialogues` — assert < 500ms ở p95, không chỉ test với DB rỗng/nhỏ

---

## SPEC 3 — TASK-004: Streaming ASR Chunk Timestamp Offset

### 3.1 Nguyên tắc cốt lõi

**Offset phải tính từ số sample audio, KHÔNG từ thời điểm server nhận chunk (wall-clock).** Đây chính là bug gốc gây lệch toàn bộ Fluency/Pronunciation.

```python
class StreamingSessionState:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.cumulative_offset_sec: float = 0.0
        self.all_words: list[WordTimestamp] = []

    def process_chunk(self, audio_chunk: np.ndarray, asr_result: ASRChunkResult):
        """asr_result.words có timestamp CỤC BỘ trong chunk này (bắt đầu từ 0.0)."""
        chunk_duration_sec = len(audio_chunk) / self.sample_rate   # TÍNH TỪ SỐ SAMPLE, không phải time.time()

        for w in asr_result.words:
            global_word = WordTimestamp(
                word=w.word,
                start_time=w.start_time + self.cumulative_offset_sec,
                end_time=w.end_time + self.cumulative_offset_sec,
                confidence=w.confidence,
            )
            self.all_words.append(global_word)

        self.cumulative_offset_sec += chunk_duration_sec   # cộng dồn SAU khi map xong từ của chunk hiện tại
```

### 3.2 Xử lý từ bị cắt đôi ở ranh giới chunk

Nếu chunk cắt cứng theo thời gian cố định (vd mỗi 3 giây) mà không theo silence, một từ có thể bị cắt làm đôi giữa 2 chunk, ASR nhận diện sai ở cả 2 phía.

**Giải pháp: overlap window + de-dup theo thời gian.**
```python
OVERLAP_SEC = 0.3   # mỗi chunk mới include thêm 0.3s audio cuối của chunk trước

def process_chunk_with_overlap(self, audio_chunk, asr_result):
    # asr_result đã chạy trên audio_chunk CÓ overlap phía đầu
    # -> loại bỏ các từ có start_time (cục bộ) < OVERLAP_SEC nếu từ đó đã được ghi nhận ở lần xử lý chunk trước
    new_words = [w for w in asr_result.words if w.start_time >= OVERLAP_SEC or self._is_new_word(w)]
    ...
```

Khuyến nghị thực dụng hơn cho MVP: **dùng VAD (Voice Activity Detection, vd webrtcvad hoặc Silero VAD) để cắt chunk theo khoảng lặng tự nhiên** thay vì cắt cứng theo thời gian — tránh hẳn vấn đề cắt đôi từ, đơn giản hơn nhiều so với logic overlap/de-dup. Nên ưu tiên hướng này cho v1, chỉ làm overlap logic nếu bắt buộc dùng fixed-size chunk vì lý do hạ tầng khác.

### 3.3 Test case biên bắt buộc

- [ ] 3 chunk liên tiếp, mỗi chunk có audio_chunk độ dài khác nhau (không đều) → assert `cumulative_offset_sec` cộng dồn đúng bằng tổng số sample/sample_rate, không lệch
- [ ] Giả lập network delay giữa lúc client gửi và server nhận chunk (mock `time.sleep` ngẫu nhiên trước khi gọi `process_chunk`) → assert kết quả offset **không đổi** dù độ trễ mạng thay đổi (chứng minh offset không phụ thuộc wall-clock)
- [ ] Chunk rỗng (silence hoàn toàn, VAD không phát hiện từ nào) → `cumulative_offset_sec` vẫn phải cộng đúng chunk_duration, không bị bỏ qua
- [ ] So sánh tổng `cumulative_offset_sec` cuối session với độ dài audio file gốc ghép lại (nếu test bằng file .wav giả lập streaming) → phải khớp trong sai số < 10ms

---

## SPEC 4 — TASK-013: EMA Band Smoothing + Confidence Weighting

### 4.1 Làm rõ: ai gọi hàm này, khi nào (điểm hay bị nhầm)

`update_band()` chỉ được gọi bởi **Tier 2** (mỗi 5-10 lượt), dùng `raw_score` đầy đủ 4 trục. Tier 1 (mỗi lượt) chỉ update session-level `difficulty_signal` tạm thời (Redis/cache), **không gọi hàm EMA này**.

### 4.2 Công thức alpha động (confidence weighting)

```python
def compute_effective_alpha(base_alpha: float, word_count: int, avg_asr_confidence: float) -> float:
    # Factor 1: độ dài câu trả lời — câu quá ngắn không đủ tín hiệu ngôn ngữ để đánh giá
    if word_count < 5:
        word_count_factor = 0.0
    elif word_count < 10:
        word_count_factor = (word_count - 5) / 5      # nội suy tuyến tính 0->1 trong khoảng 5-10 từ
    else:
        word_count_factor = 1.0

    # Factor 2: độ tin cậy ASR — audio nhiễu thì transcript không đáng tin để chấm
    if avg_asr_confidence < 0.6:
        confidence_factor = 0.0
    else:
        confidence_factor = min(1.0, (avg_asr_confidence - 0.6) / 0.35)   # 0.6->0, 0.95+->1.0

    effective_alpha = base_alpha * word_count_factor * confidence_factor
    return effective_alpha
```

### 4.3 Update function với clamp + chống "đứng hình" band vĩnh viễn

```python
BAND_MIN, BAND_MAX = 4.0, 9.0

def update_band(user_id: str, raw_score: float, word_count: int, avg_asr_confidence: float,
                 base_alpha: float, consecutive_skip_count: int) -> dict:
    old_band = get_current_band(user_id)   # từ user_profile

    effective_alpha = compute_effective_alpha(base_alpha, word_count, avg_asr_confidence)

    # Chống đứng hình: nếu bị skip (alpha=0) quá nhiều lượt liên tiếp, ép một sàn alpha nhỏ
    # để band vẫn có thể dịch chuyển chậm thay vì đóng băng vô thời hạn
    MAX_CONSECUTIVE_SKIPS = 5
    FLOOR_ALPHA = 0.05
    if effective_alpha == 0.0 and consecutive_skip_count >= MAX_CONSECUTIVE_SKIPS:
        effective_alpha = FLOOR_ALPHA
        log.info(f"user={user_id}: ép floor_alpha sau {consecutive_skip_count} lượt bị skip liên tiếp")

    if effective_alpha == 0.0:
        return {
            "new_band": old_band,
            "updated": False,
            "reason": "insufficient_confidence",
            "consecutive_skip_count": consecutive_skip_count + 1,
        }

    raw_score_clamped = max(BAND_MIN, min(BAND_MAX, raw_score))
    new_band = old_band * (1 - effective_alpha) + raw_score_clamped * effective_alpha
    new_band = max(BAND_MIN, min(BAND_MAX, new_band))   # clamp lần cuối, phòng lỗi số học

    persist_band(user_id, new_band)
    return {
        "new_band": new_band,
        "updated": True,
        "effective_alpha": effective_alpha,
        "consecutive_skip_count": 0,   # reset counter vì lượt này đã update thành công
    }
```

### 4.4 Test case biên bắt buộc

- [ ] `word_count = 4` → `effective_alpha` phải = 0 tuyệt đối, band không đổi dù `raw_score` là giá trị cực đoan (vd 9.0 hoặc 0.0)
- [ ] `word_count = 7, avg_asr_confidence = 0.75` → `effective_alpha` phải nằm trong khoảng (0, base_alpha), không phải giá trị nhị phân 0/base_alpha
- [ ] `raw_score = 15.0` (giá trị lỗi ngoài thang) → phải bị clamp về `BAND_MAX=9.0` trước khi đưa vào công thức EMA, không làm band vọt ra ngoài [4,9]
- [ ] Giả lập 6 lượt liên tiếp đều có `word_count < 5` → lượt thứ 6 (vượt `MAX_CONSECUTIVE_SKIPS=5`) phải kích hoạt `FLOOR_ALPHA`, band phải nhích nhẹ thay vì đứng yên tuyệt đối
- [ ] `old_band = 4.0` (biên dưới), `raw_score = 0.0` (giả lập lỗi) → `new_band` sau clamp không được nhỏ hơn `BAND_MIN=4.0`

---

## SPEC 5 — TASK-023: Data Flywheel — 3-Layer Safety Filter

### 5.1 Nguyên tắc bắt buộc: KHÔNG insert trực tiếp, luôn qua staging + human/secondary-AI review

```sql
CREATE TABLE harvest_review_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  candidate_ai_line TEXT NOT NULL,
  candidate_user_answer TEXT NOT NULL,
  source_user_id UUID NOT NULL,          -- để truy vết, KHÔNG lưu vào sample_dialogues cuối cùng
  source_turn_id UUID NOT NULL,
  tier2_scores JSONB NOT NULL,           -- {fluency, lexical, grammar, pronunciation}
  pii_check_passed BOOLEAN NOT NULL,
  pii_entities_found TEXT[],             -- log lại loại entity phát hiện, để audit
  dedup_max_similarity FLOAT,
  dedup_status TEXT CHECK (dedup_status IN ('unique','similar_variant','duplicate_rejected')),
  review_status TEXT DEFAULT 'pending' CHECK (review_status IN ('pending','approved','rejected')),
  reviewed_by TEXT,                       -- 'human:<id>' hoặc 'llm_judge:<model>'
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### 5.2 Layer 1 — PII Scrubbing (chính sách: REJECT, không cố redact)

**Quyết định thiết kế quan trọng:** thay vì cố "làm sạch" (thay tên bằng [NAME]) rồi vẫn giữ câu, chính sách mặc định là **loại bỏ hoàn toàn** candidate nếu phát hiện PII — vì redact tự động dễ sót (biệt danh, địa danh nhỏ không nằm trong NER model) và rủi ro giữ lại 1 câu rò rỉ còn tệ hơn mất 1 mẫu dữ liệu tốt.

```python
import spacy
nlp = spacy.load("en_core_web_trf")   # dùng bản transformer, chính xác hơn en_core_web_sm cho NER

PII_ENTITY_TYPES = {"PERSON", "GPE", "ORG", "FAC", "NORP"}  # tên người, địa danh, tổ chức, cơ sở, quốc tịch/tôn giáo
PHONE_REGEX = r'(\+?\d[\d\-\s]{7,}\d)'
EMAIL_REGEX = r'[\w\.-]+@[\w\.-]+\.\w+'

def check_pii(text: str) -> tuple[bool, list[str]]:
    """Trả về (passed: bool, entities_found: list[str]).
    passed=False nếu phát hiện BẤT KỲ PII nào -> reject toàn bộ candidate."""
    doc = nlp(text)
    found = [f"{ent.label_}:{ent.text}" for ent in doc.ents if ent.label_ in PII_ENTITY_TYPES]

    if re.search(PHONE_REGEX, text):
        found.append("PHONE_PATTERN")
    if re.search(EMAIL_REGEX, text):
        found.append("EMAIL_PATTERN")

    return (len(found) == 0, found)
```

**Lưu ý quan trọng:** NER có thể nhầm tên địa danh/người trong câu chuyện *hư cấu* mà user kể (vd "I once met someone called Tom") thành PII thật — đây là **false positive chấp nhận được** theo đúng nguyên tắc "thà loại nhầm còn hơn giữ sót". Không cố tinh chỉnh model để giảm false positive bằng cách nới lỏng ngưỡng.

### 5.3 Layer 2 — Grammar & Lexical Verification (chống ASR nhận nhầm câu nói bồi)

```python
MIN_AXIS_SCORE = 7.0     # MỌI trục đều phải đạt tối thiểu — không cho phép 1 trục kém được bù bởi trục khác cao
MIN_AVERAGE_SCORE = 7.5
MIN_ASR_CONFIDENCE = 0.85   # cao hơn ngưỡng dùng cho scoring thường (0.6) — vì đây là ngưỡng để LÀM MẪU, không phải chỉ để chấm điểm user

def check_quality(tier2_scores: dict, avg_asr_confidence: float) -> bool:
    axes = [tier2_scores["fluency"], tier2_scores["lexical"],
            tier2_scores["grammar"], tier2_scores["pronunciation"]]

    if avg_asr_confidence < MIN_ASR_CONFIDENCE:
        return False   # ASR không chắc chắn -> không tin transcript, dù điểm có cao

    if min(axes) < MIN_AXIS_SCORE:
        return False   # có trục yếu -> không đạt chuẩn "mẫu band cao toàn diện"

    if sum(axes) / len(axes) < MIN_AVERAGE_SCORE:
        return False

    return True
```

### 5.4 Layer 3 — Vector Deduplication

```python
DUPLICATE_THRESHOLD = 0.92     # quá giống -> loại, không thêm giá trị
SIMILAR_VARIANT_THRESHOLD = 0.75   # giống vừa -> vẫn giữ nhưng đánh dấu, ưu tiên thấp hơn hàng "unique"

def check_dedup(candidate_embedding: list[float]) -> tuple[str, float]:
    max_sim = query_max_cosine_similarity(candidate_embedding, table="sample_dialogues")
    if max_sim >= DUPLICATE_THRESHOLD:
        return ("duplicate_rejected", max_sim)
    if max_sim >= SIMILAR_VARIANT_THRESHOLD:
        return ("similar_variant", max_sim)
    return ("unique", max_sim)
```

```sql
-- Query hỗ trợ check_dedup — tìm điểm gần nhất trong toàn bộ sample_dialogues hiện có
SELECT 1 - (embedding <=> %(candidate_embedding)s) AS similarity
FROM sample_dialogues
ORDER BY embedding <=> %(candidate_embedding)s
LIMIT 1;
```

### 5.5 Rate cap chống vòng lặp thiên lệch (feedback loop bias)

```python
MAX_AUTO_HARVEST_PER_TOPIC_PER_WEEK = 10

def check_rate_cap(topic_tag: str) -> bool:
    count_this_week = count_harvested_this_week(topic_tag)
    return count_this_week < MAX_AUTO_HARVEST_PER_TOPIC_PER_WEEK
```

Không có rate cap, topic phổ biến nhất (vd "daily routine") sẽ áp đảo Template DB theo thời gian, trong khi topic ít user chọn (vd "arts and sciences") mãi mãi không được làm giàu — làm lệch cân bằng nội dung ban đầu.

### 5.6 Pipeline tổng hợp (thứ tự bắt buộc — dừng sớm nếu fail bất kỳ layer nào)

```python
def harvest_candidate(turn_data: TurnData) -> str:
    """Trả về status cuối: 'queued_for_review' | 'rejected_pii' | 'rejected_quality' | 'rejected_duplicate' | 'rejected_rate_cap'."""

    # Layer 2 trước Layer 1 hay ngược lại? -> PII PHẢI kiểm tra ĐẦU TIÊN,
    # vì nếu để lọt qua layer khác trước rồi mới check PII, dữ liệu PII vẫn có thể
    # bị log/cache tạm ở các bước trung gian (rủi ro rò rỉ dù cuối cùng bị reject)
    pii_passed, pii_entities = check_pii(turn_data.user_transcript)
    if not pii_passed:
        log_rejection(turn_data, reason="pii", entities=pii_entities)
        return "rejected_pii"

    if not check_rate_cap(turn_data.topic_tag):
        return "rejected_rate_cap"

    if not check_quality(turn_data.tier2_scores, turn_data.avg_asr_confidence):
        return "rejected_quality"

    embedding = embed(turn_data.user_transcript)
    dedup_status, max_sim = check_dedup(embedding)
    if dedup_status == "duplicate_rejected":
        return "rejected_duplicate"

    insert_into_review_queue(turn_data, pii_entities, dedup_status, max_sim)
    return "queued_for_review"
```

### 5.7 Test case biên bắt buộc

- [ ] Câu chứa tên riêng hư cấu trong câu chuyện kể (không phải PII thật của user) → vẫn phải bị reject (false positive chấp nhận được theo policy — test này xác nhận policy, không phải bug)
- [ ] `tier2_scores = {fluency: 9.0, lexical: 9.0, grammar: 9.0, pronunciation: 5.0}` (1 trục thấp, trung bình vẫn cao) → phải reject vì `min(axes) < MIN_AXIS_SCORE`, dù trung bình đạt
- [ ] Candidate giống hệt (similarity ~1.0) 1 sample đã có sẵn từ sách gốc → phải `duplicate_rejected`, không được ghi đè/trùng lặp dữ liệu gốc
- [ ] Topic đã đạt `MAX_AUTO_HARVEST_PER_TOPIC_PER_WEEK` → candidate tiếp theo dù chất lượng tốt vẫn phải bị chặn ở rate cap, KHÔNG bỏ qua bước này
- [ ] Toàn bộ pipeline chạy trên 1 candidate hợp lệ 100% → phải kết thúc ở `queued_for_review`, TUYỆT ĐỐI không có đường nào insert thẳng vào `sample_dialogues` mà bỏ qua bảng `harvest_review_queue`