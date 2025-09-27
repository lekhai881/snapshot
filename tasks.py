# tasks.py
import os
import threading
import time
from datetime import datetime

from grafana_auth import GrafanaSession
from captures.dynatrace_capture import capture_dynatrace
from config import GRAFANA_CONFIG, DYNATRACE_DASHBOARDS
from utils import cleanup_files
from state import completed_captures, total_captures, current_capturing, grafana_session


# ... (Toàn bộ phần code còn lại của file tasks.py giữ nguyên) ...
# ... (Sao chép y hệt phần code cũ của bạn từ def process_screenshots(...) trở đi) ...
def process_screenshots(start, end, services, grafana_user, grafana_pass):
    """Hàm điều phối chính, bắt đầu quá trình chụp ảnh."""
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M")
        
        dashboards = _build_dashboard_list(start_dt, end_dt, services)
        
        cleanup_files()
        
        # Reset tiến trình
        completed_captures.clear()
        current_capturing.value = "Đang khởi tạo..."
        total_captures.value = len(dashboards)
        print(f"Total dashboards to capture: {total_captures.value}")

        grafana_tasks = [item for item in dashboards if item['type'] == 'grafana']
        dynatrace_tasks = [item for item in dashboards if item['type'] == 'dynatrace']
        out_dir = os.path.dirname(os.path.abspath(__file__))
        
        for task in dynatrace_tasks:
            threading.Thread(target=_run_dynatrace_capture, args=(task, out_dir), daemon=True).start()
        
        if grafana_tasks:
            threading.Thread(target=_run_all_grafana, args=(grafana_tasks, grafana_user, grafana_pass, out_dir), daemon=True).start()

    except Exception as e:
        print(f"Error processing screenshots: {e}")


def _run_dynatrace_capture(task, out_dir):
    """Chạy một tác vụ chụp ảnh Dynatrace."""
    key, url, fname, w, h = task['key'], task['url'], task['filename'], task['width'], task['height']
    out_path = os.path.join(out_dir, fname)
    
    current_capturing.value = key
    print(f"Starting Dynatrace capture: {key}")
    capture_dynatrace(url, out_path, "khails", "Ha@noi!23456", width=w, height=h)
    completed_captures.add(key)
    current_capturing.value = f"Đã chụp ảnh {key}"
    print(f"Completed: {key} ({len(completed_captures)}/{total_captures.value})")


def _run_all_grafana(tasks, username, password, out_dir):
    """Chạy tất cả các tác vụ Grafana một cách tuần tự."""
    global grafana_session
    grafana_session.session = GrafanaSession(enable_cache=True)
    
    try:
        if not grafana_session.session.login(username, password):
            print("Grafana login failed, skipping all Grafana captures.")
            for task in tasks:
                completed_captures.add(task['key'])
            return

        for task in tasks:
            key, url, fname, w, h, q = task['key'], task['url'], task['filename'], task['width'], task['height'], task['quality']
            out_file = os.path.join(out_dir, fname)
            
            current_capturing.value = key
            print(f"Starting Grafana capture: {key}")
            grafana_session.session.capture(url, out_file, w, h, q)
            completed_captures.add(key)
            current_capturing.value = f"Đã chụp ảnh {key}"
            print(f"Completed: {key} ({len(completed_captures)}/{total_captures.value})")
            
    except Exception as e:
        print(f"Error in Grafana capture thread: {e}")
    finally:
        if grafana_session.session:
            grafana_session.session.close()


def _build_dashboard_list(start_dt, end_dt, services):
    """Xây dựng danh sách các dashboard cần chụp từ cấu hình."""
    start_unix = int(time.mktime(start_dt.timetuple()) * 1000)
    end_unix = int(time.mktime(end_dt.timetuple()) * 1000)
    start_t24 = start_dt.strftime("%Y-%m-%dT%H:%M:00+07:00")
    end_t24 = end_dt.strftime("%Y-%m-%dT%H:%M:00+07:00")
    start_node = start_t24.replace('+', '%2B')
    end_node = end_t24.replace('+', '%2B')

    tasks = []
    for config in DYNATRACE_DASHBOARDS:
        url = config["url_template"].format(start_t24=start_t24, end_t24=end_t24, start_node=start_node, end_node=end_node)
        tasks.append({
            "type": "dynatrace", "key": config["key"], "filename": config["filename"],
            "url": url, "width": config["width"], "height": config["height"]
        })

    if services:
        service_list = [s.strip() for s in services.split(',')]
        for service in service_list:
            if service:
                url = f"{GRAFANA_CONFIG['base_url']}{GRAFANA_CONFIG['params']}&var-deployment={service}&from={start_unix}&to={end_unix}"
                w, h, q = GRAFANA_CONFIG['custom_settings'].get(service, GRAFANA_CONFIG['default_settings'])
                tasks.append({
                    "type": "grafana", "key": f"Grafana_{service}", "filename": f"Grafana_{service}.jpg",
                    "url": url, "width": w, "height": h, "quality": q
                })
    return tasks