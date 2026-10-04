# WAW 完整資料流程與端對端時序全解析 (CHATGPT_DATA_FLOW.md)

> **文件身分**：WAW 專案資料流向深探文件 (專供 ChatGPT 深度解析)  
> **關聯總索引**：`knowledge/CHATGPT_CONTEXT.md` (實體位置: `brains/knowledge/CHATGPT_CONTEXT.md`)  
> **最後校驗日期**：2026-09-24  
> **維護權限**：HQ (協調中心唯一寫入)  
> **狀態標記準則**：【已實作】/【已驗證】/【已設計但尚未實作】/【計畫中】/【未確認】

---

## 1. 核心資料流程總覽

WAW 系統的資料流程依照業務型態區分為兩大體系、四條獨立管道：
1. **流程一：SignalHub 電腦型街機開洗分流 (PC-Based Online Flow - Event Trigger)**
2. **流程二：SignalHub 遊戲主板分數歸零通報流 (Session End Inbound Flow)**
3. **流程三：傳統街機手機掃碼開分流 (Traditional Arcade Scan & Credit Flow - game_v0)**
4. **流程四：兌幣機紙鈔暫存與入箱兌換流 (Kiosk Escrow & Exchange Flow - kiosk_v0)**
5. **流程五：機械碼表脈衝稽核與日結流 (Mechanical Counter Auditing - UI3/UI4)**

---

## 2. 流程一：SignalHub 電腦型街機開洗分流程 (核心旗艦流程)

本流程適用於電腦型街機（如聯網捕魚機、老虎機、推幣機），服務員收取玩家現金後，按下吧台開分或洗分實體鍵。

### 2.1 物理事件到雲端轉發時序 【已驗證】

```
[吧台實體按鈕] 
       │ 1. 服務員按下按鍵 (短接 100ms)
       ▼
[光耦隔離輸入 (UI1/UI2)]
       │ 2. 電平反轉 (下降沿/上升沿)
       ▼
[ESP32-S3 (Coli 韌體)]
       │ 3. PCNT 計數器捕獲中斷，軟體累加 raw_value，設定 delta_value = 1
       │ 4. 生成流水 delivery_id (例: 982341)
       ├────────────────────────────────────────────────────────┐
       │ (雲端軌道: Wi-Fi MQTTS)                                 │ (地端軌道: USB CDC 串列埠)
       ▼                                                        ▼
[Mosquitto Broker @ infra (Port 8883)]              [現場收銀 PC (第三方 POS)]
       │ 5. 發布至 waw/v1/{site}/signal/{chip_id}/event          │ 5a. 收到單行 JSON
       ▼                                                        ▼
[Infra MQTT Listener (Python Daemon)]               [收銀軟體處理]
       │ 6. 監聽封包，驗證 chip_id                               │ 6a. 3秒內回寫 Serial
       │ 7. POST internal/signal/event                          ▼
       ▼                                            [ESP32 接收 cleared_points]
[SignalHub 後端 (signal.tg25.win @ yd174)]                       (完成地端結算)
       │ 8. 驗證 X-Internal-Key
       │ 9. 寫入 iotv9.signal_events (原始物理事件流水)
       │ 10. 查詢 signal_pin_mappings 與 signal_webhooks
       │ 11. 建立 iotv9.signal_webhook_deliveries (狀態: pending)
       │ 12. 透過非同步佇列調度 Webhook 發送
       ▼
[第三方遊戲伺服器 (小猴系統)]
       │ 13. 接收帶有 X-WAW-Signature 簽名之 Webhook POST
       │ 14. 遊戲伺服器在 3 秒內決定實際點數 (actual_points)
       ▼
[雙向確認完成 (Two-Way Settlement)]
  - 同步模式：小猴在 Webhook HTTP Response 直接回傳 JSON (含 actual_points: 500)
  - 非同步模式：小猴呼叫 POST /v9/signal-hub/callback-ack 異步回報
       ▼
[SignalHub 結算落地]
       │ 15. 更新 signal_webhook_deliveries (cleared_points = actual_points, status = success)
       │ 16. 廣播 WebSocket 事件至店主即時大看板
```

### 2.2 關鍵資料封包細節

#### (A) ESP32 上報 MQTT Event Payload
```json
{
  "chip_id": "DF1E4C4B1105",
  "pin": "UI1",
  "event_type": "credit_in",
  "raw_value": 10582,
  "delta_value": 1,
  "occurred_at": 1725339600
}
```

#### (B) SignalHub 轉發第三方 Webhook Payload
```json
{
  "delivery_id": 982341,
  "event": "credit_in",
  "chip_id": "df1e4c4b1105",
  "pin_code": "UI1",
  "raw_value": 10582,
  "delta_value": 1,
  "occurred_at": "2026-09-24T12:00:00+08:00"
}
```
> **架構決策驗證**：已徹底不傳輸 `machine_number` 與 `machine_name`。

#### (C) 第三方回覆 Payload (必須在 3 秒內抵達)
```json
{
  "status": "success",
  "delivery_id": 982341,
  "actual_points": 500
}
```

---

