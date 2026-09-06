# Realtime 即時監控頁流程規範

> **版本**: 1.0.0  
> **建立日期**: 2026-07-14  
> **狀態**: Active / Authoritative  
> **維護者**: HQ  
> **讀取策略**: On-Demand  

本文件定義 `https://iot.tg25.win/realtime` 即時監控頁的正確載入順序、資料來源分工與更新規則。後續任何 Agent 修改 realtime 頁面、WebSocket、Reverb、Infra broadcast 或設備列表 API 時，必須先讀本文件。

---

## 一、核心原則

### 1. DB 是設備列表來源

`/realtime` 頁面一載入，必須先從資料庫撈取所有可顯示、已存在、已綁定或可監控的設備，並立即渲染設備卡片。

初始卡片至少應包含：

| 欄位 | 來源 | 初始顯示 |
|---|---|---|
| 機器名稱 | DB | 實際名稱 |
| `chip_id` / `node_id` | DB | 實際 ID |
| 場地 | DB | 實際場地或未配置 |
| 機型 | DB | 實際類型 |
| 在線狀態 | DB / Infra 狀態 API | unknown / offline / online |
| 今日入金 | DB 初始統計或預設 | 0 |
| 出金 / 洗分 | DB 初始統計或預設 | 0 |
| 最後更新時間 | DB / Infra 狀態 API | `-` |

### 2. Reverb 不是設備列表來源

Reverb / WebSocket 事件只負責更新既有卡片的即時欄位，不負責建立設備清單。

禁止設計成：

```text
等待 device.updated 事件
→ 收到事件才建立設備卡片
```

正確設計是：

```text
DB/API 先產生完整設備卡片
→ Reverb 後續依 chip_id 更新卡片數值與狀態
```

### 3. `chip_id` 是即時更新定位鍵

Realtime 頁面收到 `.device.updated` 時，必須用事件 payload 的 `device_id`（實際為 `chip_id`）找到既有卡片並局部更新。

若收到未知 `chip_id`：

1. 不應直接建立不完整卡片。
2. 應記錄 warning 或提示「未知設備事件」。
3. 可選擇重新拉取 `/api/v9/realtime/devices`，但必須避免頻繁重刷。

---

## 二、實際載入順序

### 第一段：頁面載入

```text
GET https://iot.tg25.win/realtime
→ Laravel auth / iot.access
→ routes/web.php closure
→ resources/views/iot/realtime.blade.php
```

查證結果：`/realtime` 目前沒有 Controller，路由直接回 `iot.realtime` Blade。

### 第二段：初始化設備卡片

```text
Blade Alpine init()
→ fetchInitialData()
→ GET /api/v9/realtime/devices?periodStart=...
→ Api\V9\RealtimeController@getDevices
→ 回傳 DB 中可顯示設備
→ 前端先畫出所有設備卡片
```

此階段必須在沒有任何 Reverb 即時事件的情況下，也能讓 Joe 或店家看到「目前有哪些機器」。

### 第三段：建立即時通訊

```text
connectWebSocket()
→ Laravel Echo / Pusher.js
→ Reverb
→ channel: realtime
→ event: .device.updated
```

### 第四段：Infra 上送即時事件

```text
採集卡 / 模擬採集卡
→ MQTT device/{chip_id}/data 或舊相容 topic
→ Infra Listener
→ POST https://iot.tg25.win/api/internal/broadcast/device-update
→ VerifyInternalKey
→ InternalBroadcastController@deviceUpdate
```

Payload 範例：

```json
{
  "device_id": "sr9adyxpdyt1tuf7",
  "data": {
    "coin_in_count": 116607,
    "status": "online",
    "timestamp": 1707500000
  }
}
```

### 第五段：Owner 寫入與廣播

目前實作會更新：

| 欄位 | 寫入對象 |
|---|---|
| `coin_in_count` | `devices.lifetime_credit_in` |
| `payout_count` | `devices.lifetime_credit_out` |
| `status` | `devices.last_seen_at`，不寫 `is_online` |

然後觸發：

```text
DeviceUpdated implements ShouldBroadcast
→ channel: realtime
→ event: device.updated
→ frontend listens .device.updated
```

