import os
from pathlib import Path
from playwright.sync_api import Page, expect

def test_homepage_title_and_screenshot(page: Page):
    """
    Test cơ bản:
    1. Mở file static/index.html của dự án
    2. Kiểm tra Title trang web
    3. Chụp 1 tấm ảnh màn hình (screenshot) lưu vào thư mục output
    """
    # Đường dẫn tuyệt đối đến file static/index.html trong dự án
    html_path = Path(__file__).parent.parent / "static" / "index.html"
    file_url = f"file://{html_path.resolve()}"

    # 1. Điều hướng trình duyệt tới trang
    page.goto(file_url)

    # 2. Kiểm tra tiêu đề trang (Playwright assertion có cơ chế auto-wait)
    expect(page).to_have_title("Haku Haku's — AI English Speaking Practice")

    # 3. Tạo thư mục output nếu chưa có và chụp ảnh màn hình
    os.makedirs("output", exist_ok=True)
    screenshot_path = "output/step2_homepage.png"
    page.screenshot(path=screenshot_path)

    print(f"\n✅ Đã mở trang thành công và lưu ảnh tại: {screenshot_path}")
