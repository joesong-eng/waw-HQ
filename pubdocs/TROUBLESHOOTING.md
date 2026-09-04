# 常見問題排解

> **適用對象**：所有 Agent  
> **最後更新**：2026-08-16  
> **版本**：v1.0

---

## 🔌 MQTT 連線問題

### 問題：設備無法連線到 MQTT
**症狀**：設備顯示 "MQTT connection failed"

**檢查步驟**：
1. 確認 MQTT broker 正常運作
   ```bash
   # 在 Infra 伺服器上
   systemctl status mosquitto
   ```

2. 檢查設備的 WiFi 連線
   ```bash
   # ESP32 序列埠輸出
   WiFi connected: true
   IP address: 192.168.1.x
   ```

3. 驗證 MQTT 認證資訊
   - username 是否正確（通常是 device_id）
   - password 是否正確
   - ACL 權限是否設定

4. 測試 MQTT 連線
   ```bash
   mosquitto_sub -h mqtt.example.com -p 1883 \
     -u KIOSK001 -P password \
     -t "v9/kiosk/KIOSK001/status"
   ```

**常見原因**：
- ❌ WiFi 訊號弱或不穩定
- ❌ MQTT broker 服務停止
- ❌ 防火牆阻擋 1883 port
- ❌ 認證資訊錯誤

---

## 🗄️ 資料庫連線問題

### 問題：API 回應 "Connection refused"
**症狀**：API 無法連接資料庫

**檢查步驟**：
1. 確認 SSH tunnel 正常
   ```bash
   ps aux | grep "ssh.*3308:127.0.0.1:3306"
   ```

2. 測試本地連線
   ```bash
   mysql -h 127.0.0.1 -P 3308 -u root -p
   ```

3. 檢查 Laravel .env 設定
   ```env
   DB_HOST=127.0.0.1
   DB_PORT=3308
   DB_DATABASE=iotv9
   DB_USERNAME=root
   DB_PASSWORD=***
   ```

4. 清除 Laravel 快取
   ```bash
   php artisan config:clear
   php artisan cache:clear
   ```

**常見原因**：
- ❌ SSH tunnel 斷線
- ❌ 資料庫伺服器停止
- ❌ 連線數超過限制
- ❌ .env 設定錯誤

---

## 📱 前端無法載入資料

### 問題：Vue 頁面顯示空白或錯誤
**症狀**：畫面無資料或 Console 顯示錯誤

**檢查步驟**：
1. 開啟瀏覽器 DevTools (F12)
2. 查看 Console 錯誤訊息
3. 查看 Network tab 的 API 請求
   - 狀態碼是否為 200？
   - 回應格式是否正確？

4. 檢查 API 基礎路徑
   ```javascript
   // nuxt.config.js 或 .env
   API_BASE_URL=http://localhost:8000
   ```

5. 檢查 CORS 設定
   ```php
   // Laravel config/cors.php
   'allowed_origins' => ['http://localhost:3000'],
   ```

**常見原因**：
- ❌ API 未啟動
- ❌ CORS 阻擋請求
- ❌ Token 過期或無效
- ❌ API 回應格式錯誤

---

## 🔐 認證與權限問題

### 問題：API 回應 401 Unauthorized
**症狀**：已登入但 API 請求失敗

**檢查步驟**：
1. 確認 Token 是否正確
   ```javascript
   console.log(localStorage.getItem('auth_token'));
   ```

2. 檢查 Token 是否過期
   ```bash
   # Laravel
   php artisan tinker
   >>> $user = User::find(1);
   >>> $user->tokens;
   ```

3. 確認 Authorization header
   ```javascript
   axios.defaults.headers.common['Authorization'] = 
     'Bearer ' + token;
   ```

**解決方式**：
- 重新登入取得新 Token
- 檢查 Token 儲存位置
- 確認 API middleware 設定

---

## 🔄 設備狀態不同步

### 問題：後台顯示的設備狀態與實際不符
**症狀**：設備明明在線但顯示離線

