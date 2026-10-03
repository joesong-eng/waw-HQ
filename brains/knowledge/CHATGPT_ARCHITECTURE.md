# WAW 系統架構與拓撲全解析 (CHATGPT_ARCHITECTURE.md)

> **文件身分**：WAW 專案架構深探文件 (專供 ChatGPT 深度解析)  
> **關聯總索引**：`knowledge/CHATGPT_CONTEXT.md` (實體位置: `brains/knowledge/CHATGPT_CONTEXT.md`)  
> **最後校驗日期**：2026-09-24  
> **維護權限**：HQ (協調中心唯一寫入)  
> **狀態標記準則**：【已實作】/【已驗證】/【已設計但尚未實作】/【計畫中】/【未確認】

---

## 1. 全域實體拓撲與主機職責架構

WAW (wawIoT) 是一套軟硬體高度整合的遊藝場/街機與物聯網點數清算管理平台。全系統部署於 Oracle Cloud 基礎設施與本地邊緣節點，並受嚴格的遠端運維治理規範約束。

### 1.1 伺服器主機與別名對照表 (SSOT) 【已驗證】

所有伺服器均位於 Oracle Cloud，所有 Agent 與協調者禁止使用原始 IP 或預設 Port 22 直連，必須使用 SSH 別名。

| 主機 SSH 別名 | 實體 IP 位址 | SSH 端口 | 使用者 | 憑證路徑 | 負責 Agent | 託管站點 / 核心服務 | 伺服器實體目錄 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`yd174`**<br>(別名: `v9`, `Owner`, `blc`) | 129.153.116.174 | 39022 | ubuntu | `~/.ssh/id_rsa` | **Sophie**<br>**Sidney** | • **Owner 營運後台** (`iot.tg25.win`)<br>• **SignalHub 信號中心** (`signal.tg25.win`) | `/www/wwwroot/iot.tg25.win`<br>`/www/wwwroot/signal.tg25.win` |
| **`yd177`**<br>(別名: `mina`, `ihub`, `yd47`) | 129.146.103.177 | 39022 | ubuntu | `~/.ssh/id_rsa` | **Mina**<br>**Hubie** | • **Member 會員前端** (`win.tg25.win`)<br>• **iHub 平板 API** (`ihub.tg25.win`) | `/www/wwwroot/win.tg25.win`<br>`/www/wwwroot/ihub.tg25.win` |
| **`yd16`**<br>(別名: `alliance`) | 137.131.50.16 | 39022 | ubuntu | `~/.ssh/id_rsa` | **Allie** | • **Alliance 聯盟/燒錄後台** (`ali.tg25.win`) | `/www/wwwroot/ali.tg25.win` |
| **`infra`**<br>(別名: `db`) | 141.148.165.50 | 39022 | ubuntu | `~/.ssh/id_rsa` | **Ina** | • **Central MySQL (`iotv9`)**<br>• **MQTT Broker (Mosquitto TLS)**<br>• MQTT 信號監聽器 (Daemon) | `/home/ubuntu/tg25-infra` |
| **`bessie202`**<br>(別名: `HQ`, `PM`) | 132.226.87.202 | 39022 | ubuntu | `~/.ssh/id_rsa` | **HQ** | • HQ Taskflow 派工總控<br>• Redis Pub/Sub 神經網路 | `/home/ubuntu` |

### 1.2 網路與安全拓撲規則 【已驗證】
1. **非標準 SSH 端口**：所有 VPS 統一使用 Port **39022**，絕對禁止直連預設 Port 22。
2. **連線唯一憑據**：強制使用本機 `~/.ssh/config` 別名連線（如 `ssh yd174`），嚴禁在命令列使用 Raw IP 或明文密碼。
3. **資料庫集中隔離**：
   - Web 伺服器（`yd174`, `yd177`, `yd16`）本機**不存放業務資料庫**。
   - 核心 MySQL `iotv9` 僅託管於 `infra` (141.148.165.50)。各 Web 專案透過內部安全通道或 Port 3308 穿透連線。在 Web 伺服器本地執行 `mysql` 指令必屬錯誤。
4. **HTTPS / TLS 加密**：
   - 外部流量由 Cloudflare CDN / SSL 代理，對內反向代理至 Nginx。
   - MQTT 通訊採用 MQTTS (TLS v1.2/1.3) Port **8883**，ESP32 韌體內建 Let's Encrypt / DigiCert 憑證包進行伺服器身分驗證。
