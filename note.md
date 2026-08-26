1. Tôi nói:
hệ thống character hiện tại tạo ra câu nói quá kỳ quặc. Ví dụ nhân vật Alex level 1 topic "hello how are you" khi chọn vô nói :Hello. I am good. You are good. We are here now. It is a big day. Many people walk outside. They look happy. They have music and food. Do you want to go see the big festival with me?

Đó ko phải 1 cuộc trò chuyện bình thường. Bạn đứng ở vị trí 1 giáo viên dạy tiếng anh giao tiếp, bạn thấy có hợp lý ko ? Sao ko phải đơn giản hỏi như là "Hey, how are you today? Do you have anything new to tell me" hay là "How is the weather today at your place? In mine it was a rainy day and I stay home all the day."

Kiểm tra cho tôi nguyên nhân root cause xảy ra vấn đề này, và giải pháp để nó ra 1 câu tự nhiên như khi nói với người hoặc thâm chí khi tôi nói chuyện với AI trực tiếp trên giao diện web nó còn thông mình và hiểu chuyện, biết cách bắt chuyện hơn là gọi qua API trả kết quả này. Nếu vậy tôi dùng app làm gì?

2. AI nói:
Đứng ở vị trí của một giáo viên dạy tiếng Anh giao tiếp, câu hội thoại hiện tại của nhân vật Alex Level 1:

"Hello. I am good. You are good. We are here now. It is a big day. Many people walk outside. They look happy. They have music and food. Do you want to go see the big festival with me?"

👉 Hoàn toàn KHÔNG hợp lý và không tự nhiên. Đây là kiểu "ngôn ngữ máy ghép câu" (word padding), tạo ra cảm giác gượng gạo, ngô nghê và phản sư phạm đối với người học tiếng Anh.

🔍 PHÂN TÍCH NGUYÊN NHÂN GỐC RỄ (ROOT CAUSE ANALYSIS)
Qua kiểm tra toàn bộ mã nguồn của hệ thống AI Engine và Prompt Factory, có 4 nguyên nhân chính dẫn đến hiện tượng này:

1. Ràng buộc số từ tối thiểu (min_words) bị đặt quá cao ở Level thấp
Trong 

app/core/level_config.py
, Level 1 (Pre-A1) đang được cấu hình:
"min_words": 35, "max_words": 70
"vocab_tier": "ONLY the 100 most common English words"
"grammar_allowed": "Subject + Verb only. Present simple tense ONLY."
Với chủ đề chào hỏi đơn giản ("hello how are you"), một câu nói tự nhiên chỉ dài 8 - 15 từ (ví dụ: "Hey, how are you today? Do you have anything new to tell me?").
Tuy nhiên, Prompt trong 

app/core/ai_engine.py
 ép AI: Between 35 and 70 words. COUNT YOUR WORDS.
Do bị giới hạn chỉ được dùng từ cực kỳ cơ bản (Subject + Verb) nhưng lại bắt buộc phải nói đủ 35 từ trở lên, LLM rơi vào thế bế tắc và phải tự sinh các câu đơn lặp đi lặp lại vô nghĩa (Hello. I am good. You are good. We are here now...) chỉ để "đủ chỉ tiêu số từ".
2. Mâu thuẫn giữa Ví dụ mẫu (Example Response) và Quy tắc Prompt
Trong 

app/core/level_config.py
, ví dụ mẫu cho Level 1 là: "I like food. Food is good. Do you like food?" (chỉ có 10 từ).
Nhưng ngay bên dưới, Prompt lại bắt: YOU MUST WRITE EXACTLY LIKE THE EXAMPLE BELOW đồng thời Between 35 and 70 words.
LLM bị xung đột logic: Nó bắt chước mô hình 3 câu ngắn (10 từ) của ví dụ mẫu và nhân bản chuỗi câu đó lên 3-4 lần để thỏa mãn yêu cầu 35 từ.
3. Ép nhét kịch bản ngẫu nhiên (SCENARIO_ANGLES) vào chủ đề thông thường
Trong 

app/core/ai_engine.py
, hệ thống luôn chọn ngẫu nhiên 1 "Scenario Angle" (ví dụ: "Focus on cultural festivals, evening entertainment...") và RAG Mandatory Vocabulary từ 

