from playwright.sync_api import sync_playwright
from utils import scroll_full_page_smooth
from browser_path import get_chrome_path

def capture_dynatrace(url, out_file, username, password, width=3400, height=4900):
    """ width, height có thể truyền riêng cho từng dashboard """
    try:
        print(f"Starting capture: {out_file}")
        with sync_playwright() as p:
            try:
                chrome_path = get_chrome_path()
                if chrome_path:
                    browser = p.chromium.launch(headless=True, executable_path=chrome_path)
                else:
                    browser = p.chromium.launch(headless=True)
            except:
                try:
                    browser = p.chromium.launch(headless=True)
                except:
                    browser = p.webkit.launch(headless=True)
            page = browser.new_page(viewport={'width': width, 'height': height})
            print(f"Going to: {url}")
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(3000)
            
            if page.locator('input[name="user"]').count() > 0:
                print("Login form found, filling credentials...")
                page.fill('input[name="user"]', username)
                page.fill('input[name="pass"]', password)
                page.click('input[type="submit"]')
                page.wait_for_timeout(8000)
            else:
                print("No login form found, proceeding...")
            
            page.wait_for_timeout(10000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(5000)

            scroll_full_page_smooth(page, step=300, delay=500, max_wait_empty=3)

            page.screenshot(path=out_file, full_page=True, quality=73)
            print(f"Screenshot saved: {out_file}")
            browser.close()
    except Exception as e:
        print(f"Error capturing {out_file}: {e}")
        with open(out_file, 'w') as f:
            f.write(f"Capture failed: {e}")