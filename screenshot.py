# screenshot.py
from flask import Flask, render_template, request, send_file, Response
from datetime import datetime, timedelta
import os, webbrowser, threading, time, zipfile, glob
from io import BytesIO

# Import lớp GrafanaSession từ file mới
from grafana_auth import GrafanaSession
from captures.dynatrace_capture import capture_dynatrace

app = Flask(__name__)

# Các biến toàn cục quản lý tiến trình chung
completed_captures = set()
total_captures = 0
current_capturing = "Đang khởi tạo..."

# Biến toàn cục để giữ session Grafana, giúp các route khác có thể truy cập
grafana_session = None

# Cấu hình cache và Grafana
ENABLE_CACHE = True
cached_grafana_user = ""
cached_grafana_pass = ""
current_session = {"services": "", "start_unix": 0, "end_unix": 0}

grafana_config = {
    "base_url": "https://g-fc11b5da8e.grafana-workspace.ap-southeast-1.amazonaws.com/d/PlBgdfv7h/16be689c-e129-5788-bb7b-b17af4cba983",
    "params": "?orgId=1&var-Cluster=r8Nd0NUSk&var-namespace=rdb-pt&var-pod=All",
    "default_settings": (2800, 3500, 80),
    "custom_settings": {
        'rdb-identity-confirmation': (2800, 5000, 55),
        'rdb-payment-dis': (2800, 5000, 55), 
        'rdb-payment-order-service-extension': (2800, 5000, 55),
        'rdb-transaction-manager-extension':(2800, 5000, 55),
        'rdb-access-control-extension':(2800, 6000, 55),
        'rdb-user-manager-extension':(2800, 4500, 55)
    }
}

@app.route("/", methods=["GET", "POST"])
def index():
    global cached_grafana_user, cached_grafana_pass
    timeout = 3600
    if request.method == "POST":
        start = request.form.get("start")
        end = request.form.get("end")
        services = request.form.get("services")
        grafana_user = request.form.get("grafana_user")
        grafana_pass = request.form.get("grafana_pass")
        
        # Cache credentials nếu người dùng gửi form
        if ENABLE_CACHE:
            cached_grafana_user = grafana_user
            cached_grafana_pass = grafana_pass
            
        # Xử lý logic chụp ảnh
        process_screenshots(start, end, services, grafana_user, grafana_pass)
        
        return render_template("dashboard.html", 
                                    start=start, end=end, services=services or "", timeout=timeout,
                                    login_display="none", form_display="block",
                                    grafana_user=grafana_user, grafana_pass=grafana_pass)
    
    # Logic cho GET request
    now = datetime.now()
    end_default = now.strftime("%Y-%m-%d %H:%M")
    start_default = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    
    return render_template("dashboard.html", 
                                start=start_default, end=end_default, services="", timeout=timeout,
                                login_display="block" if not (ENABLE_CACHE and cached_grafana_user) else "none",
                                form_display="none" if not (ENABLE_CACHE and cached_grafana_user) else "block",
                                grafana_user=cached_grafana_user, grafana_pass=cached_grafana_pass)

def process_screenshots(start, end, services, grafana_user, grafana_pass):
    global total_captures, completed_captures, current_capturing, current_session
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M")
        
        # Xây dựng danh sách dashboard từ config
        dashboards = build_dashboard_list(start_dt, end_dt, services)
        
        cleanup_files()
        
        # Reset tiến trình
        completed_captures.clear()
        current_capturing = "Đang khởi tạo..."
        total_captures = len(dashboards)
        print(f"Total dashboards to capture: {total_captures}")

        # Tách riêng các services của Grafana và Dynatrace
        grafana_tasks = [item for item in dashboards if item['type'] == 'grafana']
        dynatrace_tasks = [item for item in dashboards if item['type'] == 'dynatrace']
        out_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Chạy Dynatrace captures song song
        for task in dynatrace_tasks:
            threading.Thread(target=run_dynatrace_capture, args=(task, out_dir), daemon=True).start()
        
        # Chạy Grafana captures tuần tự trong một thread riêng
        if grafana_tasks:
            threading.Thread(target=run_all_grafana, args=(grafana_tasks, grafana_user, grafana_pass, out_dir), daemon=True).start()

    except Exception as e:
        print(f"Error processing screenshots: {e}")

