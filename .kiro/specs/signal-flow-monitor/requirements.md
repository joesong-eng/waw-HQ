# Requirements Document

> **版本**: 1.1.0
> **日期**: 2026-05-07
> **狀態**: ✅ 審核完成（第十一輪），可以實作
> **設計者**: HQ
> **審核者**: Mina

---

## Introduction

Signal Flow Monitor 是一個嵌入在 `win.tg25.win/engineering/kiosk` 頁面的「通信流可視化面板」。

V9 系統橫跨韌體（ESP32）、MQTT、Infra（api.tg25.win）、Member（win.tg25.win）、iHub（ihub.tg25.win）五個系統，一條紙鈔機入帳流要經過 8+ 個節點。任何一個節點的名稱對不上（例如 `chip_id` 用錯、`kiosk_id` 格式不一致），整條流就斷掉，且完全沒有錯誤訊息，只能翻 log 一個一個查。

本 spec 只實作**第一條流：紙鈔機入帳流**，驗證概念後再擴展。**擴展方式**：在同一個 Engineering_Channel 加入新的 node 識別碼前綴（例如 `game.*` 代表遊戲機流），前端 Signal_Flow_Monitor 根據 node 前綴決定顯示在哪條流，不需要新增頻道。

資料來源全部走 Member WebSocket（Laravel Reverb），Member 後端在每個關鍵事件時廣播 WebSocket 事件到 `engineering.{kiosk_id}` 頻道，前端訂閱後即時更新面板。

---

## Glossary

- **Signal_Flow_Monitor**：通信流可視化面板，本功能的主體元件
- **Node**：通信流中的一個處理節點（例如「Infra Listener」、「Member 裁決」）
- **Side_Monitor_Node**：不在主流程箭頭上的側邊監控節點，顯示在相關主節點旁邊，不影響主流程視覺
- **Pulse_Light**：脈衝燈，節點收到訊號時亮起、慢慢暗掉的視覺指示器
- **Field_Value**：節點收到的訊號中帶有的實際名稱值（例如 `chip_id: test-esp32`）
- **Expected_Value**：工程師預先設定的預期值，用於與 Field_Value 比對
- **Dynamic_Field**：每次值不同的欄位（如 `amount`、`tokens_credited`），不設 Expected_Value，顯示為灰色（⚫）
- **Alignment_Status**：Field_Value 與 Expected_Value 的比對結果（吻合 / 不符 / 未設定）
- **Timeout_Threshold**：節點超過此時間無訊號即視為斷線，預設 30 秒
- **Failsafe_Window**：韌體 escrow 後等待雲端指令的最大時間，固定 15 秒（依據 `phase_5_bill_flow.md`：Hold 機制可延長 Escrow 到 5 分鐘，雲端裁決時限設計為 15 秒）
- **Engineering_Channel**：Member WebSocket 頻道，格式為 `engineering.{kiosk_id}`（全小寫）
- **WebSocket_Event**：Member 後端廣播到 Engineering_Channel 的標準格式事件
- **Event_Timestamp**：WebSocket_Event payload 中的 `timestamp` 欄位，為 Unix 秒，由廣播方在事件發生當下記錄，用於時序量測（非瀏覽器本地時間）。各節點 timestamp 來源：Node B1 用韌體 MQTT payload 裡的 `timestamp` 欄位（由 Infra 在 escrow webhook body 中原樣帶入）；Node B6 用 Member 收到 stacked/rejected webhook 時的伺服器時間；其餘節點用 Member 廣播當下的伺服器時間
- **Bill_Acceptor_Flow**：紙鈔機入帳流，本 spec 唯一實作的通信流
- **Kiosk_ID**：兌幣機識別碼，格式為 `kiosk_000`（全小寫）
- **Chip_ID**：ESP32 韌體識別碼，格式為 MAC address 小寫無冒號，例如 `test-esp32`（測試用）
- **Node_ID**：Infra Listener 內部對應的兌幣機識別碼，應與 Kiosk_ID 一致
- **Member_Backend**：`win.tg25.win` Laravel 後端，負責廣播 WebSocket 事件
- **Engineering_Page**：`win.tg25.win/engineering/kiosk` 工程測試頁面

---

## Requirements

### Requirement 1：通信流面板嵌入工程頁面

**User Story:** As an engineer, I want a signal flow visualization panel on the engineering page, so that I can see the bill acceptor flow at a glance without digging through logs.

#### Acceptance Criteria

