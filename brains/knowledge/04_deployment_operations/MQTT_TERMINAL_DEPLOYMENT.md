# MQTT Terminal 部署檢查清單

> **最後更新**: 2026-08-16  
> **適用頁面**: https://mqtt.tg25.win/  
> **VPS**: infra (141.148.165.50:39022)

---

## ✅ 部署前檢查

### 1. 本地檔案確認
```bash
# 確認源檔案存在
ls -lh /Users/ilawusong/Documents/WaW/PROJECT/Infra/mqtt/scripts/mqtt-terminal.html

# 確認 Nginx 配置存在
ls -lh /Users/ilawusong/Documents/WaW/PROJECT/Infra/mqtt/config/nginx-mqtt.conf
```

### 2. SSH 連線測試
```bash
# 測試 SSH 連線
ssh infra "echo 'SSH 連線正常'"
```

---

## 🚀 完整部署流程

### 步驟 1: 創建目錄（首次部署）
```bash
ssh infra "sudo mkdir -p /var/www/mqtt && sudo chown www-data:www-data /var/www/mqtt"
```

### 步驟 2: 上傳 HTML 檔案
```bash
scp /Users/ilawusong/Documents/WaW/PROJECT/Infra/mqtt/scripts/mqtt-terminal.html \
    infra:/tmp/mqtt-terminal.html

ssh infra "sudo mv /tmp/mqtt-terminal.html /var/www/mqtt/index.html && \
           sudo chown www-data:www-data /var/www/mqtt/index.html && \
           sudo chmod 644 /var/www/mqtt/index.html"
```

### 步驟 3: 部署 Nginx 配置（首次部署）
```bash
scp /Users/ilawusong/Documents/WaW/PROJECT/Infra/mqtt/config/nginx-mqtt.conf \
    infra:/tmp/mqtt.tg25.win.conf

ssh infra "sudo mv /tmp/mqtt.tg25.win.conf /etc/nginx/sites-available/mqtt.tg25.win && \
           sudo ln -sf /etc/nginx/sites-available/mqtt.tg25.win /etc/nginx/sites-enabled/mqtt.tg25.win"
```

### 步驟 4: 測試 Nginx 配置
```bash
ssh infra "sudo nginx -t"
```

### 步驟 5: 重載 Nginx
```bash
ssh infra "sudo systemctl reload nginx"
```

---

## 🔍 部署後驗證

### 1. 檢查檔案部署
```bash
ssh infra "ls -lah /var/www/mqtt/"
# 預期輸出: index.html (33KB 左右)
```

### 2. 檢查 Nginx 配置
```bash
ssh infra "ls -la /etc/nginx/sites-enabled/ | grep mqtt"
# 預期輸出: mqtt.tg25.win -> ../sites-available/mqtt.tg25.win
```

### 3. 測試本地訪問
```bash
ssh infra "curl -I http://localhost/ -H 'Host: mqtt.tg25.win'"
# 預期輸出: HTTP/1.1 301 Moved Permanently (重定向到 HTTPS)
```

### 4. 測試 HTTPS 訪問
```bash
ssh infra "curl -Ik https://localhost/ -H 'Host: mqtt.tg25.win'"
# 預期輸出: HTTP/2 200
```

### 5. 測試 WebSocket 端點
```bash
ssh infra "curl -I http://localhost:9001/"
# 預期輸出: 檢查 Mosquitto WebSocket 是否運行
```

### 6. 從瀏覽器訪問
開啟瀏覽器訪問: **https://mqtt.tg25.win/**

預期看到:
- ✅ 黑底綠字的終端風格介面
- ✅ 頂部顯示 "mqtt-terminal — tg25 Engineering Mode"
- ✅ 連線設定面板 (Broker, User, Password)
- ✅ 設備狀態側邊欄

---

## 🔄 更新流程（日常更新）

### 快速更新 HTML
```bash
# 一行命令完成更新
scp /Users/ilawusong/Documents/WaW/PROJECT/Infra/mqtt/scripts/mqtt-terminal.html \
    infra:/tmp/mqtt-terminal.html && \
ssh infra "sudo mv /tmp/mqtt-terminal.html /var/www/mqtt/index.html && \
           sudo chown www-data:www-data /var/www/mqtt/index.html"
```

### 更新 Nginx 配置
```bash
scp /Users/ilawusong/Documents/WaW/PROJECT/Infra/mqtt/config/nginx-mqtt.conf \
    infra:/tmp/mqtt.tg25.win.conf && \
ssh infra "sudo mv /tmp/mqtt.tg25.win.conf /etc/nginx/sites-available/mqtt.tg25.win && \
           sudo nginx -t && \
           sudo systemctl reload nginx"
```

---

## 🐛 故障排查

### 問題 1: 頁面無法訪問 (502/504)
```bash
# 檢查 Nginx 狀態
ssh infra "sudo systemctl status nginx"

# 檢查 Nginx 錯誤日誌
ssh infra "sudo tail -50 /var/log/nginx/error.log"

# 檢查 SSL 證書
ssh infra "sudo certbot certificates | grep mqtt.tg25.win"
```

### 問題 2: WebSocket 無法連線
```bash
# 檢查 Mosquitto 狀態
ssh infra "sudo systemctl status mosquitto"

# 檢查 Mosquitto WebSocket 監聽
ssh infra "sudo ss -tlnp | grep 9001"

# 檢查 Mosquitto 日誌
ssh infra "sudo journalctl -u mosquitto -n 50"
```

### 問題 3: 頁面顯示空白
```bash
# 檢查檔案完整性
ssh infra "wc -l /var/www/mqtt/index.html"
# 預期: 約 1000 行以上

# 檢查檔案權限
ssh infra "ls -la /var/www/mqtt/index.html"
# 預期: -rw-r--r-- www-data www-data

# 檢查 Nginx access log
ssh infra "sudo tail -20 /var/log/nginx/mqtt.tg25.win.access.log"
```

---

## 📝 重要配置參數

### MQTT 連線資訊 (內嵌在 HTML 中)
```javascript
Broker:   wss://mqtt.tg25.win/mqtt-ws/
User:     backend_user
Password: backend_mqtt_2024
Subscribe: device/#
```

### Nginx 端點映射
| 前端 URL | 後端服務 | 說明 |
|---------|---------|------|
| `/` | `/var/www/mqtt/` | MQTT Terminal 頁面 |
| `/mqtt-ws/` | `http://127.0.0.1:9001/` | Mosquitto WebSocket |
| `/api/` | `http://127.0.0.1:8080` | Credit API |
| `/line-api/` | `http://127.0.0.1:8083/api/` | Line API |

---

## 📚 相關文檔

- `DATA_MONITORING_DASHBOARDS.md` — 所有監控頁面總覽
- `INFRASTRUCTURE_REFERENCE.md` — VPS SSH 連線資訊
- `DEPLOYMENT_GUIDE.md` — 通用部署指南

---

## 📅 部署歷史

| 日期 | 操作 | 執行者 | 備註 |
|------|------|--------|------|
| 2026-08-16 | 創建部署檢查清單 | HQ | 初始版本 |


