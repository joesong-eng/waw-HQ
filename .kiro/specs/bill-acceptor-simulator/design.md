# Design Document: Bill Acceptor Simulator

> **最後更新**：2026-05-11 UTC+8  
> **版本**：4.1（STACKED 後進入 DISABLED，等待 iHub 發 enable）  
> **實作代碼位置**：`iHub/public/sim-bill/index.html`、`iHub/server/index.js`

---

## ⚠️ 實作前必讀

在修改任何功能前，**必須先對照本文件的接口表**，確認名稱、格式、大小寫完全一致，不得自行發明任何名稱。

參考標準文件：
- 識別碼體系：`brains/knowledge/kiosk_identification_system.md`
- WebSocket 頻道標準：`brains/knowledge/02_technical_standards/WEBSOCKET_CHANNEL_STANDARD.md`
- MQTT 主題標準：`brains/knowledge/02_technical_standards/MQTT_TOPIC_STANDARD.md`

---

## 識別碼使用規則

| 識別碼 | 格式範例 | 用於 | 不可用於 |
|--------|---------|------|---------|
| `chip_id` | `test-esp32` | API 請求的 `chip_id` / `esp32_mac` 欄位、MQTT 主題 | WebSocket 頻道名稱 |
| `node_id` / `kiosk_id` | `kiosk_000` | WebSocket 頻道名稱、Member API 的 `kiosk_id` 欄位 | MQTT 主題 |

**localStorage key 對照**（讀寫必須用同一個 key）：

| 用途 | key 名稱 | 預設值 |
|------|---------|--------|
| 儲存 chip_id | `sim_chip_id` | `test-esp32` |
| 儲存 node_id | `sim_node_id` | `kiosk_000` |

---

## 系統架構與完整鏈路

> **版本 4.0 架構**：sim-bill 改用真實 MQTT 鏈路，與真實韌體行為完全一致。

```
sim-bill (Browser)
    │
    ├─[A] POST /api/simulator/bill ──► iHub Server (port 8083)
    │                                       │
    │                                       ├─[B] POST api.tg25.win/api/kiosk/hardware-status
    │                                       │         → 發布 MQTT kiosk/{chip_id}/status (QoS 1)
    │                                       │
    │                                       └─[C] POST api.tg25.win/api/internal/mqtt/publish
    │                                                 → 發布 MQTT kiosk/{chip_id}/event (QoS 2)
    │                                                 → Infra Listener 收到 → POST win.tg25.win/internal/kiosk/escrow
    │                                                 → Member 廣播 KioskEscrowPending (WebSocket)
    │
    ├─[D] WSS win.tg25.win:443 ──► Member Reverb WebSocket
    │         訂閱 kiosk.{node_id}
    │         監聽 .MemberBoundToKiosk → DISABLED 轉 IDLE
    │         （不再監聽 infra.cmd，改由 MQTT 接收）
    │
    └─[E] GET /api/simulator/events ──► iHub Server SSE
              iHub Server 訂閱 MQTT kiosk/{chip_id}/cmd
              收到指令後透過 SSE 推給前端
              前端根據指令更新狀態並發 MQTT 事件

iHub 平板（真實硬體）
    │
    └─[F] POST api.tg25.win/api/kiosk/escrow/confirm
              → Infra bridge → Member escrowConfirm
              → Member 發 MQTT kiosk/{chip_id}/cmd (stack)
              → iHub Server 收到 MQTT → SSE 推給 sim-bill
              → sim-bill ESCROW 轉 STACKING → 發 MQTT stacked 事件
```

### 新舊架構對比

| 項目 | 舊架構（v3） | 新架構（v4） |
|------|------------|------------|
| 收到 stack/reject 指令 | WebSocket `infra.cmd` | MQTT `kiosk/{chip_id}/cmd` |
| 發 stacked/rejected 事件 | 透過 `/api/simulator/bill` proxy | 透過 `/api/simulator/bill` proxy（不變） |
| 與真實韌體一致性 | ❌ 不一致（走 WebSocket） | ✅ 完全一致（走 MQTT） |