1. THE Signal_Flow_Monitor SHALL be displayed on the Engineering_Page as a new panel section, without modifying any existing functionality on the page.
2. THE Signal_Flow_Monitor SHALL display the Bill_Acceptor_Flow with all nodes arranged in the correct sequence as defined in Requirement 2.
3. WHEN the Engineering_Page loads, THE Signal_Flow_Monitor SHALL initialize in a dormant state with all nodes shown in grey.
4. THE Signal_Flow_Monitor SHALL subscribe to the Engineering_Channel corresponding to the currently selected Kiosk_ID on the Engineering_Page. WHEN no Kiosk_ID is selected（下拉框顯示「-- 請選擇綁定組合 --」），THE Signal_Flow_Monitor SHALL display a prompt "請先選擇綁定組合" and SHALL NOT subscribe to any channel or call `GET /api/kiosk/device-info`.
5. WHEN the selected Kiosk_ID changes on the Engineering_Page, THE Signal_Flow_Monitor SHALL unsubscribe from the previous Engineering_Channel and subscribe to the new one.

---

### Requirement 2：紙鈔機入帳流節點定義

**User Story:** As an engineer, I want to see all nodes of the bill acceptor flow in the correct order, so that I can identify exactly which node in the chain is broken. Each node represents an independent role (Delegate concept) — sender and receiver are separate nodes, displayed as pairs so engineers can immediately spot "sent but not received" breakpoints.

#### Acceptance Criteria

1. THE Signal_Flow_Monitor SHALL display the Bill_Acceptor_Flow in two sections: **掃碼綁定段** and **投幣入帳段**。

   **掃碼綁定段**（階段 0–1）主流程節點（線性，有箭頭連接）：
   - Node A1: `iHub 平板心跳` — 監聽欄位：`kiosk_id`（代表 iHub 角色有在發送）
   - Node A2: `Member 後台（心跳）` — 監聽欄位：`kiosk_id`（代表 Member 角色有收到，與 A1 成對顯示）
   - Node A3: `會員掃碼 bind` — 監聽欄位：`kiosk_id`、`result`
   - Node A4: `Infra enable cmd` — 監聽欄位：`chip_id`、`action`
   - Node A5: `韌體 IDLE` — 監聽欄位：`ba_state`、`chip_id`

   **掃碼綁定段** Side_Monitor_Node（不在主流程箭頭上，顯示在 A3 旁邊）：
   - Node A6: `會員手機心跳` — 監聽欄位：`member_id`（掃碼成功後才啟動監控，詳見 Requirement 9）

   **投幣入帳段**（階段 2–4）主流程節點（線性，有箭頭連接）：
   - Node B1: `韌體 escrow` — 監聽欄位：`chip_id`、`amount`（Dynamic_Field）（代表韌體角色有發出，Member 收到 escrow webhook 後用 webhook body 中的韌體 timestamp 廣播）
   - Node B2: `Infra Listener（escrow）` — 監聽欄位：`chip_id`、`node_id`（代表 Infra 角色有收到，與 B1 成對）
   - Node B3: `Member webhook（escrow）` — 監聽欄位：`chip_id`、`amount`（Dynamic_Field）（代表 Member 收到 escrow webhook 的時間點）
   - Node B4: `Member 裁決` — 監聽欄位：`action`（`stack` 或 `reject`）（代表 Member 完成裁決的時間點，B3→B4 的耗時即查 session + 計算 token_rate 的時間）
   - Node B5: `Infra MQTT（cmd）` — 監聽欄位：`action`（代表 Infra 角色有發出）
   - Node B6: `韌體收到 cmd` — 監聽欄位：`action`（代表韌體角色有收到，與 B5 成對。**B6 為推算節點**：韌體不回報收到確認，B6 的訊號由 B7 事件到達時同時廣播，timestamp 用韌體事件的 timestamp，代表韌體已收到並執行 cmd）
   - Node B7: `韌體回報結果` — 監聽欄位：`event_type`（`stacked` 或 `rejected`）、`amount`（Dynamic_Field）、`reason`（退鈔時：`rejected_by_server` / `timeout`）
   - Node B8: `Infra Listener（結果）` — 監聽欄位：`chip_id`、`event_type`
   - Node B9: `Member 入帳 / 記錄退鈔` — 監聽欄位：`result`（`credited` / `noted`）、`tokens_credited`（Dynamic_Field，入帳時）

2. THE Signal_Flow_Monitor SHALL display directed arrows between consecutive main flow nodes to represent the signal flow direction. Side_Monitor_Nodes SHALL NOT have arrows connecting them to the main flow.
3. THE Signal_Flow_Monitor SHALL display each Node's label as a fixed, non-editable text.
4. WHEN Node B4 (`Member 裁決`) receives `action: reject`, THE Signal_Flow_Monitor SHALL immediately visually indicate the reject path by turning the arrows from B4 onward through B5, B6, B7 to **amber color**（深黃，與節點的 yellow 區分）. WHEN Node B7 subsequently receives `reason: timeout` (orange), THE Signal_Flow_Monitor SHALL update the arrow color from amber to orange to match Node B7's state.
5. WHEN Node B7 receives `event_type: rejected` with `reason: timeout`, THE Signal_Flow_Monitor SHALL display the node in orange with label "⏰ Fail-Safe 退鈔".
6. WHEN Node B7 receives `event_type: rejected` with `reason: rejected_by_server`, THE Signal_Flow_Monitor SHALL display the node in yellow with label "↩️ 伺服器退鈔".
7. WHEN Node B7 receives `event_type: stacked`, THE Signal_Flow_Monitor SHALL display the node in green with label "✅ 收鈔成功".

