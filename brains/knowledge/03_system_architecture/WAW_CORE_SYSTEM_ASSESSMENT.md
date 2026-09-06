# WAW Core (waw-core / iot.tg25.win) 系統評估文檔

> **評估日期**: 2026-08-19  
> **評估方法**: 基於代碼分析、配置文件、知識庫文檔  
> **專案路徑**: `/Users/ilawusong/Documents/WaW/PROJECT/Owner`  
> **資料來源**: 實際代碼 + config/*.php + 知識庫 (非 .env.example)  
> **最後更新**: 20260819

---

## 📋 系統概述

這是一個 **Laravel 11 IoT 夾娃娃機管理平台** (`waw-core` / `iot.tg25.win`)，負責：
- 設備管理與遠端控制
- 用戶訂閱與權限管理
- 場地營運與分潤結算
- 即時監控與數據分析
- LINE Bot 整合與通知推送

---

## 🏗️ 核心架構

### 後端技術棧
- **框架**: Laravel 11.31
- **PHP 版本**: 8.2+
- **依賴管理**: Composer
- **關鍵套件**:
  - `laravel/reverb`: ^1.7 (WebSocket 伺服器)
  - `pusher/pusher-php-server`: ^7.2 (事件廣播)
  - `barryvdh/laravel-dompdf`: ^3.1 (PDF 生成)

### 前端技術棧
- **模板引擎**: Blade
- **JavaScript 框架**: Alpine.js 3.x (輕量級響應式框架)
- **CSS 框架**: Tailwind CSS 3.x
- **構建工具**: Vite 4.x
- **套件管理**: pnpm
- **即時通訊**: Laravel Echo + Pusher.js
- **圖表庫**: Chart.js 4.5
- **日期處理**: dayjs 1.11

### 資料庫
- **主資料庫**: MySQL `iotv9`
  - 位置: Infra VPS (遠端)
  - 用途: 業務數據、用戶、設備、交易記錄
- **快取/佇列**: Redis
  - 預設端口: `6379`
  - 用途: Session、Queue、Cache

### 即時通訊
- **服務**: Laravel Reverb (WebSocket)
- **前端配置** (`resources/js/echo.js`):
  ```javascript
  broadcaster: 'reverb',
  wsPort: VITE_REVERB_PORT ?? 80,
  wssPort: VITE_REVERB_PORT ?? 443,
  forceTLS: (VITE_REVERB_SCHEME === 'https' || 'wss')
  ```
- **端口**: 由 `.env` 的 `VITE_REVERB_PORT` 決定 (預設 443 for wss)

### 硬體通訊 (MQTT)
- **Broker**: `mqtt.tg25.win`
- **配置來源**: `config/mqtt.php`
- **連接端口**:
  - **8883**: MQTT over TLS (預設)
  - **1883**: MQTT 標準端口 (non-TLS)
  - **8083**: MQTT over WebSocket
- **認證**:
  - Username: `backend_user` (預設)
  - Password: 從 `MQTT_PASSWORD` 環境變數
- **TLS 設定**: `verify_peer: false` (開發模式)
- **用途**: Owner 不直接連 MQTT，透過 Infra API 中繼控制

### 背景任務
- **佇列驅動**: Redis (`QUEUE_CONNECTION=redis`)
- **排程器**: Laravel Scheduler (cron)
- **關鍵 Jobs**:
  - `SyncDeviceCreditsJob`: 同步設備信用額 (每 5 分鐘)
  - `SendNotificationJob`: 通知推送
  - `ProcessSettlementJob`: 結算處理

---

## 🔌 API 端點架構

### 1. 前端 API (`/api/v9/*`)
- **驗證方式**: Laravel Session + CSRF Token
- **用途**: 前端 AJAX 請求
- **主要端點**:
  - `/api/v9/realtime/*`: 即時監控 (M9)
  - `/api/v9/devices/*`: 設備管理 (M3)
  - `/api/v9/venues/*`: 場地管理 (M4)
  - `/api/v9/billing/*`: 帳單管理 (M8)
  - `/api/v9/revenue/*`: 營收計算 (M6)
  - `/api/v9/machine/*`: 機台控制 (開洗分)
  - `/api/v9/line/*`: LINE Webhook

### 2. Infra 內部 API (`/api/internal/*`)
- **驗證方式**: `X-Internal-Key` header
- **Middleware**: `VerifyInternalKey`
- **配置**: `config/infra.php` → `INFRA_INTERNAL_KEY`
- **用途**: MQTT Listener 呼叫
- **端點**:
  - `POST /api/internal/devices/register`: 設備註冊
  - `POST /api/internal/pulse/credit-in`: 投幣脈衝
  - `POST /api/internal/pulse/credit-out`: 出獎脈衝
  - `POST /api/internal/credit/callback`: 信用額回調
  - `POST /api/internal/broadcast/device-update`: 設備狀態廣播
  - `POST /api/internal/kiosk/event`: Kiosk 事件
  - `POST /api/internal/kiosk/callback`: Kiosk 回調

### 3. iHub 整合 API (`/api/v1/*`)
- **驗證方式**: `Authorization: Bearer <token>`
- **Middleware**: `VerifyIhubToken`
- **配置**: `config/services.php` → `services.ihub.token` → `IHUB_API_TOKEN`
- **端點**:
  - `POST /api/v1/audit/report`: 審計報表
  - `POST /api/v1/event/pulse`: 事件脈衝

### 4. LINE Bot Webhook (`/api/v9/line/*`)
- **驗證方式**: `LINE_WEBHOOK_SECRET`
- **用途**: LINE 帳號綁定、推播

---

## 🌐 外部依賴服務

### Infra API (api.tg25.win)
Owner 透過 `MqttCommandService` 呼叫 Infra API 進行硬體控制：

| **API 端點** | **用途** | **方法** |
|------------|--------|--------|
| `https://api.tg25.win/api/credit` | 開分/洗分 (Credit Control) | POST |
| `https://api.tg25.win/api/v1/kiosk/command` | Kiosk 指令 (收鈔/退鈔) | POST |
| `https://api.tg25.win/api/ota/trigger` | OTA 韌體更新 | POST |

### LINE Bot
- **服務 URL**: `LINE_SERVICE_URL`
- **API Key**: `LINE_SERVICE_API_KEY`
- **Timeout**: 30 秒
- **用途**: 推播通知、帳號綁定驗證

### iHub
- **Base URL**: 未在 Owner 配置中定義 (由 iHub 主動呼叫)
- **Token**: `IHUB_API_TOKEN`
- **用途**: 第三方審計、事件同步

---

## 📦 功能模組 (M0–M9)

| **模組** | **功能** | **關鍵 Model/Controller** |
|--------|--------|----------------------|
| **M0** | Portal 儀表板入口頁 | `DashboardController` |
| **M1** | 用戶認證 (帳密 + LINE Login)、用戶管理、權限管理 | `User`, `AuthController` |
| **M2** | 訂閱管理 (Pro/Enterprise 方案、續購、grace period) | `Subscription`, `SubscriptionController` |
| **M3** | 設備管理 (ESP32 韌體)、參數設定、parameter templates、device types | `Device`, `Machine`, `DeviceController` |
| **M4** | 場地 (Venue/Store) 管理、場地員工、分潤提案審批 | `Venue`, `ProfitSharingProposal`, `VenueController` |
| **M5** | 通知中心 (in-app inbox + LINE Bot 推播) | `Notification`, `NotificationController` |
| **M6** | BI 報表與數據分析 (RevenueFact 脈衝流水、dashboard summary) | `RevenueFact`, `ReportController` |
| **M7** | 財務結算 (settlements, PDF 結算單, debt collection) | `Settlement`, `SettlementController` |
| **M8** | 帳單管理 (billing requests, 付款證明上傳, admin 審批) | `BillingRequest`, `BillingController` |
| **M9** | 即時監控 (realtime device status, alerts, system settings) | `RealtimeController`, `RadarController` |

---

## 🔄 關鍵業務流程

### 1. 設備註冊與認領
```
1. ESP32 上電 → 發送 MQTT register 消息
2. Infra MQTT Listener 收到 → 呼叫 Owner /api/internal/devices/register
3. Owner 自動建立 device 記錄 (status: pending)
4. Owner 用戶透過前端「認領」設備 (claim)
5. 分配到 venue_id → 設備變為 active
```

### 2. 開分/洗分流程
```
1. Owner 用戶透過前端觸發「開分」
2. Owner 呼叫 MqttCommandService::assignCredit()
3. MqttCommandService 發送 HTTPS 請求到 Infra API
4. Infra 下發 MQTT 指令到設備
5. 設備執行開分 → 回傳結果 → Infra 回調 Owner /api/internal/credit/callback
```

### 3. 脈衝採集與營收計算
```
1. 玩家投幣 → 設備發送 MQTT credit_in 消息
2. Infra MQTT Listener → 呼叫 Owner /api/internal/pulse/credit-in
3. Owner MqttPulseDataHandler 處理:
   - 查找 Device (by chip_id)
   - 驗證 device 狀態 (active + venue_id 存在)
   - 使用 PulseConverter 轉換 pulse → revenue
   - 寫入 machine_transactions 表
4. M6 報表模組彙總營收
```

### 4. 分潤機制
```
1. Venue Owner 建立 ProfitSharingProposal (提案分成比例)
2. Machine Owner 審批
3. 審批通過 → 建立 ProfitSharingAgreement (生效協議)
4. 結算時根據協議計算 store_revenue / machine_owner_revenue
```

### 5. 訂閱續購流程
```
1. 用戶發起續購 (BillingRequest)
2. 上傳付款證明 (payment proof)
3. Admin 審批 (approve/reject)
4. 審批通過 → 延長 Subscription.expires_at
5. Grace period 機制: 過期後 7 天內仍可使用
```

### 6. 結算流程 (M7)
```
1. 系統每日自動產生 daily revenue report
2. Admin 觸發結算 (settlement)
3. 生成 PDF 結算單 (含分潤明細)
4. 場地方確認付款
5. Admin 標記結算完成
```

### 7. OTA 韌體更新
```
1. Admin 選擇設備 + 韌體版本
2. Owner 呼叫 Infra OTA API
3. Infra 下發 MQTT OTA 指令
4. 設備下載並安裝韌體
5. 更新完成後回報版本號
```

### 8. 即時監控與警報 (M9)
```
1. 設備定期發送 heartbeat (MQTT status)
2. Infra 更新 devices.last_seen_at / machines.last_seen_at (雙寫)
3. Owner 前端 Radar 頁面透過 WebSocket 即時更新
4. 超過閾值 → 觸發警報 → LINE Bot 推播
```

---

## 🗄️ 資料庫架構重點

### WAW 2.0 遷移狀態
- **舊表**: `devices` (legacy, 仍在使用)
- **新表**: `machines` (WAW 2.0, migration 進行中)
- **雙寫策略**: MQTT Listener 同時更新兩表的 `last_seen_at`
- **狀態保護原則**: MQTT Listener **不得**修改 `status` 欄位 (僅限 Owner 商務邏輯修改)

### 關鍵資料表
- `users`: 用戶 (Owner, Venue Manager, Admin)
- `devices` / `machines`: 設備/機台
- `venues`: 場地
- `subscriptions`: 訂閱
- `machine_transactions`: 交易流水 (脈衝記錄)
- `revenue_facts`: 營收彙總 (BI 用)
- `settlements`: 結算單
- `billing_requests`: 帳單請求
- `profit_sharing_proposals`: 分潤提案
- `profit_sharing_agreements`: 分潤協議
- `notifications`: 通知記錄

---

## 🔐 安全機制

### API 驗證
1. **前端 API**: Session + CSRF Token
2. **Internal API**: `X-Internal-Key` header (與 Infra 共享密鑰)
3. **iHub API**: `Authorization: Bearer <token>`
4. **LINE Webhook**: `LINE_WEBHOOK_SECRET` 驗證

### Middleware
- `auth`: Laravel 標準認證
- `EnsureSubscriptionActive`: 檢查訂閱狀態
- `check.user.management.access`: Admin 權限檢查
- `VerifyInternalKey`: Internal API 驗證
- `VerifyIhubToken`: iHub API 驗證

### 失敗記錄
所有驗證失敗都會記錄到 Laravel Log，包含：
- IP 位址
- User-Agent
- URL
- 提供的 Key 長度 (不記錄完整 Key)

---

## ⚠️ 限制與注意事項

### 1. 配置依賴生產環境
以下配置**無法從代碼確定**，必須從 VPS 的 `.env` 確認：
- Reverb 實際端口 (`VITE_REVERB_PORT`)
- MQTT 實際 Host/Port (可能不是預設值)
- Redis 實際端口 (可能不是 6379)
- MySQL 連線資訊 (Host, Port, 用戶名)
- 各種 API Key 與 Token

### 2. MQTT 連線限制
- Owner 專案**不直接**連 MQTT Broker
- 所有硬體控制指令透過 Infra API (`api.tg25.win`) 中繼
- 原因: 解耦硬體層與商務層，方便獨立部署與擴展

### 3. WAW 2.0 遷移中
- `devices` 表與 `machines` 表雙寫運行
- 新功能應優先使用 `Machine` model
- 遷移完成前需保持雙寫邏輯

### 4. 訂閱檢查
- 多數功能受 `EnsureSubscriptionActive` 保護
- 過期後有 7 天 grace period
- Admin 功能不受訂閱限制

---

## 📊 技術債與改進方向

### 已知問題
1. **雙表維護成本**: `devices` + `machines` 雙寫增加複雜度
2. **MQTT TLS 驗證**: 目前 `verify_peer: false`，生產環境應改為 `true`
3. **硬編碼 API URL**: `MqttCommandService` 中的 Infra API URL 應移到配置
4. **前端依賴少**: 僅用 Chart.js + dayjs，可考慮引入更完整的 UI 框架

### 建議改進
1. **完成 WAW 2.0 遷移**: 移除 `devices` 表依賴
2. **API 版本管理**: 統一 API 版本 (目前混用 v1/v9/internal)
3. **測試覆蓋率**: 增加單元測試與整合測試
4. **監控告警**: 接入 Sentry/Prometheus 等監控服務
5. **文檔補全**: API 文檔自動生成 (Swagger/OpenAPI)

---

## 🎯 總結

### 優勢
✅ 清晰的模組化設計 (M0–M9)  
✅ 完善的 API 驗證機制  
✅ 即時通訊能力 (Reverb + Echo)  
✅ 彈性的分潤機制  
✅ LINE Bot 整合良好  

### 挑戰
⚠️ 雙表遷移增加維護成本  
⚠️ 部分配置依賴生產環境  
⚠️ 測試覆蓋率待提升  

### 架構特色
🎯 **解耦設計**: 商務邏輯 (Owner) 與硬體層 (Infra) 分離  
🎯 **中繼控制**: 透過 Infra API 統一硬體控制介面  
🎯 **雙寫保護**: 遷移期間保持業務連續性  

---

## 📚 相關文檔

- [MQTT Topic Standard](./02_technical_standards/MQTT_TOPIC_STANDARD.md)
- [Revenue Integration](./REVENUE_INTEGRATION.md)
- [Database Migration Strategy](./DATABASE_MIGRATION_STRATEGY.md)
- [MQTT Terminal Deployment](./04_deployment_operations/MQTT_TERMINAL_DEPLOYMENT.md)

---

**文檔生成時間**: 2026-08-19  
**基於版本**: Laravel 11.31, WAW 2.0 (Migration Phase)  
**評估者**: Kiro Agent  
**資料來源**: 代碼分析 + 配置文件 + 知識庫文檔

