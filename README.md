# 🦉 Duolingo Speak — AI Roleplay Speaking Practice (Harness Hub)

**Duolingo Speak** is an AI-powered conversational speaking practice web application built with a **FastAPI** backend and a **Duolingo-inspired UI/UX** frontend. It enables learners to practice continuous, natural, long-context roleplays across 20 CEFR-aligned difficulty levels.

---

## 🧭 Harness Engineering Hub (MD-File System)
This project is governed by **Harness Engineering** principles (*Mirza Asceric — 29 Tips*):

| Document | Purpose & Relevant Tips |
| :--- | :--- |
| **[`AGENTS.md`](file:///home/avandall1999/Projects/Doulingo_speak/AGENTS.md)** | **Agent Entry Point**: Core directives, session hygiene, and execution boundaries (*Tips 1, 8, 15, 28*). |
| **[`docs/29_TIPS.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/29_TIPS.md)** | **Harness Cheat Sheet**: All 29 tips in a short, straight, and memorable field note format. |
| **[`docs/architecture.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/architecture.md)** | **System Architecture & Tech Stack**: Live code mapping, data flow, and 0ms cache design (*Tips 3, 5, 25*). |
| **[`docs/rules.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/rules.md)** | **Coding & UI/UX Rules**: Duolingo tokens (`#58CC02`), 3D buttons, git standards, and QA (*Tips 1, 7, 10, 25*). |
| **[`docs/specs.md`]** | **Specs-Driven Development**: Functional requirements with visible checkboxes & logical units (*Tips 12, 13, 14*). |
| **[`docs/WORK_BOARD.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/WORK_BOARD.md)** | **Kanban Work Board**: Multi-agent task tracking across TODO, IN PROGRESS, REVIEW, DONE (*Tips 26, 27, 29*). |
| **[`docs/TECH_DEBT.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/TECH_DEBT.md)** | **Tech Debt Ledger**: Non-blocking refactoring, TODOs, and legacy improvements (*Tip 6, 11*). |
| **[`docs/BLOCKED.md`]** | **The Handbrake**: Dedicated log for unresolvable errors and missing dependencies (*Tip 16, 19*). |
| **[`docs/RALPH_LOOP.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/RALPH_LOOP.md)** | **Autonomous Loop Manual**: Build-test-fix loop, exit codes, git reset recovery, and logging (*Tips 17–24*). |
| **[`docs/plan.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/plan.md)** | **Original Vietnamese Plan**: Legacy project roadmap and design DNA reference. |

---
---

# [VI] 🦉 Duolingo Speak — Luyện Nói AI Ngữ Cảnh Dài (Trung Tâm Harness)

**Duolingo Speak** là ứng dụng web luyện nói tiếng Anh tương tác với AI, sử dụng backend **FastAPI** và giao diện người dùng frontend đậm chất **Duolingo UI/UX**. Ứng dụng giúp học viên thực hành liên tục các cuộc hội thoại ngữ cảnh dài theo 20 cấp độ chuẩn CEFR.

---

## 🧭 Trung Tâm Tài Liệu Harness Engineering (Hệ Thống File MD)
Dự án được điều phối theo triết lý **Harness Engineering** (*29 Lời Khuyên của Mirza Asceric*):

| Tài Liệu | Mục Đích & Lời Khuyên Liên Quan |
| :--- | :--- |
| **[`AGENTS.md`](file:///home/avandall1999/Projects/Doulingo_speak/AGENTS.md)** | **Điểm Vào Cho Agent**: Quy tắc cốt lõi, vệ sinh phiên làm việc và giới hạn thực thi (*Tips 1, 8, 15, 28*). |
| **[`docs/29_TIPS.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/29_TIPS.md)** | **Cẩm Nang 29 Tips**: Tóm tắt 29 lời khuyên ngắn gọn, súc tích và dễ nhớ. |
| **[`docs/architecture.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/architecture.md)** | **Kiến Trúc & Code Tham Chiếu**: Sơ đồ luồng dữ liệu, ánh xạ code thực tế và cache 0ms (*Tips 3, 5, 25*). |
| **[`docs/rules.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/rules.md)** | **Quy Chuẩn Code & UI/UX**: Màu xanh Duolingo (`#58CC02`), nút bo 3D, git commit và kiểm tra chất lượng (*Tips 1, 7, 10, 25*). |
| **[`docs/specs.md`]** | **Đặc Tả Kỹ Thuật**: Yêu cầu tính năng kèm checklist rõ ràng (`[ ]`, `[x]`) theo đơn vị logic (*Tips 12, 13, 14*). |
| **[`docs/WORK_BOARD.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/WORK_BOARD.md)** | **Bảng Việc Kanban**: Theo dõi tiến độ đa agent theo TODO, IN PROGRESS, REVIEW, DONE (*Tips 26, 27, 29*). |
| **[`docs/TECH_DEBT.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/TECH_DEBT.md)** | **Sổ Theo Dõi Nợ Kỹ Thuật**: Ghi nhận việc tái cấu trúc, TODO và cải tiến hệ thống cũ (*Tip 6, 11*). |
| **[`docs/BLOCKED.md`]** | **Phanh Khẩn Cấp (Handbrake)**: Nhật ký ghi nhận lỗi không thể giải quyết và phụ thuộc còn thiếu (*Tip 16, 19*). |
| **[`docs/RALPH_LOOP.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/RALPH_LOOP.md)** | **Cẩm Nang Vòng Lặp Tự Động (Ralph Loop)**: Luồng build-test-fix tự động, mã thoát, `git reset` và log (*Tips 17–24*). |
| **[`docs/plan.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/plan.md)** | **Kế Hoạch Gốc Tiếng Việt**: Tài liệu thiết kế ban đầu và hướng dẫn phong cách UI/UX của dự án. |

---

## ⚡ Khởi Động Nhanh (Quick Start)

```bash
# 1. Kích hoạt môi trường ảo & cài đặt thư viện
uv venv .venv && source .venv/bin/activate && uv pip install -r requirements.txt

# 2. Khởi chạy máy chủ phát triển cục bộ
npm run dev # hoặc: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
