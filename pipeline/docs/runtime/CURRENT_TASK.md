# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** RUNTIME (Auto-Generated / Synced) | **Cập nhật:** 2026-09-09 23:45

---

## 🎯 Task Spec: TASK-004
### 📌 TASK-004: Tích Hợp Silero VAD WASM Âm Học & Audio Engine State Machine

#### Metadata
```
Task ID:         TASK-004
Task Name:       Tích Hợp Silero VAD WASM Âm Học & Audio Engine State Machine
Phase:           Phase 3 (WebAssembly Client)
Task Type:       feat
Priority:        P1-Normal
Trạng thái:      [/] IN_PROGRESS
Ngày tạo:        2026-09-09
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Khắc phục tình trạng micro tự ngắt khi học viên ngập ngừng bằng mô hình âm học VAD thuần túy, loại bỏ sự phụ thuộc vào đếm từ của Web Speech API, và chống xung đột mic trên iOS.
- **What:**
  1. Xây dựng State Machine trong `static/js/speech.js`: `LEGACY_FALLBACK` -> `WASM_LOADING` -> `WASM_STAGED` -> `WASM_ACTIVE` (chỉ chuyển trạng thái khi `MIC_STATE == "IDLE"`).
  2. Tích lũy biến `accumulated_voiced_duration_ms` trong AudioWorklet. Tại $t_{\text{silence}} \ge 3.5\text{s}$:
     - Nếu $\ge 1500\text{ms}$: Tự động đóng mic và gửi request.
     - Nếu $< 1500\text{ms}$: Reset trạng thái, không đóng mic.
  3. Tại backend `app/scoring/tier1_realtime.py`: Thêm Pydantic clamping cho `AcousticMetricsInput` (kẹp `pause_duration_ms <= 60000`, `wpm <= 350`) và fallback về STT timestamps nếu dữ liệu client out-of-bounds.

#### Acceptance Criteria
- [ ] Audio Engine State Machine không bao giờ hot-swap AudioWorklet khi mic đang ở trạng thái RECORDING.
- [ ] Tự động gửi câu trả lời khi khoảng lặng $\ge 3.5\text{s}$ VÀ tổng thời lượng giọng nói $\ge 1.5\text{s}$.
- [ ] Backend kẹp ngưỡng an toàn, không bị crash bởi dữ liệu âm học bất thường.

#### Scope
- **Files được sửa/tạo:** `static/js/speech.js`, `app/scoring/tier1_realtime.py`, `tests/test_tier1_realtime.py`

#### Verification Commands
```bash
python3 pipeline/scripts/verify.py --quick
```

