# ⚡ docs/29_TIPS.md — Cẩm Nang 29 Lời Khuyên Harness Engineering (Generic Actionable Guide)

Tài liệu hướng dẫn hành động cụ thể cho toàn bộ **29 Lời khuyên (29 Tips)** từ Mirza Asceric. Sử dụng ngôn ngữ tiếng Việt kết hợp các thuật ngữ kỹ thuật tiêu chuẩn (`checkbox`, `interview`, `tests`, `logical unit`, `chrome devtool MCP`, `specs.md`, `git reset`, v.v.) để chỉ rõ **hành động cần thực hiện** trong từng tình huống cho bất kỳ dự án phần mềm nào.

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
* **Hành động cần thực hiện:** Kỹ sư con người phải quyết định system architecture, API schema, design tokens và lựa chọn công nghệ cho dự án. Viết rõ các ràng buộc không thể thương lượng vào `docs/rules.md` và `docs/architecture.md`. Không cho phép AI tự ý thêm framework hay đổi database nếu không có human approval.

### 2. Write Detailed Docs (Viết Tài Liệu Chi Tiết)
* **Hành động cần thực hiện:** Soạn thảo tài liệu markdown (`*.md`) cụ thể từng bước, quy định rõ ràng chuẩn code style, type hints và cách error handling. Thay vì đưa ra yêu cầu mờ nhạt trong chat, hãy update trực tiếp tài liệu trong harness để mọi subagent trong các phiên sau đều đọc được và thực thi nhất quán.

### 3. Point Docs at Live Code (Trỏ Tài Liệu Vào Code Thực Tế)
* **Hành động cần thực hiện:** Trong mọi file tài liệu (ví dụ `docs/architecture.md`), luôn gắn clickable links trỏ đúng file path, function name hoặc dòng code cụ thể (`src/main.py:L31-34`). Không mô tả chung chung hoặc mơ hồ về vị trí chức năng.

### 4. Main File Under 100 Lines (File Điều Phối Gốc Dưới 100 Dòng)
* **Hành động cần thực hiện:** Giữ file hub chính (`README.md` hoặc `AGENTS.md`) cực kỳ ngắn gọn, giới hạn nghiêm ngặt dưới 100 dòng. Viết một bảng mục lục (Table of Contents) dẫn link trực tiếp đến các file chuyên sâu (`specs.md`, `rules.md`, `TECH_DEBT.md`) để tiết kiệm context window cho AI.

### 5. Document Caching and Precomputing (Tài Liệu Hóa Lớp Cache & Tính Toán Trước)
* **Hành động cần thực hiện:** Viết tài liệu tường minh trong `docs/architecture.md` cho toàn bộ các lớp bộ nhớ đệm (in-memory cache, Redis, SQLite cache) và các giới hạn tốc độ API (rate limits) để AI hiểu và không bao giờ viết code gọi lại external API phung phí hoặc phá vỡ cấu trúc cache.

### 6. Refactor When You Want to (Tái Cấu Trúc Khi Bạn Muốn)
* **Hành động cần thực hiện:** Không cho phép AI tự động refactor hoặc làm sạch code "tiện tay" khi đang phát triển một tính năng mới. Khi con người muốn refactor, hãy tạo một checkbox riêng biệt trong `docs/TECH_DEBT.md` và yêu cầu AI thực thi độc lập trong một clean chat session mới.

### 7. Smarter With Every Repetition (Thông Minh Hơn Sau Mỗi Lần Lặp)
* **Hành động cần thực hiện:** Mỗi khi phát hiện một bug lặp lại hoặc lỗi AI hiểu sai schema, kỹ sư lập tức cập nhật luật mới vào `docs/rules.md` hoặc thêm hướng dẫn phòng tránh vào tài liệu chuyên sâu để AI trong các lượt sau không bao giờ tái phạm.

---

## 💬 II. Vệ Sinh Giao Tiếp & Quản Lý Ngữ Cảnh (Tips 8–11)

