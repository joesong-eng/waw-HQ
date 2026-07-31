# wawOwner 即時數據流 (Realtime Data Flow) 規格與實作分析

**Agent**: Sophie
**專案**: Owner (iot.tg25.win)
**最後更新**: 2026-07-14

本文件詳細記錄 `https://iot.tg25.win/realtime` 即時數據流的完整鏈路，涵蓋初始設備列表載入、Infra 接收 Webhook 到前端 WebSocket 廣播的所有明確規格（不含猜測與未來擴充）。

> **HQ 2026-07-14 補充裁定**：`/realtime` 頁面一進入時，必須先由 DB/API 載入所有可監控設備並渲染卡片。Reverb / WebSocket 只負責補即時數據與狀態，不得作為設備列表來源。

---

## 1. 初始設備列表載入

Realtime 頁面的第一責任是讓使用者立即看到「目前有哪些設備」。因此頁面載入時必須先撈 DB 中已存在、已綁定或可監控的設備列表，並先渲染卡片框架。

### 實際頁面載入順序

```text
GET https://iot.tg25.win/realtime
→ auth / iot.access
→ routes/web.php closure
→ resources/views/iot/realtime.blade.php
→ Alpine init()
→ fetchInitialData()
→ GET /api/v9/realtime/devices?periodStart=...
→ Api\V9\RealtimeController@getDevices
→ 前端先渲染所有設備卡片
```

初始卡片的即時數值可以是 `0`、`-`、`unknown` 或 `waiting`，但設備卡片本身必須先出現。使用者不應因為 MQTT / Reverb 尚未收到事件而看不到設備。

### 資料來源分工

| 資料 | 正確來源 | 說明 |
|---|---|---|
| 設備列表 | DB / `/api/v9/realtime/devices` | 一進頁面立即載入 |
| 設備名稱、場地、類型 | DB | 靜態或低頻資料 |
| `coin_in_count`、`payout_count` | DB 初始值 + Reverb 後續更新 | 即時欄位 |
| online / offline 狀態 | Infra 狀態 API + Reverb 後續更新 | 即時狀態 |
| timeline event | Reverb | 即時事件 |

### 禁止的設計

```text
等待 Reverb device.updated
→ 收到事件才建立設備卡片
```

Reverb 事件只能用 `device_id` / `chip_id` 找到既有卡片並更新，不應承擔設備清單建立責任。

---

## 2. 接收來自 Infra 的 Webhook

- **Endpoint**: `POST /api/internal/broadcast/device-update`
- **安全驗證**: 必須包含 Header `X-Internal-Key`。
- **Payload 結構**:

```json
{
  "device_id": "sr9adyxpdyt1tuf7",  
  "data": {
    "coin_in_count": 116607,
    "payout_count": 48273,
    "status": "online",
    "timestamp": 1707500000
  }
}
```

**Owner 後端實際解析與處理的欄位**：
- `device_id`: 必填字串，對應資料庫的 `chip_id`。
- `data.coin_in_count`: 若存在，進行脈衝轉換並寫入 DB。
- `data.payout_count`: 若存在，進行脈衝轉換並寫入 DB。
- `data.status`: 若存在且為 `'online'`，判定為在線並更新最後出沒時間。
- `data.timestamp` / `data.alarm_count` / `data.alarm_type`: 若存在，僅做保留，用於 WebSocket 廣播。

### ⚠️ 異常流程處理 (Error Handling)
1. **Header 密鑰驗證失敗**：
   當 Header 中的 `X-Internal-Key` 缺失或與配置密鑰不符時，`VerifyInternalKey` 中間件（或 `BroadcastController`）將拒絕訪問並回傳 **`401 Unauthorized`** 狀態碼，伴隨以下 JSON Payload：
   ```json
   {
       "error": "Unauthorized",
       "message": "Invalid internal API key"
   }
   ```
2. **Payload 格式有誤 (遺失關鍵欄位)**：
   若請求中缺失 `device_id`，後端將直接中斷處理，並回傳 **`400 Bad Request`** 狀態碼，伴隨以下 JSON：
   ```json
   {
       "error": "Missing device_id"
   }
   ```
3. **設備未註冊**：
   若傳入的 `device_id` 在 `devices` 表中找不到對應的 `chip_id`，後端會判定為未知設備並安靜跳過。為避免造成發送端（Infra）判定失敗而進入重試風暴，此時會回傳 **`200 OK`**，但 JSON Payload 中會標明跳過原因：
   ```json
   {
       "status": "skipped",
       "reason": "device_not_registered"
   }
   ```

---

## 3. 寫入資料庫 (iotv9)

收到 Webhook 後，`BroadcastController` 確定會對 `devices` 表執行以下寫入：
- 若收到 `data.coin_in_count`，則更新 `lifetime_credit_in` = `data.coin_in_count`。
- 若收到 `data.payout_count`，則更新 `lifetime_credit_out` = `data.payout_count`。
- 若收到 `data.status`，則更新 `last_seen_at` = 伺服器當前時間 (`now()`)。