---

### Requirement 3：掃碼綁定結果顯示

**User Story:** As an engineer, I want to see the result of the QR code scan and bind operation, so that I can verify the session was established correctly before testing the bill flow.

#### Acceptance Criteria

1. WHEN Node A3 (`會員掃碼 bind`) receives a WebSocket_Event, THE Signal_Flow_Monitor SHALL display the bind result based on the `result` and `error` field values:
   - `result: success` → 綠色，顯示 `kiosk_id` 值
   - `result: 409`, `error: kiosk_busy` → 紅色，顯示「機台使用中」
   - `result: 503`, `error: tablet_offline` → 紅色，顯示「平板離線」（判斷標準：`kiosk_sessions.last_active_at` 超過 120 秒，需 Mina 在 bind 邏輯加入此檢查）
   - `result: 422`, `error: qr_expired` → 紅色，顯示「QR Code 已過期」
   - `result: 422`, `error: kiosk_unavailable` → 紅色，顯示「兌幣卡離線」
2. WHEN Node A3 shows a non-success result, THE Signal_Flow_Monitor SHALL display the Node border in red and stop the flow visualization at that node (nodes A4, A5 remain grey and SHALL NOT respond to any subsequent WebSocket_Events until A3 receives a new `result: success` event).
3. WHEN Node A3 subsequently receives a new `result: success` event (re-scan), THE Signal_Flow_Monitor SHALL clear the error state on A3 (border returns to default color, result field updates to `success`) and restore A4, A5 to their normal dormant (grey) state with all Field_Values reset to `—` (em dash), ready to receive new signals.
4. WHEN Node A5 (`韌體 IDLE`) receives `ba_state: IDLE`, THE Signal_Flow_Monitor SHALL display the node in green to confirm the bill acceptor is ready.
5. WHEN Node A5 does not receive a signal within 10 seconds after Node A4 fires（計時以瀏覽器本地時間為準，從前端收到 A4 的 WebSocket_Event 起計算），THE Signal_Flow_Monitor SHALL display a warning on Node A5 showing "⚠️ 未收到 IDLE 確認". WHEN Node A5 subsequently receives `ba_state: IDLE`, THE Signal_Flow_Monitor SHALL remove the warning.

---

### Requirement 4：脈衝燈行為

**User Story:** As an engineer, I want each node to flash when it receives a signal, so that I can see in real time which nodes are active.

#### Acceptance Criteria

1. WHEN a Node receives a WebSocket_Event, THE Pulse_Light of that Node SHALL immediately illuminate.
2. WHEN a Pulse_Light illuminates, THE Signal_Flow_Monitor SHALL transition the Pulse_Light from bright to dim over a 2-second CSS transition.
3. WHEN a Node has not received any WebSocket_Event for longer than the Timeout_Threshold, THE Signal_Flow_Monitor SHALL display that Node in a "timed out" visual state (grey background, dimmed text). **測試邊界條件**：「timed out」狀態由 AC5 的時間戳計算觸發，當時間戳超過 Timeout_Threshold 時切換視覺狀態；時間戳本身從收到訊號起就持續顯示（見 AC5）。
4. WHEN a Node has never received any WebSocket_Event since the panel was loaded, THE Signal_Flow_Monitor SHALL display that Node in grey without a timestamp.
5. THE Signal_Flow_Monitor SHALL display a relative timestamp (e.g., "剛剛", "5 秒前") below each Node's Pulse_Light **from the moment a signal is received, continuously updated every second**. WHEN a Node transitions to "timed out" state (AC3), the timestamp continues to update (e.g., "35 秒前", "2 分前"). The distinction is: AC3 controls the visual state (grey/dimmed), AC5 controls the timestamp display (always shown once a signal has been received).

---

### Requirement 5：欄位值顯示

**User Story:** As an engineer, I want to see the actual field values carried in each signal, so that I can verify the correct identifiers are being passed between systems.

#### Acceptance Criteria

1. WHEN a Node receives a WebSocket_Event, THE Signal_Flow_Monitor SHALL display the Field_Value for each monitored field of that Node.
2. THE Signal_Flow_Monitor SHALL display each monitored field as a key-value pair in the format `{field_name}: {value}` within the Node card.
3. WHEN a Node has not yet received any WebSocket_Event, THE Signal_Flow_Monitor SHALL display each monitored field value as `—` (em dash).
4. THE Signal_Flow_Monitor SHALL retain and display the most recently received Field_Value for each Node until a new WebSocket_Event updates it.