### 8. Never Compact Your Chat (Không Bao Giờ Nén Ngữ Cảnh)
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
* **Hành động cần thực hiện:** Prompt ask the AI to interview you: ("Ask me about any unclear decision, every knowledge gap, everything that looks wrong in my plan.") Then ask AI to chunk full plan into logical unit (a group of work that belongs together - e.g a shared components, 1 endpoint with everything around it,...) với checkbox cho mỗi cái. AI tự plan tests cho mỗi feature trong mỗi `docs/specs.md` dùng chrome devtool MCP.

### 13. Define Done Visibly (Định Nghĩa Hoàn Thành Trực Quan)
* **Hành động cần thực hiện:** Sử dụng markdown checkboxes (`[ ]`, `[/]`, `[x]`) cho từng item trong `docs/specs.md`. Một task chỉ được đánh dấu là "Done" (`[x]`) khi đã hoàn thành code, chạy tests thành công và có bằng chứng xác nhận trực quan.

### 14. Implement by Logical Units (Triển Khai Theo Đơn Vị Logic)
* **Hành động cần thực hiện:** Chia nhỏ một feature lớn thành các logical unit nhỏ gọn (ví dụ: 1 database query + 1 API endpoint + 1 UI component tương ứng) để mỗi lần thực thi đều độc lập, có thể compile và test ngay lập tức mà không làm vỡ các module khác.

### 15. One Item, One Fresh Chat (Một Mục, Một Phiên Làm Việc Mới)
* **Hành động cần thực hiện:** Mỗi phiên chat (fresh session) chỉ chọn đúng 1 checkbox chưa xong từ `docs/specs.md` (`[ ]` -> `[/]`). Hoàn thành item đó, chạy test verification, đánh dấu `[x]`, commit code và kết thúc phiên. Không gộp nhiều task không liên quan vào cùng 1 chat session.

### 16. The `BLOCKED.md` Handbrake (Phanh Khẩn Cấp `BLOCKED.md`)
* **Hành động cần thực hiện:** Khi gặp lỗi không thể tự khắc phục (missing API key, library hỏng, requirement mâu thuẫn) sau 2 lần thử hợp lý, lập tức dừng lại! Ghi chi tiết lỗi, lệnh thực thi và nguyên nhân vào `docs/BLOCKED.md`, trả về exit code `2`, và gọi con người vào xử lý thay vì rơi vào infinite retry loop.

---

## 🔁 IV. Tự Động Hóa & Vòng Lặp Ralph (Tips 17–24)

### 17. Automate It All: The Ralph Loop (Tự Động Hóa Vòng Lặp Ralph)
* **Hành động cần thực hiện:** Thay vì con người phải ngồi gõ lệnh mở từng chat session mới, hãy viết một bash script/runner tự động hóa toàn bộ chu trình phát triển qua đêm (gọi là **Ralph Loop**):
  1. **Khởi tạo phiên lặp (Loop Trigger):** Script khởi chạy một AI CLI agent ở chế độ tự động (non-interactive, không chờ con người gõ prompt).
  2. **Nạp luật chơi:** Agent tự động đọc `AGENTS.md` và `docs/rules.md` để hiểu các giới hạn kỹ thuật và chuẩn code.
  3. **Chọn đúng 1 mục (Pick Task):** Agent quét `docs/specs.md`, tìm checkbox đầu tiên chưa xong (`[ ]`), đổi thành đang thực hiện (`[/]`) và cập nhật trạng thái sang `IN_PROGRESS` trên `docs/WORK_BOARD.md`.
  4. **Code & Kiểm thử (Build & Test):** Agent viết code cho tính năng đó, sau đó tự động chạy bộ kiểm thử đã chỉ định trong spec (ví dụ: `pytest` hoặc test CLI).
  5. **Xử lý kết quả & Commit:**
     * **Nếu Test Pass:** Agent tạo git commit theo định dạng chuẩn (*Tip 10*), đánh dấu hoàn thành (`[x]`) trên `specs.md`, chuyển sang `DONE` trên `WORK_BOARD.md`, trả về **Exit Code `0`** và tự kết thúc session để script mở session mới cho tính năng tiếp theo.
     * **Nếu Test Fail (sau 2 lần thử):** Agent chạy `git reset --hard HEAD` để khôi phục code sạch (*Tip 18*), log lỗi chi tiết vào `docs/BLOCKED.md`, và thoát với **Exit Code `2`** (*Tip 16, 19*) để dừng vòng lặp, báo động phanh khẩn cấp cho con người.