---

## 接口完整對照表

### 1. sim-bill → iHub Server（前端呼叫 Proxy）

| 項目 | 值 |
|------|---|
| 方法 | `POST` |
| 路徑 | `/api/simulator/bill` |
| Header | `Content-Type: application/json` |
| Auth | 無（同源請求） |

**情境 A：純狀態更新（開機 DISABLED、心跳 IDLE、狀態轉換）**

| 欄位 | 類型 | 說明 |
|------|------|------|
| `chip_id` | string | 硬體識別碼，例如 `test-esp32` |
| `ba_state` | string | 狀態值（全大寫），見狀態表 |

**情境 B：投幣請求（iHub Server 自動發 ESCROW 狀態 + MQTT 事件）**

| 欄位 | 類型 | 說明 |
|------|------|------|
| `chip_id` | string | 硬體識別碼 |
| `amount` | number | 面額整數：100 / 500 / 1000 |

> 有 `amount` 時，前端不需另外發 ESCROW 狀態，iHub Server 會自動處理。

**回應格式**：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `success` | boolean | 是否成功 |
| `message` | string | 說明文字 |
| `detail` | object | Infra API 的原始回應 |

---

### 2. iHub Server → Infra API（Proxy 轉發）

#### 2a. 硬體狀態更新

| 項目 | 值 |
|------|---|
| 方法 | `POST` |
| URL | `https://api.tg25.win/api/kiosk/hardware-status` |
| Header | `Content-Type: application/json` |
| Header | `X-Internal-Key: v9-internal-key-2026` |

Request Body：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `chip_id` | string | 硬體識別碼（Infra 會自動 lowercase） |
| `ba_state` | string | 狀態值（全大寫） |

Infra 收到後：發布 MQTT `kiosk/{chip_id}/status`，payload `{"ba_state": "..."}` QoS 1，Retain 不設定（由韌體規範決定，模擬器不設 Retain）

成功回應：`{"success": true, "message": "Status {ba_state} published to kiosk/{chip_id}/status"}`

#### 2b. MQTT 事件發布（投幣時）

| 項目 | 值 |
|------|---|
| 方法 | `POST` |
| URL | `https://api.tg25.win/api/internal/mqtt/publish` |
| Header | `Content-Type: application/json` |
| Header | `X-Internal-Key: v9-internal-key-2026` |

Request Body：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `topic` | string | `kiosk/{chip_id}/event`（chip_id 小寫） |
| `payload` | object | 見下方 |
| `qos` | number | `2` |

Payload 物件（目前 sim-bill 實際發送的格式）：

| 欄位 | 類型 | 說明 | 備註 |
|------|------|------|------|
| `event` | string | `"escrow"` | Infra Listener 同時接受 `event` 和 `event_type`，兩者皆可 |
| `amount` | number | 面額整數 | |
| `event_id` | string | `sim-{毫秒timestamp}` | 用於 Member 冪等性檢查 |
| `timestamp` | number | Unix timestamp（秒） | |

> 標準韌體格式用 `event_type`，sim-bill 用 `event`。Infra Listener 第 262 行：`event_type = payload.get('event_type') or payload.get('event')`，兩者都能正常運作。

成功回應：`{"status": "published"}`

---

### 3. Infra Listener → Member Webhook（Infra 轉發）

Infra Listener 訂閱主題：`kiosk/+/event`（QoS 2）、`kiosk/+/status`（QoS 2）

#### 3a. Escrow 事件轉發

| 項目 | 值 |
|------|---|
| 方法 | `POST` |
| URL | `https://win.tg25.win/internal/kiosk/escrow` |
| Header | `X-Internal-Key: v9-internal-key-2026` |
| Header | `Content-Type: application/json` |

