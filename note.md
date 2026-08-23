❌ Thiếu Overview Document chuẩn tên file (Section 6):
Phải có file My 10x Solution - {Your Name and Surname}.md (1-2 trang) trả lời 2 câu hỏi cốt lõi:
Câu 1: Vấn đề bạn giải quyết là gì? (3 câu tóm tắt, ai gặp vấn đề, 10x claim, non-goals).
Câu 2: Triển khai như thế nào? (Bảng đối chiếu 5 concepts, vị trí file code, lý do chọn 2 Swaps, hướng dẫn chạy).
❌ Thiếu README.md chuẩn cấu trúc Capstone (Section 5):
Cần bảng Concept -> Where it lives in the code.
Cần "5-minute demo path" tường minh từng bước (ví dụ: 1. Mở trình duyệt -> 2. Chọn nhân vật Lily -> 3. Nói vào mic -> 4. Quan sát phản hồi AI & điểm phát âm -> 5. Click vào từ để tra nghĩa 0ms).
❌ Thiếu Script Seed Data tự động 1 lệnh (scripts/seed_demo_data.py):
Giúp người chấm bài chỉ cần clone về, chạy 1 lệnh là có sẵn DB mẫu, từ vựng và kịch bản test mà không cần setup thủ công.
❌ Cần làm sạch Repository & Bảo mật Git (.gitignore & .env.example):
Đảm bảo không lộ API key (Gemini, Turso, ElevenLabs).
Cung cấp file .env.example rõ ràng.

graph TD
    A["Phase 1: Dọn rác & Clean Architecture"] --> B["Phase 2: Chuẩn hóa Demo & Seed Script"]
    B --> C["Phase 3: Viết Overview Document & README"]
    C --> D["Phase 4: Kiểm thử Clean Machine & Đóng gói"]


 Phase 2: Chuẩn bị 10x Metric & Demo Script
Xác định 10x Claim đo lường được (Quantifiable Metric):
Trước (Truyền thống): Luyện IELTS Speaking với gia sư 1-1 tốn 300.000đ - 500.000đ/giờ, phải đặt lịch trước, không có tra cứu từ vựng tức thì tại chỗ.
10x Sau (Duolingo Speak): Luyện nói 24/7 với 9 nhân vật AI đa ngữ điệu, thích ứng trình độ 20 cấp độ (A1 $\rightarrow$ C2), tra từ điển tức thì 0ms, chấm điểm phát âm & phản xạ thời gian thực với chi phí 0đ và độ trễ phản hồi < 500ms.
Tạo scripts/seed_demo_data.py:
Tự động kiểm tra / khởi tạo database SQLite mẫu nếu chạy lần đầu trên máy mới.
🔹 Phase 3: Soạn Thảo Tài Liệu Nộp Bài (Deliverables)
Tạo file My 10x Solution - {Tên Bạn}.md:
Phần 1: Problem & 10x Claim:
Problem (3 câu): Người học tiếng Anh thiếu môi trường luyện phản xạ giao tiếp tự nhiên không sợ sai; chi phí học gia sư quá đắt đỏ; các app học tập hiện tại chỉ là bài tập tĩnh nhàm chán.
Target Audience: Người ôn thi IELTS Speaking và người đi làm cần cải thiện phản xạ giao tiếp.
10x Claim: Tiết kiệm 100% chi phí luyện nói, tăng tốc độ tra cứu từ vựng lên 10 lần (0ms), cá nhân hóa 20 cấp độ khó theo thời gian thực.
Non-goals: Không làm app di động đa nền tảng phức tạp; không xây dựng hệ thống thanh toán hay quản lý tài khoản người dùng nhiều tầng.
Phần 2: Architecture & Concept Table:
Bảng chi tiết 5 concepts + 2 Swaps (có giải thích ngắn gọn tại sao không dùng Auth/PDF mà dùng RAG/Agent Guardrails).
Hướng dẫn cài đặt và chạy trong 2 lệnh.
Cập nhật README.md:
Thêm Architecture Diagram (Clean Architecture).
Thêm 5-Minute Demo Path chi tiết từng bước click/nói.
Thêm hướng dẫn Quickstart với uv hoặc pip.
🔹 Phase 4: Verification & Git Security Check
Bảo mật: Kiểm tra .gitignore đảm bảo không commit .env, log keys, hay file binary thừa.
Kiểm thử Clean Machine:
Chạy toàn bộ 233 test cases qua pytest.
Chạy python3 pipeline/scripts/verify.py kiểm tra Lint, Types, Security (Bandit).