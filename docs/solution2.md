# PLAN & CONTEXT SPECIFICATION: AI ENGLISH SPEAKING APP

## 1. CONTEXT & PROBLEM STATEMENT
- **App Concept:** AI-powered English Speaking App (Duolingo-style for speaking skills).
- **Core Mechanism:** Generative AI (LLM API Calls) roleplays and interacts with users in real-time.
- **Current Issue:** Generated content feels generic and lacks academic IELTS-standard vocabulary, structures, and topic-specific depth.
- **Resource:** IELTS Speaking PDFs will be converted into structured `.md` files to serve as reference materials (Ground Truth).
### 1.1 Context (Bối cảnh)
- **Ứng dụng đang phát triển là một **AI-powered English Speaking App** (mô hình tương tự Duolingo nhưng tập trung hoàn toàn vào kỹ năng Speaking).
- **Cơ chế cốt lõi:** Sử dụng Generative AI (thông qua API Call đến LLMs như Gemini / OpenAI / Claude) để đóng vai (Roleplay) và thực hiện cuộc hội thoại nói chuyện tương tác thời gian thực với người dùng.
- **Vấn đề hiện tại (Core Pain Point):** 
  - Nội dung do AI tự sinh ra (pure generation) mang tính chung chung, thiếu độ sâu học thuật, không chuẩn hóa theo khung tiêu chí IELTS Speaking (từ vựng ăn điểm, collocations, idioms, cấu trúc trả lời).
  - Cần tích hợp bộ tài liệu chuẩn IELTS Speaking (dạng PDF đã được chuyển đổi sang `.md`) làm tài liệu mẫu (Ground Truth / Reference Materials) để tham chiếu.

### 1.2 Bài toán Kiến trúc (Architectural Dilemma)
Nên tổ chức và truy vấn tài liệu mẫu như thế nào để đảm bảo 3 tiêu chí:
1. **Chất lượng nội dung:** Đạt chuẩn IELTS, phản xạ tự nhiên.
2. **Hiệu năng & Trải nghiệm (Performance/Latency):** Tốc độ phản hồi cực nhanh cho ứng dụng giao tiếp bằng giọng nói (Real-time Voice Conversation).
3. **Tính đa dạng & Cá nhân hóa (Diversity & Novelty):** Tránh việc người dùng chọn cùng một Topic + Level thì mỗi lần hội thoại đều bị lặp lại $100\%$ kịch bản cũ.
---

## 2. GOALS
1. **Academic Quality:** Ground conversations in high-quality IELTS materials.
2. **Low Latency:** Ensure fast API responses for real-time voice interactions (avoid vector search overhead).
3. **100% Diversity:** Prevent repetitive conversation flows when users select the same `Topic + Level` multiple times.

---

## 3. CORE ARCHITECTURE SOLUTION: DYNAMIC MATERIAL BANK
Avoid heavy RAG/Vector Search pipelines and static script-loading. Instead, treat `.md` files as **Material Banks** (pools of atomic ingredients) and assemble session prompts dynamically at the Backend.

### Architectural Flow:
1. **Static Ingestion:** materials are processed into clean `DB*.md` files organized by topic (containing Question Pools, Vocabulary/Collocation Pools, and Persona Pools).
2. **Dynamic Sampling (Backend Prompt Factory):** Upon starting a session (`Topic + Level`), Backend randomly samples:
   - 1 Persona (e.g., Local Resident, Backpacker, Examiner)
   - 3-4 Focus Vocabulary/Collocations
   - 1-2 Core Questions
3. **Prompt Assembly:** Backend constructs a compact System Prompt combining sampled ingredients + User Memory.
4. **API Execution:** LLM is called with tuned parameters (`temperature: 0.75 - 0.85`, `presence_penalty: 0.6`).

---

## 4. GIẢI PHÁP TỔNG THỂ: DYNAMIC MATERIAL BANK ARCHITECTURE (HYBRID PROMPT PIPELINE)

