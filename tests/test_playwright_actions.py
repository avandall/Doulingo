import functools
import http.server
import threading
import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="module", autouse=True)
def run_test_server():
    """Khởi động test server HTTP phục vụ toàn bộ static files của dự án"""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=".")
    httpd = http.server.HTTPServer(("127.0.0.1", 8088), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield
    httpd.shutdown()

def test_custom_topic_modal_interaction(page: Page):
    """
    Kịch bản tương tác đầy đủ:
    1. Mở giao diện Duolingo Speak
    2. Click mở Modal tạo Custom Topic
    3. Điền Form (Title, Description, Chọn Emoji)
    4. Đóng Modal và kiểm tra trạng thái ẩn/hiện
    """
    # 1. Truy cập qua HTTP server phục vụ static/index.html
    page.goto("http://127.0.0.1:8088/static/index.html")

    modal = page.locator("#modal-custom-topic")
    btn_open_custom = page.locator("#btn-open-custom-modal")

    # Trước khi click, modal phải đang ẩn
    expect(modal).not_to_be_visible()

    # 2. Click nút mở Modal
    print("\n[1] Đang click nút mở Custom Modal...")
    btn_open_custom.click()

    # Sau khi click, JS chạy và modal phải xuất hiện
    expect(modal).to_be_visible()
    print("[2] Modal đã hiển thị thành công trên màn hình!")

    # 3. Điền thông tin vào Form
    input_title = page.locator("#custom-topic-title")
    input_desc = page.locator("#custom-topic-desc")

    input_title.fill("Học Playwright E2E Testing")
    input_desc.fill("Thực hành tự động hóa giao diện web từng bước.")

    # Kiểm tra giá trị đã được điền chính xác vào ô input
    expect(input_title).to_have_value("Học Playwright E2E Testing")
    print("[3] Đã nhập form thành công.")

    # 4. Chọn Emoji tên lửa 🚀
    emoji_rocket = page.locator(".emoji-item[data-emoji='🚀']")
    emoji_rocket.click()
    
    # Kiểm tra class 'active' được gán cho emoji tên lửa
    expect(emoji_rocket).to_have_class("emoji-item active")
    print("[4] Đã chọn Emoji 🚀.")

    # 5. Click nút Cancel để đóng Modal
    btn_cancel = page.locator("#btn-cancel-custom-modal")
    btn_cancel.click()

    # Xác nhận Modal đã đóng hoàn toàn
    expect(modal).not_to_be_visible()
    print("[5] Đã đóng Modal thành công.")
