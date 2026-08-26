# TECH CONTEXT
# Bối cảnh kỹ thuật — Stack, Môi trường và Kiến trúc Kỹ thuật

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-26

---

## 1. Tech Stack & Environment

### Language & Framework
```
Runtime:          Python 3.10+
Framework:        FastAPI / Uvicorn
Validation:       Pydantic v2
API Protocol:     REST API (JSON)
AI Client:        Google GenAI SDK (Gemini API)
```

### Database & Storage
```
Data Storage:     JSON-based Data Banks (`app/data/*.json`)
Vector Search:    In-memory Vector Similarity / Cosine Distance cho Exemplar RAG
```

### Testing Framework
```
Test Runner:      Pytest
Types of Tests:   Unit Tests, Integration Tests for AI Prompt Pipeline
```

---

## 2. Cấu trúc Thư mục Dự án (Directory Structure)

```
Doulingo/
├── app/
│   ├── main.py                       # FastAPI Entry point
│   ├── core/
│   │   ├── ai_engine.py              # Single-Call CoT AI Engine
│   │   ├── prompt_factory.py         # 3-Tier Prompt Builder
│   │   ├── heuristic_checker.py      # Fast CEFR Level Checker (<5ms)
│   │   ├── exemplar_rag.py           # Dialogue Exemplar RAG Engine
│   │   ├── grammar_validator.py      # Grammar Structure Validator
│   │   └── adaptive_level_detector.py # IRT Adaptive Level Detector
│   ├── data/                         # Data Banks
│   │   ├── vocab_bank.json           # Vocabulary by CEFR Level
│   │   ├── sample_dialogue_bank.json # Dialogue Exemplars
│   │   ├── persona_definitions.json  # 9 Personas definitions
│   │   ├── topic_bank.json           # Structured Topics
│   │   ├── grammar_bank.json         # Grammar structures by level
│   │   └── cefr_gold_set.json        # Gold-set for level classifier
│   └── characters/                   # Character definitions & routes
├── pipeline/
│   └── docs/                         # Pipeline Harness Docs
├── tests/                            # Test Suite
├── to_do.md                          # Task list for Human User
└── pyproject.toml                    # Dependencies
```

---

## 3. Data Models & JSON Schemas

### Single-Call CoT JSON Response Schema
```json
{
  "natural_draft": "Hi there! It is a beautiful rainy day outside. How are you feeling today?",
  "vocab_check": [],
  "final_response": "Hi there! It is a rainy day today. How are you feeling?"
}
```

---

## 4. Build, Run & Verification Commands

```bash
# Chạy test suite toàn hệ thống
pytest

# Verification script chính của Pipeline
python3 pipeline/scripts/verify.py
```
