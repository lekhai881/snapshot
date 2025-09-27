import os, platform

def get_chrome_path():
    system = platform.system()
    if system == "Darwin":  # macOS
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif system == "Windows":
        paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
        ]
        for path in paths:
            if os.path.exists(path):
                return path
    return None