prompt_factory.py
 rồi chèn vào Prompt.
Khi vào topic chào hỏi bình thường, AI vừa bị ép chào hỏi, vừa bị ép phải bám theo góc kịch bản "lễ hội, âm nhạc và đồ ăn" + từ vựng bắt buộc, dẫn đến câu trả lời chắp vá, lạc quẻ.
4. "Bóp nghẹt" trí thông minh tự nhiên của LLM (Over-Engineering Prompt)
So với giao diện Web AI (ChatGPT / Gemini Web GUI): Khi bạn chat trên web, Prompt chỉ là "Hãy đóng vai người bạn/giáo viên thân thiện trò chuyện tiếng Anh". LLM tự do phát huy trí thông minh giao tiếp (social intelligence, empathy, warmth) vốn có.
Trong App hiện tại: LLM đang bị bọc quá nhiều "vòng kim cô" cứng nhắc (JSON output, 35-70 min words, Present Simple restriction, Mandatory Vocab, Scenario Angle, Active Listening rules...). Điều này khiến AI hoạt động như một "thuật toán trả bài tuân thủ luật" chứ không còn là một người bạn giao tiếp.
💡 GIẢI PHÁP TỔNG THỂ (ACTION PLAN)
Để hệ thống tạo ra câu hội thoại tự nhiên, ấm áp như người thật hoặc trên Web AI:

1. Điều chỉnh dải số từ (min_words / max_words) hợp lý theo Level
Thay vì ép Level 1 phải nói 35-70 từ, hãy hạ mức tối thiểu xuống phù hợp với giao tiếp thực tế:

Level 1 (Pre-A1): min_words: 8, max_words: 25 (Cho phép câu chào ngắn gọn 1-2 câu tự nhiên).
Level 2 (A1): min_words: 12, max_words: 30.
Level 3 (A1+): min_words: 15, max_words: 35.
Level 4-5 (A2): min_words: 20, max_words: 45.
2. Cập nhật Example Response & Response Style tự nhiên hơn
Sửa ví dụ mẫu trong LEVEL_CONFIGS[1] & LEVEL_CONFIGS[2] sang phong cách thân thiện, chuẩn giao tiếp:

Level 1 Example mới: "Hi there! I am doing good today. How are you feeling today?"
Level 2 Example mới: "Hello! How is the weather today at your place? Here it is a rainy day."
3. Làm mềm (Soften) Scenario Angles cho các chủ đề giao tiếp cơ bản
Với các topic cơ bản/chào hỏi (như "hello_how_are_you", "daily_greeting"), không bắt buộc chèn kịch bản ép buộc (Scenario Angle) hay từ vựng IELTS học thuật gượng gạo.
4. Thêm ưu tiên "Conversational Warmth & Natural Flow" vào Prompt
Bổ sung chỉ thị cốt lõi vào 

ai_engine.py
:

"HIGHEST PRIORITY: Prioritize conversational warmth, human-like flow, and natural English phrasing above rigid word counts. Speak like a friendly, encouraging native English teacher chatting with a student."

5. Nâng cấp System Prompt cho nhân vật Alex
Cập nhật nhân vật Alex trong 

app/characters/
init
.py
 từ "Plain AI assistant with no persona..." thành một người bạn đồng hành giao tiếp tiếng Anh tự nhiên, thân thiện và ấm áp.

Bạn có muốn tôi tiến hành cập nhật các file cấu hình (

level_config.py
, 

ai_engine.py
, 

characters/
init
.py
) ngay bây giờ để sửa triệt để vấn đề này không?

Run pytest to check test suite finished
Tôi đã hoàn thành việc kiểm tra nguyên nhân gốc rễ và phân tích mã nguồn.

Hệ thống đã có kế hoạch chỉnh sửa chi tiết cho dải số từ (min_words), cập nhật mẫu câu tự nhiên cho các Level thấp, làm mềm kịch bản cho các chủ đề chào hỏi thông thường, và tối ưu hóa Prompt cho nhân vật Alex.

Bạn hãy xác nhận nếu muốn tôi bắt đầu áp dụng các chỉnh sửa này vào dự án ngay bây giờ nhé!

3. Tôi nói:

