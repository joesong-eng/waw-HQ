# Design Document — Signal Flow Monitor

> **版本**: 1.0.0
> **日期**: 2026-05-07
> **狀態**: 草稿，待審核
> **設計者**: HQ
> **對應 Requirements**: v1.1.0

---

## 1. 系統架構

Signal Flow Monitor 橫跨兩個系統，各自獨立實作：

**前端（Member，Alpine.js）**
- 嵌入現有工程頁面 `win.tg25.win/engineering/kiosk`（kiosk.blade.php）
- 使用現有 Alpine.js，不引入新框架
- 使用現有 Laravel Echo + Pusher.js 訂閱 WebSocket

**後端（Member，Laravel）**
- 新增 `EngineeringBroadcast` service class 集中管理所有廣播邏輯
- 新增 `EngineeringEvent` Broadcast event class
- 各 Controller 只需呼叫 `EngineeringBroadcast::emit()`，不在 Controller 裡直接廣播
- 新增兩條 API（詳見第 4 節）

**跨系統（需要 @Ina 配合）**
- Infra Listener 在 escrow/stacked/rejected webhook body 加入 `firmware_timestamp` 欄位
- Infra Listener 新增呼叫 `POST /internal/kiosk/status`（ba_state=IDLE 時）

---

## 2. 前端設計決策

### 2.1 Alpine.js Component

整個面板是一個 Alpine.js component `signalFlowMonitor()`，管理以下狀態：

- `selectedKioskId`：從頁面現有下拉框取得
- `chipId` / `nodeId`：從 `GET /api/kiosk/device-info` 動態載入
- `wsStatus`：WebSocket 連線狀態（connected / disconnected / connecting）
- `nodes`：所有節點的狀態 map（key = node identifier）
- `timings`：B1/B3/B4/B6 的 Event_Timestamp，用於計算四個時序量測值
- `banner`：全域警告 banner（投幣流程中斷時顯示）
- `expectedValues`：各節點的預期值 map，從 device-info API 動態建立

### 2.2 節點狀態

每個節點維護以下狀態：
- `lastSignalAt`：瀏覽器本地時間（用於計算相對時間戳和 timed_out 判斷）
- `lastEventTimestamp`：Event_Timestamp（用於時序量測）
- `fields`：各監聽欄位的最新值
- `alignment`：各欄位的比對結果（match / mismatch / unset）
- `visualState`：dormant / active / timed_out
- `specialLabel` / `specialColor`：Fail-Safe 退鈔等特殊狀態標籤

### 2.3 B7 節點處理

`firmware.stacked` 和 `firmware.rejected` 都對應 Node B7，前端根據收到的 node identifier 決定顯示哪個狀態，兩者共用同一個節點卡片位置。

### 2.4 B1 新 escrow 時的重置行為

收到新的 `firmware.escrow` 事件時：
1. 重置所有時序量測（B1/B3/B4/B6 timestamp 清空）
2. 清空 B2~B9 所有節點的 Field_Value（顯示 `—`）
3. B1 保留新收到的值

### 2.5 Expected_Values 動態載入

前端在訂閱 Engineering_Channel 時，呼叫 `GET /api/kiosk/device-info` 取得 `chip_id` 和 `node_id`，動態建立所有節點的 Expected_Value map。若 API 回傳 404，chip_id 相關欄位顯示 `—`（不設預期值）。

### 2.6 Mock 注入

`window.__sfm_inject(event)` 在工程頁面永遠啟用，供測試邊界條件用。

---

## 3. 後端設計決策

### 3.1 EngineeringBroadcast Service

集中管理廣播邏輯的原因：
- 避免廣播代碼散落在各個 Controller
- 統一處理 kiosk_id 為空時的靜默略過邏輯
- 統一處理廣播失敗不中斷主流程的邏輯

Service 提供三個方法：
- `emit($kioskId, $node, $data)`：廣播事件
- `getKioskIdBySession($sessionId)`：memberHeartbeat 用，查 session 取 kiosk_id
- `getKioskIdByMac($esp32Mac)`：kioskRejected 用，查 session 取 kiosk_id

### 3.2 各 Controller 廣播點

