# My 10x Solution - Vu Nguyen

## Overview Information
* **Project Name:** Duolingo Speak - Unlimited AI IELTS Speaking & Conversation Platform
* **Author:** Vu Nguyen (Avandall)
* **Track:** FlyRank Internship - Backend Development Track
* **Public GitHub Repository:** [https://github.com/avandall/Doulingo](https://github.com/avandall/Doulingo)
* **Live Deployment URL:** [https://doulingo.onrender.com](https://doulingo.onrender.com)

---

## Part 1: What is the problem you are solving?

### 1. Problem Statement (3 Sentences)
English learners preparing for IELTS Speaking face immense barriers due to high 1-on-1 tutoring costs ($15-$30/hour), scheduling friction, and anxiety when speaking to human examiners. Traditional language learning platforms only offer static grammar drills or flashcards without realistic, adaptive conversational turn-taking or real-time pronunciation feedback. As a result, learners struggle to build genuine speaking confidence, natural intonation, and spontaneous responses under pressure.

### 2. Target Audience
* **IELTS Candidates:** Students aiming for Band 6.0–8.5 needing daily realistic mock test practice across Part 1, Part 2, and Part 3 topics.
* **Working Professionals:** Non-native English speakers wanting to improve spontaneous workplace fluency without fear of judgment.

### 3. The 10x Claim
**Quantifiable Metric:** Reduces IELTS Speaking practice cost by **100%** ($0 vs $20/hr tutoring) while eliminating wait time (0s on-demand access 24/7), providing instant 0ms dictionary lookup and real-time pronunciation scoring per turn.

### 4. Explicit Non-Goal (Scope Boundary)
**Non-Goal:** This system focuses **exclusively on Speaking Practice, IELTS Exam Simulation, and Real-Time Audio-driven AI Roleplay**. It explicitly does **NOT** build a multi-skill English course platform (no reading comprehension drills, no written essay grading, no flashcard mini-games).

---

## Part 2: How did you implement your solution?

### 1. Architecture & Core Concepts Implemented

The solution follows **Clean Architecture** principles with decoupled presentation endpoints, domain logic engines, RAG context constructors, and SQLite/Turso persistence adapters.

| # | Concept Name | Implementation Type | Location in Codebase | Description / Role in System |
|---|---|---|---|---|
| 1 | **API Endpoints** | Core Concept 1 | [`app/api/routers/`](file:///home/avandall/project/Doulingo/app/api/routers/) | FastAPI RESTful routes with strict Pydantic validation and HTTP status codes (`/api/process_turn`, `/api/tts`, `/api/det/evaluate_speech`). |
| 2 | **Database** | Core Concept 2 | [`app/storage/db.py`](file:///home/avandall/project/Doulingo/app/storage/db.py) | SQLite / Turso persistence layer for custom scenarios, permanent dictionary cache, saved vocabulary, and XP stats. |
| 3 | **LLM Integration** | Core Concept 7 | [`app/core/ai_engine.py`](file:///home/avandall/project/Doulingo/app/core/ai_engine.py) | Narrow AI integration using Google Gemini API with token usage logging, structured JSON schema validation, and fallback handling. |
| 4 | **RAG with Citations** | Allowed Swap 1 | [`app/rag/`](file:///home/avandall/project/Doulingo/app/rag/) | Contextual retrieval system matching IELTS Band levels (4.0–9.0) with sample dialogue banks and vocabulary targets. |
| 5 | **Agent with Guardrails** | Allowed Swap 2 | [`app/core/conversational_agent.py`](file:///home/avandall/project/Doulingo/app/core/conversational_agent.py) | Persona memory engine & anti-repetition guardrails ensuring AI character stays strictly in role and avoids lopsided loops. |

#### Swap Justifications (Max 2 Swaps):
* **Swap 1 (RAG with Citations instead of Auth):** User authentication was swapped for RAG because speaking practice requires immediate context-grounded IELTS Band materials, whereas single-user local state simplifies zero-friction demo access.
* **Swap 2 (Agent with Guardrails instead of PDF Reporting):** PDF export was swapped for real-time Agent Guardrails to ensure AI character dialogues stay strictly within pedagogical boundaries and adaptive difficulty thresholds.

---

### 2. Steps to Run on a Clean Machine

```bash
# 1. Clone the public repository
git clone https://github.com/avandall/Doulingo.git
cd Doulingo

# 2. Setup environment variables
cp .env.example .env
# Edit .env and insert your GEMINI_API_KEY

# 3. Seed demo data (1 command)
python3 scripts/seed_demo_data.py

# 4. Start application
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Open your browser at `http://localhost:8000` to start practicing immediately!