Chúng ta dùng kiến trúc **Dynamic Material Bank (Ngân hàng nguyên liệu động)** `DB*.md` kết hợp **Backend Prompt Factory**.

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                          LOCAL / DATABASE MATERIAL BANK                           │
│  ├── /data/materials/                                                             │
│  │   ├── topic_travel.md  (Contains: Question Pool, Vocab Pool, Persona Pool)     │
│  │   └── topic_hometown.md                                                        │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                             BACKEND PROMPT FACTORY                                │
│  1. User selects: [Topic: Travel] & [Target Level: 5.0 - 6.0]                     │
│  2. Fetch User Profile & Memory (History: talked about "Da Nang beaches")         │
│  3. DYNAMIC SAMPLING ALGORITHM:                                                   │
│     - Randomly pick 1 Persona from Persona Pool (e.g., "Backpacker Traveller")    │
│     - Randomly sample 3-4 Focus Collocations from Vocab Pool                     │
│     - Randomly select 2 Anchor Questions from Question Pool                       │
│  4. Assemble final Custom System Prompt for this exact session                    │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                              LLM GENERATIVE ENGINE                                │
│  API Call with Parameters:                                                        │
│  - Temperature: 0.8                                                               │
│  - System Prompt: [Assembled Unique Prompt]                                       │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                     DYNAMIC, NON-REPETITIVE IELTS CONVERSATION                    │
└───────────────────────────────────────────────────────────────────────────────────┘
```
---

## 5. THIẾT KẾ CẤU TRÚC FILE MATERIAL BANK (`DB*.md` SCHEMA)

Tất cả sách PDF sau khi OCR/chuyển đổi sẽ không lưu dạng đoạn văn xuôi, mà được bóc tách và tái cấu trúc thành các file `DB*.md` nguyên liệu chuẩn hóa theo Schema sau:

```markdown
---
topic_id: "travel_01"
topic_name: "Travel & Holidays"
target_levels: ["5.0-6.0", "6.5-7.5"]
---

# TOPIC: TRAVEL & HOLIDAYS

## 1. PERSONA POOL (Các vai diễn của AI)
- [ID: P1] **Friendly Local Resident**: An enthusiastic local who loves sharing hidden gems of their hometown.
- [ID: P2] **Adventurous Backpacker**: A budget traveller who has explored various countries and cultures.
- [ID: P3] **Strict IELTS Examiner**: A professional, neutral examiner assessing fluency, vocabulary, and grammar.

## 2. QUESTION POOL (Ngân hàng câu hỏi phân cấp)
### Band 5.0 - 6.0 (Part 1 Focus)
- Q_5_01: Do you like travelling in your free time? Why or why not?
- Q_5_02: What kind of places do you usually like to visit on holiday?
- Q_5_03: Have you visited many foreign countries?
- Q_5_04: Do you prefer travelling alone or with friends/family?

### Band 6.5+ (Part 2 & Part 3 Focus)
- Q_7_01: How has the tourism industry changed in your country over the past decade?
- Q_7_02: What are the environmental impacts of mass tourism on famous landmarks?

## 3. VOCABULARY & COLLOCATION POOL (Từ vựng & Cụm từ mục tiêu)
### Level: Intermediate (Band 5.5 - 6.5)
- **off the beaten track**: far away from main tourist areas.
- **catch the sun**: to get a suntan/enjoy sunny weather.
- **picturesque scenery**: attractive and interesting, especially like a picture.
- **breathtaking view**: an extremely beautiful view.
- **pack a bag and go**: to travel spontaneously.

### Level: Advanced (Band 7.0+)
- **tourist trap**: a place that attracts many tourists and charges high prices.
- **cultural immersion**: fully experiencing a foreign culture.

## 4. GRAMMAR & RESPONSE PATTERNS (Mẫu câu gợi ý)
- Pattern_1: "To be completely honest, I'd say I'm more of a [type of person] because..."
- Pattern_2: "If I were given the opportunity to visit [place], I would definitely..."
```