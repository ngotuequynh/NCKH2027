"""Mở app Streamlit Community Cloud bằng trình duyệt không giao diện (headless). Nếu app đang
ngủ thì bấm nút đánh thức, rồi đợi tới khi giao diện app tải xong. Chạy định kỳ bởi
.github/workflows/keep-alive.yml.

Gọi HTTP đơn thuần (curl) không đủ: app Streamlit chỉ tính là "có người dùng" khi trình
duyệt mở kết nối websocket, và trang ngủ cần bấm nút mới thức dậy.

Biến môi trường: APP_URL (vd https://ten-app.streamlit.app).
"""
import os
import re
import sys
import time

from playwright.sync_api import sync_playwright

WAKE_BUTTON = re.compile(r"get this app back up", re.IGNORECASE)
APP_READY = '[data-testid="stAppViewContainer"]'
WAIT_SECONDS = 300


def _click_wake_button(page) -> bool:
    for frame in page.frames:
        button = frame.get_by_role("button", name=WAKE_BUTTON)
        if button.count():
            button.first.click()
            return True
    return False


def _app_loaded(page) -> bool:
    return any(frame.locator(APP_READY).count() for frame in page.frames)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    url = os.environ.get("APP_URL")
    if not url:
        print("Thiếu biến môi trường APP_URL.")
        return 1

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=120_000)
        page.wait_for_timeout(8_000)

        if _click_wake_button(page):
            print("App đang ngủ — đã bấm nút đánh thức.")

        deadline = time.time() + WAIT_SECONDS
        while time.time() < deadline:
            if _app_loaded(page):
                # Giữ kết nối thêm 1 lúc để Streamlit ghi nhận phiên truy cập.
                page.wait_for_timeout(20_000)
                print("App đã chạy:", url)
                browser.close()
                return 0
            # Nút đánh thức có thể hiện chậm sau khi trang tải.
            _click_wake_button(page)
            page.wait_for_timeout(5_000)

        page.screenshot(path="keep_alive_failed.png", full_page=True)
        browser.close()
    print(f"App không tải xong sau {WAIT_SECONDS} giây.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