Request Body（Infra Listener 組裝）：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `kiosk_id` | string | node_id（Listener 從 device cache 查出） |
| `esp32_mac` | string | chip_id |
| `amount` | number | 面額 |
| `event_id` | string | 原始 event_id |
| `firmware_timestamp` | number | 原始 timestamp |

Member 回應（`CallbackController::kioskEscrow`）：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `status` | string | `"pending"` |
| `member_name` | string | 會員名稱 |
| `member_phone` | string | 會員手機 |
| `tokens_credited` | number | 預計入帳代幣數 |

> Member 收到 escrow 後廣播 `KioskEscrowPending` 到 `kiosk.{kiosk_id}`，iHub 平板顯示確認畫面。

#### 3b. Stacked 事件轉發

| 項目 | 值 |
|------|---|
| URL | `https://win.tg25.win/internal/kiosk/stacked` |
| Header | `X-Internal-Key: v9-internal-key-2026` |

Request Body 同 3a（`kiosk_id`, `esp32_mac`, `amount`, `event_id`, `firmware_timestamp`）

Member 回應（`CallbackController::kioskStacked`）：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `status` | string | `"credited"` |
| `tokens_credited` | number | 實際入帳代幣數 |
| `idempotent` | boolean | 是否為重複請求 |

#### 3c. Rejected 事件轉發

| 項目 | 值 |
|------|---|
| URL | `https://win.tg25.win/internal/kiosk/rejected` |
| Header | `X-Internal-Key: v9-internal-key-2026` |

Request Body 同 3a，額外有 `reason` 欄位（`"timeout"` / `"rejected_by_server"` / `"hardware"`）

Member 回應：`{"status": "logged"}`

#### 3d. 硬體狀態轉發

| 項目 | 值 |
|------|---|
| URL | `https://win.tg25.win/internal/kiosk/status` |
| Header | `X-Internal-Key: v9-internal-key-2026` |

Request Body：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `kiosk_id` | string | node_id |
| `chip_id` | string | chip_id |
| `ba_state` | string | 狀態值（全大寫） |

Member 回應：`{"status": "ok"}`

---

### 4. iHub 平板 → Infra Bridge → Member（人工確認鏈路）

> 此鏈路由真實 iHub 平板觸發，sim-bill 不直接呼叫，但 sim-bill 會收到最終的 WebSocket 事件。

#### 4a. iHub 平板呼叫 Infra Bridge

| 項目 | 值 |
|------|---|
| 方法 | `POST` |
| URL | `https://api.tg25.win/api/kiosk/escrow/confirm` 或 `/escrow/reject` |
| Header | `X-Internal-Key: v9-internal-key-2026` |
| Header | `Content-Type: application/json` |

Request Body：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `kiosk_id` | string | node_id |

#### 4b. Infra Bridge → Member

Infra 收到後橋接到：

| 項目 | 值 |
|------|---|
| URL | `https://win.tg25.win/api/kiosk/escrow/confirm` 或 `/escrow/reject` |
| Header | `X-Internal-Key: v9-internal-key-2026` |
| Body | `{"kiosk_id": "{node_id}"}` |

Member 收到後（`KioskController::escrowConfirm`）：
1. 呼叫 Infra MQTT API 發送 `{"action": "stack"}` 到 `kiosk/{chip_id}/cmd`
2. 廣播 `KioskInfraCmd` 事件到 `kiosk.{kiosk_id}`（`infra.cmd`，action=stack）

> ⚠️ v4 架構：sim-bill **不再**監聽 `infra.cmd`。Member 發出的 MQTT cmd 由 iHub Server 訂閱後透過 SSE 推給 sim-bill。

---

### 5. iHub Server SSE（sim-bill 接收 MQTT 指令）

iHub Server 在啟動時建立持久 MQTT client，訂閱 `kiosk/{chip_id}/cmd`，收到指令後透過 SSE 推給前端。

