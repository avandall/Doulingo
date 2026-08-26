# Tổng hợp Data cần chuẩn bị cho hệ thống Speaking AI theo Level

Có 6 tập dữ liệu chính. Mỗi tập phục vụ một mục đích khác nhau trong pipeline (retrieval, simplification, level detection, persona).

---

## 1. Vocabulary Bank theo CEFR Level

**Mục đích:** dùng để lọc/kiểm tra từ vựng AI dùng có đúng level không (simplifier ở bước post-processing).

**Nguồn gợi ý:** Cambridge English Vocabulary Profile (EVP), Oxford 3000/5000, CEFR-J Wordlist.

**Schema:**

| Trường | Kiểu | Ví dụ | Ghi chú |
|---|---|---|---|
| `word` | string | "happy" | dạng gốc (lemma) |
| `pos` | string | "adjective" | từ loại |
| `cefr_level` | enum | A1 | A1/A2/B1/B2/C1/C2 |
| `synonyms_lower_tier` | array | ["good", "nice"] | từ đồng nghĩa ở level thấp hơn, dùng khi cần hạ cấp |
| `synonyms_higher_tier` | array | ["delighted", "content"] | dùng khi cần nâng cấp cho level cao |
| `example_sentence` | string | "She is happy today." | câu ví dụ chuẩn ở đúng level |
| `topic_tags` | array | ["emotion", "daily_life"] | để lọc theo chủ đề |

**Kích thước cần có:** tối thiểu 800–1500 từ mỗi level A1–B1 (đủ dùng), B2 trở lên có thể ít hơn vì app speaking thường tập trung A1–B1.

---

## 2. Grammar Structure Bank theo Level

**Mục đích:** định nghĩa cấu trúc ngữ pháp được phép dùng ở mỗi level — thay thế cho rule cứng kiểu "chỉ Present Simple".

**Schema:**

| Trường | Kiểu | Ví dụ |
|---|---|---|
| `level` | enum | A1 |
| `structure_name` | string | "Present Simple – affirmative" |
| `pattern` | string | "S + V(s/es) + O" |
| `allowed` | boolean | true |
| `example` | string | "I go to school." |
| `max_clauses_per_sentence` | int | 1 |

**Lưu ý:** đừng liệt kê theo kiểu cấm/cho phép tuyệt đối — nên có 2 cột `introduced_at_level` (lần đầu xuất hiện) và `mastered_at_level` (được dùng tự do), vì thực tế người học vẫn hiểu passive câu đơn giản dù chưa "học" cấu trúc đó chính thức.

---

## 3. Sample Dialogue Bank (Exemplar Bank cho RAG)

**Mục đích:** ngân hàng câu mẫu để retrieval động, đảm bảo AI bám đúng "giọng" tự nhiên + đúng level + đúng persona.

**Schema:**

| Trường | Kiểu | Ví dụ |
|---|---|---|
| `id` | string | "ex_00231" |
| `level` | enum | 1 (hoặc CEFR nếu bạn map lại) |
| `persona` | string | "Alex" |
| `persona_trait` | string | "friendly, warm" |
| `topic` | string | "greeting" |
| `dialogue_act` | enum | greeting / follow_up_question / empathy_response / topic_transition / clarification / closing |
| `user_input_context` | string | "Hello how are you" | câu/ý mà user vừa nói trước đó |
| `ai_response` | string | "Hi there! I am doing good today. How are you feeling today?" |
| `word_count` | int | 12 |
| `reviewed_by` | string | "teacher_id_04" |
| `quality_score` | float | 4.8 | điểm đánh giá tự nhiên (do giáo viên chấm 1-5) |
| `embedding_vector` | vector | [đã tính sẵn khi index] |

**Số lượng cần có:** khoảng 15–30 mẫu cho mỗi tổ hợp (level × dialogue_act), nhân với 9 persona → ước tính vài nghìn dòng cho toàn hệ thống. Không cần làm hết 1 lần — có thể build dần theo topic phổ biến nhất trước (greeting, small talk, feelings, daily routine).

---

## 4. Persona / Character Definition Data