## 3. 流程二：SignalHub 遊戲主板分數歸零通報流 (Session End)

當玩家離場或遊戲結束，電腦型機台內部分數歸零時，遊戲主控程式主動向 SignalHub 呈報，用於計算該位玩家的在席遊玩時長與營收對帳。

```
[遊戲主板 / 小猴程式] (檢測到遊戲內存分數從 >0 變為 0)
       │
       │ POST https://signal.tg25.win/api/v9/signal-hub/inbound/session-end
       │ Header: Content-Type: application/json
       ▼
[SignalHub Inbound Controller]
       │ 1. 驗證 chip_id 歸屬與有效性
       │ 2. 記錄 session_end 事件至資料庫
       │ 3. 計算並更新最後遊戲時長 (last_played_duration_seconds)
       │ 4. 觸發營收結算統計規則 (signal_stat_rules)
       ▼
[HTTP 200 回應] {"status": "accepted", "session_id": "sess_884912"}
```

---

## 4. 流程三：傳統街機手機掃碼開分流程 (game_v0)

此模式針對傳統單機投幣機（如瑪莉機、輪盤、框體），機台本身無聯網 PC，完全由 WAW 採集卡充當投幣器模擬中樞。

```
[玩家手機] 掃描機台貼附之 QR Code (https://win.tg25.win/m/play?node_id=device_001)
       │
       ▼
[Member 前端 (win.tg25.win)]
       │ 1. 建立/恢復 device_sessions (檢查一人一台限制)
       │ 2. 玩家在手機介面點擊「開分 1 代幣」
       │ 3. 檢查 member_wallets 代幣餘額 (必須 >= 1)
       │ 4. 凍結代幣 (-1 TOKEN, status = pending)
       │ 5. 依據場地配置換算脈衝 (例: pulse_to_token = 0.5 -> 2 脈衝)
       ▼
[Member 後端]
       │ 6. 呼叫 Infra 內部觸發端點
       │ POST https://api.tg25.win/api/device/trigger-pulse
       │ Header: X-Internal-Key: v9-internal-key-2026
       │ Payload: {"chip_id": "iot002", "count": 2, "action": "assign_credit"}
       ▼
[Infra API (api.tg25.win)]
       │ 7. 發布 MQTT 指令
       │ Topic: device/{chip_id}/cmd
       │ Payload: {"command": "assign_credit", "params": {"count": 2}}
       ▼
[ESP32 採集卡 (Coli)]
       │ 8. 收到 cmd 指令
       │ 9. 驅動 PIN_OUT1 (GPIO 45) 產生 2 次方波脈衝 (高電位 50ms, 低電位 50ms)
       ▼
[實體機台主板] 投幣引腳接收到 2 下短接，機台螢幕分數跳動增加
       │
       ▼
[實體碼表反饋 (UI3)] 機台電磁計數器跳動，ESP32 PCNT 累加 raw_value 並發布 MQTT event 回雲端
       │
       ▼
[Member 後端收到反饋] 解除代幣凍結，標記交易為 success
```

---

## 5. 流程四：兌幣機紙鈔暫存與入箱兌換流 (kiosk_v0)

本流程涵蓋現金紙鈔防偽、雙向安全暫存 (Escrow) 與代幣充值。

```
[玩家] 走近兌幣機，手機掃描 iHub 工控平板上動態產生的 QR Code
       │
       ▼
[Member 系統] 建立 kiosk_sessions (綁定會員與 kiosk_001)，狀態進入 ACTIVE
       │
       ▼
[Member API] 透過 Infra 派發 MQTT 指令給兌幣卡
       │ Topic: kiosk/{chip_id}/cmd
       │ Payload: {"command": "enable"}
       ▼
[ESP32 兌幣卡 (Fio)]
       │ 驅動紙鈔機 (ICT 104U) 亮起綠色投幣指示燈，脫離 DISABLED 保護態
       │
[玩家投鈔] 投入一張新台幣 100 元紙鈔
       │
       ▼
[紙鈔機 104U]
       │ 1. 馬達捲入紙鈔，光學/磁性防偽驗證通過
       │ 2. 停留在 Escrow 閘門位置，不壓入錢箱
       │ 3. 透過 RS232 回報 ESP32: bill_accepted, bill_value = 100
       ▼
[ESP32 兌幣卡]
       │ 發布 MQTT 事件: kiosk/{chip_id}/event
       │ Payload: {"event_type": "escrow", "amount": 100, "currency": "TWD"}
       ▼
[Infra Listener] 轉發 Webhook 給 Member
       ▼
[Member 後端]
       │ 1. 建立 pending 交易
       │ 2. 廣播 WebSocket 事件 KioskEscrowPending 至 iHub 平板頻道
       ▼
[iHub 平板介面]
       │ 螢幕彈出提示：「收到 100 元，將充值 100 代幣，請按確認」
       │
[人工按鈕確認] 現場服務員或玩家在平板螢幕點擊【確認入箱】
       │
       ▼
[iHub 平板] POST https://api.tg25.win/api/kiosk/escrow/confirm
       ▼
[Member 後端] 驗證成功，透過 Infra 發布 MQTT: {"command": "stack"}
       ▼
[ESP32 兌幣卡] 透過 RS232 發送壓箱指令至 104U
       │
       ▼
[紙鈔機 104U] 馬達轉動將 100 元壓入防盜保險箱，光耦閉合
       │ 回報 ESP32: bill_stacked
       ▼
[ESP32 兌幣卡] 發布 MQTT: {"event_type": "bill_stacked", "amount": 100}
       ▼
[Member 後端]
       │ 1. 寫入 member_wallets 增加 100 TOKEN (整數)
       │ 2. 寫入 wallet_transactions 審計流水
       │ 3. 結束 kiosk_sessions
```