| Controller / Method | 廣播的 node 識別碼 |
|---------------------|------------------|
| `kioskHeartbeat` | `tablet.heartbeat`, `member.tablet_heartbeat` |
| `bind`（成功或失敗） | `member.bind` |
| `bind`（Infra MQTT 成功後） | `infra.enable` |
| `kioskStatus`（新路由） | `firmware.idle` |
| `kioskEscrow` | `firmware.escrow`（需 firmware_timestamp）, `infra.escrow`, `member.escrow_received` |
| `escrowConfirm` | `member.decision`（action: stack）, `infra.cmd`（action: stack） |
| `escrowReject` | `member.decision`（action: reject）, `infra.cmd`（action: reject） |
| `kioskStacked` | `firmware.stacked`（需 firmware_timestamp）, `firmware.cmd_received`（action: stack）, `infra.result`, `member.credited` |
| `kioskRejected` | `firmware.rejected`（需 firmware_timestamp）, `firmware.cmd_received`（action: reject）, `infra.result`, `member.noted` |
| `memberHeartbeat` | `member.heartbeat` |
| `KioskSession::terminate()` | `member.session_ended` |

### 3.3 kiosk_id 取得方式

部分觸發點的 context 裡沒有直接的 kiosk_id：
- `memberHeartbeat`：用 session_id 查 `kiosk_sessions.kiosk_id`
- `kioskRejected`：用 esp32_mac 查 active session 的 kiosk_id
- bind 失敗且 kiosk_id 無效（kiosk_unavailable）：靜默略過，不廣播

---

## 4. 新增 API

### 4.1 GET /api/kiosk/device-info（Member）

- **用途**：前端取得 kiosk 的 chip_id，用於動態建立 Expected_Values
- **認證**：Sanctum Bearer token（工程頁面已登入）
- **Request**：`?kiosk_id={kiosk_id}`
- **Response 200**：`{ "kiosk_id": "kiosk_000", "chip_id": "test-esp32", "node_id": "kiosk_000" }`
- **Response 404**：kiosk_id 不存在
- **實作**：Member 呼叫 Infra `GET /api/kiosk/info` 取得 esp32_mac，不直接查 Owner DB

### 4.2 POST /internal/kiosk/status（Member，新路由）

- **用途**：Infra Listener 通知 Member 韌體 ba_state 已變為 IDLE
- **認證**：X-Internal-Key
- **Request body**：`{ "chip_id": "...", "ba_state": "IDLE", "kiosk_id": "..." }`
- **Response 200**：`{ "status": "ok" }`
- **Member 動作**：廣播 `firmware.idle` 事件到 Engineering_Channel

---

## 5. Infra 需要的修改（@Ina）

### 5.1 webhook body 加入 firmware_timestamp

Infra Listener 在轉發以下 webhook 時，需要把韌體 MQTT payload 裡的 `timestamp` 欄位原樣帶入為 `firmware_timestamp`：
- `POST /internal/kiosk/escrow`
- `POST /internal/kiosk/stacked`
- `POST /internal/kiosk/rejected`

完整 webhook body 範例（以 escrow 為例）：
```json
{
  "kiosk_id": "kiosk_000",
  "esp32_mac": "test-esp32",
  "amount": 100,
  "event_id": "sim-123",
  "firmware_timestamp": 1713253800
}
```

### 5.2 新增呼叫 POST /internal/kiosk/status

Infra Listener 收到 `kiosk/{chip_id}/status` 且 `ba_state = IDLE` 時，呼叫 Member `POST /internal/kiosk/status`，payload 帶 `chip_id`、`ba_state`、`kiosk_id`（從 chip_id → node_id 對應取得）。

---

## 6. 實作順序

### Phase 1：後端廣播基礎（不需要跨系統）

1. 建立 `EngineeringEvent` class
2. 建立 `EngineeringBroadcast` service
3. 在各 Controller 加廣播（不需要 firmware_timestamp 的 10 個事件）
4. 新增 `GET /api/kiosk/device-info` API

### Phase 2：前端面板

5. 建立 Alpine.js `signalFlowMonitor()` component
6. 實作節點狀態管理、時序量測、視覺渲染
7. 嵌入工程頁面，用 mock 注入驗證

### Phase 3：跨系統整合（需要 @Ina 配合）

8. Ina：webhook body 加 `firmware_timestamp`
9. Ina：新增呼叫 `POST /internal/kiosk/status`
10. Mina：新增 `POST /internal/kiosk/status` 路由
11. Mina：補上需要 `firmware_timestamp` 的廣播（B1、B7）

### Phase 4：整合測試

12. 實機測試完整投幣流程
13. 驗證所有邊界條件（時鐘不同步、Fail-Safe 超時等）

---

## 7. 跨系統依賴清單

| 依賴 | 負責方 | Phase |
|------|--------|-------|
| escrow/stacked/rejected webhook body 加 `firmware_timestamp` | @Ina | 3 |
| 新增呼叫 `POST /internal/kiosk/status` | @Ina | 3 |
| 新增 `POST /internal/kiosk/status` 路由 | @Mina | 3 |
| 新增 `GET /api/kiosk/device-info` API | @Mina | 1 |

---

*設計者: HQ | 日期: 2026-05-07 | 版本: 1.0.0*