| 項目 | 值 |
|------|---|
| 端點 | `GET /api/simulator/events` |
| 協議 | Server-Sent Events（SSE） |
| Auth | 無（同源請求） |

**SSE 事件格式**：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `event` | string | `"mqtt_cmd"` |
| `data` | JSON string | `{"action": "stack", "chip_id": "test-esp32"}` |

**前端處理邏輯**：

| 收到 action | 前端行為 |
|------------|---------|
| `enable` | DISABLED → IDLE |
| `disable` | 任何狀態 → DISABLED |
| `stack` | ESCROW → STACKING → 500ms → 發 MQTT stacked 事件 → STACKED → 1.5s → **DISABLED**（等待 iHub 按 [↩ 繼續兌換]） |
| `reject` | ESCROW → REJECTING → 500ms → 發 MQTT rejected 事件 → REJECTED → 1.5s → IDLE |

> 收到 `stack`/`reject` 後，前端透過 `/api/simulator/bill` 發對應的 MQTT event（stacked/rejected），模擬真實韌體行為。

---

### 6. WebSocket 訂閱（sim-bill 監聽，僅用於 bind 事件）

| 項目 | 值 |
|------|---|
| WebSocket Server | `win.tg25.win`（Member Reverb） |
| Port | `443` |
| Protocol | `WSS`（forceTLS: true） |
| Broadcaster | `pusher`（Laravel Echo 用 pusher 模式連 Reverb） |
| App Key | `waw-member-key` |
| Channel Type | Public Channel |
| 訂閱頻道 | `kiosk.{node_id}`（全小寫） |

**監聽事件**（v4 只監聽 bind，不再監聽 infra.cmd）：

| 前端監聽名稱 | 觸發時機 | 行為 |
|------------|---------|------|
| `.MemberBoundToKiosk` | 會員掃碼綁定成功 | DISABLED → IDLE |

> `infra.cmd` 已移除，改由 MQTT `kiosk/{chip_id}/cmd` 接收。

---

### 7. 狀態值對照表

| 狀態 | 值（全大寫） | 燈號 | 投幣按鈕 | 說明 |
|------|------------|------|---------|------|
| `DISABLED` | `"DISABLED"` | 🔴 紅 | 禁用 | 開機預設，等待會員綁定 |
| `IDLE` | `"IDLE"` | 🟢 綠 | 啟用 | 可投幣 |
| `ESCROW` | `"ESCROW"` | 🟡 黃（閃爍） | 禁用 | 鈔票懸停，等待裁決 |
| `STACKING` | `"STACKING"` | 🔵 藍（閃爍） | 禁用 | 吞鈔中（收到 stack 指令後） |
| `REJECTING` | `"REJECTING"` | 🟡 黃（閃爍） | 禁用 | 退鈔中（收到 reject 指令後） |
| `STACKED` | `"STACKED"` | 🔴 紅 | 禁用 | 收鈔成功（1.5 秒後自動回 DISABLED，等待 iHub 操作） |
| `REJECTED` | `"REJECTED"` | 🔴 紅 | 禁用 | 退鈔完成（1.5 秒後自動回 IDLE） |

> 狀態值全大寫，傳給 Infra API 的 `ba_state` 也是全大寫。

---

### 8. 狀態轉換規則

| 當前狀態 | 可轉換到 | 觸發條件 |
|---------|---------|---------|
| `DISABLED` | `IDLE` | 收到 `.MemberBoundToKiosk`（`event.status === 'bound'`） |
| `IDLE` | `ESCROW` | 用戶點擊投幣按鈕 |
| `IDLE` | `DISABLED` | 收到 MQTT `{"action":"disable"}` |
| `ESCROW` | `STACKING` | 收到 MQTT `{"action":"stack"}` |
| `ESCROW` | `REJECTING` | 收到 MQTT `{"action":"reject"}` 或 15 秒超時 |
| `STACKING` | `STACKED` | 500ms 後自動（同時發 MQTT stacked 事件） |
| `REJECTING` | `REJECTED` | 500ms 後自動（同時發 MQTT rejected 事件） |
| `STACKED` | `DISABLED` | 1.5 秒後自動（等待 iHub 按 [↩ 繼續兌換] 或 [離開]） |
| `REJECTED` | `IDLE` | 1.5 秒後自動 |
| `DISABLED` | `IDLE` | 收到 MQTT `{"action":"enable"}` |