---

### Requirement 6：名稱對齊比對

**User Story:** As an engineer, I want to see whether the field values match the expected values, so that I can immediately spot mismatches that break the flow.

#### Acceptance Criteria

1. THE Signal_Flow_Monitor SHALL compare each received Field_Value against its corresponding Expected_Value for the selected Kiosk_ID.
2. WHEN a Field_Value matches its Expected_Value, THE Signal_Flow_Monitor SHALL display that field in green (🟢) to indicate alignment.
3. WHEN a Field_Value does not match its Expected_Value, THE Signal_Flow_Monitor SHALL display that field in red (🔴) to indicate a mismatch.
4. WHEN no Expected_Value is configured for a field, THE Signal_Flow_Monitor SHALL display that field in grey (⚫) without a comparison indicator. Dynamic_Fields（如 `amount`、`tokens_credited`）因每次值不同，不設 Expected_Value，一律顯示為灰色（⚫）。
5. THE Signal_Flow_Monitor SHALL use the following Expected_Values for the selected Kiosk_ID. **Expected_Values 為動態設定**：前端在訂閱 Engineering_Channel 時，呼叫 `GET win.tg25.win/api/kiosk/device-info?kiosk_id={kiosk_id}`（**Member API**，使用現有 Sanctum Bearer token 認證；Response：`{ "kiosk_id": "kiosk_000", "chip_id": "test-esp32", "node_id": "kiosk_000" }`；若 kiosk_id 不存在回傳 404，前端顯示 chip_id 為 `—`）取得對應的 `chip_id`（即 `esp32_mac`），並以此更新所有節點的 `chip_id` Expected_Value。以下為 Kiosk_ID `kiosk_000`（`chip_id: test-esp32`）的預設設定範例：

   **掃碼綁定段：**
   - Node A1 `iHub 平板心跳` → `kiosk_id: kiosk_000`
   - Node A2 `Member 後台（心跳）` → `kiosk_id: kiosk_000`
   - Node A3 `會員掃碼 bind` → `kiosk_id: kiosk_000`, `result: success`
   - Node A4 `Infra enable cmd` → `chip_id: test-esp32`, `action: enable`
   - Node A5 `韌體 IDLE` → `ba_state: IDLE`, `chip_id: test-esp32`

   **投幣入帳段：**
   - Node B1 `韌體 escrow` → `chip_id: test-esp32`（`amount` 為 Dynamic_Field，不設預期值）
   - Node B2 `Infra Listener（escrow）` → `chip_id: test-esp32`, `node_id: kiosk_000`
   - Node B3 `Member webhook（escrow）` → `chip_id: test-esp32`（`amount` 為 Dynamic_Field，不設預期值）
   - Node B4 `Member 裁決` → `action` 不設預期值（⚫）。`stack` 和 `reject` 均為合法裁決結果，reject 路徑由 R2 AC4 的黃色箭頭視覺呈現，不以紅燈表示錯誤
   - Node B5 `Infra MQTT（cmd）` → `action` 不設預期值（⚫），值跟隨 B4 裁決結果
   - Node B6 `韌體收到 cmd` → `action` 不設預期值（⚫），值跟隨 B4 裁決結果
   - Node B7 `韌體回報結果` → `event_type` 不設預期值（⚫），值跟隨 B4 裁決結果（`stacked` 或 `rejected`）；`amount` 為 Dynamic_Field，不設預期值
   - Node B8 `Infra Listener（結果）` → `chip_id: test-esp32`；`event_type` 不設預期值（⚫），值跟隨 B4 裁決結果
   - Node B9 `Member 入帳 / 記錄退鈔` → `result: credited`（`tokens_credited` 為 Dynamic_Field，不設預期值）

6. IF a Field_Value is received and the Expected_Value comparison results in a mismatch, THEN THE Signal_Flow_Monitor SHALL highlight the Node border in red to make the mismatch visible at a glance.

---

### Requirement 7：節點斷線與 Fail-Safe 偵測

**User Story:** As an engineer, I want to see which nodes have gone silent and whether a Fail-Safe timeout occurred, so that I can identify where the flow is broken and whether the bill was returned to the user.

#### Acceptance Criteria