### 18. Recover With Git Reset (Phục Hồi Trạng Thái Với Git Reset)
* **Tại sao cần thiết:** Khi AI thử code mà fail, nếu bạn để AI "patch" đè lên code hỏng thì vòng lặp sẽ tích lũy nợ kỹ thuật và ngày càng xa rời trạng thái hoạt động. `git reset --hard` đảm bảo mỗi lần thử là một trang trắng sạch hoàn toàn.
* **Các bước thực hiện:**
  1. **Phát hiện thất bại:** Sau khi chạy bộ tests (`pytest`, `npm test`, v.v.), kiểm tra exit code — nếu khác `0`, kích hoạt cơ chế phục hồi.
  2. **Reset ngay lập tức:** Chạy `git reset --hard HEAD` để hoàn toàn xóa bỏ mọi thay đổi chưa commit từ lần thử vừa rồi.
  3. **Không được patch thủ công:** Tuyệt đối không để AI hoặc con người sửa thêm vào code hỏng. Mỗi lần thử là code sạch từ `HEAD`.
  4. **Phân tích nguyên nhân gốc rễ:** Sau khi reset, KHÔNG code lại ngay. Hãy truy vết tại sao thất bại: spec sai? Rule thiếu? Prompt chưa rõ? Sửa tài liệu trước.
  5. **Cập nhật rules:** Ghi lại bài học vào `docs/rules.md` để lần sau AI không tái phạm cùng lỗi đó.
  6. **Thử lại với context mới:** Mở fresh chat session, load spec đã sửa, và thực thi lại từ đầu.

> [!WARNING]
> **Đừng build on top of broken code.** Nếu bạn để AI tiếp tục patch thêm lên code hỏng, lỗi sẽ chồng chất và không bao giờ có trạng thái ổn định. Một lần reset sạch luôn hiệu quả hơn 10 lần patch.

> [!CAUTION]
> `git reset --hard HEAD` sẽ **mất vĩnh viễn** mọi thay đổi chưa commit. Chỉ dùng trong automated loop khi bạn đã biết code đang hỏng và muốn xóa sạch nó.

### 19. Exit Codes for Every Ending (Mã Thoát Cho Mọi Kết Thúc)
* **Tại sao cần thiết:** Khi loop chạy tự động qua đêm, bạn không thể ngồi đọc từng dòng log. Exit codes là ngôn ngữ giao tiếp giữa agent và harness runner — harness cần biết agent dừng vì lý do gì để quyết định bước tiếp theo một cách tự động.
* **Các bước thực hiện:**
  1. **Định nghĩa toàn bộ kịch bản kết thúc có thể xảy ra** ngay từ đầu khi thiết kế harness. Không để agent dừng mà không có exit code.
  2. **Triển khai bảng exit codes chuẩn:**
     | Exit Code | Tên trạng thái | Ý nghĩa | Hành động tự động của runner |
     |-----------|----------------|---------|-----------------------------|
     | `0` | `DONE` | Thành công, tests pass, đã commit | Mở session mới cho task tiếp theo |
     | `1` | `RETRY` | Lỗi nhẹ, có thể thử lại (syntax error, timeout mạng) | Chạy `git reset --hard` rồi thử lại (tối đa 2 lần) |
     | `2` | `BLOCKED` | Tắc nghẽn nghiêm trọng, cần human can thiệp | Ghi `BLOCKED.md`, dừng loop, gửi alert |
     | `3` | `BUDGET` | Hết token/giới hạn API, cần đợi | Tự động schedule retry sau N giây |
     | `4` | `OUTAGE` | Dịch vụ bên ngoài (API, CI) bị lỗi | Đợi và ping lại sau, không tính là lỗi của agent |
  3. **Nhúng exit code vào mọi script:** Mọi test script, validation hook đều phải kết thúc bằng `sys.exit(code)` hoặc `exit $CODE` tương ứng.
  4. **Harness runner đọc exit code:** Sau mỗi vòng lặp, runner script kiểm tra exit code từ agent/test và rẽ nhánh tự động theo bảng trên.
  5. **Log exit code vào iteration log:** Mỗi lần lặp phải ghi `exit_code=X` vào file log (xem Tip 20).

