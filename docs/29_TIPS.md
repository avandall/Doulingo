# ⚡ docs/29_TIPS.md — Cẩm Nang 29 Lời Khuyên Harness Engineering (Actionable Guide)

Tài liệu hướng dẫn hành động cụ thể cho toàn bộ **29 Lời khuyên (29 Tips)** từ Mirza Asceric. Sử dụng ngôn ngữ tiếng Việt kết hợp các thuật ngữ kỹ thuật tiêu chuẩn (`checkbox`, `interview`, `tests`, `logical unit`, `chrome devtool MCP`, `specs.md`, `git reset`, v.v.) để chỉ rõ **hành động cần thực hiện** trong từng tình huống.

---

## 🚀 Quy Trình 4 Bước Setup Agent AI Để Áp Dụng Harness & Ralph Loop (Cho Mọi Dự Án)

Để áp dụng thành công bộ 29 lời khuyên và tự động hóa chu trình **The Ralph Loop** (*Tip 17*), hãy thực hiện 4 bước thiết lập chuẩn sau:
1. **Bước 1 — Chuẩn Bị Bộ Docs Chuẩn (Harness Hub):**
   * Đặt 2 file gốc `README.md` (mục lục < 100 dòng) và `AGENTS.md` (hiến pháp AI) tại **thư mục gốc (`/`)**.
   * Đặt toàn bộ tài liệu chuyên sâu (`rules.md`, `architecture.md`, `specs.md`, `WORK_BOARD.md`, `BLOCKED.md`, `TECH_DEBT.md`, `29_TIPS.md`, `RALPH_LOOP.md`) vào thư mục `/docs/`.
2. **Bước 2 — Thiết Lập Bộ Kiểm Thử Tự Động (Automated Test Hook):**
   * Dự án **bắt buộc phải có lệnh test tự động** (ví dụ `pytest`, `npm test`, hoặc script CLI kiểm tra hệ thống). AI trong vòng lặp dựa vào Exit Code (`0`: thành công, `1`: thử lại, `2`: cản trở) để tự biết code đúng hay sai.
3. **Bước 3 — Cấu Hình CLI AI (Antigravity CLI / IDE Non-Interactive Mode):**
   * Cấu hình **Antigravity CLI/IDE** (hoặc CLI tương đương) ở chế độ non-interactive (không chờ người dùng gõ phím) và cấp quyền tự động cho các thao tác: đọc/viết file (`write_file`), chạy lệnh terminal (`run_command`) và `git commit`.
   * Bắt buộc bật tham số **`enable_subagents=True`** (trong Python SDK) hoặc cờ **`--enable-subagents`** (trong CLI) theo *Tip 9 (Spawn Helper Agents)* để main agent có thể gọi subagent tìm kiếm codebase.
4. **Bước 4 — Chạy Vòng Lặp Tự Động (`ralph_loop.sh`):**
   * Đặt script mẫu `ralph_loop.sh` ở thư mục gốc, cấp quyền thực thi `chmod +x ralph_loop.sh`, và khởi chạy qua đêm (ví dụ: `nohup ./ralph_loop.sh > ralph.log 2>&1 &` hoặc trong `tmux`).

---

## 🧠 I. Triết Lý & Thao Tác Hệ Thống File MD (Tips 1–7)

### 1. You Make the Decisions, AI Executes (Con Người Quyết Định, AI Thực Thi)
* **Hành động cần thực hiện:** Kỹ sư con người phải quyết định system architecture, API schema, design tokens và lựa chọn công nghệ cho dự án. Viết rõ các ràng buộc không thể thương lượng vào [`docs/rules.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/rules.md) và [`docs/architecture.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/architecture.md). Không cho phép AI tự ý thêm framework hay đổi database nếu không có human approval.

### 2. Write Detailed Docs (Viết Tài Liệu Chi Tiết)
* **Hành động cần thực hiện:** Soạn thảo tài liệu markdown (`*.md`) cụ thể từng bước, quy định rõ ràng chuẩn code style, type hints và cách error handling. Thay vì đưa ra yêu cầu mờ nhạt trong chat, hãy update trực tiếp tài liệu trong harness để mọi subagent trong các phiên sau đều đọc được và thực thi nhất quán.

