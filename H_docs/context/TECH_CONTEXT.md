# TECH CONTEXT
# Bối cảnh Kỹ thuật & Chi tiết Kiến trúc — Duolingo Speak Refactor

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-10

---

## 1. Kiến trúc Tổng quan (Architecture Overview)

Dự án refactor Duolingo Speak chuyển đổi từ cơ chế sinh kịch bản ngẫu nhiên hoặc scenario tĩnh sang **Dynamic Material Bank Architecture** kết hợp tầng **Cloud Database Persistence (Turso Cloud SQLite - 9GB Free Tier)** để đảm bảo dữ liệu lưu trữ tồn tại vĩnh viễn trên mảng Free Tier của Render.

```
                                  [ DB1..DB5.md ]
                                         │
                                         ▼ (Startup Markdown AST / Regex Parser)
                              ┌────────────────────┐
                              │    MaterialBank    │  (In-Memory Thread-Safe Index)
                              └─────────┬──────────┘
                                        │
                                        ▼ (topic_id, level)
                              ┌────────────────────┐
                              │   PromptFactory    │  (Dynamic Sampling Engine)
                              └─────────┬──────────┘
                                        │
                                        ▼ (Assembled System Prompt)
                              ┌────────────────────┐
                              │      ai_engine     │  (Multi-Key LLM Engine)
                              └─────────┬──────────┘
                                        │
                                        ▼ (JSON Response + Speech Feedback)
                              ┌────────────────────┐
                              │  FastAPI Endpoints │ ◄────► [ Turso Cloud SQLite DB (9GB) ]
                              └────────────────────┘        (Custom Topics, Saved Vocab, Stats)
```

---

## 2. Dynamic Material Bank Schema (`app/material_bank.py`)

Tất cả các thành phần trong file `DB*.md` được parse thành các Data Structure mạnh mẽ (Pydantic models hoặc Dataclasses):

```python
from pydantic import BaseModel
from typing import List, Dict, Optional

class Persona(BaseModel):
    id: str                  # e.g., "P1"
    name: str                # e.g., "Friendly Local Resident"
    description: str         # Persona context & demeanor

class Question(BaseModel):
    id: str                  # e.g., "Q_5_01"
    band_level: str          # e.g., "5.0-6.0" or "6.5+"
    text: str                # e.g., "Do you like travelling in your free time?"

class VocabularyItem(BaseModel):
    phrase: str              # e.g., "off the beaten track"
    meaning: str             # e.g., "far away from main tourist areas"
    band_level: str          # e.g., "5.0-6.0" or "6.5+"

class GrammarPattern(BaseModel):
    id: str                  # e.g., "Pattern_1"
    template: str            # e.g., "To be completely honest, I'd say I'm more of a..."

class TopicBank(BaseModel):
    topic_id: str            # e.g., "travel_01" or "hometown"
    topic_name: str          # e.g., "Travel & Holidays"
    source_file: str         # e.g., "DB1_Personal_and_Daily_Life.md"
    target_levels: List[str] # e.g., ["5.0-6.0", "6.5+"]
    personas: List[Persona]
    questions: List[Question]
    vocabulary: List[VocabularyItem]
    grammar_patterns: List[GrammarPattern]
```

---

## 3. Database & Deployment Architecture (Render + Turso Cloud SQLite)

### Render Free Tier Ephemeral Disk Constraint & Turso Solution
Render Web Service gói miễn phí tự động tắt container sau 15 phút không có traffic và reset đĩa đệm (Ephemeral Disk). Do đó:
- File SQLite local (`data/custom_topics.db`) sẽ bị reset về bản gốc khi container khởi động lại.
- **Giải pháp:** Sử dụng **Turso DB (Managed Cloud SQLite - 9GB Free Tier)** thông qua biến môi trường `TURSO_DATABASE_URL` (`libsql://...`) và `TURSO_AUTH_TOKEN`.
- Tầng `app/db.py` kiểm tra `TURSO_DATABASE_URL`: Nếu có biến môi trường Turso, app kết nối tới Turso Cloud SQLite; nếu không có, app dùng local SQLite (`data/custom_topics.db`) làm fallback cho môi trường offline.
- Giữ nguyên 100% cú pháp câu lệnh SQL của SQLite, không cần refactor SQL dialect.

---

## 4. Thuật toán Dynamic Sampling (`app/prompt_factory.py`)

Khi một phiên hội thoại khởi tạo (`/api/start_scenario` hoặc `/api/process_turn`):

1. **Map User Level -> Band Category:**
   - Level 1 - 10 (A1 - B1): Ưu tiên lấy Question & Vocab thuộc nhóm `Band 5.0 - 6.0`.
   - Level 11 - 20 (B2 - C2): Ưu tiên lấy Question & Vocab thuộc nhóm `Band 6.5+`.
2. **Dynamic Sampling:**
   - `sampled_persona` = `random.choice(topic.personas)`
   - `sampled_questions` = `random.sample(topic.questions_by_band, k=min(2, len(...)))`
   - `sampled_vocab` = `random.sample(topic.vocab_by_band, k=min(4, len(...)))`
   - `sampled_pattern` = `random.choice(topic.grammar_patterns)` (nếu có)
3. **Prompt Assembly:**
   - Ghép nguyên liệu đã sample vào System Prompt template:
     ```text
     ROLE: You are roleplaying as {persona.name} ({persona.description}).
     TOPIC: {topic_name}
     FOCUS VOCABULARY TO GUIDE USER TO USE OR DEMONSTRATE:
     {formatted_vocab_list}
     ANCHOR CONVERSATION QUESTIONS:
     {formatted_question_list}
     SUGGESTED SENTENCE STRUCTURE:
     {pattern_template}
     FORMAT & CONSTRAINTS:
     - Keep responses natural, concise, and under {max_words} words.
     - Provide JSON containing ai_response, ai_response_vi, user_feedback.
     ```

---

## 5. Hiệu năng & Cache Strategy (0ms Latency Guarantee)

- **Startup Indexing:** Khi FastAPI app khởi chạy (`@app.on_event("startup")`), `MaterialBank.load_all()` đọc toàn bộ 5 file `DB*.md` vào bộ nhớ RAM (`dict[topic_id, TopicBank]`).
- **Access Speed:** Truy vấn `MaterialBank.get_topic(topic_id)` lấy từ RAM hashmap đạt tốc độ $O(1)$ (< 0.1ms).
- **Sampling Overhead:** Thuật toán random sampling + string assembly hoàn thành trong **< 1ms**.
- **No Vector Search Overhead:** Tiết kiệm từ 300ms - 1500ms so với giải pháp Vector Database / RAG Search.

---

## 6. Môi trường & Dependencies

- Python 3.10+
- FastAPI, Pydantic v2
- `libsql-experimental` / `sqld` (cho Turso Cloud SQLite)
- pytest (Unit & Integration tests)
- `python-dotenv` cho `.env` credentials
