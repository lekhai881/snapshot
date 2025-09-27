# config.py

# Cấu hình cache
ENABLE_CACHE = True

# Cấu hình Grafana
GRAFANA_CONFIG = {
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

# Cấu hình các dashboard của Dynatrace
DYNATRACE_DASHBOARDS = [
    {"key": "Dynatrace_T24", "filename": "dashboard_T24.jpg",
     "url_template": "https://dynatracetest.techcombank.com.vn/e/8016500b-51f5-42fe-8ade-89b9b59bb26c/#dashboard;gtf={start_t24}%20to%20{end_t24};gf=all;id=3c90dc59-ec07-4f9c-814e-541a5f63d1e9",
     "width": 2800, "height": 4900},
    {"key": "Dynatrace_ESB", "filename": "dashboard_ESB.jpg",
     "url_template": "https://dynatracetest.techcombank.com.vn/e/8016500b-51f5-42fe-8ade-89b9b59bb26c/ui/entity/HOST-0CC233A090E87228?gtf={start_node}%20to%20{end_node}&gf=-815432565033324387",
     "width": 2600, "height": 1800},
    {"key": "Dynatrace_Node1", "filename": "dashboard_APIGW_Node1.jpg",
     "url_template": "https://dynatracetest.techcombank.com.vn/e/8016500b-51f5-42fe-8ade-89b9b59bb26c/ui/entity/HOST-4725B65FC5E6984C?gtf={start_node}%20to%20{end_node}&gf=all",
     "width": 2600, "height": 1800},
    {"key": "Dynatrace_Node2", "filename": "dashboard_APIGW_Node2.jpg",
     "url_template": "https://dynatracetest.techcombank.com.vn/e/8016500b-51f5-42fe-8ade-89b9b59bb26c/ui/entity/HOST-DD969D733CE5DFEB?gtf={start_node}%20to%20{end_node}&gf=all",
     "width": 2600, "height": 1800},
    {"key": "Dynatrace_RDS_ROC", "filename": "RDS(DB)_ROC.jpg",
     "url_template": "https://dynatracetest.techcombank.com.vn/e/8016500b-51f5-42fe-8ade-89b9b59bb26c/#dashboard;gtf={start_t24}%20to%20{end_t24};gf=all;id=8c5975ff-7a23-4e7e-974c-c688983dbfc0",
     "width": 2600, "height": 1800},
    {"key": "Dynatrace_Dashboard_ROC", "filename": "Dashboard_ROC.jpg",
     "url_template": "https://dynatracetest.techcombank.com.vn/e/8016500b-51f5-42fe-8ade-89b9b59bb26c/#dashboard;gtf={start_t24}%20to%20{end_t24};gf=-7151761915816887563;id=21676786-9e66-4479-84d8-d438b4728f07",
     "width": 2600, "height": 1800},
    {"key": "Dynatrace_Main_Functions_ROC", "filename": "Main_Functions_ROC.jpg",
     "url_template": "https://dynatracetest.techcombank.com.vn/e/8016500b-51f5-42fe-8ade-89b9b59bb26c/#dashboard;gtf={start_t24}%20to%20{end_t24};gf=all;id=ae4e88fe-de6b-486a-b29e-11030dab8a0a",
     "width": 2600, "height": 1800}
]