**Mục đích:** tách rõ "chất giọng" nhân vật khỏi ràng buộc level, để dev áp dụng nhất quán cho toàn bộ 9 nhân vật thay vì sửa từng file riêng.

**Schema:**

| Trường | Kiểu | Ví dụ |
|---|---|---|
| `persona_id` | string | "alex" |
| `name` | string | "Alex" |
| `personality_summary` | string | "Ấm áp, kiên nhẫn, hay khích lệ" |
| `speech_style_notes` | string | "Dùng câu hỏi mở, ít mỉa mai, hay khen ngợi" |
| `sample_phrases` | array | ["That's great!", "Tell me more about..."] | các cụm từ đặc trưng, KHÔNG ràng buộc theo level |
| `avoid_phrases` | array | [] | tránh lặp/tránh phong cách không hợp |

---

## 5. CEFR Level Classifier Training Data (nếu làm Adaptive Level Detection)

**Mục đích:** huấn luyện/đánh giá mô hình đo trình độ user dựa trên transcript nói thật (không phải level user tự chọn).

**Schema:**

| Trường | Kiểu | Ví dụ |
|---|---|---|
| `transcript_text` | string | câu user nói (từ ASR) |
| `cefr_label` | enum | A2 | do giáo viên gắn nhãn tay |
| `error_type_tags` | array | ["tense_error", "word_order"] |
| `sentence_length` | int | |
| `vocab_tier_used` | enum | cao nhất trong câu |
| `fluency_notes` | string | optional, nếu có audio đánh giá |

**Nguồn:** dataset công khai như **CEFR-SP**, **EFCAMDAT** (xin quyền academic), hoặc tự thu thập từ chính người dùng app hiện tại (nếu đã có transcript + để giáo viên gắn nhãn lại một phần làm gold-set).

---

## 6. Topic / Scenario Bank

**Mục đích:** thay thế "Scenario Angles" ngẫu nhiên hiện tại bằng dữ liệu có cấu trúc, biết khi nào nên ép kịch bản, khi nào để tự do.

**Schema:**

| Trường | Kiểu | Ví dụ |
|---|---|---|
| `topic_id` | string | "hello_how_are_you" |
| `topic_type` | enum | free_conversation / structured_scenario |
| `force_scenario_angle` | boolean | false | true nếu là topic dạng nhập vai (order food, phỏng vấn...) |
| `mandatory_vocab` | array | [] | chỉ điền nếu topic yêu cầu từ vựng bắt buộc |
| `suitable_levels` | array | [1,2,3] | topic nào dùng được cho level nào |

---

## Tổng kết mối liên hệ giữa các bảng

```
User nói → ASR transcript
              │
              ▼
   [5] Level Classifier ── xác định level thực tế
              │
              ▼
   [6] Topic Bank ── xác định có ép scenario không
              │
              ▼
   [3] Dialogue Bank (RAG) ── retrieve câu mẫu phù hợp
              │         (lọc theo level + persona + dialogue_act)
              ▼
   [4] Persona Data ── áp giọng nhân vật
              │
              ▼
        LLM sinh câu trả lời (Pass 1 - tự nhiên)
              │
              ▼
   [1] Vocabulary Bank + [2] Grammar Bank ── kiểm tra/simplify (Pass 2 hoặc rule-based)
              │
              ▼
        Câu trả lời cuối cùng
```

## Ưu tiên triển khai (nếu làm dần theo giai đoạn)

1. **Giai đoạn 1 (bắt buộc, làm trước):** Bảng 1 (Vocabulary) + Bảng 3 (Dialogue Bank cho topic phổ biến nhất) — đây là 2 bảng có tác động trực tiếp và nhanh nhất đến chất lượng câu trả lời hiện tại.
2. **Giai đoạn 2:** Bảng 4 (Persona) + Bảng 6 (Topic) — dọn kiến trúc, áp dụng đồng bộ 9 nhân vật.
3. **Giai đoạn 3 (đầu tư dài hạn):** Bảng 2 (Grammar) + Bảng 5 (Level Classifier) — cần nhiều công sức gắn nhãn hơn, nên làm sau khi đã ổn định 2 giai đoạn trên.