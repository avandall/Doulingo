# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** RUNTIME (Auto-Generated / Synced by harness.sh) | **Cập nhật:** 2026-09-06 23:06

---

## 🎯 Task Spec: TASK-001
### 📌 TASK-001: Cài đặt Jinja2 Template & Playwright PDF Reporting Engine

#### Metadata
```
Task ID:         TASK-001
Task Name:       Cài đặt Jinja2 Template & Playwright PDF Reporting Engine
Phase:           Phase 1
Task Type:       feat
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-09-06
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Học viên sau bài thi IELTS/DET cần bảng điểm Speaking Report Card chi tiết, định dạng PDF chuẩn in ấn A4.
- **What:** Tạo `app/templates/reports/speaking_report.html` và `app/services/pdf_report_service.py` sử dụng Playwright Headless Chromium để render HTML sang PDF. Đảm bảo Print CSS có `@page { size: A4; margin: 12mm; }`, `tr { break-inside: avoid; }`, và `<thead>` tự động lặp lại trên mọi trang.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [ ] Thư viện `playwright` và `jinja2` sẵn sàng trong project.
- [ ] Template HTML chứa: Header bài thi, Thẻ điểm CEFR / Overall Band, Bảng điểm thành phần (Fluency, Pronunciation, Grammar, Lexical), Bảng chi tiết toàn bộ lượt đối thoại (turn-by-turn).
- [ ] Hàm `generate_speaking_pdf(report_data: dict, output_path: str)` xuất file PDF $\ge 2$ trang đẹp mắt, không cắt ngang dòng chữ.
- [ ] Script test đơn lẻ xuất thử file `reports/sample_report.pdf` thành công.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/templates/reports/**`, `app/services/pdf_report_service.py`, `requirements.txt`, `reports/**`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
python3 -c "import playwright; import jinja2; print('Dependencies OK')"
pytest tests/test_pdf_reporting.py -k "test_render_pdf"
```

---

---

## 🛡️ JIT Environment Context
- **Tech Stack:** ```,Runtime:          Python 3.10+ (WSL Linux Ubuntu / CPython) Framework:        FastAPI >= 0.115.0,Web Server:       Uvicorn (ASGI) Validation:       Pydantic v2,API Protocol:     RESTful JSON API + Binary File Streams (FileResponse) PDF Engine:       Playwright Headless Chromium + Jinja2 Templates + Print CSS,Background Engine: Inngest Python SDK / FastAPI BackgroundTasks + Async IO
- **Scope Boundaries:** ```,✅ app/**                               (Router, Services, Schemas, Templates) ✅ tests/**                              (Unit & Integration test suites),✅ reports/**, output/**                 (Thư mục lưu PDF và output artifacts) ✅ pipeline/docs/context/Tasks_list.md   (Cập nhật tiến độ task [ ] -> [/] -> [x]),✅ pipeline/docs/runtime/**              (Logs, status, plans của harness) ✅ requirements.txt, pyproject.toml      (Thêm packages cần thiết: playwright, inngest, jinja2),✅ .gitignore                            (Đảm bảo bỏ qua reports/, *.db, __pycache__)
- **Last Synced:** 2026-09-06 23:06:18
