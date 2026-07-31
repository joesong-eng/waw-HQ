# Implementation Plan: Signal Flow Monitor

## Overview

實作分四個 Phase，依照 design.md 第 6 節的順序：後端廣播基礎 → 前端面板 → 跨系統整合 → 整合測試。後端使用 Laravel (PHP)，前端使用 Alpine.js，嵌入現有工程頁面 `win.tg25.win/engineering/kiosk`。

---

## Tasks

- [x] 1. 建立後端廣播基礎架構（Phase 1）
  - [x] 1.1 建立 `EngineeringEvent` Broadcast event class
    - 在 `app/Events/` 建立 `EngineeringEvent.php`
    - 實作 `ShouldBroadcast` interface
    - 廣播到 `engineering.{kiosk_id}` Public Channel（全小寫）
    - payload 格式：`{ "node": "...", "timestamp": unix_seconds, "data": {...} }`
    - _Requirements: 10.2, 10.5_

  - [x] 1.2 建立 `EngineeringBroadcast` service class
    - 在 `app/Services/` 建立 `EngineeringBroadcast.php`
    - 實作 `emit($kioskId, $node, $data)` 方法：kiosk_id 為空時靜默略過，廣播失敗時 log 並繼續
    - 實作 `getKioskIdBySession($sessionId)` 方法：查 `kiosk_sessions.kiosk_id`
    - 實作 `getKioskIdByMac($esp32Mac)` 方法：查 active session 的 kiosk_id
    - _Requirements: 10.1, 10.4_

  - [ ]* 1.3 為 `EngineeringBroadcast::emit()` 寫單元測試
    - 測試 kiosk_id 為空時不廣播
    - 測試廣播失敗時不拋出例外、主流程繼續
    - 測試 payload 格式符合 R10 AC2 規範
    - _Requirements: 10.4_

- [x] 2. 在各 Controller 加入廣播（不需要 firmware_timestamp 的事件）
  - [x] 2.1 `kioskHeartbeat` — 廣播 `tablet.heartbeat` 和 `member.tablet_heartbeat`
    - data: `{ "kiosk_id": "..." }`
    - _Requirements: 10.1, 10.3_

  - [x] 2.2 `bind` — 廣播 `member.bind`（成功與各種失敗情境）
    - 成功：`{ "result": "success", "kiosk_id": "..." }`
    - 失敗：`{ "result": "409", "error": "kiosk_busy" }` 等四種錯誤格式
    - kiosk_unavailable 時靜默略過
    - _Requirements: 10.1, 10.3_

  - [x] 2.3 `bind`（Infra MQTT 成功後）— 廣播 `infra.enable`
    - 廣播時機：Member 呼叫 Infra MQTT API 並收到成功回應後
    - data: `{ "chip_id": "...", "action": "enable" }`
    - _Requirements: 10.1, 10.3_

  - [x] 2.4 `kioskEscrow` — 廣播 `infra.escrow` 和 `member.escrow_received`
    - `infra.escrow` data: `{ "chip_id": "...", "node_id": "..." }`（node_id 用 `$request->kiosk_id`）
    - `member.escrow_received` data: `{ "chip_id": "...", "amount": ... }`，timestamp 用 Member 收到 webhook 的伺服器時間
    - 注意：`firmware.escrow`（B1）需要 firmware_timestamp，留待 Phase 3
    - _Requirements: 10.1, 10.3_

  - [x] 2.5 `escrowConfirm` — 廣播 `member.decision`（action: stack）和 `infra.cmd`（action: stack）
    - `member.decision` data: `{ "chip_id": "...", "amount": ..., "action": "stack" }`
    - `infra.cmd` data: `{ "chip_id": "...", "action": "stack" }`
    - _Requirements: 10.1, 10.3_

  - [x] 2.6 `escrowReject` — 廣播 `member.decision`（action: reject）和 `infra.cmd`（action: reject）
    - `member.decision` data: `{ "chip_id": "...", "amount": ..., "action": "reject" }`
    - `infra.cmd` data: `{ "chip_id": "...", "action": "reject" }`
    - _Requirements: 10.1, 10.3_

  - [x] 2.7 `kioskStacked` — 廣播 `firmware.cmd_received`（action: stack）、`infra.result`、`member.credited`
    - `firmware.cmd_received` data: `{ "action": "stack" }`，timestamp 用韌體事件 timestamp（Phase 3 補 firmware_timestamp 後完整）
    - `infra.result` data: `{ "chip_id": "...", "event_type": "stacked" }`，timestamp 用 Member 收到 webhook 的伺服器時間
    - `member.credited` data: `{ "result": "credited", "tokens_credited": ... }`
    - 注意：`firmware.stacked`（B7）需要 firmware_timestamp，留待 Phase 3
    - _Requirements: 10.1, 10.3_

  - [x] 2.8 `kioskRejected` — 廣播 `firmware.cmd_received`（action: reject）、`infra.result`、`member.noted`
    - `firmware.cmd_received` data: `{ "action": "reject" }`
    - `infra.result` data: `{ "chip_id": "...", "event_type": "rejected" }`，timestamp 用 Member 收到 webhook 的伺服器時間
    - `member.noted` data: `{ "result": "noted" }`
    - kiosk_id 用 esp32_mac 查 active session 取得（`getKioskIdByMac`）
    - 注意：`firmware.rejected`（B7）需要 firmware_timestamp，留待 Phase 3
    - _Requirements: 10.1, 10.3_

  - [x] 2.9 `memberHeartbeat` — 廣播 `member.heartbeat`
    - data: `{ "member_id": "..." }`
    - kiosk_id 用 session_id 查 `kiosk_sessions.kiosk_id`（`getKioskIdBySession`）
    - _Requirements: 10.1, 10.3_

  - [x] 2.10 `KioskSession::terminate()` — 廣播 `member.session_ended`
    - data: `{ "kiosk_id": "..." }`
    - 涵蓋所有結束路徑：手動結束、超時排程、iHub complete、新 session 取代
    - _Requirements: 10.1, 10.3_

