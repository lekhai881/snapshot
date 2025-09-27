 function togglePassword() {
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
    
    function handleGrafanaLogin() {
        const user = document.getElementById('grafana_user').value;
        const pass = document.getElementById('grafana_pass').value;
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
        document.getElementById('loginSection').style.display = 'none';
        document.getElementById('mainForm').style.display = 'block';
        document.getElementById('hidden_user').value = user;
        document.getElementById('hidden_pass').value = pass;
    }
    
    function hideButtonAndSubmit(form) {
        // ===================================================================
        // BẮT ĐẦU PHẦN MÃ VALIDATE THỜI GIAN ĐƯỢC THÊM VÀO
        // ===================================================================
        const startTimeValue = form.elements['start'].value.trim();
        const endTimeValue = form.elements['end'].value.trim();
        const statusMsg = document.getElementById('status_msg');

        // Chuyển đổi chuỗi thời gian thành đối tượng Date để so sánh
        const startDate = new Date(startTimeValue);
        const endDate = new Date(endTimeValue);

        // Thực hiện so sánh
        if (endDate <= startDate) {
            // Nếu thời gian kết thúc nhỏ hơn hoặc bằng thời gian bắt đầu -> báo lỗi
            statusMsg.innerText = '❌ Lỗi: Thời gian kết thúc phải lớn hơn thời gian bắt đầu.';
            statusMsg.style.color = 'red';
            return false; // Ngăn không cho form được gửi đi
        }
        // Nếu thời gian hợp lệ, xóa thông báo lỗi (nếu có)
        statusMsg.innerText = "";
        statusMsg.style.color = 'green';
        // ===================================================================
        // KẾT THÚC PHẦN MÃ VALIDATE
        // ===================================================================


        // Mã gốc của bạn tiếp tục từ đây
        const user = document.getElementById('hidden_user').value;
        const pass = document.getElementById('hidden_pass').value;
        if (!user || !pass) {
            alert('Vui lòng đăng nhập Grafana trước!');
            return false;
        }
        
        // Submit form using fetch to avoid page reload
        const formData = new FormData(form);
        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(() => {
            document.getElementById("capture_btn").style.display = "none";
            document.getElementById("status_msg").innerText = "⏳ Screenshot đang được tạo, vui lòng đợi...";
            document.getElementById("progress_section").style.display = "block";
            // Clear MFA display khi bắt đầu capture mới
            document.getElementById("mfa_display").innerHTML = "";
            mfaTimedOut = false;
            if(mfaInterval) clearInterval(mfaInterval);
            mfaInterval = null;
            // Chỉ gọi checkMFACode nếu có services
            const servicesValue = document.getElementById('services-input').value.trim();
            if (servicesValue) {
                checkMFACode();
            }
            checkProgress();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Lỗi khi gửi yêu cầu!');
        });
        
        return false; // Prevent normal form submission
    }
    let mfaTimedOut = false;
    let mfaCountdown = 90;
    let mfaInterval = null;
    
    function startMFACountdown() {
        if(mfaInterval) clearInterval(mfaInterval);
        mfaCountdown = 90;
        mfaInterval = setInterval(() => {
            mfaCountdown--;
            // Cập nhật hiển thị ngay lập tức
            updateMFADisplay();
            if(mfaCountdown <= 0) {
                clearInterval(mfaInterval);
                mfaTimedOut = true;
                document.getElementById("mfa_display").innerHTML = 
                    '<div class="mfa-code" style="background:#f8d7da;color:#721c24;">❌ Hết thời gian xác thực MFA!</div>';
                return;
            }
        }, 1000);
    }
    
    let currentMFACode = '';
    function updateMFADisplay() {
        if(currentMFACode && /^\d{2,3}$/.test(currentMFACode)) {
            let displayText = '🔐 Mã xác thực MFA: ' + currentMFACode;
            if(mfaCountdown < 90) {
                displayText += ' <span style="color:#666; font-size:14px;">(' + mfaCountdown + 's)</span>';
            }
            document.getElementById("mfa_display").innerHTML = 
                '<div class="mfa-code">' + displayText + '</div>';
        }
    }
    
    function checkMFACode() {
        if(mfaTimedOut) return; // Stop if already timed out
        
        // Kiểm tra nếu không có services thì không hiển thị MFA
        const servicesValue = document.getElementById('services-input').value.trim();
        if (!servicesValue) {
            return;
        }
        
        fetch('/mfa_code')
        .then(response => response.json())
        .then(data => {
            if(data.timeout || data.denied) {
                if(mfaInterval) clearInterval(mfaInterval);
                let bgColor = data.denied ? '#fff3cd' : '#f8d7da';
                let textColor = data.denied ? '#856404' : '#721c24';
                let icon = data.denied ? '⚠️' : '❌';
                let message = data.denied ? 'Mã xác thực đã nhập sai!' : data.code;
                document.getElementById("mfa_display").innerHTML = 
                    '<div class="mfa-code" style="background:' + bgColor + ';color:' + textColor + ';">' + icon + ' ' + message + '</div>';
                // Không set mfaTimedOut = true để tiếp tục check progress
                return;
            }
            if(data.confirmed) {
                if(mfaInterval) clearInterval(mfaInterval);
                document.getElementById("mfa_display").innerHTML = 
                    '<div class="mfa-code" style="background:#d4edda;color:#155724;">✅ Đã xác thực MFA thành công!</div>';
            } else if(!mfaTimedOut) {
                // Chỉ bắt đầu countdown khi có mã mới lần đầu
                if(data.updated && data.code && /^\d{2,3}$/.test(data.code) && !mfaInterval) {
                    startMFACountdown();
                }
                // Nếu có mã và chưa có countdown, bắt đầu countdown
                else if(data.code && data.code !== '🔐 Mã xác thực MFA: ' && /^\d{2,3}$/.test(data.code) && !mfaInterval) {
                    startMFACountdown();
                }
                
                currentMFACode = data.code;
                updateMFADisplay();
                
                // Check if countdown reached 0
                if(mfaCountdown <= 0) {
                    mfaTimedOut = true;
                    return;
                }
                
                setTimeout(checkMFACode, 2000);
            }
        })
        .catch(error => {
            if(!mfaTimedOut) {
                setTimeout(checkMFACode, 2000);
            }
        });
    }
    
    function checkProgress() {
        // Không dừng polling khi MFA timeout để tiếp tục theo dõi progress
        
        fetch('/progress')
        .then(response => {
            if (!response.ok) throw new Error('Network error');
            return response.json();
        })
        .then(data => {
            console.log('Progress data:', data);
            const progress = data.total > 0 ? (data.completed / data.total) * 100 : 0;
            document.getElementById('progress-bar').style.width = progress + '%';
            document.getElementById('progress-bar').innerText = data.completed + '/' + data.total + ' ảnh';
            
            let currentText;
            // Force "Đang khởi tạo..." when no progress yet
            if(data.completed === 0) {
                currentText = 'Đang khởi tạo...';
            } else {
                currentText = data.current || 'Đang khởi tạo...';
                if(currentText.startsWith('Đã chụp ảnh Dynatrace_')) {
                    currentText = currentText.replace('Đã chụp ảnh Dynatrace_', 'Đã chụp ảnh ');
                } else if(currentText.startsWith('Dynatrace_')) {
                    currentText = currentText.replace('Dynatrace_', '');
                }
                if(currentText.startsWith('Đã chụp ảnh Grafana_')) {
                    currentText = currentText.replace('Đã chụp ảnh Grafana_', 'Đã chụp ảnh Grafana: ');
                } else if(currentText.startsWith('Grafana_')) {
                    currentText = currentText.replace('Grafana_', 'Đã chụp ảnh Grafana: ');
                }
            }
            document.getElementById('current-capture').innerText = currentText;
            
            // Check if MFA timed out from server
            if(data.mfa_timeout) {
                mfaTimedOut = true;
                if(mfaInterval) clearInterval(mfaInterval);
                let message = data.denied ? '❌ Mã xác thực nhập sai!' : '❌ Hết thời gian xác thực MFA!';
                document.getElementById("mfa_display").innerHTML = 
                    '<div class="mfa-code" style="background:#f8d7da;color:#721c24;">' + message + '</div>';
                // Tiếp tục kiểm tra progress để đợi các Dynatrace hoàn thành
            }
            
            // Kiểm tra nếu MFA timeout và đã capture đủ Dynatrace
            if(data.mfa_timeout && data.dynatrace_completed >= data.dynatrace_total) {
                document.getElementById('current-capture').innerText = '❌ Hoàn thành với lỗi MFA';
                document.getElementById('status_msg').innerHTML = '❌ Hoàn thành nhưng thiếu ảnh Grafana do lỗi xác thực!';
                showDownloadList();
                return;
            }
            
            if(data.completed < data.total) {
                setTimeout(checkProgress, 1000);
            } else {
                document.getElementById('current-capture').innerText = '✅ Hoàn thành tất cả!';
                document.getElementById('status_msg').innerHTML = '✅ Hoàn thành! Các file đã sẵn sàng tải xuống:';
                showDownloadList();
            }
        })
        .catch(error => {
            console.error('Progress check error:', error);
            if(!mfaTimedOut) {
                setTimeout(checkProgress, 2000);
            }
        });
    }
    
    function showDownloadList() {
        fetch('/get_files')
        .then(response => response.json())
        .then(files => {
            let downloadHtml = '<div style="margin-top:20px;"><h3>Tải xuống các file:</h3>';
            downloadHtml += '<button onclick="downloadZip()" style="background:#28a745; color:white; border:none; padding:10px 20px; margin:10px 0; border-radius:5px; cursor:pointer;">🗆 Tải tất cả (ZIP)</button><br>';
            files.forEach(file => {
                downloadHtml += `<div style="margin:5px 0;"><a href="/download/${file}" download style="color:#007bff; text-decoration:none;">📁 ${file}</a></div>`;
            });
            downloadHtml += '</div>';
            document.getElementById('progress_section').innerHTML += downloadHtml;
        })
        .catch(error => console.error('Error getting files:', error));
    }
    
    function downloadZip() {
        const link = document.createElement('a');
        link.href = '/download_zip';
        link.download = 'screenshots.zip';
        link.click();
    }
    
    const services = [
        'rdb-transaction-integration-external-pull-service',
        'rdb-identity-confirmation',
        'rdb-identity-userinfo',
        'rdb-payment-dis', 
        'rdb-payment-order-service-extension',
        'rdb-transaction-manager-extension',
        'rdb-access-control-extension',
        'rdb-customer-support-dis',
        'rdb-edge',
        'rdb-retail-banking-web-app',
        'rdb-cards-presentation-service',
        'rdb-account-bundle',
        'rdb-foreign-currency-exchange-dis',
        'rdb-gift-card-service',
        'rdb-family-banking-dis',
        'rdb-iadvisory-service',
        'rdb-new-to-bank',
        'rdb-payment-order-external-outbound-service',
        'rdb-reward-loyalty-worker',
        'rdb-web-edge',
        'rdb-document-service',
        'rdb-overseas-transfer-dis',
        'rdb-vneid-integration-service',
        'rdb-message-center-dis',
        'rdb-batch-schedule-transfer-dis',
        'rdb-identity-devicemanagementservice',
        'rdb-investment-integration',
        'rdb-promotion-service',
        'rdb-token-converter-extension',
        'rdb-aml-integration-dis',
        'rdb-card-service-dis',
        'rdb-cxs-portal',
        'rdb-icap-dis',
        'rdb-merchant-dis',
        'rdb-esg-service-dis',
        'rdb-otp-service',
        'rdb-unsecured-lending-service',
        'rdb-action-service-extension',
        'rdb-cardless-withdrawal',
        'rdb-communications-service',
        'rdb-loyalty',
        'rdb-payment-order-external-inbound-service',
        'rdb-scheduler-service',
        'rdb-savings-goal-dis',
        'rdb-user-manager-extension',
        'ops-box-1',
        'rdb-identity-mobileauthentication',
        'rdb-lucky-account',
        'rdb-audit-auditservice',
        'rdb-int-edge',
        'rdb-push-integration-extension',
        'wiremock',
        'rdb-digital-branch-dis',
        'rdb-installment-service',
        'rdb-billing-service-extension',
        'rdb-approval-extension',
        'rdb-arrangement-manager-extension',
        'rdb-atm-service-dis',
        'rdb-billing-dis-service',
        'rdb-term-deposit-dis',
        'rdb-actions-actionsintegrationmock',
        'rdb-device-management-dis',
        'rdb-disbursement-service-dis',
        'rdb-employee-upload-service',
        'rdb-nfc-integration-dis',
        'rdb-unsecured-lending-action-service',
        'rdb-financial-assistance',
        'rdb-biometric-worker',
        'rdb-employee-integration',
        'rdb-iadvisory-web-app',
        'rdb-lounge-service-dis',
        'rdb-sync-dis',
        'rdb-lead-management-dis',
        'rdb-notifications-service-extension',
        'rdb-employee-web-app',
        'rdb-fido-service-dis',
        'rdb-forgot-password-web-app',
        'rdb-limit-service-extended',
        'rdb-notifications-service-dis',
        'rdb-unsecured-lending-worker',
        'rdb-banca-onboarding',
        'rdb-chat-agents-dis',
        'rdb-contact-manager-extended',
        'rdb-investment-trading-dis',
        'rdb-onboarding-worker',
        'rdb-ingestion-service',
        'rdb-user-background-dis',
        'rdb-backoffice-report-service',
        'rdb-event-bridge',
        'rdb-identity-fidoservice',
        'rdb-tcbpay-dis',
        'rdb-gi-policy',
        'rdb-user-manager-dis',
        'rdb-account-integration-service',
        'rdb-cxs-provisioning',
        'rdb-nudge-dis',
        'rdb-onboarding-service',
        'rdb-pdms-service-dis',
        'rdb-qms-service-dis',
        'rdb-registration-service',
        'rdb-tcbf-dis',
        'rdb-billing-external-outbound-service',
        'rdb-centralized-configuration',
        'rdb-identity-identityintegrationservice',
        'rdb-reward-loyalty-service',
        'rdb-device-supported-web',
        'rdb-backoffice-upload-service',
        'rdb-ebank-web-app',
        'rdb-ep-edge',
        'rdb-mock-service',
        'rdb-rewind-dis',
        'rdb-account-bundle-worker',
        'rdb-banca-service-dis',
        'rdb-cxs-contentservices',
        'rdb-payment-agents-dis',
        'rdb-pre-approval-card',
        'rdb-identity-extended'
    ];
    
    let selectedServices = [];
    
    function initServices() {
      const input = document.getElementById('services-input');
      const dropdown = document.getElementById('services-dropdown');
      const searchInput = document.getElementById('search-input');
      const servicesList = document.getElementById('services-list');
      
      // Parse existing services
      if (input.value) {
        selectedServices = input.value.split(',').map(s => s.trim()).filter(s => s);
      }
      
      function renderServices(filter = '') {
        servicesList.innerHTML = '';
        services.filter(s => s.toLowerCase().includes(filter.toLowerCase())).forEach(service => {
          const div = document.createElement('div');
          div.style.cssText = 'padding:8px; cursor:pointer; border-bottom:1px solid #eee;';
          div.innerHTML = `<input type="checkbox" ${selectedServices.includes(service) ? 'checked' : ''}> ${service}`;
          div.onclick = () => {
            const checkbox = div.querySelector('input');
            checkbox.checked = !checkbox.checked;
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
      
      input.onclick = () => {
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
        if (dropdown.style.display === 'block') {
          renderServices();
          searchInput.focus();
        }
      };
      
      searchInput.oninput = (e) => renderServices(e.target.value);
      
      document.onclick = (e) => {
        if (!e.target.closest('.multiselect-container')) {
          dropdown.style.display = 'none';
        }
      };
    }
    
    window.onload = function() {
      initServices();
      // Auto show form if already has login data
      if (document.getElementById('grafana_user').value && document.getElementById('grafana_pass').value) {
        document.getElementById('loginSection').style.display = 'none';
        document.getElementById('mainForm').style.display = 'block';
        document.getElementById('hidden_user').value = document.getElementById('grafana_user').value;
        document.getElementById('hidden_pass').value = document.getElementById('grafana_pass').value;
      }
    };
    
    window.addEventListener('DOMContentLoaded', () => {
        let counterEl = document.getElementById("counter");
        let countdown = parseInt(counterEl.getAttribute("data-timeout")) || 3600;

        function formatTime(seconds) {
            let m = Math.floor(seconds / 60);
            let s = seconds % 60;
            return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }

        let interval = setInterval(() => {
            counterEl.innerText = formatTime(countdown);
            countdown--;
            if (countdown < 0) {
                clearInterval(interval);
                // Chỉ đóng nếu tab mở bằng window.open()
                window.close();
            }
        }, 1000);
    });

    function autoAppendDomain(el) {
        const domain = "@techcombank.com.vn";
        let val = el.value;

        // Nếu xóa hết hoặc chỉ nhập domain thì clear
        if (!val || val === domain) {
            el.value = "";
            return;
        }

        // Nếu chưa có @ hoặc có @ nhưng không đúng domain thì thêm lại
        if (!val.endsWith(domain)) {
            let username = val.split("@")[0].replace(/\s+/g, ""); // chỉ lấy phần trước @
            el.value = username + domain;

            // Đặt con trỏ ngay trước phần domain
            el.setSelectionRange(username.length, username.length);
        }
    }