def run_dynatrace_capture(task, out_dir):
    global current_capturing, completed_captures
    key, url, fname, w, h = task['key'], task['url'], task['filename'], task['width'], task['height']
    out_path = os.path.join(out_dir, fname)
    
    current_capturing = key
    print(f"Starting Dynatrace capture: {key}")
    capture_dynatrace(url, out_path, "khails", "Ha@noi!23456", width=w, height=h)
    completed_captures.add(key)
    current_capturing = f"Đã chụp ảnh {key}"
    print(f"Completed: {key} ({len(completed_captures)}/{total_captures})")

def run_all_grafana(tasks, username, password, out_dir):
    global grafana_session, current_capturing, completed_captures
    
    # Tạo một instance GrafanaSession và gán vào biến global
    grafana_session = GrafanaSession(enable_cache=ENABLE_CACHE)
    
    try:
        if not grafana_session.login(username, password):
            print("Grafana login failed, skipping all Grafana captures.")
            # Đánh dấu tất cả task Grafana là hoàn thành (thất bại)
            for task in tasks:
                completed_captures.add(task['key'])
            return

        for task in tasks:
            key, url, fname, w, h, q = task['key'], task['url'], task['filename'], task['width'], task['height'], task['quality']
            out_file = os.path.join(out_dir, fname)
            
            current_capturing = key
            print(f"Starting Grafana capture: {key}")
            grafana_session.capture(url, out_file, w, h, q)
            completed_captures.add(key)
            current_capturing = f"Đã chụp ảnh {key}"
            print(f"Completed: {key} ({len(completed_captures)}/{total_captures})")
            
    except Exception as e:
        print(f"Error in Grafana capture thread: {e}")
    finally:
        # Quan trọng: Luôn đóng session để dọn dẹp tài nguyên
        if grafana_session:
            grafana_session.close()

def build_dashboard_list(start_dt, end_dt, services):
    start_unix = int(time.mktime(start_dt.timetuple()) * 1000)
    end_unix = int(time.mktime(end_dt.timetuple()) * 1000)
    start_t24 = start_dt.strftime("%Y-%m-%dT%H:%M:00+07:00")
    end_t24 = end_dt.strftime("%Y-%m-%dT%H:%M:00+07:00")
    start_node = start_t24.replace('+', '%2B')
    end_node = end_t24.replace('+', '%2B')

    dashboard_configs = [
        {"key": "Dynatrace_T24", "filename": "dashboard_T24.jpg", "type": "dynatrace",
         "url_template": "https://dynatracetest.techcombank.com.vn/e/8016500b-51f5-42fe-8ade-89b9b59bb26c/#dashboard;gtf={start_t24}%20to%20{end_t24};gf=all;id=3c90dc59-ec07-4f9c-814e-541a5f63d1e9",
         "width": 2800, "height": 4900},
        {"key": "Dynatrace_ESB", "filename": "dashboard_ESB.jpg", "type": "dynatrace",
         "url_template": "https://dynatracetest.techcombank.com.vn/e/8016500b-51f5-42fe-8ade-89b9b59bb26c/ui/entity/HOST-0CC233A090E87228?gtf={start_node}%20to%20{end_node}&gf=-815432565033324387",
         "width": 2600, "height": 1800},
        {"key": "Dynatrace_Node1", "filename": "dashboard_APIGW_Node1.jpg", "type": "dynatrace",
         "url_template": "https://dynatracetest.techcombank.com.vn/e/8016500b-51f5-42fe-8ade-89b9b59bb26c/ui/entity/HOST-4725B65FC5E6984C?gtf={start_node}%20to%20{end_node}&gf=all",
         "width": 2600, "height": 1800},
        {"key": "Dynatrace_Node2", "filename": "dashboard_APIGW_Node2.jpg", "type": "dynatrace",
         "url_template": "https://dynatracetest.techcombank.com.vn/e/8016500b-51f5-42fe-8ade-89b9b59bb26c/ui/entity/HOST-DD969D733CE5DFEB?gtf={start_node}%20to%20{end_node}&gf=all",
         "width": 2600, "height": 1800},
        {"key": "Dynatrace_RDS_ROC", "filename": "RDS(DB)_ROC.jpg", "type": "dynatrace",
         "url_template": "https://dynatracetest.techcombank.com.vn/e/8016500b-51f5-42fe-8ade-89b9b59bb26c/#dashboard;gtf={start_t24}%20to%20{end_t24};gf=all;id=8c5975ff-7a23-4e7e-974c-c688983dbfc0",
         "width": 2600, "height": 1800},
        {"key": "Dynatrace_Dashboard_ROC", "filename": "Dashboard_ROC.jpg", "type": "dynatrace",
         "url_template": "https://dynatracetest.techcombank.com.vn/e/8016500b-51f5-42fe-8ade-89b9b59bb26c/#dashboard;gtf={start_t24}%20to%20{end_t24};gf=-7151761915816887563;id=21676786-9e66-4479-84d8-d438b4728f07",
         "width": 2600, "height": 1800},
        {"key": "Dynatrace_Main_Functions_ROC", "filename": "Main_Functions_ROC.jpg", "type": "dynatrace",
         "url_template": "https://dynatracetest.techcombank.com.vn/e/8016500b-51f5-42fe-8ade-89b9b59bb26c/#dashboard;gtf={start_t24}%20to%20{end_t24};gf=all;id=ae4e88fe-de6b-486a-b29e-11030dab8a0a",
         "width": 2600, "height": 1800}
    ]
    
    tasks = []
    for config in dashboard_configs:
        url = config["url_template"].format(start_t24=start_t24, end_t24=end_t24, start_node=start_node, end_node=end_node)
        tasks.append({
            "type": "dynatrace", "key": config["key"], "filename": config["filename"],
            "url": url, "width": config["width"], "height": config["height"]
        })

    if services:
        service_list = [s.strip() for s in services.split(',')]
        for service in service_list:
            if service:
                url = f"{grafana_config['base_url']}{grafana_config['params']}&var-deployment={service}&from={start_unix}&to={end_unix}"
                w, h, q = grafana_config['custom_settings'].get(service, grafana_config['default_settings'])
                tasks.append({
                    "type": "grafana", "key": f"Grafana_{service}", "filename": f"Grafana_{service}.jpg",
                    "url": url, "width": w, "height": h, "quality": q
                })
    return tasks