- [x] 3. 新增 `GET /api/kiosk/device-info` API（Phase 1）
  - 建立 Controller method，接受 `?kiosk_id={kiosk_id}` query param
  - 呼叫 Infra `GET /api/kiosk/info` 取得 esp32_mac，不直接查 Owner DB
  - Response 200: `{ "kiosk_id": "kiosk_000", "chip_id": "test-esp32", "node_id": "kiosk_000" }`
  - Response 404: kiosk_id 不存在
  - 認證：Sanctum Bearer token
  - 在 `routes/api.php` 加入路由
  - _Requirements: 6.5_

- [x] 4. Checkpoint — 後端廣播基礎完成
  - 確認所有廣播事件格式符合 R10 AC3 表格
  - 確認 `GET /api/kiosk/device-info` 回傳正確格式
  - 確認所有測試通過，ask the user if questions arise.

- [x] 5. 建立前端 Alpine.js 面板骨架（Phase 2）
  - [x] 5.1 在 `kiosk.blade.php` 加入面板 HTML 結構
    - 新增獨立 `<section>` 區塊，不修改任何現有元素
    - 加入 `x-data="signalFlowMonitor()"` Alpine.js component 掛載點
    - 加入 WebSocket 連線狀態指示器（已連線 / 連線中斷 / 連線中）
    - 加入「請先選擇綁定組合」提示區（無 kiosk_id 時顯示）
    - _Requirements: 1.1, 1.3, 1.4, 11.4, 12.1_
    - **HQ 審核通過**：commit `0e1dd49`，第 877 行確認 component 存在（2026-05-07 06:23:15）

  - [x] 5.2 建立 `signalFlowMonitor()` Alpine.js component 基礎狀態
    - 在對應的 JS 檔案建立 `signalFlowMonitor()` function
    - 初始化狀態：`selectedKioskId`、`chipId`、`nodeId`、`wsStatus`、`nodes`、`timings`、`banner`、`expectedValues`
    - 每個節點初始狀態：`lastSignalAt: null`、`lastEventTimestamp: null`、`fields: {}`、`alignment: {}`、`visualState: 'dormant'`、`specialLabel: null`、`specialColor: null`
    - _Requirements: 1.3, 4.4_
    - **HQ 審核通過**：commit `0e1dd49`（2026-05-07 06:23:15）

  - [x] 5.3 實作 kiosk_id 選擇監聽與 WebSocket 訂閱管理
    - 監聽頁面現有下拉框的 kiosk_id 變更
    - kiosk_id 變更時：取消訂閱舊頻道、訂閱新的 `engineering.{kiosk_id}` 頻道
    - 無 kiosk_id 時不訂閱任何頻道、不呼叫 device-info API
    - 使用現有 Laravel Echo + Pusher.js
    - _Requirements: 1.4, 1.5, 11.1_
    - **HQ 審核通過**：`sfm:kiosk-changed` 事件監聽存在（第 902 行）（2026-05-07 06:23:15）

  - [x] 5.4 實作 WebSocket 連線狀態管理與自動重連
    - 監聽 Echo 的 connected / disconnected / connecting 事件
    - 更新 `wsStatus` 並顯示對應中文狀態
    - 斷線時顯示「連線中斷」並自動重連
    - _Requirements: 11.2, 11.3, 11.4_
    - **HQ 審核通過**：Echo `.signal` 監聽存在（第 988 行）（2026-05-07 06:23:15）

  - [x] 5.5 實作 `GET /api/kiosk/device-info` 呼叫與 Expected_Values 動態建立
    - 訂閱 Engineering_Channel 時呼叫 API
    - 根據回傳的 `chip_id` 和 `node_id` 動態建立所有節點的 Expected_Value map
    - 404 時 chip_id 相關欄位設為 `—`（不設預期值）
    - _Requirements: 6.5_
    - **HQ 審核通過**：API 已在 Phase 1 實作並驗證（2026-05-07 05:56:29）

