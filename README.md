# 🦜 Duolingo Speak - Unlimited AI Roleplays & IELTS Practice

[![Live Demo](https://img.shields.io/badge/Live_Demo-Render-brightgreen?style=for-the-badge&logo=render)](https://doulingo.onrender.com)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-blue?style=for-the-badge&logo=github)](https://github.com/avandall/Doulingo)
[![Python Version](https://img.shields.io/badge/Python-3.11+-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)

> **FlyRank Internship Capstone Project — Backend Track**  
> **Author:** Vu Nguyen (Avandall)  
> **Submission Overview Document:** [`My 10x Solution - Vu Nguyen.md`](./My%2010x%20Solution%20-%20Vu%20Nguyen.md)

---

## 🎯 What is Duolingo Speak?

**Duolingo Speak** is an adaptive, AI-powered conversational platform designed specifically for English learners and IELTS candidates. It replaces static grammar exercises with **24/7 unlimited AI voice roleplay**, 9 distinct persona voices, adaptive difficulty scaling (CEFR A1 $\rightarrow$ C2), instant 0ms dictionary translation, and real-time speech evaluation.

### 🚀 The 10x Claim
* **Cost Reduction:** **100% free** ($0 vs $20–$30/hr for 1-on-1 human tutoring).
* **Instant Lookup:** **0ms** dictionary definition and instant sentence translation directly inside the speech bubble.
* **On-Demand Access:** **0s wait time** — practice speaking anytime without booking appointments.

### 🚫 Non-Goal (Explicit Scope Guard)
This project is **exclusively focused on Speaking Practice and IELTS AI Roleplay**. It does **NOT** attempt to be a general multi-skill language learning app (no written grammar drills, no reading tests, no flashcard mini-games).

---

## 🛠️ Program Concepts Mapping (5+ Concepts Rule)

In accordance with Section 2 of the Capstone Brief, the system implements 5 core engineering concepts (3 Core + 2 Swaps):

| # | Concept | Category | Where it lives in the code | Description |
|---|---|---|---|---|
| **1** | **API Endpoints** | Core 1 | [`app/api/routers/`](./app/api/routers/) | FastAPI REST endpoints with strict Pydantic models for speech audio processing, scenario starts, TTS, and analytics. |
| **2** | **Database** | Core 2 | [`app/storage/db.py`](./app/storage/db.py) | SQLite / Turso persistence layer surviving server restarts for saved words, user XP, scenarios, and evaluation logs. |
| **3** | **LLM Integration** | Core 7 | [`app/core/ai_engine.py`](./app/core/ai_engine.py) | Gemini LLM integration behind strict API endpoints with turn cost estimation, JSON validation, and fallback mechanisms. |
| **4** | **RAG with Citations** | Swap 1 | [`app/rag/`](./app/rag/) | Contextual retrieval pipeline matching user Band level with IELTS material banks and targeted vocabulary. |
| **5** | **Agent with Guardrails** | Swap 2 | [`app/core/conversational_agent.py`](./app/core/conversational_agent.py) | AI character persona memory engine preventing repetition and enforcing level-appropriate vocabulary. |
| *Extra* | *Test Suite* | Swap Extra | [`tests/`](./tests/) | 233 automated test cases covering core scoring, RAG retrieval, audio processor, and database persistence. |

* **Swap 1 Reason:** Replaced Authentication with RAG with Citations to ground AI responses directly in IELTS Band standards without friction.
* **Swap 2 Reason:** Replaced PDF/Email Reporting with Agent Guardrails to keep AI persona responses inside safe, adaptive pedagogical boundaries.

---

## 🏃 5-Minute Demo Path (Stranger Verification)

To experience the full capability of Duolingo Speak in under 5 minutes, follow these exact steps:

1. **Launch App:** Open browser at `http://localhost:8000` (or visit [Live Demo](https://doulingo.onrender.com)).
2. **Select Character:** On the main dashboard, choose character **Lily** (Sarcastic Goth) or **Vikram** (Academic IELTS Examiner).
3. **Start Scenario:** Click on **"IELTS Speaking Part 3: Technology"** or a custom scenario.
4. **Voice Practice:** Click the **Microphone icon**, speak a response in English, and press stop.
5. **Observe Real-Time Feedback:**
   * Watch the AI transcribe your speech.
   * Listen to the AI character reply with natural voice TTS.
   * Click on any word in the AI's response bubble for **instant 0ms Vietnamese translation**.
   * View your **Pronunciation & Fluency Score** and earned **XP points**.

---

## 💻 Quickstart (Clean Machine Setup)

### Prerequisites
* Python 3.10+
* `pip` or `uv`

### 1. Clone Repository
```bash
git clone https://github.com/avandall/Doulingo.git
cd Doulingo
```

### 2. Configure Environment
```bash
cp .env.example .env
# Open .env and add your GEMINI_API_KEY
```

### 3. Install Dependencies & Seed Demo Data
```bash
pip install -r requirements.txt
python3 scripts/seed_demo_data.py
```

### 4. Run Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Visit `http://localhost:8000` in your web browser.

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Single-Page UI                       │
│        (Web Speech API, Audio FX, Duo Mascot, HTML5)        │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / REST API
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Router Layer                     │
│   (/api/chat, /api/scenarios, /api/audio, /api/dictionary)  │
└──────┬───────────────────────┬───────────────────────┬──────┘
       │                       │                       │
       ▼                       ▼                       ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  AI Engine   │       │  RAG Module  │       │ TTS Service  │
│ (Gemini LLM) │       │ (IELTS Bank) │       │ (Edge/gTTS)  │
└──────┬───────┘       └──────┬───────┘       └──────┬───────┘
       │                      │                      │
       └──────────────────────┼──────────────────────┘
                              ▼
               ┌──────────────────────────────┐
               │  Persistence Layer (SQLite)  │
               │   (custom_topics.db / Turso) │
               └──────────────────────────────┘
```

---

## 🧪 Running Automated Tests

Run the test suite with single command:
```bash
pytest tests/ -v
```

---

## 📄 License & Credits
Built for **FlyRank Internship - Backend Track Capstone Project**. All tools used are $0 / free tier compliant.