> [!IMPORTANT]
> Bạn cần định nghĩa sẵn exit codes **trước** khi chạy vòng lặp đầu tiên. Nếu thiếu, runner không biết phân biệt giữa "xong" và "bị kẹt", dẫn đến loop vô tận hoặc bỏ sót lỗi nghiêm trọng.

### 20. Log Every Iteration (Ghi Log Từng Lần Lặp)
* **Tại sao cần thiết:** Loop tự động chạy nhanh. Nếu không có log riêng từng vòng lặp, khi một lần chạy thất bại bạn sẽ phải đọc hàng nghìn dòng log hỗn độn để tìm nguyên nhân. Mỗi iteration log là một "crime scene report" độc lập.
* **Các bước thực hiện:**
  1. **Tạo thư mục log chuyên biệt:** Ví dụ `logs/iterations/` với file log riêng cho từng vòng chạy: `run_20260803_143000.log`.
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
  5. **Tóm tắt vào WORK_BOARD.md:** Sau mỗi session thành công, agent ghi 1 dòng tóm tắt vào `docs/WORK_BOARD.md`: `✅ [2026-08-03 14:30] STT endpoint - DONE (commit: def5678)`.

> [!TIP]
> Đặt log của từng iteration vào file riêng với timestamp trong tên file. Điều này giúp bạn tìm ngay log của lần chạy cụ thể khi cần debug, thay vì phải `grep` qua file khổng lồ.

### 21. Improve the Loop From Inside (Cải Tiến Vòng Lặp Từ Bên Trong)
* **Tại sao cần thiết:** Harness không phải là bất biến. Mỗi vòng lặp cung cấp dữ liệu thực tế về những gì không hoạt động — prompt nào gây nhầm, rule nào thiếu, tool nào bị lỗi. Nếu không cập nhật harness sau mỗi chu kỳ, bạn sẽ lặp lại cùng thất bại mãi mãi.
* **Các bước thực hiện:**
  1. **Cấp quyền cho agent cập nhật harness:** Cho phép agent được viết vào `docs/rules.md` và `docs/TECH_DEBT.md` khi nó phát hiện pattern lỗi mới.
  2. **Phân tích iteration log sau mỗi thất bại:** Sau mỗi exit code `1` hoặc `2`, hỏi agent: *"Nhìn lại log lần này, prompt/spec/rule nào cần cập nhật để tránh thất bại tương tự?"*
  3. **Cập nhật ngay, không để sau:** Ngay trong phiên hiện tại (hoặc fresh chat tiếp theo), agent hoặc engineer phải update tài liệu trước khi chạy lại.
  4. **Ghi ngắn gọn vào `docs/rules.md`:** Ví dụ: *"Rule #47: Luôn kiểm tra file đã tồn tại trước khi gọi `open()` để tránh FileNotFoundError".*
  5. **Reviewer agent định kỳ:** Chạy một reviewer agent hằng tuần chỉ để đọc toàn bộ iteration logs, tổng hợp patterns lỗi và đề xuất cải tiến harness.

> [!NOTE]
> Harness phải được xem là **sản phẩm sống** cần bảo trì. Mỗi lần loop thất bại là một bài học miễn phí — hãy tận dụng nó bằng cách cập nhật rules thay vì chỉ chạy lại.

