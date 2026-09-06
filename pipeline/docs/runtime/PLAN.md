# TASK EXECUTION PLAN
# Task TASK-004: Xây dựng Cron Job Tự động Dọn dẹp Audio Cache

> **Trạng thái:** COMPLETED | **Ngày:** 2026-09-07

---

## 🎯 Task Goal
Tạo scheduled cron job `cleanup-audio-cache` (chạy định kỳ qua Inngest `inngest.TriggerCron(cron="0 3 * * *")` hoặc function service) để quét và dọn dẹp các file audio tạm thời trong thư mục cache/temp có thời gian tạo > 24 giờ:
1. Thư mục audio cache/temp rỗng hoặc chưa tồn tại không làm crash server.
2. Chỉ xóa các file audio cũ hơn 24 giờ (mtime > 24h), giữ nguyên file mới tạo.
3. Ghi log số lượng file đã xóa và dung lượng đã giải phóng (bytes / MB).

---

## 📋 Atomic Steps

### [x] Step 1: Audio Cache Cleanup Service (`app/services/cron_service.py`)
- Định nghĩa hàm `cleanup_audio_cache(cache_dir: str | None = None, max_age_hours: float = 24.0) -> dict[str, Any]` trong `app/services/cron_service.py`.
- Xử lý safe check nếu thư mục chưa tồn tại hoặc rỗng.
- Quét và xóa file có `mtime` > 24h, tính toán số file đã xóa và bytes giải phóng.
- Ghi log kết quả dọn dẹp audio cache.

### [x] Step 2: Inngest Cron Background Job (`app/services/background_job_service.py`, `app/main.py`)
- Khởi tạo Inngest cron job function `cleanup-audio-cache` (trigger `inngest.TriggerCron(cron="0 3 * * *")`) trong `app/services/background_job_service.py`.
- Đăng ký `cleanup_audio_cache_job` vào `inngest.fast_api.serve` trong `app/main.py`.

### [x] Step 3: Integration Test Suite (`tests/test_background_jobs.py`)
- Viết unit & integration tests `test_cron_cleanup_*` trong `tests/test_background_jobs.py`:
  - Test quét thư mục rỗng / không tồn tại không crash.
  - Test chỉ xóa file > 24h và giữ file < 24h.
  - Test ghi log và trả về số lượng file + bytes giải phóng.

### [x] Step 4: Verification (`python3 pipeline/scripts/verify.py`)
- Chạy `pytest tests/test_background_jobs.py -k "test_cron_cleanup"` và `python3 pipeline/scripts/verify.py` kiểm định PASS 100%.
