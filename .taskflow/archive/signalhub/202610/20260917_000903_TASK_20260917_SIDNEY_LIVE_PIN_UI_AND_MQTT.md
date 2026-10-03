# 工單：TASK_20260917_SIDNEY_LIVE_PIN_UI_AND_MQTT

**派發時間**：2026-09-17 00:15
**派發者**：HQ
**執行者**：Sidney (SignalHub Lead)
**優先級**：HIGH
**前置條件**：Coli (IOTwawS3) 韌體 v2.0.5 已實作完成並編譯通過

---

## 任務目標

在 SignalHub Web 後台實作 Live Pin（存活腳位）與超時秒數設定介面，於儲存時自動發送 MQTT 指令同步至 ESP32-S3 採集卡，並支援接收採集卡上報之 `session_end` 事件。

---

## 具體工作項目

### 1. 資料庫 Migration
- 於 `signal_profiles` 表新增欄位：
  - `live_pin`: tinyint unsigned, 預設 0 (0: 停用, 3: UI3, 4: UI4)
  - `live_timeout_sec`: smallint unsigned, 預設 120 (範圍 30 ~ 600)

### 2. 前端 UI（profiles/{id}/pins 頁面）
- 位於腳位設定卡片區塊，新增「存活感測 / 離場偵測 (Live Pin)」區塊：
  - **存活腳位**：下拉選單（停用、UI3、UI4）
  - **無活動逾時秒數**：數字輸入框（30 ~ 600 秒，預設 120 秒）
  - 文案清晰說明：『當玩家投幣後，只要此腳位有動作即自動續命；若超過指定秒數無動作，判定玩家離場並結算本局』

### 3. 後端 API 與 MQTT 指令下發
- Controller 儲存/更新腳位時校驗：
  - `live_pin` 必須為 `0, 3, 4`
  - `live_timeout_sec` 必須介於 `30 ~ 600`
- 儲存成功後，若該 Profile 有綁定在線設備（`devices.chip_id`）：
  - 透過 MQTT 發布設定至採集卡：
    - **Topic**：`waw/v1/{site_id}/cmd/{chip_id}`（向下相容 `device/{chip_id}/cmd`）
    - **Payload**：
      ```json
      {
        "command": "set_live_config",
        "transaction_id": "txn_{uniqid}",
        "params": {
          "live_pin": 4,
          "timeout_sec": 180
        }
      }
      ```

### 4. 接收 session_end 事件處理
- 當收到採集卡上報之 `session_end` 事件（MQTT 或 Webhook）：
  - 格式：`{"chip_id":"...","event":"session_end","reason":"timeout|cash_out","last_played_duration_seconds":182}`
  - 記錄至 `signal_events` 或遊戲局日誌，標記離場原因與遊戲時長。

### 5. 測試與部署
- 執行遷移與快取清理（`php artisan migrate`, `php artisan optimize:clear`）。
- 部署至 `signal.tg25.win` 並驗證頁面與 API 正常無 500 報錯。

---

## 回報格式
完成後使用 `agent_report_to_hq_v2.sh` 提交報告至 HQ outbox。