- [x] 6. 實作節點卡片渲染與訊號接收（Phase 2）
  - [x] 6.1 實作 WebSocket 事件接收與節點狀態更新
    - 訂閱 Engineering_Channel 後，監聽所有 WebSocket_Event
    - 根據 `event.node` 識別碼更新對應節點的 `fields`、`lastSignalAt`（瀏覽器本地時間）、`lastEventTimestamp`（event.timestamp）
    - 更新 `visualState` 為 `active`
    - _Requirements: 4.1, 5.1, 5.4_
    - **Mina 測試通過**：所有節點正常接收訊號並顯示（2026-05-07 06:54:33）

  - [x] 6.2 實作欄位值顯示與名稱對齊比對
    - 顯示各節點監聽欄位的 key-value pair（格式：`{field_name}: {value}`）
    - 未收到訊號時顯示 `—`（em dash）
    - 比對 Field_Value 與 Expected_Value：match → 🟢，mismatch → 🔴，unset/Dynamic_Field → ⚫
    - mismatch 時節點 border 顯示紅色
    - _Requirements: 5.2, 5.3, 6.1, 6.2, 6.3, 6.4, 6.6_
    - **Mina 測試通過**：節點初始狀態顯示 `—`（2026-05-07 06:54:33）

  - [x] 6.3 實作脈衝燈（Pulse_Light）動畫
    - 收到訊號時立即亮起
    - 2 秒 CSS transition 從亮到暗
    - _Requirements: 4.1, 4.2_
    - **Mina 測試通過**：節點視覺狀態 active（綠色邊框）正常運作（2026-05-07 06:54:33）

  - [x] 6.4 實作相對時間戳顯示（每秒更新）
    - 收到第一個訊號後開始顯示：「剛剛」、「5 秒前」、「2 分前」等
    - 每秒更新一次（`setInterval`）
    - 未收到任何訊號時不顯示時間戳
    - _Requirements: 4.4, 4.5_
    - **Mina 測試通過**：時間戳顯示正常（2026-05-07 06:54:33）

  - [x] 6.5 實作節點 timed_out 視覺狀態
    - 超過 Timeout_Threshold（30 秒）無訊號時切換為 `timed_out`（灰色背景、文字變暗）
    - timed_out 後收到新訊號時立即恢復 active 狀態
    - timed_out 狀態下時間戳繼續更新
    - _Requirements: 4.3, 7.1, 7.2, 7.3_
    - **Mina 測試通過**：30 秒超時邏輯正常（2026-05-07 06:54:33）

- [x] 7. 實作掃碼綁定段節點邏輯（Phase 2）
  - [x] 7.1 實作 Node A3 `會員掃碼 bind` 結果顯示
    - `result: success` → 綠色，顯示 kiosk_id 值
    - `result: 409, error: kiosk_busy` → 紅色，顯示「機台使用中」
    - `result: 503, error: tablet_offline` → 紅色，顯示「平板離線」
    - `result: 422, error: qr_expired` → 紅色，顯示「QR Code 已過期」
    - `result: 422, error: kiosk_unavailable` → 紅色，顯示「兌幣卡離線」
    - 非 success 時：border 紅色，A4/A5 停止響應後續事件
    - 重新 success 時：清除錯誤狀態，A4/A5 恢復 dormant，所有 Field_Value 重置為 `—`
    - _Requirements: 3.1, 3.2, 3.3_
    - **Mina 測試通過**：A1~A6 節點顯示正常（2026-05-07 06:54:33）

  - [x] 7.2 實作 Node A5 `韌體 IDLE` 10 秒警告
    - A4 收到訊號後，以瀏覽器本地時間起計 10 秒計時
    - 10 秒內未收到 A5 訊號時顯示「⚠️ 未收到 IDLE 確認」
    - A5 收到 `ba_state: IDLE` 後移除警告，顯示綠色
    - _Requirements: 3.4, 3.5_
    - **Mina 測試通過**：10 秒警告邏輯已實作（2026-05-07 06:54:33）

  - [x] 7.3 實作 Node A6 `會員手機心跳` Side_Monitor_Node
    - 顯示在 A3 旁邊，不連接主流程箭頭
    - A3 收到 `result: success` 前：A6 保持灰色，不顯示任何警告
    - A3 成功後開始監控：90 秒無心跳顯示「⚠️ 會員可能已離線」
    - 收到心跳後移除警告
    - 收到 `member.session_ended` 事件後重置 A6 為初始灰色狀態，停止監控
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_
    - **Mina 測試通過**：A6 Side Monitor 已實作（2026-05-07 06:54:33）

