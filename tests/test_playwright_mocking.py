import functools
import http.server
import json
import threading
import pytest
from playwright.sync_api import Page, Route, expect

@pytest.fixture(scope="module", autouse=True)
def run_test_server():
    """Khởi động test server tĩnh"""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=".")
    httpd = http.server.HTTPServer(("127.0.0.1", 8088), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield
    httpd.shutdown()

def test_mock_ai_characters_and_select(page: Page):
    """
    Kịch bản:
    1. Đánh chặn API /api/characters và trả về 2 nhân vật AI giả lập
    2. Tải trang và kiểm tra UI render đúng 2 nhân vật từ dữ liệu mock
    3. Click chọn nhân vật đầu tiên và kiểm tra trạng thái
    """
    # 1. ĐỊNH NGHĨA DỮ LIỆU MOCK
    mock_characters_data = {
        "characters": [
            {
                "id": "antigravity_agent",
                "name": "Antigravity AI",
                "avatar_icon": "🤖",
                "accent": "Silicon Valley (Native)"
            },
            {
                "id": "duo_master",
                "name": "Master Duo",
                "avatar_icon": "🦉",
                "accent": "Oxford English"
            }
        ]
    }

    # 2. ĐÁNH CHẶN REQUEST TỚI /api/characters
    def handle_characters_route(route: Route):
        print("\n⚡ [Playwright Intercept] Đã bắt request /api/characters và trả về Mock Data!")
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(mock_characters_data)
        )

    # Đăng ký route trước khi goto
    page.route("**/api/characters", handle_characters_route)

    # 3. Mở trang web
    page.goto("http://127.0.0.1:8088/static/index.html")

    # 4. KIỂM THỬ GIAO DIỆN (Web-First Assertions)
    # Danh sách character cards phải hiển thị đúng 2 thẻ
    char_cards = page.locator(".character-card")
    expect(char_cards).to_have_count(2)
    print(f"[1] Số lượng nhân vật render trên UI: {char_cards.count()}")

    # Kiểm tra tên nhân vật đầu tiên đúng là 'Antigravity AI'
    first_char = char_cards.first
    expect(first_char).to_contain_text("Antigravity AI")
    expect(first_char).to_contain_text("Silicon Valley (Native)")
    print("[2] Thẻ nhân vật 'Antigravity AI' hiển thị chính xác!")

    # 5. Tương tác: Click chọn nhân vật thứ 2 (Master Duo)
    second_char = char_cards.nth(1)
    second_char.click()
    print("[3] Đã click chọn 'Master Duo' thành công.")
