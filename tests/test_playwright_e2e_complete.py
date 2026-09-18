import functools
import http.server
import json
import threading
import pytest
from playwright.sync_api import Page, Route, expect

@pytest.fixture(scope="module")
def server_url():
    """Khởi động test server trên một cổng tự do ngẫu nhiên do OS cấp"""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=".")
    # Port 0 -> Hệ điều hành tự động chọn 1 port còn trống
    httpd = http.server.HTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()

def test_full_roleplay_flow(page: Page, server_url: str):
    """
    Kịch bản E2E hoàn chỉnh:
    1. Mock danh sách AI Characters
    2. Truy cập trang web (theo dynamic server_url)
    3. Chọn AI Partner 'Antigravity AI'
    4. Lọc chủ đề bằng ô input filter
    5. Mở và tương tác với Topic Explorer Modal
    """
    # 1. Mock Characters API
    page.route(
        "**/api/characters",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "characters": [
                    {"id": "antigravity", "name": "Antigravity AI", "avatar_icon": "🤖", "accent": "Silicon Valley"}
                ]
            })
        )
    )

    # 2. Mở ứng dụng
    page.goto(f"{server_url}/static/index.html")

    # 3. Chọn nhân vật Antigravity AI
    char_card = page.locator(".character-card").first
    expect(char_card).to_contain_text("Antigravity AI")
    char_card.click()

    # 4. Tìm kiếm lọc chủ đề trong bảng Roleplay
    input_filter_name = page.locator("#roleplay-filter-name")
    input_filter_name.fill("Coffee")
    
    # 5. Mở Topic Explorer Modal
    btn_explorer = page.locator("#btn-open-explorer-modal")
    btn_explorer.click()

    modal_explorer = page.locator("#modal-topic-explorer")
    expect(modal_explorer).to_be_visible()

    # Đóng Explorer Modal
    btn_close = page.locator("#btn-close-explorer-modal")
    btn_close.click()
    expect(modal_explorer).not_to_be_visible()

    print("\n🎉 Toàn bộ kịch bản E2E đã chạy thành công 100%!")