### 第六段：前端局部更新

前端收到事件後：

```text
用 device_id/chip_id 找既有卡片
→ 更新 coin_in_count / status / timeline
→ 不重新建立整張設備列表
```

目前已知限制：

| 欄位 | 現況 |
|---|---|
| `coin_in_count` | 前端有處理 |
| `status` | 前端有處理 |
| `payout_count` | 前端目前未處理 |
| `alarm_count` / `alarm_type` | 前端目前未處理 |

---

## 三、已查證的現況差異

Sophie 於 `TASK_20260713_SOPHIE_VERIFY_REALTIME_FLOW_RETRY2` 查證：

| 項目 | 查證結果 |
|---|---|
| 部署 HEAD | 本機與 yd174 均為 `01d7f4b` |
| `/realtime` route | `routes/web.php` closure，無 Controller |
| Blade | `resources/views/iot/realtime.blade.php` |
| 初始 API | `/api/v9/realtime/devices?periodStart=...` |
| API Controller | `Api\V9\RealtimeController@getDevices` |
| WebSocket | `realtime` / `.device.updated` |
| Internal webhook | `/api/internal/broadcast/device-update` |
| webhook Controller | `App\Http\Controllers\Api\InternalBroadcastController@deviceUpdate` |
| Broadcast event | `DeviceUpdated implements ShouldBroadcast` |
| Broadcast driver | `reverb` |
| Queue connection | `sync` |

### 需要 review 的差異

1. 文件曾記載 Reverb 廣播走非同步 queue；但線上 runtime 為 `QUEUE_CONNECTION=sync`，實際是同步廣播。
2. 初始列表目前讀 `Machine`，Internal broadcast 寫 `Device`，有資料來源不一致風險。
3. realtime UI 未處理 `payout_count` 與 alarm 欄位。
4. repo 存在未被路由使用的平行 BroadcastController，容易造成維護誤判。

---

## 四、修復方向原則

正式修復前，HQ 需先裁定以下事項：

1. **設備清單來源統一**：`/api/v9/realtime/devices` 應明確以 WAW 2.0 正式設備模型為準，並確保所有可監控設備一進頁面就出現。
2. **即時寫入來源統一**：Internal broadcast 寫入的模型需與初始列表來源一致，避免 `Machine` / `Device` 分叉。
3. **Reverb queue 策略**：選擇同步 broadcast 或非同步 queue；若改非同步，必須同時監控 queue worker health。
4. **前端事件處理補齊**：若後端會送 `payout_count`、alarm 欄位，前端必須消費；否則後端不要送無消費者欄位。

---

## 五、驗收標準

修復或重構 realtime 頁面時，至少需驗收：

1. 無 MQTT / 無 Reverb 事件時，頁面仍顯示所有 DB 可監控設備卡片。
2. 收到 `.device.updated` 後，只更新對應 `chip_id` 卡片。
3. 未知 `chip_id` 事件不會建立錯誤卡片，也不會讓頁面崩潰。
4. `coin_in_count`、`payout_count`、`status` 的 UI 行為與後端 payload 對齊。
5. queue / Reverb 故障時，有 log、告警或降級策略。

---

## 🔗 文件神經連結

### 強關聯

- `docs/sophie/realtime_data_flow.md` - Sophie Owner realtime 實作資料流。
- `02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - MQTT topic 與 payload 命名標準。
- `02_technical_standards/WEBSOCKET_CHANNEL_STANDARD.md` - WebSocket 頻道與事件規範。

### 中關聯

- `03_system_architecture/SYSTEM_ENTRYPOINTS_AND_DOMAINS.md` - 系統入口與域名分工。
- `05_business_flows/device_connectivity/DEVICE_CONNECTION_STATUS_FLOW.md` - 設備連線狀態流程。
- `03_system_architecture/V9_SYSTEM_SPLITTING_DESIGN.md` - 人與物拆分與即時事件聯動。

### 查證證據

- `/Users/ilawusong/Documents/sysWawIot/waw-core/_agent/REPORT_20260713_185021_TASK_20260713_SOPHIE_VERIFY_REALTIME_FLOW_RETRY2.md`