### 22. Loop Everything Repetitive (Lặp Tự Động Cho Mọi Thao Tác Lặp Lại)
* **Tại sao cần thiết:** Loop không chỉ để implement feature. Bất kỳ thao tác nào bạn làm thủ công nhiều lần (QA check, documentation sync, regression test, code review) đều tốn thời gian và dễ bỏ sót. Loop giải phóng bạn khỏi những việc lặp lại này.
* **Các bước thực hiện:**
  1. **Nhận diện công việc lặp lại:** Liệt kê mọi thao tác bạn làm thủ công nhiều lần trong tuần (ví dụ: "chạy linting sau mỗi commit", "kiểm tra API docs còn sync không", "test toàn bộ endpoints").
  2. **Đưa vào loop runner:** Mỗi thao tác lặp lại phải có script/agent tự động hóa nó.
  3. **Ví dụ các loại loop phụ trợ nên có:**
     - **QA Loop:** Tự động gọi thử tất cả API endpoints sau mỗi build, ghi kết quả vào `logs/qa/`.
     - **Documentation Sync Loop:** Kiểm tra `docs/architecture.md` còn khớp với code thực tế không, tự cập nhật nếu an toàn.
     - **Regression Loop:** Chạy toàn bộ test suite sau mỗi merge vào `main`.
     - **Dependency Check Loop:** Quét `requirements.txt` và cảnh báo nếu có security vulnerability.
  4. **Lập lịch (schedule) cho từng loop:** Dùng cron job, GitHub Actions, hay script launcher để các loop chạy đúng thời điểm cần thiết.

> [!TIP]
> Coi loop như **factory floor**: mọi công việc lặp lại trên dây chuyền đều nên được tự động hóa. Bạn chỉ nên can thiệp khi có vấn đề cần phán xét của con người.

### 23. Climb One Level at a Time (Nâng Cấp Hệ Thống Từng Bước)
* **Tại sao cần thiết:** Mỗi mức độ tự động hóa có các failure mode riêng. Nếu bạn nhảy thẳng lên multi-agent orchestration khi chưa thành thạo single-agent loop, bạn sẽ gặp tất cả failure modes cùng lúc và không biết cái nào là gốc rễ.
* **5 cấp độ tự động hóa — leo từng bước:**
  | Cấp độ | Mô tả | Điều kiện để lên cấp |
  |--------|--------|----------------------|
  | **1** | Viết code thủ công (không dùng AI) | Hiểu codebase 100% |
  | **2** | Làm việc với AI từng chat session | Đã quen với prompt engineering cơ bản |
  | **3** | Chạy loop thủ công từng item | Loop đơn (1 item + 1 test) chạy được ≥ 5 lần |
  | **4** | Tự động hóa loop qua đêm | Loop tự động chạy ổn định ≥ 3 đêm liên tiếp |
  | **5** | Multi-agent orchestration | Cấp 4 đã hoạt động tin cậy với hàng chục items |
* **Các bước thực hiện:**
  1. **Đánh giá bạn đang ở cấp nào:** Xem lịch sử loop, số lần thành công/thất bại, và mức độ can thiệp thủ công cần thiết.
  2. **Chỉ lên cấp khi cấp hiện tại ổn định:** Tiêu chí: 3 lần chạy liên tiếp thành công, không cần can thiệp thủ công.
  3. **Lên cấp từng bước:** Thêm đúng một layer phức tạp mới (ví dụ: thêm parallel agents) rồi test kỹ trước khi thêm layer tiếp theo.
  4. **Luôn có khả năng thoái lui:** Nếu cấp cao hơn không ổn định, roll back về cấp thấp hơn đã proven.

> [!WARNING]
> Đừng nhảy từ cấp 2 lên cấp 5 chỉ vì thấy demo hấp dẫn. Multi-agent orchestration khi chưa có loop cơ bản ổn định = thảm họa khó debug.

