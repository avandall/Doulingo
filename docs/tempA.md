1. TEMPLATE A — Progressive Band Ladder

Dùng khi bạn muốn AI hiểu: cùng một topic, nhưng độ khó tăng dần thì hội thoại thay đổi như thế nào (không chỉ là từ khó hơn, mà là ý tưởng, cấu trúc, độ dài turn, khả năng phản biện...).


2. Nội dung temp

template_id: A-<topic_slug>-001
topic: "Ví dụ: Work & Career"
subtopic: "Ví dụ: Career change / Work-life balance"
source: "Tên sách, chương, trang (để truy vết, không phải để AI đọc)"
target_skill_focus: "Ví dụ: giving opinion + hedging language"

band_ladder:
  - band: "4.0 - 5.0 (Elementary–Pre-Intermediate)"
    can_do: "Mô tả điều học viên LÀM ĐƯỢC ở band này, theo hành vi, không phải điểm số suông. Vd: trả lời câu hỏi trực tiếp, câu đơn, ít liên từ."
    grammar_required:
      - "Present simple / Present continuous"
      - "Basic comparatives (more...than / -er)"
    vocabulary_core:
      - "job, salary, boss, colleague, busy, tired"
    vocabulary_avoid: "Từ trừu tượng, idiom — band này chưa nên dùng"
    sentence_length_target: "6-10 từ/câu, 1-2 câu/turn"
    common_errors_to_simulate: "Sai thì, thiếu mạo từ — AI có thể chèn nhẹ để luyện correction"

  - band: "5.5 - 6.5 (Intermediate)"
    can_do: "Đưa ra lý do đơn giản, nối ý bằng because/so/but, so sánh 2 lựa chọn"
    grammar_required:
      - "Present perfect (kinh nghiệm)"
      - "Conditional loại 1"
      - "Linking words: however, on the other hand"
    vocabulary_core:
      - "work-life balance, promotion, overtime, deadline"
    vocabulary_stretch:
      - "burnout, flexible hours, career path"
    sentence_length_target: "10-16 từ/câu, 2-3 câu/turn, có ví dụ cá nhân"

  - band: "7.0 - 8.0+ (Advanced)"
    can_do: "Phản biện quan điểm, dùng hedging (I'd argue that.../ arguably), đưa ví dụ xã hội rộng hơn cá nhân"
    grammar_required:
      - "Mixed conditionals"
      - "Inversion for emphasis (Rarely have I...)"
      - "Cleft sentences (What really matters is...)"
    vocabulary_core:
      - "job satisfaction, meritocracy, work culture, autonomy"
    vocabulary_stretch:
      - "presenteeism, quiet quitting, imposter syndrome"
    sentence_length_target: "16-25 từ/câu, có mệnh đề phụ, tự sửa ý giữa câu (self-correction) như người bản ngữ"

sample_dialogues:  # >5 mẫu, TRẢI ĐỀU qua các band, không dồn 1 band
  - id: 1
    band: "5.0"
    exchange:
      ai: "Do you like your current job?"
      user_model_answer: "Yes, I like it, but sometimes it's very busy."
      ai_followup: "Why is it busy?"
  - id: 2
    band: "5.0"
    exchange:
      ai: "What time do you usually start work?"
      user_model_answer: "I start at eight. It's a bit early for me."
  - id: 3
    band: "6.0"
    exchange:
      ai: "Would you rather have a high salary or more free time?"
      user_model_answer: "I'd probably choose more free time, because money isn't everything, and I've seen colleagues burn out from overworking."
  - id: 4
    band: "6.5"
    exchange:
      ai: "Has your idea of a 'good job' changed since you started working?"
      user_model_answer: "Actually, yes. I used to think salary was the most important thing, but now I care more about flexible hours."
  - id: 5
    band: "7.5"
    exchange:
      ai: "Some people say remote work is killing company culture. Do you agree?"
      user_model_answer: "I'd argue it depends on how the company handles it. Arguably, culture was always more about shared values than physical presence — companies that fail at remote culture were probably already weak on that front."
  - id: 6
    band: "8.0"
    exchange:
      ai: "Is it fair to pay people differently for the same job in different countries?"
      user_model_answer: "Rarely do we consider that cost of living varies so drastically — what looks unfair on paper might actually reflect purchasing power parity, though I admit this argument can be used to justify exploitation too."

notes_for_ai_generation:
  register: "Casual nhưng lịch sự, phù hợp hội thoại 1-1, không phải văn viết học thuật"
  diversity_hint: "Khi generate, tránh lặp lại đúng câu hỏi mẫu — dùng mẫu này để suy ra CẤU TRÚC câu hỏi/độ phức tạp phù hợp band, không copy nguyên văn"
  follow_up_bank:
    - "Can you give an example?"
    - "Why do you think that is?"
    - "Has that always been true for you?"

diagnostic_signals:          # để AI "nghe" ra band, không phải đoán
  - signal: "sentence_length_avg"
    band_5: "6-10 từ"
    band_6_5: "10-16 từ"
    band_8: "16-25 từ, có mệnh đề phụ"
  - signal: "self_correction"       # band cao thường tự sửa câu giữa chừng — dấu hiệu bản ngữ hoá
    band_8_marker: "có false start rồi tự sửa (What I— I mean, what I really think is...)"
  - signal: "hedging_density"       # tần suất dùng arguably/to some extent
    band_8_marker: ">=1 lần/3 câu"
  - signal: "silence_or_filler_ratio"  # từ ASR, không phải từ text
    band_5_marker: "nhiều 'umm', câu ngắn rời rạc"

hook_bank:                    # chống sáo rỗng — mồi câu hỏi có tính tò mò, KHÔNG trung tính kiểu thi
  - "Nếu ngày mai bạn phải chuyển nhà gấp, thứ đầu tiên bạn cứu là gì?"
  - "Bạn có từng hối hận vì đã KHÔNG mua một món đồ không?"
  anti_cliche_list:            # câu hỏi/khuôn KHÔNG được lặp lại quá 1 lần/user/tuần
    - "Do you like your job?"
    - "Tell me about your hometown."

reaction_policy:               # thay cho branch cứng low/high — quy tắc tổng quát
  if_band_estimate_rising_2_turns: "tăng độ trừu tượng câu hỏi, giảm gợi ý từ vựng"
  if_band_estimate_flat_or_hesitant: "chuyển câu hỏi cụ thể hơn, thêm 1 ví dụ mồi"
  never: "lặp lại nguyên văn 1 phrase từ phrase_bank quá 1 lần trong cùng hội thoại"