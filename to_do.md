# 📋 TO-DO LIST DÀNH CHO USER (HUMAN TASKS)
# Danh sách công việc Người dùng cần chuẩn bị và duyệt theo từng Giai đoạn

---

## 🛑 THỜI ĐIỂM BẠN (HUMAN) CẦN THỰC HIỆN TO-DO LIST NÀY:

> 💡 **Quy trình phối hợp liên mạch giữa AI và Bạn:**
> 1. AI chạy liền mạch các task Phase 1: **TASK-001** (Seed Data) $\rightarrow$ **TASK-002** (Heuristic Checker) $\rightarrow$ **TASK-003** (Hybrid RAG Engine) $\rightarrow$ **TASK-004** (CoT Engine).
> 2. 🛑 **DỪNG LẠI TẠI ĐÂY (ĐIỂM DỪNG 1):** Sau khi AI làm xong TASK-004, AI đã tạo đầy đủ file dữ liệu thô ban đầu (`vocab_bank.json` & `sample_dialogue_bank.json`). **Đây là lúc bạn vào làm Giai đoạn 1 dưới đây.**
> 3. Sau khi bạn duyệt xong Giai đoạn 1, AI mới chạy tiếp các task Phase 2: **TASK-005** (3-Tier Prompt 9 Personas), **TASK-006** (Topic Bank), **TASK-007** (Rating API).
> 4. 🛑 **DỪNG LẠI TẠI ĐÂY (ĐIỂM DỪNG 2):** Sau khi AI xong TASK-007, bạn duyệt Giai đoạn 2.
> 5. AI chạy tiếp Phase 3: **TASK-008** (Grammar Bank) $\rightarrow$ **TASK-009** (Adaptive Level Detector).

---

## 🎯 GIAI ĐOẠN 1: Chuẩn bị Dữ liệu Cốt lõi & Kiểm duyệt (Thực hiện SAU TASK-004)

- [ ] **1.1. Duyệt & Chuẩn hóa Vocabulary Bank (CEFR A1 - B1)**
  - **Mô tả:** AI đã cào/seed sẵn bộ từ vựng thô tại `app/data/vocab_bank.json`. Bạn hãy mở file check lại danh sách từ vựng A1-B1 và các từ đồng nghĩa (`synonyms_lower_tier`, `synonyms_higher_tier`).
  - **File:** `app/data/vocab_bank.json`.

- [ ] **1.2. Kiểm duyệt & Đánh giá Quality Score cho Dialogue Bank (RAG Câu Mẫu)**
  - **Mô tả:** AI đã sinh bộ dữ liệu câu mẫu thô tại `app/data/sample_dialogue_bank.json`. Bạn (hoặc giáo viên tiếng Anh) kiểm duyệt 1 lượt:
    - Đánh giá `quality_score` (từ 1.0 đến 5.0) cho từng câu.
    - Sửa những câu nghe còn gượng gạo để thành "mẫu chuẩn gold-set".
  - **File:** `app/data/sample_dialogue_bank.json`.

---

## 🏛️ GIAI ĐOẠN 2: Định nghĩa Tính cách Nhân vật, Topic & Phản hồi User (Thực hiện SAU TASK-007)

- [ ] **2.1. Phê duyệt Bảng tính cách 9 Nhân vật (Persona Data)**
  - **Mô tả:** Đọc và tinh chỉnh file định nghĩa tính cách của 9 nhân vật (`Alex`, `Lily`, `Oscar`, `Viktor`...). Đảm bảo mô tả giọng văn (`speech_style_notes`) và câu mẫu đặc trưng (`sample_phrases`) thể hiện đúng phong cách nhân vật mà không bị ràng buộc bởi level.
  - **File:** `app/data/persona_definitions.json`.

- [ ] **2.2. Gắn nhãn phân loại Scenario / Topic Bank**
  - **Mô tả:** Kiểm tra file danh sách topic/chủ đề (`topic_bank.json`). Xác định topic nào là `free_conversation` (tự do), topic nào là `structured_scenario` (nhập vai order đồ ăn, phỏng vấn...).
  - **File:** `app/data/topic_bank.json`.

- [ ] **2.3. Quy định nhãn Đánh giá Phản hồi Người dùng (Rating Categories)**
  - **Mô tả:** Xử lý danh sách các lý do đánh giá câu AI sinh ra: `hollow` ("Sáo rỗng"), `out_of_context` ("Sai ngữ cảnh"), `good` ("Tốt").
  - **File:** `app/data/feedback_log.json`.

---

## 🧪 GIAI ĐOẠN 3: Thu thập Data Nâng cao & Kiểm thử Thực tế (Thực hiện SAU TASK-009)

- [ ] **3.1. Cung cấp / Duyệt Gold-Set cho CEFR Level Classifier**
  - **Mô tả:** Duyệt tập transcript tiếng Anh thật của học viên (`cefr_gold_set.json`) để làm dữ liệu kiểm thử / huấn luyện mô hình đo trình độ tự động.
  - **File:** `app/data/cefr_gold_set.json`.

- [ ] **3.2. Đánh giá Trải nghiệm Người dùng (User Acceptance Test - UAT)**
  - **Mô tả:** Trực tiếp test thử voice conversation trên app web/mobile sau khi AI hoàn thành toàn bộ Tasks. Đánh giá tính năng bấm rate "Sáo rỗng", "Sai ngữ cảnh", "Tốt" trên giao diện UI.
