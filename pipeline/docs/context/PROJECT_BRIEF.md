# PROJECT BRIEF
# Tóm tắt dự án — Duolingo Speak: Fix RAG Pipeline, Context Continuity & Fallback Overhaul

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-21
>
> ✏️ **HUMAN FILLS THIS FILE.** File này định nghĩa mục tiêu sửa lỗi RAG, Context và Fallback cho Duolingo Speak.

---

## 1. Tên & Mô tả Dự án

```
Tên dự án:          Duolingo Speak - RAG & Context Pipeline Overhaul
Mô tả ngắn:        Khắc phục 5 root causes khiến AI bị mất ngữ cảnh hội thoại, câu trả lời vô cảm ("That sounds wonderful!"), không nạp được sách trong /output vào Database, rớt thiết lập độ khó Level 9/20 và bị phân mảnh 2 pipeline API.
Repo Name:         Doulingo
Track / Domain:    Backend AI Agent / RAG Pipeline / FastAPI / SQLite
Độ khó:             Medium-Hard
Thời gian ước tính: 4-6 hours
Tech Stack:        Python 3.10+, FastAPI, SQLite (libsql), Pytest, Groq / Gemini / OpenAI APIs
```

---

## 2. Mục tiêu Kinh doanh & Vấn đề Cốt lõi

### Vấn đề cần giải quyết (Root Causes từ analysis.md)
1. **Dữ liệu sách chưa nạp vào DB (R4):** Hàng chục file YAML từ sách trong `output/extracted/` chưa được ingest vào SQLite `data/custom_topics.db`, khiến DB chỉ có 67 câu thoại mẫu legacy.
2. **Endpoint chính đứt kết nối RAG (R4):** Endpoint `/api/process_turn` (Web UI chính) hoàn toàn không gọi RAG `retrieve_dialogues()`, bỏ qua dữ liệu sách.
3. **Mock Fallback tĩnh & Vô cảm (R1, R2):** Khi API Key bị hết quota (HTTP 429), hệ thống tụt về `_get_mock_fallback_response()` tĩnh, bốc ngẫu nhiên câu *"That sounds wonderful! Could you tell me more about..."* và hoàn toàn bỏ qua câu nói của user ("I lost my memory").
4. **Bỏ qua độ khó Level 9/20 (R3):** Khi ở chế độ Fallback, các quy tắc độ khó trong `LEVEL_CONFIGS` (45-85 từ, CEFR B1) bị loại bỏ hoàn toàn.
5. **Phân mảnh 2 Pipeline (R2):** `/api/process_turn` và `/api/voice/process_turn` sử dụng 2 cách dựng prompt và RAG hoàn toàn độc lập.

### Giải pháp & Mục tiêu
- **Nạp toàn bộ sách vào DB:** Ingest dữ liệu từ `output/extracted/` vào SQLite `custom_topics.db` qua `scripts/insert_turso.py`.
- **Tích hợp RAG Layer vào `/api/process_turn`:** Gọi `retrieve_dialogues()` để đưa các câu mẫu từ sách vào System Prompt dưới dạng Reference Dialogues.
- **Xây dựng Context-Aware Fallback Engine:** Thay thế mock fallback tĩnh bằng engine fallback thông minh, nhận biết được `user_transcript` và duy trì ràng buộc `LEVEL_CONFIGS`.
- **Thống nhất 2 Pipeline:** Hợp nhất luồng dựng Prompt và RAG giữa Web UI và Voice Pipeline.

---

## 3. Ground Rules & Constraints

| Quy tắc | Chi tiết bắt buộc |
|---------|-------------------|
| **1. Dedicated Repo** | Làm việc trực tiếp trong repository workspace `/home/avandall/project/Doulingo` |
| **2. Stack & Environment** | Python 3.10+, FastAPI, SQLite local (`data/custom_topics.db`) |
| **3. Secrets & Security** | Mọi secrets/keys nằm trong `.env`, không bao giờ hardcode credentials |
| **4. Data Integrity** | Bảo toàn schema `content_units` & `sample_dialogues` trong SQLite |
| **5. Harness Protocol** | Tuân thủ 10 điều luật `AGENT_CONSTITUTION.md` và quy trình 7 phase |

---

## 4. Phạm vi Dự án (Project Scope)

### Core Features / Modules
- **`scripts/insert_turso.py` & Ingestion**: Script nạp dữ liệu YAML từ `output/extracted` vào SQLite DB.
- **`app/ai_engine.py`**: Tích hợp RAG retrieval vào `_build_token_efficient_prompt()` và xây dựng `_get_context_aware_fallback()`.
- **`app/prompt_constructor.py` & `app/conversational_agent.py`**: Thống nhất quy chuẩn Prompt và Level constraints.
- **`tests/`**: Bộ unit test & integration test cho RAG retrieval, context fallback và Level 9 constraints.

---

## 5. Các Giai đoạn Phát triển (Roadmap / Tasks)

```
TASK-001: Ingest dữ liệu sách từ output/extracted/ vào SQLite DB
TASK-002: Tích hợp RAG Layer (retrieve_dialogues) vào ai_engine.process_turn (/api/process_turn)
TASK-003: Nâng cấp Context-Aware Fallback Engine thay cho Mock Fallback tĩnh
TASK-004: Thống nhất 2 Pipeline (Pipeline A & Pipeline B)
TASK-005: Kiểm thử E2E & Verify toàn bộ luồng hội thoại
```