### 3. Point Docs at Live Code (Trỏ Tài Liệu Vào Code Thực Tế)
* **Hành động cần thực hiện:** Trong mọi file tài liệu (ví dụ [`docs/architecture.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/architecture.md)), luôn gắn clickable links trỏ đúng file path, function name hoặc dòng code cụ thể (`app/main.py:L31-34`, `app/ai_engine.py`). Không mô tả chung chung hoặc mơ hồ về vị trí chức năng.

### 4. Main File Under 100 Lines (File Điều Phối Gốc Dưới 100 Dòng)
* **Hành động cần thực hiện:** Giữ file hub chính ([`README.md`](file:///home/avandall1999/Projects/Doulingo_speak/README.md) hoặc [`AGENTS.md`](file:///home/avandall1999/Projects/Doulingo_speak/AGENTS.md)) cực kỳ ngắn gọn, giới hạn nghiêm ngặt dưới 100 dòng. Viết một bảng mục lục (Table of Contents) dẫn link trực tiếp đến các file chuyên sâu (`specs.md`, `rules.md`, `TECH_DEBT.md`) để tiết kiệm context window cho AI.

### 5. Feed Outside Knowledge (Nạp Kiến Thức Bên Ngoài)
* **Hành động cần thực hiện:** Đưa các tài liệu API docs bên ngoài, bảng màu Duolingo (`#58CC02`), chuẩn CEFR 20 cấp độ, hay hướng dẫn FastAPI best practices vào docs/ hoặc references/. Đảm bảo AI nắm vững external dependencies và domain knowledge cần thiết trước khi viết code.

### 6. Track Tech Debt in Its Own File (Theo Dõi Nợ Kỹ Thuật Ở File Riêng)
* **Hành động cần thực hiện:** Khi đang lập trình tính năng mới mà phát hiện lỗi cũ hay TODO refactoring không khẩn cấp, **không được** để AI sửa ngay. Hãy mở file [`docs/TECH_DEBT.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/TECH_DEBT.md) để ghi nhận lại vấn đề, phân loại độ ưu tiên (`[HIGH]`, `[MEDIUM]`, `[LOW]`), và giữ cho active loop tiếp tục tập trung vào task hiện tại.

### 7. Smarter With Every Repetition (Thông Minh Hơn Sau Mỗi Lần Lặp)
* **Hành động cần thực hiện:** Mỗi khi gặp một bug rập khuôn, syntax error lặp đi lặp lại, hoặc AI dùng sai UI styling, ngay lập tức bổ sung một quy tắc phòng ngừa (preventive rule) vào [`docs/rules.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/rules.md) để các lượt lặp sau không bao giờ tái phạm sai lầm đó nữa.

---

## 🧼 II. Vệ Sinh Ngữ Cảnh & Phiên Làm Việc (Tips 8–11)

### 8. Never Compact Your Chat (Không Bao Giờ Nén/Tóm Tắt Lịch Sử Chat)
* **Hành động cần thực hiện:** Không dùng tính năng compact hay summarize khi chat dài vì sẽ làm mất ngữ cảnh và gây hallucinations. Khi context window gần đầy, hãy commit code, lưu trạng thái vào file markdown trong harness, tắt chat cũ và mở một clean session mới hoàn toàn.

### 9. Spawn Helper Agents (Tạo Các Agent Phụ Trợ)
* **Hành động cần thực hiện:** Sử dụng các subagent độc lập để thực hiện các tác vụ song song như tìm kiếm toàn bộ codebase (`grep_search`, `list_dir`), review pull request, hoặc nghiên cứu giải pháp kỹ thuật, tránh làm bẩn context của main agent.

### 10. Demand Detailed Commits (Yêu Cầu Commit Chi Tiết)
* **Hành động cần thực hiện:** Cấu hình và buộc AI khi commit git phải viết message theo cấu trúc chuẩn (`<type>(<scope>): <summary>`), mô tả cụ thể phần `- Why:` (lý do gốc rễ tại sao thay đổi), `- What:` (sửa đổi file nào), và `- Verification:` (đã chạy những tests/công cụ kiểm thử nào).

### 11. Fix a Bug Older Than You (Sửa Lỗi Lâu Đời Hơn Bạn)
* **Hành động cần thực hiện:** Open a chat, explain problem, retrieve context from your harness. Dig deep in the repo git (`git log`, `git blame`), give information like owner's github account, when implemented,... understand intentional constraints, then write tests to prevent same bugs trước khi chạm vào legacy code.

---

## 🎯 III. Spec & Kỷ Luật Quy Trình (Tips 12–16)

### 12. Build the Spec Together (Cùng Xây Dựng Đặc Tả Spec)
* **Hành động cần thực hiện:** Prompt ask the AI to interview you: ("Ask me about any unclear decision, every knowledge gap, everything that looks wrong in my plan.") Then ask AI to chunk full plan into logical unit (a group of work that belongs together - e.g a shared components, 1 endpoint with everything around it,...) với checkbox cho mỗi cái. AI tự plan tests cho mỗi feature trong mỗi [`docs/specs.md`] dùng chrome devtool MCP.

### 13. Define Done Visibly (Định Nghĩa Hoàn Thành Trực Quan)
* **Hành động cần thực hiện:** Sử dụng markdown checkboxes (`[ ]`, `[/]`, `[x]`) cho từng item trong [`docs/specs.md`]. Một task chỉ được đánh dấu là "Done" (`[x]`) khi đã hoàn thành code, chạy tests thành công và có bằng chứng xác nhận trực quan.

### 14. Implement by Logical Units (Triển Khai Theo Đơn Vị Logic)
* **Hành động cần thực hiện:** Chia nhỏ một feature lớn thành các logical unit nhỏ gọn (ví dụ: 1 database query + 1 API endpoint + 1 UI component tương ứng) để mỗi lần thực thi đều độc lập, có thể compile và test ngay lập tức mà không làm vỡ các module khác.

### 15. One Item, One Fresh Chat (Một Mục, Một Phiên Làm Việc Mới)
* **Hành động cần thực hiện:** Mỗi phiên chat (fresh session) chỉ chọn đúng 1 checkbox chưa xong từ [`docs/specs.md`] (`[ ]` -> `[/]`). Hoàn thành item đó, chạy test verification, đánh dấu `[x]`, commit code và kết thúc phiên. Không gộp nhiều task không liên quan vào cùng 1 chat session.

### 16. The `BLOCKED.md` Handbrake (Phanh Khẩn Cấp `BLOCKED.md`)
* **Hành động cần thực hiện:** Khi gặp lỗi không thể tự khắc phục (missing API key, library hỏng, requirement mâu thuẫn) sau 2 lần thử hợp lý, lập tức dừng lại! Ghi chi tiết lỗi, lệnh thực thi và nguyên nhân vào [`docs/BLOCKED.md`], trả về exit code `2`, và gọi con người vào xử lý thay vì rơi vào infinite retry loop.

---

## 🔁 IV. Tự Động Hóa & Vòng Lặp Ralph (Tips 17–24)

### 17. Automate It All: The Ralph Loop (Tự Động Hóa Vòng Lặp Ralph)
* **Hành động cần thực hiện:** Thay vì con người phải ngồi gõ lệnh mở từng chat session mới, hãy viết một bash script/runner tự động hóa toàn bộ chu trình phát triển qua đêm (gọi là **Ralph Loop**):
  1. **Khởi tạo phiên lặp (Loop Trigger):** Script khởi chạy một AI CLI agent ở chế độ tự động (non-interactive, không chờ con người gõ prompt).
  2. **Nạp luật chơi:** Agent tự động đọc [`AGENTS.md`] và [`docs/rules.md`] để hiểu các giới hạn kỹ thuật và chuẩn code.
  3. **Chọn đúng 1 mục (Pick Task):** Agent quét [`docs/specs.md`], tìm checkbox đầu tiên chưa xong (`[ ]`), đổi thành đang thực hiện (`[/]`) và cập nhật trạng thái sang `IN_PROGRESS` trên [`docs/WORK_BOARD.md`].
  4. **Code & Kiểm thử (Build & Test):** Agent viết code cho tính năng đó, sau đó tự động chạy bộ kiểm thử đã chỉ định trong spec (ví dụ: `pytest` hoặc test CLI).
  5. **Xử lý kết quả & Commit:**
     * **Nếu Test Pass:** Agent tạo git commit theo định dạng chuẩn (*Tip 10*), đánh dấu hoàn thành (`[x]`) trên `specs.md`, chuyển sang `DONE` trên `WORK_BOARD.md`, trả về **Exit Code `0`** và tự kết thúc session để script mở session mới cho tính năng tiếp theo.
     * **Nếu Test Fail (sau 2 lần thử):** Agent chạy `git reset --hard HEAD` để khôi phục code sạch (*Tip 18*), log lỗi chi tiết vào [`docs/BLOCKED.md`], và thoát với **Exit Code `2`** (*Tip 16, 19*) để dừng vòng lặp, báo động phanh khẩn cấp cho con người.

### 18. Recover With Git Reset (Phục Hồi Trạng Thái Với Git Reset)
* **Tại sao cần thiết:** Khi AI thử code mà fail, nếu bạn để AI "patch" đè lên code hỏng thì vòng lặp sẽ tích lũy nợ kỹ thuật và ngày càng xa rời trạng thái hoạt động. `git reset --hard` đảm bảo mỗi lần thử là một trang trắng sạch hoàn toàn.
* **Các bước thực hiện:**
  1. **Phát hiện thất bại:** Sau khi chạy `pytest tests/` hoặc `python ralph_loop.py`, kiểm tra exit code — nếu khác `0`, kích hoạt cơ chế phục hồi.
  2. **Reset ngay lập tức:** Chạy `git reset --hard HEAD` để hoàn toàn xóa bỏ mọi thay đổi chưa commit từ lần thử vừa rồi.
  3. **Không được patch thủ công:** Tuyệt đối không để AI hoặc con người sửa thêm vào code hỏng. Mỗi lần thử là code sạch từ `HEAD`.
  4. **Phân tích nguyên nhân gốc rễ:** Sau khi reset, KHÔNG code lại ngay. Truy vết tại sao thất bại: spec sai trong [`docs/specs.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/specs.md)? Rule thiếu trong [`docs/rules.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/rules.md)?
  5. **Cập nhật rules:** Ghi lại bài học vào [`docs/rules.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/rules.md) và [`docs/TECH_DEBT.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/TECH_DEBT.md) để lần sau AI không tái phạm cùng lỗi đó.
  6. **Thử lại với context mới:** Mở fresh chat session, load spec đã sửa, và thực thi lại từ đầu.

> [!WARNING]
> **Đừng build on top of broken code.** Nếu bạn để AI tiếp tục patch thêm lên code hỏng, lỗi sẽ chồng chất và không bao giờ có trạng thái ổn định. Một lần reset sạch luôn hiệu quả hơn 10 lần patch.

> [!CAUTION]
> `git reset --hard HEAD` sẽ **mất vĩnh viễn** mọi thay đổi chưa commit. Chỉ dùng trong automated loop khi bạn đã biết code đang hỏng và muốn xóa sạch nó.

### 19. Exit Codes for Every Ending (Mã Thoát Cho Mọi Kết Thúc)
* **Tại sao cần thiết:** Khi Ralph Loop chạy tự động qua đêm, bạn không thể ngồi đọc từng dòng log. Exit codes là ngôn ngữ giao tiếp giữa agent và harness runner — harness cần biết agent dừng vì lý do gì để quyết định bước tiếp theo một cách tự động.
* **Các bước thực hiện:**
  1. **Định nghĩa toàn bộ kịch bản kết thúc** ngay từ đầu khi thiết kế harness. Không để agent dừng mà không có exit code.
  2. **Triển khai bảng exit codes chuẩn** (mạu đã có trong [`ralph_loop.py`](file:///home/avandall1999/Projects/Doulingo_speak/ralph_loop.py)):
     | Exit Code | Tên trạng thái | Ý nghĩa | Hành động tự động của runner |
     |-----------|----------------|---------|-----------------------------|
     | `0` | `DONE` | Thành công, tests pass, đã commit | Mở session mới cho task tiếp theo |
     | `1` | `RETRY` | Lỗi nhẹ có thể thử lại (syntax error, network timeout) | `git reset --hard` rồi thử lại (tối đa 2 lần) |
     | `2` | `BLOCKED` | Tắc nghẽn nghiêm trọng, cần human can thiệp | Ghi [`docs/BLOCKED.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/BLOCKED.md), dừng loop, gửi alert |
     | `3` | `BUDGET` | Hết token/giới hạn API, cần đợi | Tự động schedule retry sau N giây |
     | `4` | `OUTAGE` | Groq/ElevenLabs/bên ngoài bị lỗi | Đợi và ping lại sau, không tính là lỗi của agent |
  3. **Nhúng exit code vào mọi script:** Mọi test script trong `tests/` đều phải kết thúc bằng `sys.exit(code)` tương ứng.
  4. **Harness runner đọc exit code:** [`ralph_loop.py`](file:///home/avandall1999/Projects/Doulingo_speak/ralph_loop.py) kiểm tra exit code sau mỗi vòng lặp và rẽ nhánh tự động theo bảng trên.
  5. **Log exit code vào iteration log:** Mỗi lần lặp phải ghi `exit_code=X` vào file log (xem Tip 20).

> [!IMPORTANT]
> Bạn cần định nghĩa sẵn exit codes **trước** khi chạy vòng lặp đầu tiên. Nếu thiếu, runner không biết phân biệt giữa "xong" và "bị kẹt", dẫn đến loop vô tận hoặc bỏ sót lỗi nghiêm trọng.

### 20. Log Every Iteration (Ghi Log Từng Lần Lặp)
* **Tại sao cần thiết:** Ralph Loop chạy nhanh. Nếu không có log riêng từng vòng lặp, khi một lần chạy thất bại bạn sẽ phải đọc hàng nghìn dòng log hỗn độn để tìm nguyên nhân. Mỗi iteration log là một "crime scene report" độc lập.
* **Các bước thực hiện:**
  1. **Tạo thư mục log chuyên biệt:** Thư mục `logs/iterations/` với file log riêng cho từng vòng chạy: `run_20260803_143000.log`.
  2. **Ghi tối thiểu các trường sau vào đầu mỗi log:**
     ```
     [ITERATION LOG]
     timestamp    : 2026-08-03 14:30:00
     spec_item    : "Feature: STT endpoint /api/transcribe"
     attempt_num  : 1 / 2
     git_sha_start: abc1234
     ```
  3. **Ghi kết quả cuối mỗi vòng:**
     ```
     [RESULT]
     exit_code    : 0 (DONE)
     git_sha_end  : def5678
     test_output  : "5 passed, 0 failed"
     duration_sec : 47
     ```
  4. **Không gộp log:** Mỗi vòng lặp phải có file log riêng. Không append vào cùng một file `all.log` vì sẽ khó phân tích khi số iteration tăng lên.
  5. **Tóm tắt vào WORK_BOARD.md:** Sau mỗi session thành công, agent ghi 1 dòng tóm tắt vào [`docs/WORK_BOARD.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/WORK_BOARD.md): `✅ [2026-08-03 14:30] STT endpoint - DONE (commit: def5678)`.

> [!TIP]
> Đặt log của từng iteration vào file riêng với timestamp trong tên file. Điều này giúp bạn tìm ngay log của lần chạy cụ thể khi cần debug.

### 21. Improve the Loop From Inside (Cải Tiến Vòng Lặp Từ Bên Trong)
* **Tại sao cần thiết:** Harness không phải là bất biến. Mỗi vòng lặp cung cấp dữ liệu thực tế về những gì không hoạt động. Nếu không cập nhật harness sau mỗi chu kỳ, bạn sẽ lặp lại cùng thất bại mãi mãi.
* **Các bước thực hiện:**
  1. **Cấp quyền cho agent cập nhật harness:** Cho phép agent được viết vào [`docs/rules.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/rules.md) và [`docs/TECH_DEBT.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/TECH_DEBT.md) khi phát hiện pattern lỗi mới.
  2. **Phân tích iteration log sau mỗi thất bại:** Sau mỗi exit code `1` hoặc `2`, hỏi agent: *"Nhìn lại log lần này, prompt/spec/rule nào cần cập nhật để tránh thất bại tương tự?"*
  3. **Cập nhật ngay, không để sau:** Ngay trong phiên hiện tại, agent hoặc engineer phải update tài liệu trước khi chạy lại.
  4. **Ghi ngắn gọn vào `docs/rules.md`:** Ví dụ: *"Rule: Luôn kiểm tra Groq API key tồn tại trước khi gọi STT service để tránh runtime crash".*
  5. **Reviewer agent định kỳ:** Chạy một reviewer agent hằng tuần chỉ để đọc toàn bộ iteration logs, tổng hợp patterns lỗi và đề xuất cải tiến harness.

> [!NOTE]
> Harness phải được xem là **sản phẩm sống** cần bảo trì. Mỗi lần loop thất bại là một bài học miễn phí — hãy tận dụng nó bằng cách cập nhật rules thay vì chỉ chạy lại.

### 22. Loop Everything Repetitive (Tự Động Hóa Mọi Khâu Lặp Lại)
* **Tại sao cần thiết:** Loop không chỉ để implement feature. Bất kỳ thao tác nào bạn làm thủ công nhiều lần (kiểm tra level CEFR, chạy linting, test toàn bộ endpoints) đều tốn thời gian và dễ bỏ sót.
* **Các bước thực hiện:**
  1. **Nhận diện công việc lặp lại trong Duolingo Speak:** Liệt kê mọi thao tác bạn làm thủ công nhiều lần trong tuần.
  2. **Đưa vào loop runner:** Mỗi thao tác lặp lại phải có script/agent tự động hóa nó.
  3. **Ví dụ các loop phụ trợ cụ thể cho dự án này:**
     - **CEFR Level QA Loop:** Tự động kiểm tra cả 20 cấp độ CEFR sau mỗi thay đổi STT engine.
     - **API Endpoints Loop:** Gọi thử tất cả endpoints (`/api/transcribe`, `/api/score`, `/api/feedback`) sau mỗi build, ghi kết quả vào `logs/qa/`.
     - **Translation QA Loop:** Kiểm tra bản dịch chính tả và ngữ pháp sau khi cập nhật language packs.
     - **Documentation Sync Loop:** Kiểm tra [`docs/architecture.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/architecture.md) còn khớp với code FastAPI thực tế không.
  4. **Lập lịch (schedule) cho từng loop:** Dùng cron job hoặc script launcher để các loop chạy đúng thời điểm cần thiết.

> [!TIP]
> Coi loop như **factory floor**: mọi công việc lặp lại trên dây chuyền đều nên được tự động hóa. Bạn chỉ nên can thiệp khi có vấn đề cần phán xét của con người.

### 23. Climb One Level at a Time (Nâng Cấp Hệ Thống Từng Bước Một)
* **Tại sao cần thiết:** Mỗi mức độ tự động hóa có các failure mode riêng. Nếu bạn nhảy thẳng lên multi-agent orchestration khi chưa thành thạo single-agent loop, bạn sẽ gặp tất cả failure modes cùng lúc.
* **5 cấp độ tự động hóa — leo từng bước:**
  | Cấp độ | Mô tả | Điều kiện để lên cấp |
  |--------|--------|----------------------|
  | **1** | Viết code thủ công (không dùng AI) | Hiểu codebase 100% |
  | **2** | Làm việc với AI từng chat session | Đã quen với prompt engineering cơ bản |
  | **3** | Chạy loop thủ công từng item | Loop đơn (1 item + 1 test) chạy được ≥ 5 lần |
  | **4** | Tự động hóa loop qua đêm | Loop tự động chạy ổn định ≥ 3 đêm liên tiếp |
  | **5** | Multi-agent orchestration | Cấp 4 đã hoạt động tin cậy với hàng chục items |
* **Các bước thực hiện:**
  1. **Đánh giá bạn đang ở cấp nào:** Xem lịch sử loop trong [`docs/WORK_BOARD.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/WORK_BOARD.md), số lần thành công/thất bại.
  2. **Chỉ lên cấp khi cấp hiện tại ổn định:** Tiêu chí: 3 lần chạy liên tiếp thành công, không cần can thiệp thủ công.
  3. **Lên cấp từng bước:** Thêm đúng một layer phức tạp mới rồi test kỹ trước khi thêm layer tiếp theo.
  4. **Luôn có khả năng thoái lui:** Nếu cấp cao hơn không ổn định, roll back về cấp thấp hơn đã proven.

> [!WARNING]
> Đừng nhảy từ cấp 2 lên cấp 5 chỉ vì thấy demo hấp dẫn. Multi-agent orchestration khi chưa có loop cơ bản ổn định = thảm họa khó debug.

### 24. Close the Loop With Live Logs & Chrome DevTools (Khép Kín Vòng Lặp Với Log Trực Tiếp & QA Tự Động)
* **Tại sao cần thiết:** Tốc độ cao mà không có verification = thảm họa. "Khép kín vòng lặp" nghĩa là agent phải tự kiểm tra kết quả thực tế, không chỉ kiểm tra code trên giấy.
* **Nguyên tắc cốt lõi: "Trust but verify"** — cho phép agent tự do thực thi, nhưng phải có cơ chế kiểm tra thực tế sau mỗi bước.
* **Các bước thực hiện (4 bước trong mỗi lượt chạy):**
  1. **Bước 1 — Build/Implement:** Agent chỉnh sửa mã nguồn cho 1 Đơn Vị Logic từ [`docs/specs.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/specs.md).
  2. **Bước 2 — Monitor Live Server Logs:** Agent khởi chạy `uv run uvicorn app.main:app` và **stream log thực tế (stdout/stderr)** để phát hiện ngay mọi exception, traceback, HTTP 500 theo thời gian thực.
  3. **Bước 3 — Self-QA bằng Chrome DevTools MCP:** Agent dùng **Chrome DevTools MCP** mở trang/gọi API vừa tạo, thao tác y hệt người dùng thật:
     - Click các nút tương tác, nhập text
     - Thử gửi audio ghi âm (cho STT endpoint)
     - Kiểm tra DOM output và score display
     - Đọc **Console** tab để tìm JavaScript errors
     - Đọc **Network** tab để verify API calls trả về đúng status code
  4. **Bước 4 — Diagnose & Self-Fix:**
     - **Nếu QA Pass:** Không có lỗi Console, server log trả về 200/201 → agent commit theo chuẩn Conventional Commits (*Tip 10*) và đánh dấu `[x]`.
     - **Nếu QA Fail:** Agent đọc traceback từ Live Log hoặc error từ browser, tự chuẩn đoán nguyên nhân, sửa code trong phiên đó. Nếu sau 2 lần vẫn fail → `git reset --hard` (*Tip 18*) và log vào [`docs/BLOCKED.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/BLOCKED.md).

> [!IMPORTANT]
> **Đừng chỉ dùng static analysis.** Unit tests và linting là cần thiết nhưng chưa đủ — chúng không phát hiện được runtime behavior sai hay API response format không khớp. Chrome DevTools MCP giúp đóng khoảng trống này bằng cách test như người dùng thực.

> [!TIP]
> Thứ tự kiểm tra ưu tiên: **Server Log** (phát hiện crash ngay) → **Unit Test** (logic đúng không) → **Browser/Chrome DevTools** (UX và API response đúng không). Không bỏ qua bất kỳ lớp nào.

---

## 🚀 V. Triển Khai Đa Agent & Mở Rộng (Tips 25–29)

### 25. Replicate Websites Like a Pro (Sao Chép Giao Diện Chuyên Nghiệp)
* **Tại sao cần thiết:** AI thường tái tạo UI theo "tinh thần" chứ không theo chi tiết chính xác. Validation nhiều lớp giúp đạt độ chính xác pixel-perfect so với Duolingo design gốc.
* **Các bước thực hiện (multi-layer validation):**
  1. **Cung cấp design tokens đầy đủ trước khi code:** Design tokens Duolingo (`--duo-primary-green: #58CC02`, `--duo-dark-green: #58A700`, `border-radius: 16px`, 3D button effect CSS, v.v.). Ghi rõ trong `docs/architecture.md`.
  2. **Layer 1 — Code Review:** So sánh CSS/styles với tài liệu design tokens. Kiểm tra từng property có hệ thống.
  3. **Layer 2 — Computed Style qua Chrome DevTools MCP:** Lấy `getComputedStyle()` của elements thực tế, so sánh với design spec. Phát hiện CSS bị override không mong muốn.
  4. **Layer 3 — Pixel-perfect diffing:** Chụp ảnh màn hình trang đang build, so sánh với ảnh mockup/design gốc. Xác định vùng khác biệt.
  5. **Layer 4 — Real user testing:** Dùng agent thao tác như người dùng thật: click button, hover element, scroll, resize viewport. Kiểm tra responsive layout.
  6. **Ghi lại deviation vào docs:** Mọi sai lệch so với design gốc phải được ghi chú và phân loại: ý định (intentional) hay lỗi cần sửa.

> [!TIP]
> Ghi đầy đủ design tokens Duolingo vào [`docs/architecture.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/architecture.md). Agent đọc file này sẽ tái tạo chính xác hơn nhiều so với việc chỉ "nhìn" vào ảnh mockup.

### 26. Schedule Reviewer Agents (Lập Lịch Cho Agent Kiểm Duyệt)
* **Tại sao cần thiết:** Khi loop chạy nhanh, code mới được commit liên tục. Không ai có thể review thủ công từng commit. Reviewer agent chạy định kỳ như một "QA engineer tự động" — bắt lỗi hồi tố và đảm bảo code luôn khớp với specs.
* **Các bước thực hiện:**
  1. **Tạo reviewer agent chuyên biệt (không kiêm nhiệm):** Reviewer agent chỉ làm một việc: đọc code + đối chiếu spec/rules + báo cáo. Không implement, không sửa code phức tạp.
  2. **Lập lịch chạy định kỳ:** Ví dụ: mỗi sáng 8:00 sau khi loop đêm hoàn thành, hoặc sau mỗi N commits mới.
  3. **Reviewer agent làm gì trong dự án này:**
     - Đọc commits mới (`git log --since=yesterday`) trong repo Duolingo Speak
     - Đối chiếu với [`docs/specs.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/specs.md) và [`docs/rules.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/rules.md)
     - Tìm: logic sai trong STT/scoring, vi phạm design tokens Duolingo, documentation chưa cập nhật
     - Phát hiện documentation conflict giữa các file docs
  4. **Phân loại kết quả:**
     - **Safe fixes:** Tự sửa và commit (ví dụ: cập nhật docstring lỗi thời)
     - **Issues cần human review:** Ghi vào [`docs/WORK_BOARD.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/WORK_BOARD.md) dưới cột `READY_FOR_REVIEW`
  5. **Tích hợp vào CI/CD:** Có thể chạy reviewer agent như một CI job sau mỗi PR.

> [!NOTE]
> Reviewer agent phải có access đến cả code lẫn docs. Đặc biệt hữu ích trong giai đoạn sprint nhanh khi loop implement nhiều features liên tiếp.

### 27. Make Two Agents Argue (Cho Hai Agent Tranh Luận)
* **Tại sao cần thiết:** Một agent đơn lẻ thường bị confirmation bias. Khi có 2 agents tranh luận, thiết kế phải đứng vững trước sự phản biện. Design sống sót sau "cuộc chiến" mới thực sự tốt.
* **Khi nào dùng:** Trước mọi quyết định kiến trúc lớn (chọn STT engine, thiết kế scoring system, API schema quan trọng).
* **Các bước thực hiện:**
  1. **Soạn thảo design proposal:** Mô tả ngắn gọn thiết kế đang cân nhắc.
  2. **Khởi chạy Proposer Agent** trong một chat session độc lập:
     - Trình bày ưu điểm của thiết kế
     - Liệt kê các use cases nó xử lý tốt
     - Đề xuất implementation plan chi tiết
  3. **Khởi chạy Critic/Attacker Agent** trong một chat session độc lập khác:
     - Tìm mọi điểm yếu của thiết kế
     - Xác định edge cases chưa xử lý
     - Đề xuất các thiết kế đơn giản hơn có thể thay thế
     - Chỉ ra risk và failure scenarios
  4. **Tổng hợp vào [`docs/WORK_BOARD.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/WORK_BOARD.md):** Ghi toàn bộ arguments của cả 2 phía.
  5. **Engineer con người phán xét:** Chọn thiết kế tốt nhất, ghi quyết định vào [`docs/architecture.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/architecture.md).

> [!IMPORTANT]
> **Cả 2 agents không được biết nhau tồn tại.** Chạy chúng trong 2 chat sessions độc lập. Nếu chúng biết nhau, chúng sẽ tend to agree thay vì thực sự phản biện.

> [!TIP]
> Prompt mạnh nhất cho Critic Agent: *"Assume this design has at least 3 critical flaws. Your job is to find them and propose simpler alternatives. Be ruthless."*

### 28. Choose Your Shipping Mode (Chọn Chế Độ Vận Hành)
* **Tại sao cần thiết:** Không có chế độ nào phù hợp với mọi tình huống. Dùng sai chế độ sẽ tốn tokens và tạo ra code sai hướng.
* **Hai chế độ và khi nào dùng:**

  **🔵 Sequential Mode (Chế độ Tuần Tự — Khuyến nghị cho người mới):**
  - Agent làm việc **trên một branch duy nhất**
  - Hoàn thành một item → engineer review → merge → tiếp tục item tiếp theo
  - Phù hợp khi: feature chưa được spec kỹ, rủi ro cao, cần nhiều human judgment
  - Ưu điểm: dễ kiểm soát, ít risk, dễ debug

  **🟠 Parallel Mode (Chế độ Song Song — Dành cho team có harness trưởng thành):**
  - Nhiều agents làm việc **đồng thời trên các feature branches khác nhau**
  - Cần thêm một **Senior Reviewer Agent** theo dõi repository, đọc PR và manage merging
  - Phù hợp khi: specs rõ ràng, test coverage tốt, loop đã chạy ổn định ở Sequential Mode
  - Ưu điểm: tốc độ cao gấp bội

* **Các bước thực hiện:**
  1. **Bắt đầu với Sequential Mode:** Chạy ít nhất 10 items thành công trước khi cân nhắc Parallel.
  2. **Chuyển sang Parallel khi:** Test coverage ≥ 80%, specs đã chuẩn hóa, Reviewer Agent đã được setup và test.
  3. **Luôn khai báo chế độ trong [`AGENTS.md`](file:///home/avandall1999/Projects/Doulingo_speak/AGENTS.md):** Ghi rõ chế độ hiện tại để mọi agent đọc và biết cách vận hành.
  4. **Interactive Pair Mode:** Khi muốn explore ideas, không có spec, hoặc đang debug vấn đề phức tạp — chuyển sang interactive.

> [!WARNING]
> **Đừng chạy Parallel Mode khi chưa sẵn sàng.** Nhiều agents chạy đồng thời mà không có Reviewer Agent sẽ tạo ra merge conflicts và rất khó debug.

### 29. Add a Work Board (Thêm Bảng Quản Lý Công Việc)
* **Tại sao cần thiết:** Khi loop scale lên, bạn cần một "control panel" duy nhất để thấy tất cả: item nào đang chạy, ai đang làm, chi phí bao nhiêu, kết quả ra sao. [`docs/WORK_BOARD.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/WORK_BOARD.md) chính là control panel đó.
* **Các bước thực hiện:**
  1. **Cấu trúc cột Kanban trong [`docs/WORK_BOARD.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/WORK_BOARD.md):**
     ```
     ## 📋 TODO
     | Item | Priority | Est. | Spec Link |

     ## 🔄 IN_PROGRESS
     | Item | Agent | Started | Branch |

     ## 👀 READY_FOR_REVIEW
     | Item | Agent | Commit | Proof of Work |

     ## ✅ DONE
     | Item | Agent | Commit | Duration | Cost |

     ## 🚫 BLOCKED
     | Item | Blocker | Logged | BLOCKED.md link |
     ```
  2. **"Proof of Work" là bắt buộc:** Mỗi item được chuyển sang DONE phải có: diff link (thay đổi gì), test results (pass/fail numbers), và evidence (screenshot, API response, v.v.).
  3. **Track cost mỗi run:** Ghi token usage và estimated $ cost cho mỗi iteration. Khi scale lên, điều này giúp optimize prompt length và model selection.
  4. **Work Board là nguồn sự thật duy nhất:** Mọi agent và engineer đều đọc WORK_BOARD.md để biết trạng thái thực tế — không hỏi nhau qua chat.
  5. **Tự động hóa cập nhật:** Agent phải tự cập nhật WORK_BOARD.md khi bắt đầu (`TODO → IN_PROGRESS`) và khi kết thúc (`IN_PROGRESS → DONE/BLOCKED`).

> [!NOTE]
> Work Board không phải Jira hay Trello — nó là markdown file đơn giản nằm trong repo, được cả AI agent và human đọc. Sức mạnh là ở tính **visible từ cả hai phía**.

> [!TIP]
> Khi có nhiều agents chạy song song (Tip 28), Work Board trở nên quan trọng hơn bao giờ hết. Đây là cách duy nhất để tránh 2 agents cùng nhận 1 task.

---

> [!TIP]
> **Quy Tắc Vàng:** *"Harness chính là sản phẩm; code chỉ là kết quả đầu ra."*
