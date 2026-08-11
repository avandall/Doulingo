1. TEMPLATE B — Functional-Situational Bank

Dùng cho ngôn ngữ chức năng (functional language) — cái mà sách giáo trình thường tách riêng theo mục "How to agree/disagree", "How to give opinions"... Loại này cắt ngang nhiều topic, nên tách khỏi Template A để AI có thể tái sử dụng ở bất kỳ chủ đề nào.


2. Nội dung temp

template_id: B-<function_slug>-001
function: "Ví dụ: Disagreeing politely"
applicable_topics: ["Work", "Education", "Environment", "..."]
register: "Formal / Neutral / Casual"  # chọn 1 hoặc liệt kê biến thể theo register

band_variants:
  - band: "5.0-6.0"
    phrases:
      - "I don't really agree."
      - "I see it differently."
      - "Maybe, but I think..."
    grammar_pattern: "I think / I don't think + clause"

  - band: "6.5-7.5"
    phrases:
      - "I see your point, but I'd say..."
      - "That's fair, although..."
      - "I'm not sure I fully agree with that."
    grammar_pattern: "Concession clause (although/even though) + counter-opinion"

  - band: "8.0+"
    phrases:
      - "I take your point, though I'd push back slightly on..."
      - "That's a reasonable view, but it overlooks..."
      - "I'd be cautious about that assumption, because..."
    grammar_pattern: "Hedged disagreement + justification + nuance marker (to some extent / to a degree)"

sample_dialogues:  # >5, thể hiện chức năng này áp dụng ở NHIỀU topic khác nhau
  - id: 1
    topic: "Education"
    band: "5.5"
    exchange:
      ai: "Some people say online learning is better than classroom learning. What do you think?"
      user_model_answer: "I don't really agree. I think classroom learning is better because you can ask questions directly."
  - id: 2
    topic: "Environment"
    band: "6.0"
    exchange:
      ai: "Do you think individuals can really make a difference for the environment?"
      user_model_answer: "Maybe, but I think big companies have a much bigger impact than individuals."
  - id: 3
    topic: "Technology"
    band: "7.0"
    exchange:
      ai: "AI will replace most jobs in the next decade. Agree?"
      user_model_answer: "I see your point, but I'd say it's more likely to change jobs than replace them entirely."
  - id: 4
    topic: "Work"
    band: "7.0"
    exchange:
      ai: "Open-plan offices improve teamwork. True?"
      user_model_answer: "That's fair, although in my experience they often reduce focus more than they improve collaboration."
  - id: 5
    topic: "Society"
    band: "8.0"
    exchange:
      ai: "Social media does more harm than good."
      user_model_answer: "I take your point, though I'd push back slightly on that — it depends heavily on how it's used, not the platform itself."
  - id: 6
    topic: "Education"
    band: "8.5"
    exchange:
      ai: "Standardized testing is the fairest way to assess students."
      user_model_answer: "That's a reasonable view, but it overlooks how it disadvantages students with different learning styles or backgrounds."

related_functions_to_cross_reference:
  - "Agreeing"
  - "Giving opinions"
  - "Softening a claim (hedging)"

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