> **注意**：`devices` 資料表中的 `is_online` 欄位已被 Infra 移除，目前在線狀態統一由 Infra 的 Redis 管理，Owner 不再將在線狀態寫入關聯式資料庫。
>
> **2026-07-14 查證差異**：目前初始列表實作讀取 `Machine`，但 Internal broadcast 寫入 `Device`。此為資料來源不一致風險，修復時需統一。

---

## 4. 發送 WebSocket 廣播 (Laravel Reverb)

- **Channel**: `realtime`
- **Event**: `.device.updated`

後端處理完資料庫更新後，會組合出新的 Payload 廣播出去，精確結構如下：
- `device_id`: 字串 (chip_id)
- `data`: 物件，內容**僅包含本次有變動或由 Infra 傳來的欄位**：
  - `coin_in_count` (若本次更新)
  - `payout_count` (若本次更新)
  - `status` (若本次更新)
  - `today_revenue` (若有更新投幣數據，後端重新計算得出)
  - `timestamp`, `alarm_count`, `alarm_type` (若 Infra 有傳即原封不動附上)
  - `validation_warnings`, `monitoring_alerts` (若後端驗證或監控發現異常)

### ⚙️ 同步與非同步處理效能機制 (Performance & Queue)
- **同步 DB 寫入**：本地資料庫寫入（更新 `last_seen_at` 且必要時累加 `lifetime_credit_in`/`out`）是在 Webhook 接收時**同步 (Synchronous)** 進行，保證資料的高一致性與即時性。
- **目前線上 runtime（2026-07-14 查證）**：`DeviceUpdated` 採用 `ShouldBroadcast`，broadcast driver 為 `reverb`，但 `QUEUE_CONNECTION=sync`。因此目前事件實際在 HTTP request 中同步廣播，並非背景 queue。
- **待 HQ 裁定**：若要改成非同步 queue，必須同步建立 queue worker health check、失敗告警與重送策略；若保留 sync，必須接受 Internal API latency 與 Reverb 故障被吞掉的風險。

---

## 5. 前端頁面接收與顯示 (Realtime 儀表板)

- **頁面位置**: `resources/views/iot/realtime.blade.php`

前端載入後先用 `/api/v9/realtime/devices?periodStart=...` 產生設備列表，再訂閱 `realtime` 頻道的 `.device.updated` 事件。

前端訂閱 `realtime` 頻道的 `.device.updated` 事件，並**僅針對以下欄位作動**：
- `data.command_type`: 若存在（來自於系統主動下發指令，如開洗分），在 Timeline 新增一筆指令紀錄。
- `data.coin_in_count`: 若存在，前端將計算 `(coin_in_count * pulse_ratio) - 舊餘額`，動態增加該卡片的「今日入金」，並在 Timeline 插入一筆「入金」紀錄。
- `data.status`: 若存在，切換卡片 UI 的綠燈（連線）或灰暗（斷線），並在 Timeline 插入一筆「ONLINE / OFFLINE」紀錄。

> **前端忽略的資料**：目前前端沒有針對 WebSocket 傳來的 `payout_count`、`alarm_count`、`alarm_type` 撰寫任何 UI 變更或 Timeline 紀錄邏輯，這些欄位目前會被直接忽略。

### 🔄 前端斷線自動重連機制 (Reconnection)
- **Echo 與 Pusher 核心**：前端採用 `laravel-echo` 搭配 `pusher-js` 核心來訂閱 `realtime` 頻道。
- **自動重連**：`pusher-js` 內建非常強大且成熟的 **自動重連機制 (Automatic Reconnection)**。一旦偵測到連線中斷（如網路波動、伺服器重啟），會自動採用 **指數型回退演算法 (Exponential Backoff)** 嘗試重新連線（自 1 秒起逐步增加重連間隔，最高至 120 秒），過程中會自動保持頻道訂閱狀態，在連線恢復時重新綁定，無需手動刷新頁面或調用額外代碼，保證儀表板的 24 小時高可用性。

---

## 6. 實作查證來源

本文件於 2026-07-14 根據 Sophie 任務 `TASK_20260713_SOPHIE_VERIFY_REALTIME_FLOW_RETRY2` 更新。查證報告位置：

`/Users/ilawusong/Documents/sysWawIot/waw-core/_agent/REPORT_20260713_185021_TASK_20260713_SOPHIE_VERIFY_REALTIME_FLOW_RETRY2.md`

## 🔗 文件神經連結

### 強關聯

- `brains/knowledge/03_system_architecture_designs/REALTIME_MONITORING_PAGE_FLOW.md` - Realtime 頁面載入與資料來源分工權威規範。
- `brains/knowledge/02_protocols_and_standards/WEBSOCKET_CHANNEL_STANDARD.md` - WebSocket 頻道與事件命名規範。
- `brains/knowledge/02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - MQTT topic 與 payload 命名規範。