### 24. Close the Loop With Live Logs & Chrome DevTools (Khép Kín Vòng Lặp Với Log Trực Tiếp & QA Tự Động)
* **Tại sao cần thiết:** Tốc độ cao mà không có verification = thảm họa. Agent có thể viết code có vẻ đúng về mặt cú pháp nhưng runtime behavior lại sai hoàn toàn. "Khép kín vòng lặp" nghĩa là agent phải tự kiểm tra kết quả thực tế, không chỉ kiểm tra code trên giấy.
* **Nguyên tắc cốt lõi: "Trust but verify"** — cho phép agent tự do thực thi, nhưng phải có cơ chế kiểm tra thực tế sau mỗi bước.
* **Các bước thực hiện (4 bước trong mỗi lượt chạy):**
  1. **Bước 1 — Build/Implement:** Agent chỉnh sửa mã nguồn cho 1 Đơn Vị Logic từ `docs/specs.md`.
  2. **Bước 2 — Monitor Live Server Logs:** Agent khởi chạy server thử nghiệm (`uvicorn`, `npm dev`, v.v.) và **stream log thực tế (stdout/stderr)** để phát hiện ngay mọi exception, traceback, HTTP 500 theo thời gian thực — không phải đợi tests.
  3. **Bước 3 — Self-QA bằng Chrome DevTools MCP:** Agent dùng **Chrome DevTools MCP** mở trang/gọi API vừa tạo, thao tác y hệt người dùng thật:
     - Click các nút/element tương tác
     - Nhập input, gửi form
     - Kiểm tra DOM output
     - Đọc **Console** tab để tìm JavaScript errors
     - Đọc **Network** tab để verify API calls trả về đúng status code
  4. **Bước 4 — Diagnose & Self-Fix:**
     - **Nếu QA Pass:** Không có lỗi Console, server log trả về 200/201 → agent commit theo chuẩn Conventional Commits (*Tip 10*) và đánh dấu `[x]`.
     - **Nếu QA Fail:** Agent đọc traceback từ Live Log hoặc error từ browser, tự chuẩn đoán nguyên nhân, sửa code trong phiên đó. Nếu sau 2 lần vẫn fail → `git reset --hard` (*Tip 18*) và log vào `BLOCKED.md` (*Tip 16*).

> [!IMPORTANT]
> **Đừng chỉ dùng static analysis.** Unit tests và linting là cần thiết nhưng chưa đủ — chúng không phát hiện được runtime behavior sai, UI state không nhất quán, hay API response format không khớp. Chrome DevTools MCP giúp đóng khoảng trống này bằng cách test như người dùng thực.

> [!TIP]
> Thứ tự kiểm tra ưu tiên: **Server Log** (phát hiện crash ngay) → **Unit Test** (logic đúng không) → **Browser/Chrome DevTools** (UX và API response đúng không). Không bỏ qua bất kỳ lớp nào.

---

## 🚀 V. Triển Khai Đa Agent & Mở Rộng (Tips 25–29)

### 25. Replicate Websites Like a Pro (Sao Chép Giao Diện Chuyên Nghiệp)
* **Tại sao cần thiết:** AI thường tái tạo UI theo "tinh thần" chứ không theo chi tiết chính xác. Kết quả là một phiên bản giống nhưng không giống — sai màu, sai spacing, sai animation. Validation nhiều lớp giúp đạt độ chính xác pixel-perfect.
* **Các bước thực hiện (multi-layer validation):**
  1. **Cung cấp design tokens đầy đủ trước khi code:** Đưa cho AI toàn bộ: màu sắc (hex/hsl), font family, font size, spacing system, border-radius, shadow, animation duration và easing function. Không mô tả chung chung như "màu xanh" hay "nút bo góc".
  2. **Layer 1 — Code Review:** Sau khi AI viết code, so sánh CSS/styles với tài liệu design tokens. Kiểm tra từng property một cách có hệ thống.
  3. **Layer 2 — Computed Style so sánh qua Chrome DevTools MCP:** Dùng Chrome DevTools MCP để lấy `getComputedStyle()` của elements thực tế trên trang, rồi so sánh với design spec. Phát hiện các trường hợp CSS bị override không mong muốn.
  4. **Layer 3 — Pixel-perfect diffing:** Chụp ảnh màn hình trang đang build, so sánh với ảnh mockup/design gốc bằng tool diff hình ảnh. Xác định vùng khác biệt.
  5. **Layer 4 — Real user testing:** Dùng agent thao tác như người dùng thật: click button, hover element, scroll, resize viewport. Kiểm tra responsive layout ở các breakpoints khác nhau.
  6. **Ghi lại deviation vào docs:** Mọi sai lệch so với design gốc phải được ghi chú và phân loại: ý định (intentional deviation) hay lỗi cần sửa.

> [!TIP]
> Ghi đầy đủ design tokens vào `docs/architecture.md` hoặc file riêng `docs/design_tokens.md`. Agent đọc file này sẽ tái tạo chính xác hơn nhiều so với việc chỉ "nhìn" vào ảnh mockup.