- [x] 8. 實作投幣入帳段節點邏輯（Phase 2）
  - [x] 8.1 實作 Node B1 新 escrow 時的重置行為
    - 收到新的 `firmware.escrow` 事件時：清空所有時序量測（B1/B3/B4/B6 timestamp）
    - 清空 B2~B9 所有節點的 Field_Value（顯示 `—`）
    - B1 保留新收到的值
    - _Requirements: 8.5_
    - **Mina 測試通過**：B1~B9 節點顯示正常（2026-05-07 06:54:33）

  - [x] 8.2 實作 Node B4 `Member 裁決` 10 秒接近超時警告
    - B1 收到訊號後，以 Event_Timestamp 起計 10 秒
    - 10 秒內 B4 未收到訊號時，在 B4 顯示「⚠️ 接近超時」
    - B4 收到訊號後立即移除警告
    - _Requirements: 7.5_
    - **Mina 測試通過**：B4 超時警告已驗證（2026-05-07 06:54:33）

  - [x] 8.3 實作 Node B7 特殊狀態顯示
    - `firmware.stacked`（event_type: stacked）→ 綠色，顯示「✅ 收鈔成功」
    - `firmware.rejected`（reason: rejected_by_server）→ 黃色，顯示「↩️ 伺服器退鈔」
    - `firmware.rejected`（reason: timeout）→ 橘色，顯示「⏰ Fail-Safe 退鈔」
    - `firmware.stacked` 和 `firmware.rejected` 共用同一個節點卡片位置
    - _Requirements: 2.5, 2.6, 2.7, 7.6, 7.7_
    - **Mina 測試通過**：B7 顯示「✅ 收鈔成功」（綠色）（2026-05-07 06:54:33）

  - [x] 8.4 實作 B4 reject 路徑箭頭顏色變化
    - B4 收到 `action: reject` 時：B4→B5→B6→B7 箭頭變為 amber 色
    - B7 收到 `reason: timeout` 時：箭頭從 amber 更新為 orange
    - _Requirements: 2.4_
    - **Mina 測試通過**：箭頭顏色邏輯已實作（2026-05-07 06:54:33）

  - [x] 8.5 實作投幣流程中斷 banner
    - B1 收到訊號後，若 B2~B9 全部超過 30 秒無訊號，顯示「⚠️ 投幣流程可能已中斷」banner
    - B1 本身是否超時不影響此條件
    - _Requirements: 7.4_
    - **Mina 測試通過**：流程中斷 banner 已驗證（2026-05-07 06:54:33）

- [x] 9. 實作時序量測顯示（Phase 2）
  - [x] 9.1 實作四個時序量測計算與顯示
    - B1→B4：「裁決耗時：X.Xs」
    - B3→B4：「查詢耗時：X.Xs」
    - B4→B6：「指令送達：X.Xs」
    - B1→B6：「總耗時：X.Xs / 15s」
    - 使用 Event_Timestamp（Unix 秒）計算，非瀏覽器本地時間
    - _Requirements: 8.1, 8.2_
    - **Mina 測試通過**：裁決耗時 4.0s、查詢耗時 2.0s、指令送達 3.0s、總耗時 7.0s/15s（2026-05-07 06:54:33）

  - [x] 9.2 實作時序量測顏色警告
    - B1→B6 超過 10 秒：橘色警告
    - B1→B6 超過 15 秒：紅色（Fail-Safe deadline 已超過）
    - _Requirements: 8.3, 8.4_
    - **Mina 測試通過**：顏色警告邏輯已實作（2026-05-07 06:54:33）

  - [x] 9.3 實作時鐘不同步偵測
    - B1→B6 計算結果為負數或超過 10 秒時，顯示「⚠️ 時鐘不同步」取代異常數值
    - _Requirements: 8.1_
    - **Mina 測試通過**：時鐘不同步偵測已實作（2026-05-07 06:54:33）

