# grafana_auth.py
import os
import time
import re
from playwright.sync_api import sync_playwright
from browser_path import get_chrome_path
from utils import scroll_full_page_smooth

class GrafanaSession:
    def __init__(self, enable_cache=True):
        self.playwright = None
        self.browser = None
        self.page = None
        self.mfa_code = "Chưa có mã"
        self.mfa_confirmed = False
        self.mfa_timeout = False
        self.mfa_updated = False
        self.mfa_start_time = 0
        self.mfa_code_found = False
        self.enable_cache = enable_cache
        self.cached_user = ""
        self.cached_pass = ""

    def login(self, username, password, headless=True):
        """Khởi tạo trình duyệt và đăng nhập vào Grafana."""
        print("Creating new Grafana session")
        self.close()

        self.mfa_code = "Chưa có mã"
        self.mfa_confirmed = False
        self.mfa_timeout = False
        self.mfa_updated = True
        self.mfa_start_time = 0
        self.mfa_code_found = False

        try:
            self.playwright = sync_playwright().start()
            
            try:
                chrome_path = get_chrome_path()
                self.browser = self.playwright.chromium.launch(headless=headless, executable_path=chrome_path)
            except:
                self.browser = self.playwright.chromium.launch(headless=headless)
            
            self.page = self.browser.new_page(viewport={'width': 2800, 'height': 2500})
            
            self.page.goto("https://g-fc11b5da8e.grafana-workspace.ap-southeast-1.amazonaws.com/login", wait_until="networkidle")
            self.page.wait_for_timeout(1000)
            self.page.click('a:has-text("Sign in with AWS")')
            self.page.wait_for_timeout(1000)
            
            self.page.wait_for_selector('input[name="loginfmt"]')
            self.page.fill('input[name="loginfmt"]', username)
            self.page.click('input[type="submit"]')
            self.page.wait_for_timeout(2000)
            
            self.page.fill('input[name="passwd"]', password)
            self.page.click('input[type="submit"]')
            self.page.wait_for_timeout(2000)
            
            for _ in range(90):
                current_url = self.page.url
                
                if "/login" in current_url and "microsoftonline.com" in current_url:
                    page_text = self.page.inner_text('body')
                    if "Request denied" in page_text or "you denied it" in page_text:
                        self.mfa_code = "Người dùng từ chối xác thực MFA"
                        break
                    
                    numbers = re.findall(r'\b\d{2,3}\b', page_text)
                    if numbers:
                        new_code = numbers[0]
                        if not self.mfa_code_found or self.mfa_code != new_code:
                            self.mfa_code = new_code
                            self.mfa_updated = True
                            self.mfa_code_found = True
                            self.mfa_start_time = time.time()
                            print(f"Found MFA code: {self.mfa_code}")
                    else:
                        print(f"No MFA code found in page text: {page_text[:200]}...")

                if "ProcessAuth" in current_url:
                    try:
                        self.page.click('input[id="idSIButton9"]', timeout=3000)
                    except:
                        pass
                
                if "grafana-workspace" in current_url:
                    self.mfa_confirmed = True
                    if self.enable_cache:
                        self.cached_user = username
                        self.cached_pass = password
                    print(f"Grafana login successful for user: {username}")
                    return True

                self.page.wait_for_timeout(1000)
            
            self.mfa_timeout = True
            self.mfa_confirmed = True
            if "từ chối" not in self.mfa_code:
                 self.mfa_code = "Đã bỏ qua MFA tự động do timeout"
            print("MFA timeout or denied. Auto-skipping.")
            return False

        except Exception as e:
            print(f"Grafana login error: {e}")
            self.mfa_timeout = True
            self.mfa_code = "Lỗi đăng nhập Grafana!"
            self.close()
            return False

    def capture(self, url, out_file, width, height, quality):
        """Chụp ảnh một dashboard Grafana bằng logic gốc đã hoạt động."""
        if not self.page:
            print("Grafana page is not available. Capture failed.")
            # Tạo file trống báo lỗi
            with open(out_file, 'w') as f:
                f.write("Grafana capture failed - No page available")
            return
        
        try:
            self.page.set_viewport_size({'width': width, 'height': height})
            
            self.page.goto(url, wait_until="networkidle")
            self.page.wait_for_timeout(500)
            
            collapsed_rows = [
                "SpringBoot Executors",
                "JVM Heap",
                "JVM Live Thread", 
                "JVM Thread State",
                "Hikari Connection",
                "Hikari Connection Time",
                "Http request"
            ]
            
            try:
                self.page.click('text="CPU/Mem Usage (%)"')
                self.page.wait_for_timeout(500)
                self.page.click('text="CPU/Mem Usage"')
                self.page.wait_for_timeout(500)
            except:
                pass
            
            for row in collapsed_rows:
                try:
                    self.page.click(f'text={row}')
                    self.page.wait_for_timeout(500)
                except:
                    pass
            
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self.page.wait_for_timeout(500)
            
            scroll_full_page_smooth(self.page, step=300, delay=500, max_wait_empty=3)
            
            self.page.screenshot(path=out_file, full_page=True, quality=quality)
            print(f"Grafana screenshot taken: {out_file}")
            
        except Exception as e:
            print(f"Error in capture_grafana method: {e}")
        
        # Kiểm tra lại file sau khi thực thi, tạo file lỗi nếu cần
        if not os.path.exists(out_file) or os.path.getsize(out_file) == 0:
            print(f"Creating error file for failed Grafana capture: {out_file}")
            with open(out_file, 'w') as f:
                f.write(f"Grafana capture failed")

    def close(self):
        """Đóng trình duyệt và giải phóng tài nguyên Playwright."""
        if self.page:
            try: self.page.close()
            except: pass
        if self.browser:
            try: self.browser.close()
            except: pass
        if self.playwright:
            try: self.playwright.stop()
            except: pass
        self.playwright = self.browser = self.page = None
        print("Grafana session closed.")