### 26. Schedule Reviewer Agents (Lập Lịch Cho Agent Kiểm Duyệt)
* **Tại sao cần thiết:** Khi loop chạy nhanh, code mới được commit liên tục. Không ai có thể review thủ công từng commit. Reviewer agent chạy định kỳ như một "QA engineer tự động" — bắt lỗi hồi tố và đảm bảo code luôn khớp với specs.
* **Các bước thực hiện:**
  1. **Tạo reviewer agent chuyên biệt (không kiêm nhiệm):** Reviewer agent chỉ làm một việc: đọc code + đối chiếu spec/rules + báo cáo. Không implement, không sửa code phức tạp.
  2. **Lập lịch chạy định kỳ:** Ví dụ: mỗi sáng 8:00 sau khi loop đêm hoàn thành, hoặc sau mỗi N commits mới.
  3. **Reviewer agent làm gì:**
     - Đọc tất cả commits mới kể từ lần review trước (`git log --since=yesterday`)
     - Đối chiếu từng thay đổi với `docs/specs.md` và `docs/rules.md`
     - Tìm: logic sai, violation rules, documentation chưa cập nhật, code trùng lặp (DRY violation)
     - Phát hiện documentation conflict (2 file docs mâu thuẫn nhau)
  4. **Phân loại kết quả:**
     - **Safe fixes:** Reviewer agent tự sửa và commit (ví dụ: cập nhật docstring lỗi thời)
     - **Issues cần human review:** Ghi vào `docs/WORK_BOARD.md` dưới cột `READY_FOR_REVIEW` với chi tiết cụ thể
  5. **Tích hợp vào CI/CD:** Có thể chạy reviewer agent như một CI job sau mỗi PR.

> [!NOTE]
> Reviewer agent phải có access đến cả code lẫn docs. Đặc biệt hữu ích trong giai đoạn sprint nhanh khi loop implement nhiều features liên tiếp — reviewer sẽ bắt kịp những gì bị bỏ lỡ.

### 27. Make Two Agents Argue (Cho Hai Agent Tranh Luận)
* **Tại sao cần thiết:** Một agent đơn lẻ thường bị confirmation bias — nó bảo vệ thiết kế của chính nó. Khi có 2 agents tranh luận, thiết kế phải đứng vững trước sự phản biện. Design sống sót sau "cuộc chiến" mới thực sự tốt.
* **Khi nào dùng:** Trước mọi quyết định kiến trúc lớn (chọn database, chọn architecture pattern, thiết kế API schema quan trọng).
* **Các bước thực hiện:**
  1. **Soạn thảo design proposal:** Mô tả ngắn gọn thiết kế đang cân nhắc (không cần hoàn chỉnh).
  2. **Khởi chạy Proposer Agent:** Cung cấp proposal và yêu cầu agent này:
     - Trình bày ưu điểm của thiết kế
     - Liệt kê các use cases nó xử lý tốt
     - Đề xuất implementation plan chi tiết
  3. **Khởi chạy Critic/Attacker Agent** (với cùng proposal nhưng prompt khác):
     - Tìm mọi điểm yếu của thiết kế
     - Xác định edge cases chưa được xử lý
     - Đề xuất các thiết kế đơn giản hơn có thể thay thế
     - Chỉ ra các risk và failure scenarios
  4. **Tổng hợp vào `docs/WORK_BOARD.md`:** Ghi lại toàn bộ arguments của cả 2 phía vào một section riêng.
  5. **Engineer con người phán xét:** Đọc cả 2 phía, chọn thiết kế tốt nhất (hoặc hybrid), và ghi quyết định cuối cùng vào `docs/architecture.md`.

> [!IMPORTANT]
> **Cả 2 agents không được biết nhau tồn tại.** Chạy chúng trong 2 chat sessions độc lập. Nếu chúng biết nhau, chúng sẽ tend to agree thay vì thực sự phản biện.

> [!TIP]
> Prompt mạnh nhất cho Critic Agent: *"Assume this design has at least 3 critical flaws. Your job is to find them and propose simpler alternatives. Be ruthless."*

