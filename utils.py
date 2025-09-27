# utils.py
import os
import glob
import webbrowser
import threading

def cleanup_files():
    """Xóa các file ảnh cũ."""
    out_dir = os.path.dirname(os.path.abspath(__file__))
    files_to_delete = glob.glob(os.path.join(out_dir, "*.jpg")) + glob.glob(os.path.join(out_dir, "*.png"))
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            print(f"Deleted old file: {os.path.basename(file_path)}")
        except OSError as e:
            print(f"Error deleting file {file_path}: {e}")

def open_browser_on_startup():
    """Mở trình duyệt sau khi ứng dụng khởi động."""
    def _open():
        cleanup_files()
        webbrowser.open("http://127.0.0.1:5001")
    threading.Timer(1, _open).start()
    
def scroll_full_page_smooth(page, step=300, delay=1500, max_wait_empty=3):
    """
    Cuộn toàn bộ trang mượt mà, đảm bảo lazy-load content được render.
    
    page: Playwright page object
    step: số pixel mỗi lần cuộn
    delay: thời gian chờ giữa mỗi scroll (ms)
    max_wait_empty: số lần liên tiếp không có content mới trước khi dừng
    """
    last_height = 0
    empty_loops = 0

    while True:
        # Lấy chiều cao hiện tại
        scroll_height = page.evaluate("() => document.body.scrollHeight")
        
        if scroll_height <= last_height:
            empty_loops += 1
            if empty_loops >= max_wait_empty:
                break  # Dừng nếu không có content mới sau max_wait_empty lần
        else:
            empty_loops = 0

        # Cuộn dần từ last_height tới scroll_height
        for pos in range(last_height, scroll_height, step):
            page.evaluate(f"() => window.scrollTo(0, {pos})")
            page.wait_for_timeout(delay)
        
        last_height = scroll_height

    # Cuộn về đầu trang
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(2000)