1. WHEN a Node has not received any WebSocket_Event for longer than the Timeout_Threshold (30 seconds), THE Signal_Flow_Monitor SHALL display that Node in a "timed out" visual state (grey background, dimmed text).
2. WHEN a Node is in the "timed out" state and receives a new WebSocket_Event, THE Signal_Flow_Monitor SHALL immediately restore the Node to its active visual state.
3. THE Signal_Flow_Monitor SHALL display the time elapsed since the last signal for each Node that is in the "timed out" state, updated every second.
4. WHEN Node B1 has previously received at least one signal AND **all nodes from B2 to B9** have been silent for longer than the Timeout_Threshold（即 B1 收到訊號後，後續所有節點超過 30 秒無訊號），THE Signal_Flow_Monitor SHALL display a banner above the flow indicating "⚠️ 投幣流程可能已中斷". **測試條件**：B1 收到訊號後，等待 30 秒且 B2~B9 均無訊號，banner 出現；B1 本身是否超時不影響此條件。
5. WHEN Node B1 (`韌體 escrow`) receives a signal but Node B4 (`Member 裁決`) has not received a signal within 10 seconds, THE Signal_Flow_Monitor SHALL display a warning indicator on Node B4 showing "⚠️ 接近超時"（10 秒 = Failsafe_Window 的 2/3，提前預警讓工程師有時間觀察）. WHEN Node B4 subsequently receives a signal, THE Signal_Flow_Monitor SHALL immediately remove the warning indicator. Note: this warning is displayed on Node B4 only; the timing bar in Requirement 8 provides the precise elapsed time display — engineers should refer to R8 for exact numbers and R7 AC5 for the node-level visual alert.
6. WHEN Node B7 receives `event_type: rejected` with `reason: timeout`, THE Signal_Flow_Monitor SHALL display "⏰ Fail-Safe 退鈔" on Node B7 in orange.
7. WHEN Node B7 receives `event_type: rejected` with `reason: rejected_by_server`, THE Signal_Flow_Monitor SHALL display "↩️ 伺服器退鈔" on Node B7 in yellow.

---

### Requirement 8：時序量測顯示