### 28. Choose Your Shipping Mode (Chọn Chế Độ Vận Hành)
* **Tại sao cần thiết:** Không có chế độ nào phù hợp với mọi tình huống. Dùng sai chế độ (ví dụ: autonomous mode cho task chưa rõ ràng) sẽ tốn tokens và tạo ra code sai hướng.
* **Hai chế độ và khi nào dùng:**

  **🔵 Sequential Mode (Chế độ Tuần Tự — Khuyến nghị cho người mới):**
  - Agent làm việc **trên một branch duy nhất**
  - Hoàn thành một item → engineer review → merge → tiếp tục item tiếp theo
  - Phù hợp khi: feature chưa được spec kỹ, rủi ro cao, cần nhiều human judgment
  - Ưu điểm: dễ kiểm soát, ít risk, dễ debug
  - Nhược điểm: chậm hơn, cần engineer active tham gia

  **🟠 Parallel Mode (Chế độ Song Song — Dành cho team có harness trưởng thành):**
  - Nhiều agents làm việc **đồng thời trên các feature branches khác nhau**
  - Cần thêm một **Senior Reviewer Agent** chuyên theo dõi repository, đọc các pull requests và manage merging
  - Phù hợp khi: specs rõ ràng, test coverage tốt, loop đã chạy ổn định ở Sequential Mode
  - Ưu điểm: tốc độ cao gấp bội
  - Nhược điểm: phức tạp hơn, cần Reviewer Agent đủ mạnh, merge conflicts cần xử lý

* **Các bước thực hiện:**
  1. **Bắt đầu với Sequential Mode:** Chạy ít nhất 10 items thành công trước khi cân nhắc Parallel.
  2. **Chuyển sang Parallel khi:** Test coverage ≥ 80%, specs đã được chuẩn hóa, Reviewer Agent đã được setup và test.
  3. **Luôn khai báo chế độ trong `AGENTS.md`:** Ghi rõ chế độ hiện tại để mọi agent đọc và biết cách vận hành.
  4. **Interactive Pair Mode (không phải Sequential hay Parallel):** Khi bạn muốn explore ideas, không có spec, hoặc đang debug một vấn đề phức tạp — chuyển sang interactive, hỏi ý kiến con người liên tục.

> [!WARNING]
> **Đừng chạy Parallel Mode khi chưa sẵn sàng.** Nhiều agents chạy đồng thời mà không có Reviewer Agent sẽ tạo ra merge conflicts, overwrite lẫn nhau, và rất khó track down khi có lỗi.

### 29. Add a Work Board (Thêm Bảng Quản Lý Công Việc)
* **Tại sao cần thiết:** Khi loop scale lên (nhiều features, nhiều agents), bạn cần một "control panel" duy nhất để thấy tất cả: item nào đang chạy, ai đang làm, chi phí bao nhiêu, kết quả ra sao. Work Board chính là control panel đó.
* **Các bước thực hiện:**
  1. **Tạo file `docs/WORK_BOARD.md` với cấu trúc cột Kanban:**
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
  4. **Work Board là nguồn sự thật duy nhất:** Mọi agent và engineer đều đọc WORK_BOARD.md để biết trạng thái thực tế của project — không hỏi nhau qua chat.
  5. **Tự động hóa cập nhật:** Agent phải tự cập nhật WORK_BOARD.md khi bắt đầu (`TODO → IN_PROGRESS`) và khi kết thúc (`IN_PROGRESS → DONE/BLOCKED`). Không để engineer cập nhật thủ công.

> [!NOTE]
> Work Board không phải Kanban của Jira hay Trello — nó là markdown file đơn giản nằm trong repo, được cả AI agent và human đọc. Sức mạnh của nó là ở tính **visible từ cả hai phía** (human và AI).

> [!TIP]
> Khi có nhiều agents chạy song song (Tip 28), Work Board trở nên quan trọng hơn bao giờ hết. Đây là cách duy nhất để tránh 2 agents cùng nhận 1 task.

---

> [!TIP]
> **Quy Tắc Vàng:** *"Harness chính là sản phẩm; code chỉ là kết quả đầu ra."*
