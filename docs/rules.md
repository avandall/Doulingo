# 📜 Quy Tắc & Chuẩn Mực Kỹ Thuật Cho AI Agent (Agent Rules - Harness Engineering)

Tài liệu này xác định các nguyên tắc bắt buộc mà mọi AI Agent chạy trong luồng tự động (**Ralph Loop**) phải tuân thủ nghiêm ngặt khi xây dựng dự án **Duolingo Speak**.

---

## 1. Nguyên Tắc Cốt Lõi Của Ralph Loop (Harness Engineering DNA)

### 1.1 "One Item, One Fresh Chat" (Tip 15 - Mỗi lần lặp chỉ giải quyết 1 task duy nhất)
- Trong mỗi lượt lặp lại của Ralph Loop, Agent **CHỈ ĐƯỢC CHỌN VÀ THỰC HIỆN ĐÚNG 01 TASK ĐẦU TIÊN CHƯA HOÀN THÀNH (`- [ ]`)** trong tài liệu `docs/specs.md`.
- Tuyệt đối không làm gộp nhiều task, không tự ý mở rộng phạm vi công việc sang các task tiếp theo.

### 1.2 "Don't Describe Code, Point To It" (Tip 4 & 5 - Tham chiếu code thực tế thay vì suy đoán)
- Không tự bịa cấu trúc file mới nếu đã có định nghĩa trong `docs/architecture.md`.
- Khi bổ sung tính năng mới cho FastAPI (`app/`), hãy nhìn vào các module hiện có (`app/ai_engine.py`, `app/scenarios.py`, `app/main.py`) để tuân thủ đúng phong cách viết code, cách khai báo typing, Pydantic models và error handling.

### 1.3 "Never Compact Your Chat" (Tip 8 - Không nén ngữ cảnh)
- Mỗi lượt lặp lại của Ralph Loop bắt buộc là một phiên chạy độc lập (Fresh sub-process).
- Không được giả định ghi nhớ thông tin từ các lượt chạy trước; luôn đọc lại `docs/architecture.md`, `docs/rules.md` và `docs/specs.md` từ filesystem.

### 1.4 "Recover with Git Reset" (Tip 18 - Phục hồi bằng Git nếu thất bại)
- Nếu một thay đổi gây ra lỗi cú pháp (Syntax error) hoặc làm hỏng test, hệ thống harness sẽ kích hoạt `git reset --hard` để khôi phục về trạng thái commit ổn định gần nhất.
- Agent không thực hiện các nỗ lực vá lỗi vô tận trong cùng một iteration.

---

## 2. Quy Tắc Kỹ Thuật Backend (Python / FastAPI)

1. **Quản Lý Môi Trường & Thư Viện:**
   - Sử dụng trình quản lý gói `uv` (Fast Python package installer).
   - Kiểm tra cú pháp sau mỗi chỉnh sửa backend:
     ```bash
     python -m py_compile main.py app/*.py
     ```
2. **Mock & Fallback Bắt Buộc:**
   - Khi gọi API bên ngoài (OpenAI, Gemini, Edge-TTS), luôn phải có khối `try-except` và cơ chế fallback về Mock Data để ứng dụng có thể chạy cục bộ hoặc qua đêm mà không bị crash do lỗi kết nối/API Key.
3. **Định Dạng Code:**
   - Sử dụng typing rõ ràng (Type hints: `str`, `int`, `dict`, `List`, `Optional`...).
   - Viết docstrings cho tất cả public APIs theo phong cách ngắn gọn, dễ bảo trì.

---

## 3. Quy Tắc Kỹ Thuật Frontend (Duolingo UI DNA)

1. **Tuân Thủ Bảng Màu & Nút Bấm Duolingo:**
   - Tất cả nút hành động phải tuân theo phong cách **3D Feather Button**: có bo góc (`border-radius: 16px`), màu nền xanh lá `#58CC02`, viền dưới 3D `#46A302`.
2. **Responsive & Mobile-First:**
   - Giao diện luyện nói phải hiển thị hoàn hảo trên cả trình duyệt điện thoại (Mobile 375px-430px) và màn hình máy tính (Desktop).
