"""
pdf_report_service.py — Playwright PDF Reporting Engine for Doulingo
Render Jinja2 HTML template and export print-ready A4 PDF using Playwright Headless Chromium.
"""

import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "reports"


def render_report_html(report_data: dict[str, Any]) -> str:
    """Render report_data into HTML string using Jinja2 template."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True
    )
    template = env.get_template("speaking_report.html")
    return template.render(report_data=report_data)


def generate_speaking_pdf(report_data: dict[str, Any], output_path: str) -> str:
    """
    Generate an A4 PDF report from report_data dict using Jinja2 + Playwright Headless Chromium.

    Args:
        report_data: Dictionary containing candidate info, subscores, and dialogue turns.
        output_path: Target path for the output PDF file.

    Returns:
        Absolute path to the generated PDF file.
    """
    # Ensure target output directory exists
    target = Path(output_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    # 1. Render Jinja2 Template
    rendered_html = render_report_html(report_data)

    # 2. Launch Playwright Chromium & Print to PDF
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Set HTML content and wait for network/styles to settle
        page.set_content(rendered_html, wait_until="load")
        
        page.pdf(
            path=str(target),
            format="A4",
            print_background=True,
            margin={
                "top": "12mm",
                "right": "12mm",
                "bottom": "12mm",
                "left": "12mm"
            }
        )
        browser.close()

    return str(target)


def get_sample_report_data() -> dict[str, Any]:
    """Provide structured sample report data with multi-turn dialogue (for >= 2 pages output)."""
    return {
        "exam_type": "IELTS Speaking Mock Test",
        "test_date": "2026-09-06",
        "session_id": "IELTS-SPK-99201",
        "candidate_name": "Nguyễn Văn Anh",
        "candidate_id": "STU-102938",
        "duration_minutes": 14,
        "target_score": "7.5 Band / C1",
        "overall_score": "7.5",
        "cefr_level": "C1 Advanced",
        "performance_summary": (
            "Thí sinh thể hiện trình độ giao tiếp trôi chảy và tự nhiên trong toàn bộ bài thi. "
            "Sử dụng đa dạng vốn từ vựng chuyên sâu (collocations & idioms), quản lý ngữ pháp linh hoạt với "
            "các cấu trúc câu phức. Nhịp độ nói ổn định, kiểm soát ngữ điệu tự nhiên và phản xạ nhanh."
        ),
        "subscores": {
            "fluency": {
                "score": "7.5",
                "feedback": "Mạch lạc tốt, duy trì tốc độ nói tự nhiên. Ít khi bị đứt đoạn hoặc vấp từ."
            },
            "pronunciation": {
                "score": "7.0",
                "feedback": "Âm chuẩn, trọng âm từ và nhấn câu chính xác. Một số âm cuối cần tròn và rõ hơn."
            },
            "grammar": {
                "score": "7.5",
                "feedback": "Phạm vi cấu trúc đa dạng, hòa hợp thì và thể chủ động/bị động chính xác."
            },
            "lexical": {
                "score": "8.0",
                "feedback": "Vốn từ vựng phong phú, sử dụng từ ngữ chính xác theo ngữ cảnh IELTS Part 1-3."
            }
        },
        "dialogue_turns": [
            {
                "turn_number": 1,
                "prompt": "Good morning. Could you tell me your full name and where you are from?",
                "user_response": "Good morning examiner. My full name is Nguyen Van Anh, and I was born and raised in Hanoi, the bustling capital city of Vietnam.",
                "score": "8.0",
                "feedback": "Trả lời đầy đủ, tự nhiên, mở đầu ấn tượng với cụm 'bustling capital city'.",
                "corrections": None
            },
            {
                "turn_number": 2,
                "prompt": "Do you work or are you a student at the moment?",
                "user_response": "Currently, I am a senior software developer at a technology company. My main duty is building cloud backend systems.",
                "score": "7.5",
                "feedback": "Trả lời đúng trọng tâm. Sử dụng thuật ngữ công việc chính xác.",
                "corrections": None
            },
            {
                "turn_number": 3,
                "prompt": "What do you enjoy most about your current job?",
                "user_response": "What I love most is the problem solving aspect. Every day I face complex technical challenges that require critical thinking and teamwork.",
                "score": "8.0",
                "feedback": "Diễn đạt mạch lạc, sử dụng các từ nối hiệu quả như 'critical thinking and teamwork'.",
                "corrections": None
            },
            {
                "turn_number": 4,
                "prompt": "Let's talk about hobbies. What do you usually do in your spare time?",
                "user_response": "In my leisure time, I am really keen on reading non-fiction books and playing acoustic guitar to unwind after intensive working hours.",
                "score": "7.5",
                "feedback": "Sử dụng cụm 'keen on' và 'unwind after intensive working hours' rất chuẩn IELTS.",
                "corrections": None
            },
            {
                "turn_number": 5,
                "prompt": "Did you have any different hobbies when you were a child?",
                "user_response": "When I was a kid, I used to playing football with my neighbors every afternoon, but now I don't have enough time for outdoor sports.",
                "score": "6.5",
                "feedback": "Lỗi ngữ pháp với cấu trúc 'used to + V-bare'.",
                "corrections": {
                    "original": "I used to playing football...",
                    "suggested": "I used to play football with my neighbors..."
                }
            },
            {
                "turn_number": 6,
                "prompt": "Now Part 2: Describe a memorable journey you have taken. You should say where you went, who you went with, and why it was memorable.",
                "user_response": "I would like to share about a road trip to Ha Giang province last autumn. I went with three of my closest university friends. The scenery was absolutely breathtaking with winding mountain passes and vibrant buckwheat flower fields. What made it truly unforgettable was the warm hospitality of the ethnic minorities.",
                "score": "8.5",
                "feedback": "Part 2 xuất sắc. Tính từ miêu tả cực kỳ sinh động: 'breathtaking', 'winding mountain passes', 'vibrant'.",
                "corrections": None
            },
            {
                "turn_number": 7,
                "prompt": "Do you think travelling to remote places is becoming more popular among young people?",
                "user_response": "Yes, absolutely. Nowadays young adults prefer off-the-beaten-track destinations rather than crowded commercial tourist spots because they seek authentic cultural experiences.",
                "score": "8.0",
                "feedback": "Dùng cụm idiom 'off-the-beaten-track' rất tự nhiên và phù hợp câu hỏi Part 3.",
                "corrections": None
            },
            {
                "turn_number": 8,
                "prompt": "How does tourism benefit local communities in mountainous regions?",
                "user_response": "Tourism can generate employment opportunities for local residents, such as running homestays or selling artisanal handicrafts. However, it can also lead to environmental degradation if not managed sustainably.",
                "score": "8.0",
                "feedback": "Phân tích 2 chiều tốt. Sử dụng từ vựng học thuật: 'generate employment', 'artisanal handicrafts', 'environmental degradation'.",
                "corrections": None
            },
            {
                "turn_number": 9,
                "prompt": "What are the drawbacks of rapid tourism growth?",
                "user_response": "Over-tourism can cause trash pollution and damage natural ecosystems. Furthermore, local prices might rise up, making life difficult for native people.",
                "score": "7.0",
                "feedback": "Tránh lặp từ 'rise up' bằng cụm từ học thuật hơn như 'escalate'.",
                "corrections": {
                    "original": "local prices might rise up...",
                    "suggested": "local prices might escalate / inflate dramatically..."
                }
            },
            {
                "turn_number": 10,
                "prompt": "Do you think technology will change how people travel in the future?",
                "user_response": "Undoubtedly. Virtual reality trips might become popular, allowing people to explore famous landmarks from home. However, physical travel will never lose its intrinsic charm.",
                "score": "8.0",
                "feedback": "Lập luận logic, sử dụng 'intrinsic charm' nâng cao điểm Lexical Resource.",
                "corrections": None
            },
            {
                "turn_number": 11,
                "prompt": "Should governments regulate the number of tourists visiting heritage sites?",
                "user_response": "I strongly believe governments should implement strict visitor caps to preserve historical integrity and prevent structural wear and tear.",
                "score": "8.5",
                "feedback": "Câu trả lời cô đọng, sắc sảo. Cụm 'visitor caps', 'wear and tear' rất ấn tượng.",
                "corrections": None
            },
            {
                "turn_number": 12,
                "prompt": "Thank you very much. That concludes our speaking assessment test today.",
                "user_response": "Thank you examiner. It was a pleasure talking with you today. Have a great day!",
                "score": "8.0",
                "feedback": "Kết thúc lịch sự, tự nhiên.",
                "corrections": None
            }
        ]
    }


if __name__ == "__main__":
    # Sample run
    sample_data = get_sample_report_data()
    out = generate_speaking_pdf(sample_data, "reports/sample_report.pdf")
    print(f"Generated sample report at: {out}")
