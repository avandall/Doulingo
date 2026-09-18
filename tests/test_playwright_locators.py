from pathlib import Path
from playwright.sync_api import Page, expect

def test_exploring_locators(page: Page):
    """
    Thực hành các loại Locators khác nhau trên giao diện Duolingo Speak
    """
    html_path = Path(__file__).parent.parent / "static" / "index.html"
    page.goto(f"file://{html_path.resolve()}")

    # 1. Tìm kiếm theo Role (Button có chữ 'Random')
    btn_random = page.get_by_role("button", name="🎲 Random")
    expect(btn_random).to_be_visible()
    print(f"\n[1] Nút Random có hiển thị: {btn_random.is_visible()}")

    # 2. Tìm kiếm theo Placeholder của ô Input
    input_filter = page.get_by_placeholder("Filter topic name...")
    expect(input_filter).to_be_visible()
    print(f"[2] Tìm thấy ô lọc chủ đề theo placeholder")

    # 3. Thu hẹp phạm vi (Chaining): Chỉ đếm các Category Pills trên thanh danh mục trang chủ
    home_cat_pills = page.locator(".cat-pill[data-ielts-cat]")
    pill_count = home_cat_pills.count()
    print(f"[3] Số chủ đề IELTS ở trang chủ: {pill_count}")
    expect(home_cat_pills).to_have_count(6)

    # In danh sách tên của 6 chủ đề này
    pill_names = home_cat_pills.all_text_contents()
    print(f"    Danh sách: {[name.strip() for name in pill_names]}")

    # 4. Tìm kiếm theo ID cụ thể
    btn_custom = page.locator("#btn-open-custom-modal")
    expect(btn_custom).to_contain_text("Custom")
    print(f"[4] Nút Custom có chứa text: {btn_custom.text_content().strip()}")