---

### 9. 心跳機制

| 項目 | 值 |
|------|---|
| 觸發條件 | 當前狀態為 `IDLE` |
| 間隔 | 每 25 秒（`BA_STATUS_INTERVAL_MS = 25000`，小於 MQTT Keepalive 30 秒） |
| 動作 | `POST /api/simulator/bill`，body `{"chip_id": "...", "ba_state": "IDLE"}` |
| 目的 | 維持 Infra MQTT status retain 訊息，讓工程頁面顯示硬體在線 |

---

### 10. 安全控制

| 項目 | 值 |
|------|---|
| 訪問控制 | URL 必須帶 `?key=dev` 參數 |
| API Key 保護 | `X-Internal-Key` 只在 iHub Server 端加入，前端不持有 |
| iHub Server 環境變數 | `X_INTERNAL_KEY`（值：`v9-internal-key-2026`） |
| Member 驗證方式 | `verifyIHubKey()`：接受 `services.infra.api_key` 或 `services.infra.callback_key` |

---

## 部署資訊

| 項目 | 值 |
|------|---|
| 前端檔案 | `iHub/public/sim-bill/index.html` |
| Server 路由 | `iHub/server/index.js` |
| 生產 URL | `https://ihub.tg25.win/sim-bill/?key=dev` |
| Server Port | `8083` |
| nginx proxy (API) | `/api/simulator/bill` → `http://127.0.0.1:8083` |
| nginx proxy (SSE) | `/api/simulator/events` → `http://127.0.0.1:8083` |
| nginx 靜態服務 | `/sim-bill/` → `iHub/public/sim-bill/` |
| MQTT 連線 | iHub Server 持久連線到 `mqtt.tg25.win:8883`（TLS） |
| MQTT 訂閱主題 | `kiosk/{chip_id}/cmd` |
| SSE 推送 | 將 MQTT 指令透過 SSE 推給前端 |

---

### 11. iHub 前端 → iHub Server（發送 MQTT 指令）

iHub 前端的 `continueExchange()` 需要發送 MQTT `enable` 指令給 sim-bill，透過此端點。

| 項目 | 值 |
|------|---|
| 方法 | `POST` |
| 路徑 | `/api/simulator/command` |
| Header | `Content-Type: application/json` |

Request Body：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `action` | string | `"enable"` / `"disable"` / `"stack"` / `"reject"` |

行為：iHub Server 透過 MQTT 發送 `kiosk/{chip_id}/cmd` 指令。

回應：`{"success": true}`

---

## 已知問題記錄

| 日期 | 問題 | 狀態 |
|------|------|------|
| 2026-05-08 | WebSocket 頻道用 `engineering.{id}` 而非 `kiosk.{id}` | ✅ 已修正 |
| 2026-05-08 | `.MemberBoundToKiosk` 檢查 `event.result` 而非 `event.status` | ✅ 已修正 |
| 2026-05-09 | localStorage key 不一致（`sim_node_id` vs `sim_kiosk_id`） | ✅ 已修正 |
| 2026-05-09 | `saveConfig()` 更新 `Config.kioskId` 而非 `Config.nodeId` | ✅ 已修正 |
| 2026-05-09 | 依賴 WebSocket `infra.cmd` 而非 MQTT，與真實韌體不一致 | ✅ 已修正（v4 改用 MQTT → SSE） |
