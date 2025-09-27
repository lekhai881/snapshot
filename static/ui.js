// static/ui.js
import { services, emailDomain } from './config.js';

// Biến trạng thái riêng của UI (quản lý các service đã chọn)
let selectedServices = [];

/**
 * Hiển thị hoặc ẩn mật khẩu trong ô input.
 */
export function togglePassword() {
    const passField = document.getElementById('grafana_pass');
    const toggleIcon = document.querySelector('.toggle-password');
    if (passField.type === 'password') {
        passField.type = 'text';
        toggleIcon.textContent = '🙈';
    } else {
        passField.type = 'password';
        toggleIcon.textContent = '👁️';
    }
}

/**
 * Tự động thêm tên miền vào ô username.
 * @param {HTMLInputElement} el - Ô input username.
 */
export function autoAppendDomain(el) {
    let val = el.value;
    if (!val || val === emailDomain) {
        el.value = "";
        return;
    }
    if (!val.endsWith(emailDomain)) {
        let username = val.split("@")[0].replace(/\s+/g, "");
        el.value = username + emailDomain;
        el.setSelectionRange(username.length, username.length);
    }
}

/**
 * Khởi tạo và xử lý logic cho dropdown chọn services có tìm kiếm.
 */
export function initServicesDropdown() {
    const input = document.getElementById('services-input');
    const dropdown = document.getElementById('services-dropdown');
    const searchInput = document.getElementById('search-input');
    const servicesList = document.getElementById('services-list');

    // Nếu có giá trị sẵn, parse nó
    if (input && input.value) {
        selectedServices = input.value.split(',').map(s => s.trim()).filter(s => s);
    }
    
    function renderServices(filter = '') {
        if (!servicesList) return;
        servicesList.innerHTML = '';
        services.filter(s => s.toLowerCase().includes(filter.toLowerCase())).forEach(service => {
            const div = document.createElement('div');
            div.style.cssText = 'padding:8px; cursor:pointer; border-bottom:1px solid #eee;';
            div.innerHTML = `<input type="checkbox" ${selectedServices.includes(service) ? 'checked' : ''} style="margin-right:8px;">${service}`;
            
            // Xử lý sự kiện click trên div thay vì checkbox để có vùng click lớn hơn
            div.onclick = (e) => {
                e.stopPropagation(); // Ngăn sự kiện click vào input lan ra ngoài
                const checkbox = div.querySelector('input');
                
                // Đảo ngược trạng thái checkbox nếu click không phải vào chính nó
                if (e.target.tagName !== 'INPUT') {
                    checkbox.checked = !checkbox.checked;
                }

                if (checkbox.checked) {
                    if (!selectedServices.includes(service)) selectedServices.push(service);
                } else {
                    selectedServices = selectedServices.filter(s => s !== service);
                }
                input.value = selectedServices.join(',');
            };
            servicesList.appendChild(div);
        });
    }

    if (input) {
        input.onclick = () => {
            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
            if (dropdown.style.display === 'block') {
                renderServices();
                searchInput.focus();
            }
        };
    }
    
    if (searchInput) {
        searchInput.oninput = (e) => renderServices(e.target.value);
    }
    
    // Đóng dropdown khi click ra ngoài
    document.onclick = (e) => {
        if (dropdown && !e.target.closest('.multiselect-container')) {
            dropdown.style.display = 'none';
        }
    };
}


/**
 * Cập nhật thanh tiến trình.
 * @param {object} data - Dữ liệu tiến trình từ server.
 */
export function updateProgressDisplay(data) {
    const progress = data.total > 0 ? (data.completed / data.total) * 100 : 0;
    document.getElementById('progress-bar').style.width = progress + '%';
    document.getElementById('progress-bar').innerText = `${data.completed}/${data.total} ảnh`;

    let currentText = data.current || 'Đang khởi tạo...';
    // ... (logic xử lý chuỗi text của bạn) ...
    document.getElementById('current-capture').innerText = currentText;

    if (data.mfa_timeout && data.dynatrace_completed >= data.dynatrace_total) {
        document.getElementById('current-capture').innerText = '❌ Hoàn thành với lỗi MFA';
        document.getElementById('status_msg').innerHTML = '❌ Hoàn thành nhưng thiếu ảnh Grafana do lỗi xác thực!';
    }
}