giải pháp này chỉ giải quyết 1 phần, chưa hết gốc rễ vấn đề.
a. Không chỉ nhân vật Alex mà toàn bộ nhân vật khác
b. Tôi muốn nó sử dụng hoàn toàn trí thông minh tự nhiên của LLM nhưng LLM lại ko biết phân level user chuẩn xác. tôi cần giải pháp
c. Cách giới hạn từ, độ dài câu cũng chưa giải quyết triệt để vấn đề level

Bổ sung giải pháp toàn diện hơn. Cho tôi 2+ options để lựa chọn

4. AI nói:
Tôi hoàn toàn đồng ý với phản hồi của bạn. Ba điểm bạn nêu ra chính là trọng tâm kiến trúc (architectural core) mà hệ thống hiện tại đang gặp phải:

Vấn đề chung của tất cả 9 nhân vật: Tất cả nhân vật (Lily, Alex, Oscar, Viktor...) đều đi qua cùng một pipeline xây dựng Prompt (ai_engine.py & prompt_factory.py), nên nhân vật nào chọn Level 1 cũng bị ép tạo ra chuỗi câu gượng gạo.
Nợ kỹ thuật về CEFR Level: LLM bản chất không tự biết căn chỉnh độ khó CEFR/IELTS nếu không có chỉ dẫn, nhưng khi gán chỉ dẫn quá cứng nhắc (micro-rules) thì lại làm mất đi trí thông minh giao tiếp tự nhiên (natural conversational intelligence).
Giới hạn số từ / độ dài câu không phải là bản chất của Level: Trong sư phạm tiếng Anh, trình độ Pre-A1/A1 được định nghĩa bởi độ đơn giản từ vựng & cấu trúc ngữ pháp (vocabulary & syntactic complexity) chứ không phải số lượng từ. Ép số từ tối thiểu (min_words) chỉ làm AI nói nhảm để đủ số lượng.
Để giải quyết tận gốc bài toán này, tôi đề xuất 3 GIẢI PHÁP TOÀN DIỆN (3 ARCHITECTURAL OPTIONS) dưới đây để bạn lựa chọn:

🌟 OPTION 1: "Few-Shot Exemplar Pedagogy & Structural Soft-Guardrails"
💡 Ý tưởng cốt lõi:
Loại bỏ hoàn toàn các quy tắc ép buộc cứng nhắc (xóa bỏ min_words, xóa bỏ luật "chỉ được dùng Present Simple", không ép nhét kịch bản gượng gạo). Thay vào đó, kiểm soát Level của LLM bằng Mẫu hội thoại thực tế (Few-Shot Natural Exemplars) kết hợp Trần từ vựng CEFR (Linguistic Ceilings).

🛠️ Cách thức hoạt động:
Xóa bỏ min_words tối thiểu: Cho phép AI đáp lại ngắn gọn tự nhiên (5-15 từ ở Level 1 nếu đó là câu chào), chỉ giữ lại trần tối đa (max_words) để tránh AI "nói dài dòng".
Hệ thống Few-Shot Exemplars cho từng nhóm Level: Với mỗi Level/CEFR, cung cấp cho LLM 2-3 cặp mẫu hội thoại thực tế giữa Giáo viên - Học viên. LLM học rất giỏi theo mẫu (pattern-matching) thay vì đọc các quy tắc khô khan:
Mẫu Level 1 (Pre-A1): LLM học cách chào hỏi ấm áp, dùng từ thông dụng nhất, đặt 1 câu hỏi dẫn dắt đơn giản mà không bị lặp từ.
Phân tách rõ 2 lớp trong Prompt:
Lớp Nhân vật (Character Persona): Giữ tính cách (Lily mỉa mai, Oscar sôi nổi, Alex thân thiện...).
Lớp Sư phạm (Pedagogy Guardrail): Giới hạn trần từ vựng theo khung CEFR (Ví dụ Level 1 = A1 Vocab, từ ngữ cụ thể, 1 mệnh đề/câu, không idiom).
Áp dụng đồng bộ cho TOÀN BỘ 9 nhân vật.
Ưu điểm:
Trả lại 100% trí thông minh hội thoại, sự tự nhiên và ấm áp của LLM.
Tốc độ phản hồi cực nhanh (chỉ 1 lần gọi API LLM).
Không còn hiện tượng câu từ ngô nghê hay chắp vá filler text.
Nhược điểm: Phụ thuộc vào khả năng tuân thủ Few-shot của model LLM (tuy nhiên các model hiện nay như Gemini 2.5/3.5/3.6 hay Llama-3.3-70b làm việc này rất tốt).
🌟 OPTION 2: "Two-Pass Generation: Brainstorm & CEFR Adaptor" (Hệ thống AI 2 bước)
💡 Ý tưởng cốt lõi:
Tách rời hoàn toàn "Trí thông minh hội thoại" (What to say) và "Căn chỉnh trình độ CEFR" (How to simplify standard English) thành 2 bước xử lý nối tiếp nhau.