---

## 6. 流程五：機械碼表脈衝稽核與日結流 (UI3/UI4)

為了杜絕現場人員私自拔線、偷投幣、或作弊器干擾，系統維持獨立的硬體機械碼表稽核流：

```
[實體入幣/出幣機械碼表]
       │
       │ 機台內部每次計數器轉動產生一個方波
       ▼
[ESP32 UI3 (GPIO 13) / UI4 (GPIO 14)]
       │
       │ 硬體 PCNT 自動累計 raw_value (無任何軟體運算阻礙)
       │ 定期 (每 60 秒或累積 50 脈衝) 發布 MQTT event
       ▼
[Infra Listener & Central DB (iotv9)]
       │
       │ 記錄於 iotv9.signal_events，保留原始 raw_value 里程表
       ▼
[日結清算腳本 (Daily Reconciliation Batch)]
       │
       │ 每日凌晨 04:00 自動執行：
       │ 計算：碼表增量 (Delta Meter) = 本日 raw_value 結尾 - 昨日 raw_value 結尾
       │ 計算：開分結算總額 (Total Actual Points) = SUM(actual_points from Webhooks)
       │
       ▼
[比對稽核]
  - 若 (Delta Meter * 換算比例) == Total Actual Points ──> 【綠燈：對帳無誤】
  - 若 (Delta Meter * 換算比例) != Total Actual Points ──> 【紅燈：報警，存在漏帳或偷開分】
```


---

## 7. Webhook 重試機制與死信保護 (Retry Policy & Dead Letter) 【已實作】

SignalHub 針對第三方遊戲商 (如小猴) 實作強韌的重試機制，由 Laravel 隊列 (\`ProcessWebhookDelivery\` Job) 統一調度：

### 7.1 三段式階梯重試時序 (0s, 3s, 6s)
1. **第一次嘗試 (T + 0s)**：採集卡事件抵達後，非同步佇列立即嘗試向第三方 Webhook URL 發送 POST。
2. **第二次嘗試 (T + 3s)**：若遭遇網路逾時 (Timeout > 3s)、HTTP 5xx 錯誤或連線被拒，系統等待 3 秒後觸發第一次重試。
3. **第三次嘗試 (T + 9s)**：若仍未收到正確 HTTP 200 回應，系統再等待 6 秒進行第二次重試。
4. **標記失敗與死信 (Failed / Dead Letter)**：連續 3 次失敗後，該筆派送紀錄標記為 \`status: failed\`，寫入失敗錯誤日誌 (\`error_message\`)，並觸發運維警報。

### 7.2 店主手動批量重試端點
店主或工程師可透過後台介面或 API 針對失敗紀錄進行單筆或批量重試：
- 單筆重試：\`POST /api/v9/signal-hub/deliveries/{id}/retry\`
- 批量重試：\`POST /api/v9/signal-hub/deliveries/batch-retry\`

---

## 8. 端點呼叫範例與 cURL 查驗速查 (API cURL Cheatsheet) 【已驗證】

### 8.1 內部信號寫入端點 (MQTT Listener -> SignalHub)
\`\`\`bash
curl -X POST "https://signal.tg25.win/api/internal/signal/event" \
  -H "Content-Type: application/json" \
  -H "X-Internal-Key: v9-internal-key-2026" \
  -d '{
    "chip_id": "df1e4c4b1105",
    "pin": "UI1",
    "event_type": "credit_in",
    "raw_value": 10582,
    "delta_value": 1,
    "occurred_at": 1725339600
  }'
\`\`\`

### 8.2 異步結算回執端點 (第三方 POS -> SignalHub)
\`\`\`bash
curl -X POST "https://signal.tg25.win/api/v9/signal-hub/callback-ack" \
  -H "Content-Type: application/json" \
  -d '{
    "delivery_id": 982341,
    "status": "success",
    "actual_points": 500
  }'
\`\`\`

### 8.3 遊戲主板分數歸零端點 (遊戲電腦 -> SignalHub)
\`\`\`bash
curl -X POST "https://signal.tg25.win/api/v9/signal-hub/inbound/session-end" \
  -H "Content-Type: application/json" \
  -d '{
    "chip_id": "df1e4c4b1105",
    "event": "session_end",
    "reason": "points_cleared_to_zero",
    "last_played_duration_seconds": 348,
    "occurred_at": "2026-09-24T12:00:00+08:00"
  }'
\`\`\`