/**
 * Hiển thị các trạng thái của MFA.
 * @param {object} data - Dữ liệu MFA từ server.
 * @param {number} mfaCountdown - Số giây còn lại.
 */
export function updateMFADisplay(data, mfaCountdown) {
    const mfaDisplay = document.getElementById("mfa_display");
    if (!mfaDisplay) return;

    if (data.timeout || data.denied) {
        let bgColor = data.denied ? '#fff3cd' : '#f8d7da';
        let textColor = data.denied ? '#856404' : '#721c24';
        let icon = data.denied ? '⚠️' : '❌';
        let message = data.denied ? 'Mã xác thực đã nhập sai!' : data.code;
        mfaDisplay.innerHTML = `<div class="mfa-code" style="background:${bgColor};color:${textColor};">${icon} ${message}</div>`;
        return;
    }
    
    if (data.confirmed) {
        mfaDisplay.innerHTML = `<div class="mfa-code" style="background:#d4edda;color:#155724;">✅ Đã xác thực MFA thành công!</div>`;
        return;
    }

    if (data.code && /^\d{2,3}$/.test(data.code)) {
        let displayText = `🔐 Mã xác thực MFA: ${data.code}`;
        if (mfaCountdown < 90) {
            displayText += ` <span style="color:#666; font-size:14px;">(${mfaCountdown}s)</span>`;
        }
        mfaDisplay.innerHTML = `<div class="mfa-code">${displayText}</div>`;
    }
}

/**
 * Hiển thị danh sách các file đã được chụp xong.
 * @param {string[]} files - Mảng chứa tên các file.
 * @returns {HTMLButtonElement} - Trả về nút "Download All" để file main.js có thể gán sự kiện.
 */
export function showDownloadLinks(files) {
    document.getElementById('current-capture').innerText = '✅ Hoàn thành tất cả!';
    document.getElementById('status_msg').innerHTML = '✅ Hoàn thành! Các file đã sẵn sàng tải xuống:';

    let downloadHtml = `<div style="margin-top:20px;"><h3>Tải xuống các file:</h3>`;
    // Chỉ tạo nút, không gán sự kiện onclick ở đây
    downloadHtml += `<button id="download_zip_btn" style="background:#28a745; color:white; border:none; padding:10px 20px; margin:10px 0; border-radius:5px; cursor:pointer;">🗆 Tải tất cả (ZIP)</button><br>`;
    
    files.forEach(file => {
        downloadHtml += `<div style="margin:5px 0;"><a href="/download/${file}" download style="color:#007bff; text-decoration:none;">📁 ${file}</a></div>`;
    });
    downloadHtml += '</div>';

    // Thêm vào cuối khu vực progress thay vì ghi đè
    document.getElementById('progress_section').insertAdjacentHTML('beforeend', downloadHtml);
    
    // Trả về nút để main.js có thể tìm và gán sự kiện
    return document.getElementById('download_zip_btn');
}


/**
 * Cài đặt đồng hồ đếm ngược tự động tắt.
 */
export function setupCountdownTimer() {
    const counterEl = document.getElementById("counter");
    if (!counterEl) return;
    
    let countdown = parseInt(counterEl.getAttribute("data-timeout")) || 3600;

    const formatTime = (seconds) => {
        let m = Math.floor(seconds / 60);
        let s = seconds % 60;
        return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    };

    const interval = setInterval(() => {
        counterEl.innerText = formatTime(countdown);
        countdown--;
        if (countdown < 0) {
            clearInterval(interval);
            window.close();
        }
    }, 1000);
}

/**
 * Thiết lập trạng thái ban đầu của UI khi tải trang.
 */
export function setupInitialUI() {
    const userField = document.getElementById('grafana_user');
    const passField = document.getElementById('grafana_pass');
    
    if (userField && passField && userField.value && passField.value) {
        document.getElementById('loginSection').style.display = 'none';
        document.getElementById('mainForm').style.display = 'block';
        document.getElementById('hidden_user').value = userField.value;
        document.getElementById('hidden_pass').value = passField.value;
    }
}