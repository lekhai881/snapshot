# state.py

# Lớp đơn giản để chứa giá trị và cho phép thay đổi từ các module khác
class ValueContainer:
    def __init__(self, value=None):
        self.value = value

class SessionContainer:
    def __init__(self, session=None):
        self.session = session

# --- Các biến trạng thái toàn cục của ứng dụng ---
# Chúng được định nghĩa ở đây để các module khác có thể import và sử dụng chung.
completed_captures = set()
total_captures = ValueContainer(0)
current_capturing = ValueContainer("Đang khởi tạo...")

grafana_session = SessionContainer() # Dùng để chứa đối tượng GrafanaSession
cached_grafana_user = ValueContainer("")
cached_grafana_pass = ValueContainer("")
# ----------------------------------------------------