3. **Trải Nghiệm Hội Thoại Liên Tục:**
   - Khi người dùng nói, hiệu ứng sóng âm (Waveform Visualizer) phải phản hồi chuyển động sinh động.
   - Khi nhận phản hồi từ AI, hiển thị tức thì thẻ chấm điểm và gợi ý ngữ pháp không làm đứt đoạn mạch trò chuyện.

---

## 4. Quy Tắc Bảo Mật API & Dịch Thuật Văn Nói (API Security & Localization DNA)

1. **Không Lộ API Key Nhạy Cảm (Masked Logging Only):**
   - Khi ghi log sự kiện gọi LLM hoặc kiểm tra quota, **BẮT BUỘC che (mask) phần giữa của API Key**, chỉ giữ lại 4 ký tự đầu và 4 ký tự cuối (ví dụ: `gsk_...9aB`, `AIza...x8A9`). Tuyệt đối không in toàn bộ API Key raw ra file log hay console.
2. **Quy tắc chuyển đổi Key (Automated Failover & Quota Rotation):**
   - Mọi khối gọi API trong `app/ai_engine.py` phải xử lý lỗi HTTP `429 Too Many Requests` và lỗi Quota Exceeded. Khi lỗi xảy ra, phải log thông báo chuyển key và lập tức gọi sang API Key tiếp theo.
3. **Quy tắc Dịch Thuật Văn Nói (Spoken Vietnamese Only):**
   - Khi sửa đổi hàm dịch thuật `_professional_vietnamese_localization`:
     - Không được đặt `temperature` dưới `0.35` để tránh câu dịch thô cứng kiểu word-by-word.
     - Luôn tuân theo xưng hô ngữ cảnh (*em - anh, tớ - cậu, mình - bạn*) và thêm từ đệm văn nói tự nhiên (*nhé, nha, đấy, đi, cơ mà, chứ, nè, vậy*).

---

## 5. Quy Tắc Đối Chất & Thẩm Định Mã Nguồn (Maker-Checker / Adversarial Review - Tip 19 & 26)

1. **Mô Hình Hai Vai (Generator - Validator):**
   - Không một dòng code nào được đánh dấu hoàn thành nếu chưa trải qua khâu thẩm định chéo.
   - Khi viết code cho bất kỳ task nào, AI bắt buộc phải đóng 2 vai song song:
     - **[CODER]:** Tạo ra giải pháp.
     - **[SENIOR REVIEWER]:** Soi xét khắt khe code vừa viết theo 4 tiêu chí sống còn:
       1) **Bảo mật API:** Có che masked key (`gsk_...9aB`) và xử lý rotate HTTP 429 chưa?
       2) **Dịch thuật văn nói:** `temperature` >= 0.35, xưng hô đàm thoại (*em - anh*) chưa?
       3) **UI Duolingo:** Nút 3D Feather Button có màu `#58CC02` và đổ bóng `#46A302` chưa?
       4) **Mock Fallback:** Mất mạng/mất API key ứng dụng có bị crash không?
2. **Vòng Lặp Tự Sửa Lỗi (Self-Correction Loop):**
   - Nếu Reviewer chỉ ra bất kỳ vi phạm nào, Coder phải lập tức sửa mã nguồn và nộp lại cho đến khi Reviewer xác nhận `"VERIFIED_OK"`.

---

## 6. Quy Trình Hoàn Thành Một Task (Definition of Done)

Trước khi đánh dấu `[x]` cho một task trong `docs/specs.md`:
1. Viết code hoàn chỉnh cho task và vượt qua vòng thẩm định của **Reviewer (VERIFIED_OK)**.
2. Chạy kiểm thử tự động (syntax check / test cases) để đảm bảo không có lỗi:
   ```bash
   python -m py_compile main.py app/*.py
   ```
3. Cập nhật `docs/specs.md`: Đổi dấu `- [ ]` thành `- [x]` tại đúng mục vừa làm.
4. Tạo một Git Commit với thông điệp rõ ràng theo định dạng Conventional Commits:
   - `feat: ...`, `fix: ...`, `docs: ...`, `style: ...`, hoặc `refactor: ...`