5. **本機代碼純淨原則**：
   - 本機（Mac）僅用於寫代碼與 Git 版本控制。
   - 嚴禁本機執行 `php artisan migrate`、本地 `pnpm run build`、本地 MySQL / Redis / MQTT 測試。所有驗證必須在對應 VPS 上透過 `waw_ops.sh` 執行。

---

## 2. 系統分層架構 (System Layered Architecture)

系統橫跨五個核心抽象層級，實現硬體、通訊、平台與業務應用的解耦：

```
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 4: 使用者與第三方業務層 (Partner, Cashier, Member, Venue Owner)      │
│  - Member 前端 (win.tg25.win) / Owner 後台 (iot.tg25.win)               │
│  - SignalHub 合作夥伴後台 (signal.tg25.win) / 第三方 POS (小猴收銀系統)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP(S) / WebSocket / Webhook
┌───────────────────────────────────▼────────────────────────────────────┐
│ Layer 3: 核心後端業務服務層 (Laravel Applications & Central DB)           │
│  - Owner API / Member API / SignalHub API / Alliance API               │
│  - 核心資料庫: Central MySQL (iotv9 @ infra), Member DB (yd47)          │
│  - 非同步佇列與任務調度 (Redis Queue, Horizon, crontab scheduler)        │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ Internal API / Webhook (X-Internal-Key)
┌───────────────────────────────────┴────────────────────────────────────┐
│ Layer 2: 基礎設施與信號中繼層 (Infra & Message Routing)                   │
│  - Mosquitto MQTT Broker (Port 8883 TLS @ infra)                       │
│  - MQTT Signal Listener (監聽 raw pulse 並寫入 DB / 轉發 Webhook)       │
│  - WebSocket Server (Pusher / Laravel WebSockets / Reverb)             │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ MQTT (MQTTS 8883) / USB CDC Serial
┌───────────────────────────────────┴────────────────────────────────────┐
│ Layer 1: 邊緣硬體與韌體層 (Edge Hardware & Firmware)                     │
│  - IOTwawS3 (Coli): ESP32-S3 遊戲採集卡 (PCNT 脈衝計數 + 雙軌輸出)      │
│  - IOTkiosk_v0 (Fio): ESP32-S3 / WROOM 兌幣通訊卡 (RS232 鈔票機控制)     │
│  - iHub (Hubie): 工控 Android 平板 (展示 QR Code, 兌幣 Escrow 人工確認) │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ 光耦隔離 GPIO / RS232 / 繼電器
┌───────────────────────────────────┴────────────────────────────────────┐
│ Layer 0: 實體遊藝機台與計數設備 (Physical Arcade Machine & Meters)        │
│  - PC-Based 聯網街機 (開分按鈕, 洗分按鈕, 實體電磁計數表 UI3/UI4)       │
│  - 傳統單機機板 (投退幣脈衝, 瑪莉機, 輪盤機, 框體)                       │
│  - ICT 104U 紙鈔接收機 (Pulse / RS232 協議)                             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 兩大機台營運模型邊界 (CRITICAL ARCHITECTURAL BOUNDARY)

在理解 WAW 架構時，**最致命的錯誤**就是混淆「電腦型網路遊戲機」與「傳統單機投幣機」。兩者在硬體定位、信號意義與金流邏輯上完全不同：

### 3.1 模型 A：電腦型聯網遊戲機 (PC-Based Online Game Machine)
- **代表專案**：`SignalHub` (Sidney) + `IOTwawS3` (Coli)
- **機台架構**：遊戲運行於專用電腦（PC 主機），機台內部的點數增減、遊戲規則、賠率與清算**100% 由遊戲商後端伺服器控制**。
- **採集卡定位**：**透明邊緣中繼器 (Transparent Relay)**。採集卡**絕不介入**遊戲業務邏輯，不換算點數，不修改機台記憶體。
- **兩條完全獨立的信號通道**：
  1. 🔴 **事件觸發通道 (UI1 / UI2)**：
     - **物理事件**：吧台服務員收取現金後，按下實體「開分」或「洗分」按鈕。
     - **採集卡行為**：偵測到按鍵閉合，發布事件 `delta: 1` 與當前累計里程表 `raw_value`。
     - **核心鐵律**：採集卡**不知道金額**、**不做比例換算 (Pulse Ratio)**、**不產生金額**！
     - **點數確認**：由第三方遊戲商伺服器在收到 Webhook 後，於 3 秒內透過 Callback 或 HTTP 回傳 `actual_points`。
  2. 🔵 **碼表脈衝通道 (UI3 / UI4)**：
     - **物理事件**：機台若裝有機械碼表（電磁計數器），馬達轉動產生的方波脈衝。
     - **採集卡行為**：硬體 PCNT 計數器採集物理脈衝數（累加 raw_value）。
     - **用途**：僅作為營業日結、防弊審計與對帳依據，**絕對禁止與開洗分按鍵混為一談**！

### 3.2 模型 B：傳統單機機板型 (Standalone Arcade / game_v0 / kiosk_v0)
- **代表專案**：`Owner` (Sophie) + `Member` (Mina) + `IOTkiosk_v0` (Fio) / `IOTwawS3` (Coli 舊模式)
- **機台架構**：傳統單機（如瑪莉機、水果盤、輪盤）。無聯網遊戲伺服器，投幣即時產生機台硬體脈衝。
- **採集卡定位**：**主控與觸發終端**。
- **開分機制**：玩家掃描機台 QR Code，手機點選扣除 1 代幣；Member 後台呼叫 Infra API 發送 MQTT 指令；ESP32 驅動繼電器 (PIN_OUT1) 模擬投幣脈衝送入機板。
- **脈衝比例換算**：此模式下嚴格遵守 `pulse_to_token` 換算比例（如 2 脈衝 = 1 代幣），此比例由場地主在 Owner 後台統一設定。

---

## 4. 資料庫架構與實體關聯 (Database Architecture & Governance)

系統包含兩套主要的關聯式資料庫系統：

### 4.1 核心業務資料庫：`iotv9` (MySQL 8 / MariaDB @ infra)
由 **Ina (Infra)** 獨佔 DDL 變更權限。

#### 核心實體結構：
1. **場地實體：`venues`** 【已驗證】
   - 記錄場地名稱、地址、聯絡人、代幣價值 (`token_value_twd`)。
   - 規範：全域統一使用 `venue`，廢棄舊規格書中的 `store` 命名。
2. **設備資產：`devices`** 【已驗證】
   - 實體採集卡與硬體對應表。
   - 關鍵欄位：`id` (內部整數 PK), `chip_id` (12 碼十六進位 MAC), `owner_id` (機主 FK), `venue_id` (場地 FK), `status`, `last_seen_at`。
   - **重大架構決策 (2026-09-04)**：完全移除 `machine_number` 與 `machine_name` 欄位，設備端只負責識別「我是誰 (`chip_id`)」。
3. **兌幣機設備：`kiosks`** 【已驗證】
   - 兌幣卡硬體表，綁定 `esp32_mac` (同 chip_id)、`screen_mac` (iHub 平板 MAC)、`venue_id`。
4. **SignalHub 專用表群 (2026-09 Migration 完成)** 【已驗證】：
   - `signal_profiles`：信號配置檔案（店主針對不同機型設定腳位定義、Webhook 目標、Serial 致能狀態）。
   - `signal_pin_mappings`：腳位映射表（定義 UI1~UI4 對應之事件代碼，如 `credit_in`, `credit_out`, `coin_meter`）。
   - `signal_stat_rules`：日結統計規則（加減公式配置）。
   - `signal_webhooks`：第三方 Webhook 推送端點配置與密鑰。
   - `signal_webhook_deliveries`：信號派送審計日誌（包含 `delivery_id`, `raw_value`, `delta_value`, `cleared_points` / `actual_points`, `status`, `retry_count`）。
5. **部署與分成交易：`device_deployments`, `device_transactions`** 【已實作】
   - 記錄機台在場地的進出場歷史，支援動態分潤計算 (`owner_share`, `venue_owner_share`)。

### 4.2 會員與會話資料庫：`waw_member_production` (MySQL @ yd177)
由 **Mina (Member)** 負責維護。
1. **`device_sessions`**：傳統機台遊戲掃碼會話表（記錄 `session_token`, `member_id`, `chip_id`, `status`, `started_at`, `ended_at`）。
2. **`kiosk_sessions`**：兌幣機掃碼連線會話表（記錄會員與紙鈔機的互動狀態）。
3. **`member_wallets`**：會員虛擬錢包表。
   - 貨幣類型：`CASH` (現金), `TOKEN` (遊戲代幣), `POINT` (點數), `TICKET` (彩票)。
   - **數值規範**：代幣與彩票一律為整數 (`INT`)，絕對不使用小數。
4. **`wallet_transactions`**：會員錢包變動交易日誌。

---

## 5. 通訊協定與安全架構 (Communication & Security)

### 5.1 MQTT 通訊規範 (WAW-USS v1.0) 【已實作 / 驗證中】
- **Broker 位置**：`direct-mqtt.tg25.win:8883` (TLS 加密)。
- **主題結構**：`waw/v1/{site_id}/signal/{chip_id}/{action}`
  - `action = event`：硬體事件與脈衝里程表上報 (QoS 1, Retain false)。
  - `action = status`：在線心跳、狀態回報與 LWT 遺囑 (QoS 1, Retain true)。
  - `action = cmd`：雲端下行單播控制指令 (QoS 1, Retain false)。
  - `action = ack`：硬體接收指令後之回執 (QoS 1, Retain false)。

### 5.2 邊緣雙軌輸出 (Dual-Mode Output) 【已實作】
針對現場無網際網路或要求極致低延遲的場地，採集卡支援雙軌並行輸出：
1. **雲端軌道 (Cloud Path)**：ESP32 透過 Wi-Fi 發布 MQTT 封包至雲端 Broker。
2. **地端軌道 (Local Path)**：ESP32 透過 USB-CDC / Type-C 虛擬串列埠，以 115200 鮑率直接向現場收銀 PC 發送單行 JSON，並接收 PC 回傳之 `cleared_points`。

### 5.3 跨服務內部驗證 (Service-to-Service Auth) 【已驗證】
- **內部 Webhook 通訊**：Member ↔ Infra ↔ SignalHub 內部 API 呼叫，必須在 HTTP Header 附帶：
  `X-Internal-Key: v9-internal-key-2026`
- **Infra 設備 API 授權**：呼叫 `api.tg25.win/api/device/...` 時，附帶：
  `X-API-Key: v9_backend_token_2026`
- **第三方 Webhook 簽名防偽 (HMAC-SHA256)**：
  - Header：`X-WAW-Signature: sha256={hash}`
  - 簽名計算方式：使用共享密鑰對 `timestamp + "." + raw_payload` 進行雜湊，防止重放攻擊 (Replay Attack)。

### 5.4 WebSocket 頻道架構 (WebSocket Channel Standard) 【已驗證】
由 Pusher 或 Laravel WebSockets 廣播即時事件給前端：
1. **機台即時頻道**：`waw-device.{chip_id}`
   - 事件：`DeviceStatusChanged` (在離線狀態切換)、`CreditAssigned` (開分完成回報)、`CreditSettled` (洗分結算回報)。
2. **兌幣機即時頻道**：`kiosk.{kiosk_id}`
   - 事件：`KioskEscrowPending` (紙鈔吸入，等待平板人工確認)、`KioskBillStacked` (紙鈔入箱成功)、`KioskSessionTimeout` (會話逾期結束)。
3. **場地大看板頻道**：`private-venue.{venue_id}.dashboard`
   - 事件：`LiveOdometerUpdate` (機械碼表數字跳動)、`DailyRevenueSnapshot` (當日營收快照)。

### 5.5 遠端部署與運維標準 (Deployment SOP) 【已驗證】
全專案由根目錄 `dev_tools/waw_ops.sh` 總控：
- 派工指令：`./dev_tools/waw_ops.sh task <agent> <task_id> "<desc>" [priority]`
- 遠端部署：`./dev_tools/waw_ops.sh deploy <agent>` (自動執行遠端 Git pull、composer install、artisan optimize、Nginx 重載)
- 狀態監控：`./dev_tools/waw_ops.sh status` (檢查各 Agent inbox/outbox 堆疊)
- 遠端執行：`./dev_tools/waw_ops.sh remote <agent> "<command>"` (在目標 VPS 執行指令)
