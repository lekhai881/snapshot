# main.py
from flask import Flask
from routes import main_routes
from utils import open_browser_on_startup

# Khởi tạo ứng dụng Flask
app = Flask(__name__)

# Đăng ký các routes từ file routes.py
app.register_blueprint(main_routes)


if __name__ == "__main__":
    # Mở trình duyệt tự động khi khởi động
    open_browser_on_startup()
    # Chạy ứng dụng
    app.run(debug=False, port=5001, host='127.0.0.1')