# TASK EXECUTION PLAN
# Task TASK-001: Cài đặt Jinja2 Template & Playwright PDF Reporting Engine

> **Trạng thái:** COMPLETED | **Ngày:** 2026-09-06

---

## 🎯 Task Goal
Tạo service `app/services/pdf_report_service.py` và template `app/templates/reports/speaking_report.html` sử dụng Jinja2 + Playwright Headless Chromium để render HTML sang PDF chuẩn in ấn A4 (có Print CSS `@page { size: A4; margin: 12mm; }`, `tr { break-inside: avoid; }`, `<thead>` lặp lại tự động, $\ge 2$ trang).

---

## 📋 Atomic Steps

### [x] Step 1: Dependencies & Environment Setup
- Thêm `jinja2>=3.1.0` và `playwright>=1.40.0` vào `requirements.txt`.
- Cập nhật `.gitignore` cho thư mục `reports/` và `output/`.
- Kiểm tra import dependencies.

### [x] Step 2: HTML Template & Print CSS (`app/templates/reports/speaking_report.html`)
- Thiết kế template A4 đáp ứng đầy đủ:
  - Header bài thi: Thí sinh, Ngày thi, exam_type (IELTS/DET), Candidate ID, Duration.
  - Overall Band & CEFR Level score card visual banner.
  - Bảng subscores thành phần: Fluency, Pronunciation, Grammar, Lexical Resource kèm nhận xét chi tiết.
  - Bảng Turn-by-Turn dialogue transcript (chi tiết từng lượt nói của thí sinh, AI prompt, lỗi sai và gợi ý cải thiện).
- Print CSS: `@page { size: A4; margin: 12mm; }`, `tr { break-inside: avoid; }`, `thead { display: table-header-group; }`, page breaks clean styling.

### [x] Step 3: PDF Service Implementation (`app/services/pdf_report_service.py`)
- Viết hàm `generate_speaking_pdf(report_data: dict, output_path: str) -> str`.
- Render HTML bằng Jinja2 `FileSystemLoader`.
- Sử dụng Playwright Chromium headless: `page.goto(content)`, `page.pdf(path=..., format='A4', margin={...}, print_background=True)`.
- Tạo helper sample report dictionary cho testing và standalone execution.

### [x] Step 4: Unit Test & Verification (`tests/test_pdf_reporting.py`)
- Viết test suite `test_render_pdf` chạy với pytest.
- Verify file `reports/sample_report.pdf` được tạo ra, dung lượng > 0 bytes, số trang $\ge 2$.
- Chạy `python3 pipeline/scripts/verify.py` đạt 100% PASS.
