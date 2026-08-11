1. TEMPLATE C — Deep-Dive Scenario (Role-play)

Dùng cho tình huống nhập vai hoàn chỉnh, có rẽ nhánh theo chất lượng câu trả lời — mô phỏng gần nhất với hội thoại thật, tốt cho luyện phản xạ.


2. Nội dung temp

template_id: C-<scenario_slug>-001
scenario: "Ví dụ: Complaining about a hotel room"
setting: "Khách sạn, tại quầy lễ tân"
ai_role: "Receptionist"
user_role: "Guest"
target_band_range: "5.5 - 8.0"

grammar_required:
  - "Past simple (kể lại sự việc)"
  - "Would like / could you... (yêu cầu lịch sự)"
  - "Present perfect (I've already tried...)"

vocabulary_core:
  - "reservation, refund, inconvenience, upgrade"
vocabulary_stretch:
  - "compensation, complimentary, escalate the issue"

scenario_flow:
  opening:
    ai: "Good afternoon, how can I help you?"
  branch_low_band:  # nếu user trả lời ngắn/đơn giản
    condition: "User answer < 8 từ hoặc chỉ có 1 mệnh đề"
    ai_response_style: "Đặt câu hỏi đóng, dễ trả lời, giúp user không bị đứng hình"
    example: "Is there a problem with your room?"
  branch_high_band:  # nếu user trả lời phức tạp
    condition: "User dùng >1 mệnh đề, có lý do/cảm xúc"
    ai_response_style: "Phản hồi có thương lượng, đưa ra điều kiện, buộc user phải thuyết phục thêm"
    example: "I understand your frustration. Unfortunately, we're fully booked tonight — would a partial refund and a room change tomorrow work for you?"

sample_dialogues:  # >5, đi theo trình tự 1 cuộc hội thoại hoàn chỉnh + biến thể theo band
  - id: 1
    turn: "opening"
    band: "any"
    exchange:
      ai: "Good afternoon, how can I help you?"
      user_model_answer: "Hi, there's a problem with my room."

  - id: 2
    turn: "elaborate"
    band: "5.5"
    exchange:
      ai: "I'm sorry to hear that. What's the problem?"
      user_model_answer: "The air conditioner is broken. It's very hot."

  - id: 3
    turn: "elaborate"
    band: "7.0"
    exchange:
      ai: "I'm sorry to hear that. What's the problem?"
      user_model_answer: "The air conditioner hasn't been working since I checked in, and I've already called twice, but no one came to fix it."

  - id: 4
    turn: "negotiation"
    band: "6.0"
    exchange:
      ai: "I understand. Would you like us to send someone to fix it now?"
      user_model_answer: "Yes please, or maybe I could change to another room."

  - id: 5
    turn: "negotiation"
    band: "8.0"
    exchange:
      ai: "I understand your frustration. Unfortunately, we're fully booked tonight — would a partial refund and a room change tomorrow work for you?"
      user_model_answer: "I appreciate the offer, but honestly, I don't think that fully makes up for a night without air conditioning. Could you at least throw in a late checkout as well?"

  - id: 6
    turn: "closing"
    band: "any"
    exchange:
      ai: "Of course, I'll arrange that for you right away. Anything else?"
      user_model_answer: "No, that's all. Thank you for your help."

evaluation_hooks:
  - trigger: "user_uses_past_perfect_correctly"
    ai_reaction: "Tăng độ khó câu hỏi tiếp theo"
  - trigger: "user_answer_too_short_3_turns_in_a_row"
    ai_reaction: "Chuyển sang câu hỏi đóng, dễ hơn, để tránh nản"

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