- [x] 10. 實作 mock 注入與錯誤隔離（Phase 2）
  - [x] 10.1 實作 `window.__sfm_inject()` mock 注入介面
    - 在工程頁面永遠啟用（不受環境限制）
    - 接受格式：`{ node: '...', timestamp: unix_seconds, data: {...} }`
    - 注入後觸發與真實 WebSocket 事件相同的處理邏輯
    - _Requirements: 12.4_
    - **Mina 測試通過**：使用 `window.__sfm_inject()` 完成所有功能測試（2026-05-07 06:54:33）

  - [x] 10.2 實作面板錯誤隔離
    - 用 try-catch 包裹所有事件處理邏輯
    - 發生未處理錯誤時在面板內顯示錯誤狀態，不向外傳播
    - _Requirements: 12.2_
    - **Mina 測試通過**：錯誤隔離已實作（2026-05-07 06:54:33）

- [x] 11. Checkpoint — 前端面板完成
  - 用 `window.__sfm_inject()` 驗證所有節點的視覺狀態
  - 驗證時序量測計算正確
  - 驗證 timed_out、Fail-Safe 超時等邊界條件
  - 確認不影響現有工程頁面功能
  - 確認所有測試通過，ask the user if questions arise.
  - **Mina 測試通過**：所有測試項目已驗證（2026-05-07 06:54:33）

- [x] 12. 新增 `POST /internal/kiosk/status` 路由（Phase 3，@Mina）
  - 在 `routes/internal.php`（或對應的 internal routes 檔案）加入路由
  - 建立 Controller method：接收 `{ "chip_id": "...", "ba_state": "IDLE", "kiosk_id": "..." }`
  - 認證：X-Internal-Key
  - 收到後廣播 `firmware.idle` 事件到 Engineering_Channel
  - Response 200: `{ "status": "ok" }`
  - _Requirements: 10.1, 10.3_

- [x] 13. 補上需要 firmware_timestamp 的廣播（Phase 3，待 @Ina 完成 webhook 修改後）
  - [x] 13.1 `kioskEscrow` — 補上 `firmware.escrow`（B1）廣播
    - data: `{ "chip_id": "...", "amount": ... }`
    - timestamp 用 webhook body 裡的 `firmware_timestamp` 欄位
    - _Requirements: 10.1, 10.3_
    - **HQ 審核通過**：commit `be5728b`，CallbackController 第 242-249 行（2026-05-07 06:28:08）

  - [x] 13.2 `kioskStacked` — 補上 `firmware.stacked`（B7）廣播
    - data: `{ "event_type": "stacked", "amount": ... }`
    - timestamp 用 webhook body 裡的 `firmware_timestamp` 欄位
    - _Requirements: 10.1, 10.3_
    - **HQ 審核通過**：commit `be5728b`，CallbackController 第 387-393 行（2026-05-07 06:28:08）

  - [x] 13.3 `kioskRejected` — 補上 `firmware.rejected`（B7）廣播
    - data: `{ "event_type": "rejected", "amount": ..., "reason": "timeout" 或 "rejected_by_server" }`
    - timestamp 用 webhook body 裡的 `firmware_timestamp` 欄位
    - _Requirements: 10.1, 10.3_
    - **HQ 審核通過**：commit `be5728b`，CallbackController 第 441-447 行（2026-05-07 06:28:08）

  - [x] 13.4 `kioskStacked` / `kioskRejected` — 補上 `firmware.cmd_received`（B6）timestamp 修正
    - timestamp 改用 webhook body 裡的 `firmware_timestamp` 欄位（代表韌體已收到並執行 cmd 的時間點）
    - _Requirements: 10.1, 10.3_
    - **HQ 審核通過**：commit `be5728b`，KioskController 第 504、549 行（2026-05-07 06:28:08）

- [ ] 14. Final Checkpoint — 整合測試完成
  - 確認所有 WebSocket 事件格式符合 R10 AC3 表格
  - 確認 firmware_timestamp 相關節點（B1、B6、B7）時序量測正確
  - 確認 `POST /internal/kiosk/status` 路由正常運作
  - 確認所有測試通過，ask the user if questions arise.

---

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Phase 3 的任務（Task 12、13）依賴 @Ina 完成 webhook body 修改，可在 @Ina 完成後再執行
- Task 13 的廣播在 Phase 1 已有佔位（kioskEscrow/kioskStacked/kioskRejected），Phase 3 只是補上 firmware_timestamp 欄位
- 前端 mock 注入（Task 10.1）可在 Phase 2 完成後立即用於驗證 Phase 3 的時序量測邏輯
- 設計文件無 Correctness Properties 章節，故不加入 property-based test 任務；測試以單元測試為主
