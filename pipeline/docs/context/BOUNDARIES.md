# BOUNDARIES
# Giới hạn quyền hạn — Những gì AI được và không được làm

> **Trạng thái:** CONTEXT (Active) | **Cập nhật:** 2026-09-09
>
> ✏️ **HUMAN & ARCHITECT REWRITE (v2.0 Post-Review).** File này là "hợp đồng" ranh giới kỹ thuật bất biến giữa Human và AI Agent trong sáng kiến nâng cấp Constrained Decoding, Prompt Caching và WebAssembly.

---

## 1. Phạm vi Tệp tin (File Scope)

### ✅ AI được phép tạo mới và chỉnh sửa:
```
app/core/schemas.py                      # [TẠO MỚI] Khai báo các Pydantic Schemas & to_strict_json_schema
app/core/ai_engine.py                    # [CHỈNH SỬA] Tích hợp responseSchema, strict mode, token budget 2048
app/rag/prompt_constructor.py            # [CHỈNH SỬA] Tách Static Prefix (~1,200 tokens) và Dynamic Suffix
app/scoring/tier1_realtime.py            # [CHỈNH SỬA] Tiếp nhận và kẹp ngưỡng acoustic signals từ Client VAD
app/scoring/tier2_deep.py                # [CHỈNH SỬA] Chuẩn hóa output qua Pydantic schema
scripts/build_vocab_wasm_db.py           # [TẠO MỚI] Offline script trích xuất SQLite vocab core
static/js/speech.js                      # [CHỈNH SỬA] Nhúng Audio State Machine & Silero VAD WASM
static/js/dict_wasm.js                   # [TẠO MỚI] Client-side SQLite WASM dictionary loader & query
static/data/vocab_core.sqlite            # [TẠO MỚI] File SQLite từ điển nén phục vụ RAM client
static/wasm/**                           # [TẠO MỚI] Thư mục chứa binaries WASM (silero_vad.wasm, sqlite3.wasm)
tests/**                                 # [TẠO MỚI/SỬA] Bộ test suite cho Schemas, Caching và VAD logic
pipeline/docs/context/Tasks_list.md      # [CẬP NHẬT] Trạng thái thực thi các tasks
pipeline/docs/runtime/**                 # [GHI CHÉP] Logs, plans, debate notes của harness loop
```

### ❌ AI TUYỆT ĐỐI KHÔNG được đụng vào:
```
.env                                     # API keys và credentials sản xuất
pipeline/docs/core/**                    # Hiến pháp và giao thức cốt lõi của Harness
pipeline/engine/**                       # Mã nguồn thực thi Ralph loop
data/custom_topics.db                    # Không được DROP hay làm hỏng dữ liệu chủ đề hiện có
app/api/routers/reports_router.py        # Module xuất PDF đã hoàn thiện từ trước
```

---

## 2. Quy Tắc Kỹ Thuật Bắt Buộc (Inviolable Technical Guardrails)

### 2.1. Đối với Constrained Decoding
- **Single Source of Truth:** 100% schema bắt buộc phải sinh ra từ `pydantic.BaseModel` và đi qua hàm `to_strict_json_schema(model)` trước khi gửi sang OpenAI/Groq (phải bao gồm `$defs` traversal và nullable conversion).
- **Zero Raw JSON Slicing:** Cấm tái sử dụng logic cắt chuỗi ````json ... ```` hoặc tìm kiếm `{` `}` bằng regex một khi provider đã bật Strict Schema.
- **Failover on Truncation:** Nếu model bị chạm trần token (`finish_reason == "length"`) hoặc văng `ValidationError`, hệ thống phải xem đó là lỗi provider và tự động chuyển sang provider kế tiếp trong Pool.

### 2.2. Đối với Prompt Caching
- **Ngưỡng Token Caching:** Static Prefix được giữ ở mức $\approx 1,200$ tokens. Cam kết TTFT $< 400\text{ms}$ chỉ áp dụng trên Groq/OpenAI (hỗ trợ cache từ 1,024 tokens). Không nhồi 32k tokens vào Gemini.
- **Tính Bất Biến (Immutability):** Góc tiếp cận tình huống (`scenario_angle`) phải được chọn duy nhất 1 lần tại `start_roleplay_greeting` và cố định trong Static Prefix của session đó. Tuyệt đối không sinh góc mới ở giữa các turn.

### 2.3. Đối với WebAssembly (WASM) & Audio
- **Acoustic-Only Decoupling:** VAD client chỉ đo lường thời lượng âm học (`accumulated_voiced_duration_ms >= 1500`), không phụ thuộc vào bộ đếm từ của Web Speech API để quyết định đóng micro.
- **No Hot-Swapping Audio Stream:** Chuyển đổi engine thu âm sang WASM AudioWorklet **CHỈ ĐƯỢC PHÉP THỰC HIỆN KHI `MIC_STATE == "IDLE"`**. Cấm thay đổi `AudioContext` khi micro đang ghi âm.
### 2.4. Đối với Execution & Verification Engine (Timeout & Task Isolation Protection)
- **Foreground Synchronous Execution Only:** Cấm chạy `python3 pipeline/scripts/verify.py` hoặc các công cụ kiểm thử chất lượng dưới dạng task chạy ngầm (`run_command` async background job). Mọi lệnh kiểm thử phải chạy đồng bộ (synchronous foreground) để thu về kết quả tức thì.
- **Strict Target Scoping:** Trong quá trình coding liên tục (iterative steps), bắt buộc sử dụng `--quick` hoặc `--test-target tests/test_xxx.py` để đảm bảo thời gian thực thi $< 60\text{s}$, tránh làm treo runner hoặc timeout giao tiếp (`Error: timeout waiting for response`).

---

## 3. Quyền Hạn Git & Commit

- **1 Task = 1 Commit:** Chỉ commit khi task đã đạt trạng thái `[x] DONE` và toàn bộ bài test tương ứng pass 100%.
- **Thực thi trong WSL:** Mọi lệnh Git bắt buộc phải chạy qua WSL theo đúng quy định toàn cục của môi trường (`wsl git -C /home/avandall/project/Doulingo ...`).
- **Clean Working Tree:** Dọn sạch các file nháp tạm thời trước khi kết thúc task.
