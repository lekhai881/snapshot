// static/main.js
import { submitForm, checkMFACode, checkProgress, getFiles, downloadZip } from './api.js';
import {
    initServicesDropdown,
    setupInitialUI,
    setupCountdownTimer,
    togglePassword,
    autoAppendDomain,
    updateMFADisplay,
    updateProgressDisplay,
    showDownloadLinks
} from './ui.js';

// --- Quản lý trạng thái tập trung ---
const appState = {
    mfaTimedOut: false,
    mfaCountdown: 90,
    mfaInterval: null,
    currentMFACode: ''
};

// --- Các hàm xử lý logic chính ---
function handleLogin() {
    const userEl = document.getElementById('grafana_user');
    const passEl = document.getElementById('grafana_pass');
    const user = userEl.value;
    const pass = passEl.value;
    
    // Client-side validation
    if (!user || !pass) {
        alert('Vui lòng nhập username và password!');
        return;
    }
    if (user.includes(' ')) {
            alert('Username không có khoảng trắng!');
            return;
    }
    if (pass.length < 6 || pass.includes(' ')) {
        alert('Password phải có tối thiểu 6 ký tự và không có khoảng trắng!');
        return;
    }

    // Cập nhật UI
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('mainForm').style.display = 'block';
    document.getElementById('hidden_user').value = user;
    document.getElementById('hidden_pass').value = pass;
}

function startMFAProcess() {
    if (appState.mfaTimedOut) return;
    checkMFACode().then(data => {
        // ... (Logic xử lý data và cập nhật UI cho MFA) ...
        updateMFADisplay(data, appState.mfaCountdown);
        if (!data.confirmed && !data.timeout && !data.denied) {
            setTimeout(startMFAProcess, 2000);
        }
    });
}

function startProgressCheck() {
    checkProgress().then(data => {
        updateProgressDisplay(data);
        if (data.completed < data.total && !data.mfa_timeout) {
            setTimeout(startProgressCheck, 1000);
        } else {
            getFiles().then(files => {
                const downloadZipBtn = showDownloadLinks(files);
                if (downloadZipBtn) {
                    downloadZipBtn.addEventListener('click', downloadZip);
                }
            });
        }
    }).catch(error => {
        console.error('Progress check error:', error);
        setTimeout(startProgressCheck, 2000);
    });
}

// --- Khởi tạo ứng dụng khi trang đã tải xong ---
document.addEventListener('DOMContentLoaded', () => {
    // 1. Khởi tạo các thành phần UI
    initServicesDropdown();
    setupInitialUI();
    setupCountdownTimer();

    // 2. Tìm các phần tử trong HTML
    const loginBtn = document.getElementById('login_btn');
    const togglePassBtn = document.querySelector('.toggle-password');
    const userInput = document.getElementById('grafana_user');
    const passInput = document.getElementById('grafana_pass');
    const mainForm = document.getElementById('mainForm');

    // 3. Gán sự kiện cho các phần tử
    if (loginBtn) {
        loginBtn.addEventListener('click', handleLogin);
    }
    if (togglePassBtn) {
        togglePassBtn.addEventListener('click', togglePassword);
    }
    if (userInput) {
        userInput.addEventListener('input', () => autoAppendDomain(userInput));
        userInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') handleLogin();
        });
    }
    if (passInput) {
        passInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') handleLogin();
        });
    }
    if (mainForm) {
        mainForm.addEventListener('submit', (event) => {
            event.preventDefault(); // Ngăn form submit theo cách truyền thống

            // --- Logic xử lý khi submit form ---
            const statusMsg = document.getElementById('status_msg');
            const startTimeValue = mainForm.elements['start'].value.trim();
            const endTimeValue = mainForm.elements['end'].value.trim();
            if (!startTimeValue || !endTimeValue) {
                statusMsg.textContent = 'Lỗi: Vui lòng nhập cả thời gian bắt đầu và kết thúc.';
                statusMsg.style.color = 'red';
                return;
            }
            const startDate = new Date(startTimeValue);
            const endDate = new Date(endTimeValue);

            if (endDate <= startDate) {
                statusMsg.textContent = '❌ Lỗi: Thời gian kết thúc phải lớn hơn thời gian bắt đầu.';
                statusMsg.style.color = 'red';
                return;
            }
            statusMsg.textContent = "";
            statusMsg.style.color = 'green';
            
            // Cập nhật UI
            document.getElementById("capture_btn").style.display = "none";
            statusMsg.innerText = "⏳ Screenshot đang được tạo, vui lòng đợi...";
            document.getElementById("progress_section").style.display = "block";
            document.getElementById("mfa_display").innerHTML = "";

            // Gửi form và bắt đầu polling
            submitForm(mainForm).then(() => {
                const servicesValue = document.getElementById('services-input').value.trim();
                if (servicesValue) {
                    startMFAProcess();
                }
                startProgressCheck();
            }).catch(error => {
                console.error('Lỗi khi gửi form:', error);
                alert('Có lỗi xảy ra khi gửi yêu cầu!');
                document.getElementById("capture_btn").style.display = "block";
            });
        });
    }
});