**檢查步驟**：
1. 檢查設備最後上線時間
   ```sql
   SELECT device_id, last_seen_at, online 
   FROM devices 
   WHERE device_id = 'KIOSK001';
   ```

2. 確認 MQTT 狀態訊息
   ```bash
   mosquitto_sub -h mqtt.example.com \
     -t "v9/kiosk/+/status" -v
   ```

3. 檢查 Redis 快取
   ```bash
   redis-cli
   > GET device:KIOSK001:status
   ```

4. 檢查 WebSocket 連線（如有使用）
   ```bash
   # Laravel
   php artisan websockets:serve
   ```

**常見原因**：
- ❌ MQTT listener 服務停止
- ❌ 設備未定期發送心跳
- ❌ Redis 快取過期
- ❌ WebSocket 連線斷開

---

## 📦 部署後無法啟動

### 問題：git pull 後服務無法啟動
**症狀**：500 錯誤或 "Class not found"

**標準檢查流程**：
```bash
# 1. 更新 Composer 依賴
composer install --no-dev

# 2. 清除所有快取
php artisan config:clear
php artisan cache:clear
php artisan route:clear
php artisan view:clear

# 3. 重新快取（production）
php artisan config:cache
php artisan route:cache
php artisan view:cache

# 4. 執行資料庫遷移（如有）
php artisan migrate --force

# 5. 重啟服務
sudo systemctl restart php8.2-fpm
sudo systemctl restart nginx
```

---

## 🔧 ESP32 韌體問題

### 問題：設備重複重啟 (Boot Loop)
**症狀**：設備不斷重啟，無法正常運作

**檢查步驟**：
1. 透過序列埠查看錯誤訊息
   ```bash
   # PlatformIO
   pio device monitor
   ```

2. 常見錯誤原因：
   - ❌ Watchdog timeout（程式卡住）
   - ❌ Stack overflow（記憶體不足）
   - ❌ 硬體故障（電源不穩）

3. 檢查記憶體使用
   ```cpp
   Serial.printf("Free heap: %d\n", ESP.getFreeHeap());
   ```

**解決方式**：
- 增加 Watchdog timeout
- 減少記憶體使用（縮小 buffer）
- 檢查電源供應
- 恢復出廠韌體測試

---

## 🚨 緊急處理流程

### 生產環境出現重大問題

**立即行動**：
1. 📢 通知 HQ 和相關 Agent
2. 🔍 確認影響範圍（多少用戶、多少設備）
3. 📝 記錄錯誤訊息和時間點
4. 🔄 是否可以快速 rollback？

**收集資訊**：
```bash
# Laravel 日誌
tail -f storage/logs/laravel.log

# Nginx 日誌
tail -f /var/log/nginx/error.log

# 系統日誌
journalctl -u php8.2-fpm -f

# 資料庫慢查詢
tail -f /var/log/mysql/slow-query.log
```

**回報格式**：
```markdown
## 緊急問題回報

**發生時間**：2026-08-16 15:30 (台北時間)
**影響範圍**：所有 Owner 後台用戶
**症狀**：無法登入，顯示 500 錯誤
**初步判斷**：資料庫連線失敗
**已執行動作**：重啟 SSH tunnel
**當前狀態**：問題持續中 / 已恢復
```

---

## 📞 聯絡資訊

**各 Agent 負責範圍**：
- **Ina (Infra)**：MQTT, 資料庫, 伺服器
- **Sophie (Owner)**：營運商後台 API
- **Mina (Member)**：玩家前端
- **Hubie (iHub)**：Android APK
- **Fio (Kiosk)**：兌幣卡韌體
- **Coli (Game)**：遊戲採集卡韌體

**回報問題時請提供**：
1. 錯誤訊息截圖
2. 相關日誌片段
3. 發生時間
4. 重現步驟（如可重現）

---

## 📚 延伸閱讀

詳細的技術文檔請參考：
- **系統架構**: `brains/knowledge/03_system_architecture/`
- **部署操作**: `brains/knowledge/04_deployment_operations/`

---

**維護者**：HQ  
**建立日期**：2026-08-16