**User Story:** As an engineer, I want to see how long each critical step takes, so that I can identify performance bottlenecks (including Member's internal query time for session lookup and token rate calculation), and verify the system is within the 15-second Fail-Safe deadline.

#### Acceptance Criteria

1. THE Signal_Flow_Monitor SHALL calculate elapsed time between nodes using the Event_Timestamp field from each WebSocket_Event payload（Unix 秒，由廣播方記錄，非瀏覽器本地時間），以避免網路延遲造成的量測誤差。
   - 注意：Node B1 的 Event_Timestamp 來自韌體事件的 `timestamp` 欄位（由 Infra 在 escrow webhook body 中帶入），Node B6 的 Event_Timestamp 來自伺服器時鐘，兩者時鐘來源不同（ESP32 NTP vs 伺服器時鐘），可能有 1~3 秒偏差。
   - WHEN the calculated elapsed time between B1 and B6 is negative or exceeds 10 seconds, THE Signal_Flow_Monitor SHALL display "⚠️ 時鐘不同步" instead of the abnormal elapsed time value.
2. THE Signal_Flow_Monitor SHALL measure and display the elapsed time between the following critical node pairs:
   - Node B1 (`韌體 escrow`) → Node B4 (`Member 裁決`): 顯示「裁決耗時：X.Xs」
   - Node B3 (`Member webhook 收到`) → Node B4 (`Member 裁決`): 顯示「查詢耗時：X.Xs」（查 session + token_rate 的時間）
   - Node B4 (`Member 裁決`) → Node B6 (`韌體收到 cmd`): 顯示「指令送達：X.Xs」
   - Node B1 (`韌體 escrow`) → Node B6 (`韌體收到 cmd`): 顯示「總耗時：X.Xs / 15s」
3. WHEN the total elapsed time from Node B1 to Node B6 exceeds 10 seconds, THE Signal_Flow_Monitor SHALL display the elapsed time in orange as a warning.
4. WHEN the total elapsed time from Node B1 to Node B6 exceeds 15 seconds, THE Signal_Flow_Monitor SHALL display the elapsed time in red indicating the Fail-Safe deadline was missed.
5. THE Signal_Flow_Monitor SHALL reset all elapsed time measurements when a new escrow event is received at Node B1. **同時清空 B2~B9 所有節點的 Field_Value（顯示 `—`），B1 保留新收到的值**，確保時序量測和欄位顯示都對應同一次投幣事件。

---

### Requirement 9：會員手機心跳節點

**User Story:** As an engineer, I want to see whether the member's phone is still connected after scanning, so that I can distinguish between a broken flow and a member who simply closed the app.

#### Acceptance Criteria

1. THE Signal_Flow_Monitor SHALL display Node A6 `會員手機心跳` as a Side_Monitor_Node displayed beside Node A3, with monitored field: `member_id`. Node A6 is NOT connected to the main flow arrows.
2. BEFORE Node A3 (`會員掃碼 bind`) receives a `result: success` event, THE Signal_Flow_Monitor SHALL display Node A6 in grey without any warning — the absence of heartbeat before bind is expected and normal. **（Negative test：頁面載入後不掃碼，等待超過 90 秒，確認 A6 不出現「⚠️ 會員可能已離線」警告）**
3. WHEN Node A3 receives `result: success`, THE Signal_Flow_Monitor SHALL begin monitoring Node A6 for heartbeat signals.
4. WHEN Node A6 receives a WebSocket_Event after a successful bind, THE Signal_Flow_Monitor SHALL display the Pulse_Light and the `member_id` value.
5. WHEN Node A6 has not received any signal for longer than 90 seconds **after Node A3 receives `result: success`**（從掃碼成功時起計時，不是從第一次心跳起計時）, THE Signal_Flow_Monitor SHALL display Node A6 with label "⚠️ 會員可能已離線". (依據：會員心跳 API `POST /api/kiosk/session/{id}/heartbeat` 預期前端每 30 秒打一次；90 秒 = 3 個心跳週期未收到才告警，避免掃碼後第一次心跳尚未到達時誤報)
6. WHEN Node A6 subsequently receives a heartbeat signal, THE Signal_Flow_Monitor SHALL remove the warning and restore the node to its active state.
7. WHEN the session ends (Member 廣播 `member.session_ended` 事件到 Engineering_Channel，詳見 R10 AC3 表格), THE Signal_Flow_Monitor SHALL reset Node A6 to its initial grey state and stop monitoring, so that the "⚠️ 會員可能已離線" warning does not appear after a normal session end.

---

### Requirement 10：Member 後端 WebSocket 事件廣播

**User Story:** As an engineer, I want the Member backend to broadcast a standardized WebSocket event for each key node in the bill acceptor flow, so that the frontend panel can receive and display real-time signal data.

#### Acceptance Criteria

1. THE Member_Backend SHALL broadcast a WebSocket_Event to the Engineering_Channel (`engineering.{kiosk_id}`) for each of the following trigger points. **廣播頻道的 `kiosk_id` 取得方式**：若 context 中沒有直接的 `kiosk_id`，依以下方式取得：
   - `memberHeartbeat`（A6）：用 `session_id` 查 `kiosk_sessions.kiosk_id`（一次額外 DB 查詢）
   - `kioskRejected`（B7 rejected）：用 `esp32_mac` 查 `kiosk_sessions.kiosk_id`（補查 session）
   - 若 `kiosk_id` 無效或查不到，**靜默略過，不廣播**，記錄 log

   觸發點清單：
   - iHub 平板心跳收到時
   - 會員掃碼 bind 完成時（成功或失敗；若 `kiosk_id` 無效如 `kiosk_unavailable` 錯誤，靜默略過）
   - Infra enable cmd 發出時
   - 韌體回報 ba_state = IDLE 時（**路徑：Infra Listener 收到 `kiosk/{chip_id}/status`（ba_state = IDLE）後，呼叫 Member webhook `POST /internal/kiosk/status`，payload：`{ "chip_id": "{chip_id}", "ba_state": "IDLE", "kiosk_id": "{kiosk_id}" }`；Member 收到後廣播 `firmware.idle` 事件到 Engineering_Channel。此為新增跨系統需求，需 @Ina 和 @Mina 對齊後實作**）
   - Infra Listener 收到 escrow 事件並轉發 webhook 時（**需 @Ina 在 escrow webhook body 加入 `firmware_timestamp` 欄位，值為韌體 MQTT payload 裡的 `timestamp` 欄位原樣帶入**；完整 webhook body 範例：
     ```json
     {
       "kiosk_id": "kiosk_000",
       "esp32_mac": "test-esp32",
       "amount": 100,
       "event_id": "sim-123",
       "firmware_timestamp": 1713253800
     }
     ```
     stacked/rejected webhook body 同樣需要加入 `firmware_timestamp` 欄位；Member 同時廣播 `firmware.escrow`（B1，timestamp 用 `firmware_timestamp`）和 `infra.escrow`（B2，timestamp 用 Member 收到 webhook 的伺服器時間））
   - Member webhook 收到 escrow 時（廣播 `member.escrow_received`，B3）
   - Member 完成裁決時（廣播 `member.decision`，B4）
   - Infra MQTT 發出 cmd 指令時
   - 韌體回報 stacked 或 rejected 事件時（即 Infra Listener 轉發 webhook 到 Member 後，Member 在同一個 handler `kioskStacked` / `kioskRejected` 裡廣播 B6、B7、B8、B9；firmware.stacked/firmware.rejected（B7）timestamp 用韌體事件的 timestamp；firmware.cmd_received（B6）同時推算廣播；infra.result（B8）timestamp 用 Member 收到 webhook 的伺服器時間，B7 與 B8 的 timestamp 差值 = 韌體發出 stacked → Infra 轉發 → Member 收到的總延遲）
   - Member 完成代幣入帳或記錄退鈔時
   - 會員手機心跳收到時（**路由：`POST /api/kiosk/session/{id}/heartbeat`，目前只更新 `member_last_seen_at`，需新增廣播 `member.heartbeat` 邏輯；廣播頻道用 session 的 `kiosk_id` 查詢取得**）
   - Session 結束時（**廣播 `member.session_ended`，在 `KioskSession::terminate()` 方法內統一廣播，涵蓋所有結束路徑：手動結束、超時排程、iHub complete、新 session 取代**）

2. THE Member_Backend SHALL broadcast each WebSocket_Event in the following standard format:
   ```json
   {
     "node": "{node_identifier}",
     "timestamp": 1713253800,
     "data": {
       "{field_name}": "{field_value}"
     }
   }
   ```
   其中 `timestamp` 為 Unix 秒，由廣播方在事件發生當下記錄（即 Event_Timestamp）。

3. THE Member_Backend SHALL use the following `node` identifiers, with the specified `data` fields:
   <!-- 事件格式版本：v1.0，最後更新：2026-05-07 -->

   | node 識別碼 | 對應節點 | 廣播方 | data 欄位範例 |
   |------------|---------|-------|-------------|
   | `tablet.heartbeat` | Node A1 iHub 平板心跳 | Member | `{ "kiosk_id": "kiosk_000" }` |
   | `member.tablet_heartbeat` | Node A2 Member 後台（心跳） | Member（收到平板心跳後同時廣播，代表 Member 角色有收到，與 A1 成對） | `{ "kiosk_id": "kiosk_000" }` |
   | `member.bind` | Node A3 會員掃碼 bind 結果 | Member | 成功：`{ "result": "success", "kiosk_id": "kiosk_000" }` 失敗：`{ "result": "409", "error": "kiosk_busy" }` / `{ "result": "503", "error": "tablet_offline" }` / `{ "result": "422", "error": "qr_expired" }` / `{ "result": "422", "error": "kiosk_unavailable" }` |
   | `infra.enable` | Node A4 Infra enable cmd 發出 | Member（代 Infra 廣播，**廣播時機為 Member 呼叫 Infra MQTT API 並收到成功回應後**，不代表 Infra 真的發出 MQTT，若 Infra API 呼叫失敗則不廣播） | `{ "chip_id": "test-esp32", "action": "enable" }` |
   | `firmware.idle` | Node A5 韌體回報 IDLE | Member（收到 ba_state 更新後廣播） | `{ "ba_state": "IDLE", "chip_id": "test-esp32" }` |
   | `member.heartbeat` | Node A6 會員手機心跳 | Member | `{ "member_id": "123" }` |
   | `firmware.escrow` | Node B1 韌體 escrow | Member（收到 escrow webhook 後同時廣播，代表韌體角色有發出，與 B2 成對；timestamp 用 webhook body 裡的 `firmware_timestamp` 欄位，**需 @Ina 在 escrow webhook body 加入此欄位**） | `{ "chip_id": "test-esp32", "amount": 100 }` |
   | `infra.escrow` | Node B2 Infra Listener 收到 escrow | Member（收到 escrow webhook 後廣播，代表 Infra 角色有收到，與 B1 成對） | `{ "chip_id": "test-esp32", "node_id": "kiosk_000" }` — 注意：Member 廣播時將 `$request->kiosk_id` 存入 `node_id` key，與 R2 AC1 Node B2 監聽欄位名稱一致，前端不需要做欄位映射 |
   | `member.escrow_received` | Node B3 Member webhook（escrow）收到時間點 | Member（收到 escrow webhook 時立即廣播，timestamp 用 Member 收到 webhook 的伺服器時間） | `{ "chip_id": "test-esp32", "amount": 100 }` |
   | `member.decision` | Node B4 Member 裁決完成時間點 | Member（完成裁決後廣播，B3→B4 耗時即查 session + 計算 token_rate 的時間） | `{ "chip_id": "test-esp32", "amount": 100, "action": "stack" }` — 注意：`chip_id` 和 `amount` 為 debug 用途，前端只顯示 R2 AC1 定義的監聽欄位（`action`），不顯示多餘欄位 |
   | `infra.cmd` | Node B5 Infra MQTT 發出 cmd | Member（代 Infra 廣播，**廣播時機為 Member 呼叫 Infra MQTT API 並收到成功回應後**，不代表 Infra 真的發出 MQTT，若 Infra API 呼叫失敗則不廣播） | `{ "chip_id": "test-esp32", "action": "stack" }` — chip_id 與 infra.enable 格式一致，從 session.esp32_mac 取得 |
   | `firmware.cmd_received` | Node B6 韌體收到 cmd | Member（收到 stacked/rejected webhook 後推算廣播，代表韌體角色已收到並執行 cmd，與 B5 成對；timestamp 用韌體事件的 timestamp） | `{ "action": "stack" }` |
   | `firmware.stacked` | Node B7 韌體回報 stacked | Member（收到 stacked webhook 後廣播，timestamp 用韌體事件的 timestamp，即 webhook body 裡的 `firmware_timestamp` 欄位，**需 @Ina 在 stacked webhook body 同樣加入此欄位**） | `{ "event_type": "stacked", "amount": 100 }` |
   | `firmware.rejected` | Node B7 韌體回報 rejected | Member（收到 rejected webhook 後廣播，timestamp 用韌體事件的 timestamp，即 webhook body 裡的 `firmware_timestamp` 欄位，**需 @Ina 在 rejected webhook body 同樣加入此欄位**） | `{ "event_type": "rejected", "amount": 100, "reason": "timeout" }` |
   | `infra.result` | Node B8 Infra Listener 收到 stacked/rejected | Member（與 firmware.stacked/rejected 在同一個 webhook handler 裡廣播，**timestamp 用 Member 收到 webhook 的伺服器時間**；B7 timestamp 來自韌體時鐘，B8 timestamp 來自伺服器時鐘，兩者差值 = 韌體發出 stacked/rejected → Infra 轉發 → Member 收到的總延遲，此為設計意圖） | `{ "chip_id": "test-esp32", "event_type": "stacked" }` |
   | `member.credited` | Node B9 Member 完成入帳 | Member | `{ "result": "credited", "tokens_credited": 100 }` |
   | `member.noted` | Node B9 Member 記錄退鈔 | Member | `{ "result": "noted" }` |
   | `member.session_ended` | 不對應節點（僅用於觸發 A6 重置） | Member（session 結束時廣播，涵蓋所有結束路徑：手動結束、超時排程、iHub complete；廣播時機為 `KioskSession::terminate()` 執行時，確保所有路徑都觸發） | `{ "kiosk_id": "kiosk_000" }` |

4. IF the Member_Backend encounters an error while broadcasting a WebSocket_Event, THEN THE Member_Backend SHALL log the error and continue processing the main business logic without interruption.
5. THE Member_Backend SHALL broadcast WebSocket_Events only to the `engineering.{kiosk_id}` channel, where `kiosk_id` is always lowercase. **頻道類型為 Public Channel**（不需要 Private Channel 認證，工程頁面本身已有登入保護，不另外加 WebSocket 認證層）.

---

### Requirement 11：WebSocket 連線管理

**User Story:** As an engineer, I want the panel to maintain a stable WebSocket connection and recover from disconnections, so that I don't miss signal events during a test session.

#### Acceptance Criteria

1. WHEN the Signal_Flow_Monitor initializes, THE Signal_Flow_Monitor SHALL establish a WebSocket connection to the Member Reverb server and subscribe to the Engineering_Channel for the selected Kiosk_ID.
2. WHEN the WebSocket connection is lost, THE Signal_Flow_Monitor SHALL display a connection status indicator showing "連線中斷" and attempt to reconnect automatically.
3. WHEN the WebSocket connection is successfully re-established, THE Signal_Flow_Monitor SHALL display a connection status indicator showing "已連線" and resume receiving events.
4. THE Signal_Flow_Monitor SHALL display the current WebSocket connection status (已連線 / 連線中斷 / 連線中) at all times within the panel.

---

### Requirement 12：面板不影響現有功能

**User Story:** As an engineer, I want the new panel to be additive only, so that existing engineering page functionality is not disrupted.

#### Acceptance Criteria

1. THE Signal_Flow_Monitor SHALL be implemented as a new, self-contained section appended to the Engineering_Page, without modifying any existing Alpine.js 元件、API calls, or WebSocket subscriptions already present on the page.
2. IF the Signal_Flow_Monitor encounters an unhandled error, THEN THE Signal_Flow_Monitor SHALL display an error state within its own panel boundary and SHALL NOT propagate the error to other parts of the Engineering_Page.
3. THE Signal_Flow_Monitor SHALL use only the `engineering.{kiosk_id}` WebSocket channel and SHALL NOT interfere with existing WebSocket channels used by the Engineering_Page (e.g., `kiosk.{kiosk_id}`).
4. THE Signal_Flow_Monitor SHALL support injecting mock WebSocket events via browser console（例如 `window.__sfm_inject({ node: 'firmware.escrow', timestamp: Date.now()/1000 - 20, data: { chip_id: 'test-esp32', amount: 100 } })`），以便測試邊界條件（如時鐘不同步、Fail-Safe 超時）而不需要真實硬體。**此功能在工程頁面（`/engineering/kiosk`）永遠啟用，不受環境限制**，因為工程頁面本身已有登入保護。