🛠️ Cách thức hoạt động:
Pass 1 (Natural Brainstormer): Cho LLM tự do đóng vai nhân vật (Alex, Lily, Oscar...) trả lời người học bằng tiếng Anh tự nhiên nhất (như khi bạn chat trực tiếp trên ChatGPT/Gemini Web), tập trung vào sự thấu hiểu, cảm xúc, góc nhìn và câu hỏi gợi mở.

Pass 2 (CEFR Level Adaptor): Đưa kết quả của Pass 1 qua một Prompt đơn giản đóng vai "Giáo viên biên dịch trình độ". Prompt này sẽ viết lại (rewrite/simplify) câu trả lời của Pass 2 sao cho đúng với từ vựng & cấu trúc của Level $N$ (Pre-A1 / A1 / B1...), nhưng giữ nguyên 100% ý nghĩa, sự ấm áp và câu hỏi gợi mở.

Ưu điểm:

Đảm bảo 100% AI thông minh, hiểu chuyện, biết bắt chuyện như trên Web (vì Pass 1 không bị vướng bất kỳ quy tắc sư phạm cứng nhắc nào).
Đảm bảo 100% chuẩn trình độ CEFR (vì Pass 2 chuyên trách việc hạ độ khó từ vựng mà không làm biến dạng ý nghĩa).
Nhược điểm:

Gọi API 2 lần mỗi turn (hoặc dùng Structured Output trả về 2 bước trong 1 prompt), làm tăng độ trễ (latency) thêm khoảng 200 - 400ms.
🌟 OPTION 3: "Decoupled Dynamic Prompt Architecture with Adaptive Horizon" (Tái cấu trúc lại Prompt)
💡 Ý tưởng cốt lõi:
Giữ nguyên luồng 1-Pass API nhưng tái cấu trúc lại toàn bộ kiến trúc Prompt System thành 3 tầng độc lập, xóa bỏ triệt để các xung đột logic cũ.

🛠️ Cách thức hoạt động:
Tầng 1 - Core Pedagogy & Conversational Warmth: Đặt ưu tiên tối cao cho sự tự nhiên, ấm áp, lắng nghe tích cực và chủ động gợi mở câu chuyện.
Tầng 2 - Character Trait Overlay: Áp lớp tính cách nhân vật (Lily, Alex, Oscar...) lên phong cách nói.
Tầng 3 - Adaptive CEFR Horizon:
Thay vì ép "Subject + Verb only" hay "ép 35-70 words", quy định theo CEFR Complexity Horizon:
Level 1-3: Trả lời ngắn gọn (1-2 câu), từ vựng giao tiếp hằng ngày đơn giản, rõ ràng.
Level 4-8: Trả lời 2-3 câu, mở rộng chi tiết, dùng từ nối cơ bản.
Level 9-20: Trả lời sâu sắc, từ vựng phong phú, góc nhìn đa chiều.
Tự động làm mềm (Soften) Scenario Angles: Chỉ kích hoạt kịch bản nhập vai khi người dùng vào các scenario tình huống (Order đồ ăn, Phỏng vấn...), với chủ đề tự do thì để AI tự nhiên dẫn dắt.
Ưu điểm: Kiến trúc sạch mã nguồn, dễ bảo trì, áp dụng nhất quán cho toàn bộ nhân vật.
Nhược điểm: Cần tinh chỉnh kỹ prompt tầng 3 để AI không bị vượt cấp ở các Level thấp.