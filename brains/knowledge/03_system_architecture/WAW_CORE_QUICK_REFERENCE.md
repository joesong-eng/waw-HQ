
# WAW Core 快速參考卡

> 從 WAW_CORE_SYSTEM_ASSESSMENT.md 提取的關鍵資訊

---

## 🚀 快速啟動

### 本地開發
```bash
cd /Users/ilawusong/Documents/WaW/PROJECT/Owner
pnpm install
composer install
php artisan migrate
php artisan reverb:start
php artisan queue:work
```

### VPS 部署位置
- **Domain**: iot.tg25.win
- **VPS**: Infra (141.148.165.50:39022)
- **Web Root**: /var/www/iot.tg25.win
- **Database**: MySQL iotv9 (遠端)

---

## 🔌 API 快速索引

| **端點前綴** | **驗證方式** | **用途** |
|------------|------------|---------|
| `/api/v9/*` | Session + CSRF | 前端 AJAX |
| `/api/internal/*` | X-Internal-Key | Infra → Owner |
| `/api/v1/*` | Bearer Token | iHub 整合 |
| `/api/v9/line/*` | Webhook Secret | LINE Bot |

---

## 🔑 關鍵配置環境變數

```bash
# 必須在 VPS .env 確認的配置

# WebSocket
VITE_REVERB_APP_KEY=
VITE_REVERB_HOST=
VITE_REVERB_PORT=          # 預設 443 (wss) / 80 (ws)
VITE_REVERB_SCHEME=        # 預設 https/wss

# MQTT (透過 Infra 中繼，Owner 不直連)
MQTT_HOST=mqtt.tg25.win
MQTT_PORT=8883             # TLS
MQTT_USERNAME=backend_user
MQTT_PASSWORD=

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=

# Database
DB_HOST=
DB_PORT=3306
DB_DATABASE=iotv9
DB_USERNAME=
DB_PASSWORD=

# Infra API
INFRA_INTERNAL_KEY=        # X-Internal-Key header
INFRA_API_KEY=
INFRA_OTA_URL=https://api.tg25.win/api/ota/trigger

# iHub
IHUB_API_TOKEN=            # Bearer token

# LINE Bot
LINE_SERVICE_URL=
LINE_SERVICE_API_KEY=
LINE_WEBHOOK_SECRET=
```

---

## 📦 功能模組快速查找

```
M0: Portal      → DashboardController
M1: 用戶認證     → User, AuthController
M2: 訂閱管理     → Subscription, SubscriptionController
M3: 設備管理     → Device, Machine, DeviceController
M4: 場地管理     → Venue, VenueController
M5: 通知中心     → Notification, NotificationController
M6: BI 報表     → RevenueFact, ReportController
M7: 財務結算     → Settlement, SettlementController
M8: 帳單管理     → BillingRequest, BillingController
M9: 即時監控     → RealtimeController, RadarController
```

---

## 🔄 關鍵業務流程速查

### 開分流程
```
前端觸發 → MqttCommandService::assignCredit()
         → POST https://api.tg25.win/api/credit
         → Infra 下發 MQTT
         → 設備執行
         → 回調 /api/internal/credit/callback
```

### 脈衝採集流程
```
玩家投幣 → 設備發 MQTT credit_in
         → Infra Listener
         → POST /api/internal/pulse/credit-in
         → MqttPulseDataHandler
         → 寫入 machine_transactions
```

### 即時監控流程
```
設備 heartbeat → MQTT status
               → Infra 雙寫 devices + machines (last_seen_at)
               → Owner Radar 頁面
               → WebSocket 即時更新
```

---

## ⚠️ 重要注意事項

### 1. WAW 2.0 遷移中
- ✅ 新功能用 `Machine` model
- ⚠️ 保持 `devices` 與 `machines` 雙寫
- ❌ MQTT Listener 不修改 `status` 欄位

### 2. Owner 不直連 MQTT
- ✅ 所有硬體控制透過 Infra API
- ✅ 解耦商務邏輯與硬體層
- ❌ 不要在 Owner 加 MQTT client

### 3. 訂閱檢查
- Middleware: `EnsureSubscriptionActive`
- Grace period: 7 天
- Admin 功能不受限

---

## 🛠️ 常用 Artisan 命令

```bash
# 開發
php artisan serve                    # 啟動開發伺服器
php artisan migrate                  # 執行 migration
php artisan db:seed                  # 執行 seeder
php artisan tinker                   # 進入 REPL

# 背景任務
php artisan queue:work               # 啟動 queue worker
php artisan schedule:work            # 啟動 scheduler (dev)
php artisan reverb:start             # 啟動 Reverb WebSocket

# 清除快取
php artisan cache:clear
php artisan config:clear
php artisan route:clear
php artisan view:clear

# 檢查
php artisan route:list               # 列出所有路由
php artisan queue:failed             # 列出失敗的 jobs
php artisan migrate:status           # 檢查 migration 狀態
```

---

## 🐛 疑難排解

### WebSocket 連不上
```bash
# 檢查 Reverb 是否運行
ps aux | grep reverb

# 檢查端口
netstat -tulnp | grep <VITE_REVERB_PORT>

# 檢查前端配置
grep -A 5 "Echo" resources/js/echo.js
```

### MQTT 指令無反應
```bash
# Owner 不直連 MQTT，檢查 Infra API
curl -X POST https://api.tg25.win/api/credit \
  -H "Authorization: Bearer <token>" \
  -d '{"command":"add_credits","device_id":"..."}'

# 檢查回調 URL 可達性
curl -I https://iot.tg25.win/api/internal/credit/callback
```

### 雙寫失敗
```bash
# 檢查 Infra MQTT Listener 日誌
ssh infra "tail -f /var/log/mqtt-listener.log"

# 檢查 Owner 日誌
tail -f storage/logs/laravel.log | grep -i "pulse\|device\|machine"
```

---

**文檔來源**: WAW_CORE_SYSTEM_ASSESSMENT.md  
**最後更新**: 2026-08-19  
**維護者**: HQ (Sophie/Ina)

