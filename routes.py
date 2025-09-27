# routes.py
import os
import glob
import time
import zipfile
from io import BytesIO
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, send_file, Response

from tasks import process_screenshots
from config import ENABLE_CACHE, DYNATRACE_DASHBOARDS

# THAY ĐỔI: Import các biến trạng thái từ state.py thay vì main.py
from state import (
    completed_captures, total_captures, current_capturing, 
    grafana_session, cached_grafana_user, cached_grafana_pass
)

main_routes = Blueprint('main', __name__)

# ... (Toàn bộ phần code còn lại của file routes.py giữ nguyên) ...
# ... (Sao chép y hệt phần code cũ của bạn từ @main_routes.route("/") trở đi) ...
@main_routes.route("/", methods=["GET", "POST"])
def index():
    timeout = 3600
    if request.method == "POST":
        start = request.form.get("start")
        end = request.form.get("end")
        services = request.form.get("services")
        grafana_user = request.form.get("grafana_user")
        grafana_pass = request.form.get("grafana_pass")
        
        if ENABLE_CACHE:
            cached_grafana_user.value = grafana_user
            cached_grafana_pass.value = grafana_pass
            
        process_screenshots(start, end, services, grafana_user, grafana_pass)
        
        return render_template("dashboard.html", 
                               start=start, end=end, services=services or "", timeout=timeout,
                               login_display="none", form_display="block",
                               grafana_user=grafana_user, grafana_pass=grafana_pass)
    
    now = datetime.now()
    end_default = now.strftime("%Y-%m-%d %H:%M")
    start_default = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    
    use_cache = ENABLE_CACHE and cached_grafana_user.value
    return render_template("dashboard.html", 
                           start=start_default, end=end_default, services="", timeout=timeout,
                           login_display="none" if use_cache else "block",
                           form_display="block" if use_cache else "none",
                           grafana_user=cached_grafana_user.value, 
                           grafana_pass=cached_grafana_pass.value)

@main_routes.route("/mfa_code")
def get_mfa_code():
    session = grafana_session.session
    if session:
        updated_status = session.mfa_updated
        session.mfa_updated = False
        return {
            "code": session.mfa_code, "confirmed": session.mfa_confirmed,
            "timeout": session.mfa_timeout, "updated": updated_status,
            "denied": "từ chối" in session.mfa_code.lower()
        }
    return {"code": "Chưa khởi tạo", "confirmed": False, "timeout": False, "updated": False, "denied": False}

@main_routes.route("/progress")
def get_progress():
    session = grafana_session.session
    mfa_timeout = session.mfa_timeout if session else False
    mfa_code_text = session.mfa_code if session and session.mfa_code else ""
    mfa_denied = "người dùng từ chối" in mfa_code_text.lower()
    
    dynatrace_total = len(DYNATRACE_DASHBOARDS)
    dynatrace_completed = len([k for k in completed_captures if k.startswith("Dynatrace_")])

    return {
        "completed": len(completed_captures), "total": total_captures.value,
        "current": current_capturing.value, "mfa_timeout": mfa_timeout,
        "denied": mfa_denied, "dynatrace_completed": dynatrace_completed,
        "dynatrace_total": dynatrace_total
    }

@main_routes.route("/get_files")
def get_files():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    jpg_files = glob.glob(os.path.join(out_dir, "*.jpg"))
    filenames = sorted([os.path.basename(f) for f in jpg_files if os.path.getsize(f) > 0])
    return filenames

@main_routes.route("/download_zip")
def download_zip():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    jpg_files = glob.glob(os.path.join(out_dir, "*.jpg"))
    
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in jpg_files:
            if os.path.getsize(file_path) > 0:
                zip_file.write(file_path, os.path.basename(file_path))
    
    zip_buffer.seek(0)
    return Response(zip_buffer.getvalue(), mimetype='application/zip',
                    headers={'Content-Disposition': 'attachment; filename=screenshots.zip'})

@main_routes.route("/download/<filename>")
def download_file(filename):
    out_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(out_dir, filename)
    for _ in range(300):
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return send_file(file_path, as_attachment=True)
        time.sleep(1)
    return "File not ready yet, please try again", 404