@app.route("/mfa_code")
def get_mfa_code():
    global grafana_session
    if grafana_session:
        # Reset updated flag after sending
        updated_status = grafana_session.mfa_updated
        grafana_session.mfa_updated = False
        return {
            "code": grafana_session.mfa_code,
            "confirmed": grafana_session.mfa_confirmed,
            "timeout": grafana_session.mfa_timeout,
            "updated": updated_status,
            "denied": "từ chối" in grafana_session.mfa_code.lower()
        }
    return {"code": "Chưa khởi tạo", "confirmed": False, "timeout": False, "updated": False, "denied": False}

@app.route("/progress")
def get_progress():
    global grafana_session
    mfa_timeout_status = grafana_session.mfa_timeout if grafana_session else False
    mfa_code_text = grafana_session.mfa_code if grafana_session and grafana_session.mfa_code else ""
    mfa_denied_status = "người dùng từ chối" in mfa_code_text.lower()
    
    dynatrace_completed = len([k for k in completed_captures if k.startswith("Dynatrace_")])
    dynatrace_total = 7

    return {
        "completed": len(completed_captures),
        "total": total_captures,
        "current": current_capturing,
        "mfa_timeout": mfa_timeout_status,
        "denied": mfa_denied_status,
        "dynatrace_completed": dynatrace_completed,
        "dynatrace_total": dynatrace_total
    }

@app.route("/download/<filename>")
def download_file(filename):
    out_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(out_dir, filename)
    
    # Wait for file to exist
    for _ in range(300):
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return send_file(file_path, as_attachment=True)
        time.sleep(1)
    
    return "File not ready yet, please try again", 404

@app.route("/get_files")
def get_files():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    jpg_files = glob.glob(os.path.join(out_dir, "*.jpg"))
    filenames = sorted([os.path.basename(f) for f in jpg_files if os.path.getsize(f) > 0])
    return filenames

@app.route("/download_zip")
def download_zip():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    jpg_files = glob.glob(os.path.join(out_dir, "*.jpg"))
    
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in jpg_files:
            if os.path.getsize(file_path) > 0:
                zip_file.write(file_path, os.path.basename(file_path))
    
    zip_buffer.seek(0)
    
    return Response(
        zip_buffer.getvalue(),
        mimetype='application/zip',
        headers={'Content-Disposition': 'attachment; filename=screenshots.zip'}
    )

def cleanup_files():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    files_to_delete = glob.glob(os.path.join(out_dir, "*.jpg")) + glob.glob(os.path.join(out_dir, "*.png"))
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            print(f"Deleted old file: {os.path.basename(file_path)}")
        except OSError as e:
            print(f"Error deleting file {file_path}: {e}")

def open_browser():
    cleanup_files()
    webbrowser.open("http://127.0.0.1:5001")

if __name__ == "__main__":
    threading.Timer(1, open_browser).start()
    app.run(debug=False, port=5001, host='127.0.0.1')