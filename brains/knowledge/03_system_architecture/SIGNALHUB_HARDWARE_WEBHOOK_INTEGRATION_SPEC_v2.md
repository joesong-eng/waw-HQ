# WAW SignalHub 採集卡對接、現場開洗分與通訊系統設計文檔 (System Architecture & Specification)

- **文檔版本**：v2.7 (純硬體觸發架構、移除 amount/unit/pulse_ratio 冗餘換算欄位、對齊 UI1/UI2 雙軌返回機制與 actual_points 規範)
- **發布日期**：2026-09-08
- **主管單位**：WAW HQ
- **適用對象**：HQ 協調員、Sidney (SignalHub 前端/API)、Coli (IOTwawS3 韌體)、Ina (Infra 資料庫)、第三方開發工程師 (小猴/合作商)

---

## 1. 業務場景與市場定位邊界

### 1.1 兩種現場模式定位
1. **模式一：已有 POS 系統的場館**
   - 現場已有成熟收銀 POS 系統，不需要額外裝採集卡做開洗分收銀。
   - 小猴等第三方開發者可透過 **WAW 主動上報 API**，將機台狀態與大數據同步至 WAW 雲端產生高階分析報表。
2. **模式二：無 POS 系統的中小型/傳統場地（WAW 核心賦能）**
   - 現場無電腦與 POS 系統，安裝 **WAW ESP32-S3 採集卡** 連接實體開洗分按鈕與投退幣光耦。
   - 由採集卡充當物理信號收銀結算中樞，精準完成每次開洗分上報、3秒超時重試、10秒定案與後台營運利潤統計。

### 1.2 核心原則：純硬體信號上報，不擅自干預點數與金額
- **歷史問題**：舊版設計沿用販賣機的 amount、unit、pulse_ratio 欄位，在後台擅自將脈衝次數乘上固定倍率轉換成「金額」。
- **新規確立**：遊戲機台（特別是開洗分）的點數倍率與洗分量是由現場遊戲主機與遊戲商系統自行控制，採集卡與 SignalHub **無從得知、也不應擅自定義**遊戲幣值。
- **純觸發定義**：採集卡觸發開分（UI1）或洗分（UI2）時，SignalHub 僅上報「純硬體觸發消息」（物理累計里程 raw_value 與單次差額 delta_value: 1），**絕不夾帶金額或換算比例**。實際開分或洗分點數/金額，統一由第三方遊戲商伺服器在回覆中帶回 actual_points。

---

## 2. 採集卡開洗分雙軌輸出與回覆標準 (無 POS 場地)

### 2.1 SignalHub 派發輸出 Payload (純硬體觸發規範)
當現場光耦或硬體模擬器觸發 UI1（開分）或 UI2（洗分）時，後台 Dispatcher 主動向第三方 HTTP(S) Endpoint 發送 POST：

```json
{
  "event_id": "evt_23",
  "delivery_id": "del_10284",
  "chip_id": "C8F09E010004",
  "profile_id": 21,
  "pin_code": "UI1",
  "pin_label": "開分",
  "event_type": "counter",
  "raw_value": 1582,
  "delta_value": 1,
  "reply_url": "https://signal.tg25.win/api/v9/signal-hub/callback-ack",
  "event_at": "2026-09-08T08:18:54+00:00",
  "timestamp": "2026-09-08T08:18:54+00:00"
}
```

#### 欄位定義說明：
- **event_id**：底層事件唯一識別碼（如 evt_23）。
- **delivery_id**：本次 Webhook 推送的唯一交易單號（如 del_10284）。**重試時此單號完全不變**，第三方必須作為去重與冪等保證之 Unique Key。
- **chip_id**：採集卡硬體唯一晶片號（ESP32 MAC ID，如 C8F09E010004），確保第三方明確知道是哪一張卡/哪台機台。
- **profile_id**：對應的信號配置檔案 ID。
- **pin_code**：觸發腳位代碼（UI1 為開分，UI2 為洗分，其他 UI/UO 依腳位映射定義）。
- **pin_label**：腳位名稱標籤（如「開分」、「洗分」）。
- **event_type**：事件類型（計數器脈衝統一為 counter）。
- **raw_value**：ESP32 硬體計數器累計總量（物理總里程，單調遞增防作弊）。
- **delta_value**：本次新增觸發次數（單次觸發為 1）。
- **reply_url**：當第三方需採用異步回傳時之專用回調端點（如 https://signal.tg25.win/api/v9/signal-hub/callback-ack）。URL 採用標準 JSON 字串傳輸，無任何轉義解析問題。
- **event_at** / **timestamp**：硬體事件發生時間與推送時間 (ISO 8601 格式)。

#### HTTP 自訂 Headers：
- **X-WAW-Delivery**：del_10284（交易單號）
- **X-WAW-Signature**：sha256={HMAC_SHA256(secret_key, raw_body)}（數位簽章，防篡改與防偽造）
- **X-WAW-Event**：signal.counter
- **X-WAW-Timestamp**：1725783534
- **User-Agent**：WAW-SignalHub/1.0

---

### 2.2 第三方接收端回覆規範 (對稱回傳 actual_points)

無論是開分 (UI1) 還是洗分 (UI2)，第三方收到觸發通知後，都必須回傳實際發生的開洗分點數/金額 actual_points。

#### A. 開分回覆 (UI1 - credit_in)：
```json
{
  "status": "success",
  "delivery_id": "del_10284",
  "chip_id": "C8F09E010004",
  "pin_code": "UI1",
  "action_type": "credit_in",
  "actual_points": 1000,
  "message": "開分確認入帳",
  "timestamp": "2026-09-08T08:18:55+00:00"
}
```

#### B. 洗分回覆 (UI2 - credit_out)：
```json
{
  "status": "success",
  "delivery_id": "del_10284",
  "chip_id": "C8F09E010004",
  "pin_code": "UI2",
  "action_type": "credit_out",
  "actual_points": 3500,
  "message": "洗分結算完成",
  "timestamp": "2026-09-08T08:18:55+00:00"
}
```

#### 回覆欄位說明：
- **status**：處理結果（"success" 表示入帳/結算成功）。
- **delivery_id**：對應的交易單號，必須與收到的 delivery_id 一致。
- **chip_id**：採集卡晶片號，對齊設備。
- **pin_code**：對應觸發之腳位代碼（UI1 或 UI2）。
- **action_type**：業務動作類型（開分為 credit_in，洗分為 credit_out）。
- **actual_points**：**核心數值**。遊戲端實際操作的開分數或洗分數（純數值，如 1000、3500）。後台據此計入營業報表計算店內實收與利潤。
- **message** / **timestamp**：處理說明文字與回覆時間戳。

---

### 2.3 雙軌返回模式 (同步原路返回 vs 異步 reply_url)

為了滿足不同第三方開發者的系統架構偏好，SignalHub 支援完全對等的雙軌返回機制：

#### 模式一：同步原路返回 (首選、推薦)
- **架構優勢**：無需任何額外 HTTP 往返與連線開銷，毫秒級完成。
- **執行方式**：第三方接收端伺服器在接收到 SignalHub 的 POST 請求後，在同一個 HTTP 連線內，於 **3 秒內** 回傳 HTTP 200 OK，並在 HTTP Response Body 中直接附帶上述 JSON。
- **適用場景**：第三方能快速完成開洗分記帳（絕大多數場景建議採用此方式）。

#### 模式二：異步回調 (備選，針對長耗時業務)
- **架構優勢**：第三方無需保持長連線，避免因自身業務計算拖延造成 HTTP 超時斷線。
- **執行方式**：
  1. 第三方收到 POST 請求後，立即回傳 HTTP 200 OK（空內容或表示收到）。
  2. 第三方內部進行耗時結算或跨系統核算。
  3. 結算完成後，在 **10 秒內** 主動向 Payload 中攜帶的 reply_url（如 https://signal.tg25.win/api/v9/signal-hub/callback-ack）發送 HTTP POST，Body 攜帶上述相同的 JSON 內容。
  4. SignalHub 接收到該 POST 後，根據 delivery_id 自動將對應記錄更新為 success，並記錄實際點數 actual_points。

---

## 3. 異常處理、3秒超時、重試排程與 10 秒極速定案

### 3.1 3秒超時與 0s/3s/6s 重試
1. **單次超時**：SignalHub 向第三方發起 HTTP POST 的連線超時時間嚴格限制為 **3 秒**。
2. **同單號重試排程**：
   - 若 3 秒內未收到 HTTP 200 OK，或網路連線拋出異常（如 Connection Refused、DNS 失敗、5xx 錯誤），系統將啟動重試機制。
   - 重試時，**保持完全相同的 delivery_id**（絕不更換單號，保障第三方冪等去重）。
   - 重試間隔：**0s ➔ 3s ➔ 6s**（最多重試 3 次）。

### 3.2 10 秒極速定案失敗 (Expired) 與人工對帳防線
- **定案機制**：若經過三次重試、累計超過 10 秒第三方伺服器始終未能成功回覆，SignalHub 將該筆推送記錄標記為 expired（過期失效），終止自動重試。
- **即時系統告警**：觸發 webhook 失敗即時告警（站內通知、LINE/TG 機器人告警），標註晶片號、腳位與單號。
- **人工查帳機制**：
  - 若第三方系統「有執行開/洗分，但因網路中斷導致 SignalHub 沒收到回覆」，雙方系統均有完整日誌（SignalHub 端有 delivery_id、raw_value 里程數；第三方有接收記錄）。
  - 後台提供 Webhook 交付日誌（/signal-hub/webhooks）與硬體終端歷史，管理員可輸入單號一鍵對帳，確認實際分數後手動補單，保證帳目分毫不差。

---

## 4. 端到端防盜與安全機制架構 (End-to-End Security)

### 4.1 採集卡 ➔ WAW Server (硬體上報 4 重防線)
1. **mTLS 雙向硬體證書認證 (8883 端口)**：
   - 採集卡出廠內嵌晶片私鑰與雙向證書 (client.crt / client.key)，非授權 ESP32 設備根本無法連上 MQTT Broker。
2. **現場動態/浮動 IP 適配 (零白名單阻礙)**：
   - 現場 Wi-Fi / 4G 網卡為動態 DHCP 浮動 IP。採集卡採主動對外連線 (Outbound mTLS)，伺服器端無須設置現場 IP 白名單，現場隨插即用、秒連不掉線。
3. **64-bit 單調遞增里程數 (raw_value)**：
   - 物理計數只能變大不能變小，Server 檢驗若收到小於或等於歷史值的里程數，直接判定作弊攔截。
4. **動態流水號 (msg_id) + 毫秒時間戳**：
   - 杜絕網路抓包重放攻擊 (Anti-Replay Attack)，超過 30 秒或重複單號自動作廢。

### 4.2 WAW Server ➔ 第三方伺服器 (雲端 Webhook 防偽 4 重防線)
1. **HMAC-SHA256 數位簽名**：
   - Header 帶入 X-WAW-Signature = sha256={HMAC_SHA256(secret_key, raw_body)}。第三方驗簽失敗直接 401 拒絕，任何偽造請求均無法被採納。
2. **時間戳時效檢查 (X-WAW-Timestamp)**：
   - 超過 5 分鐘的請求直接作廢，防範中間人重放。
3. **delivery_id 唯一冪等性校驗**：
   - 第三方資料庫以 delivery_id 為 Unique Key，已入帳單號自動去重，重試不重複給分。
4. **WAW Server 固定出站 IP 白名單**：
   - SignalHub 主機固定出站 IP：129.153.116.174。第三方防火牆可限制只接受此 IP 之請求。

---

## 5. 小猴遊戲主板主動通知 API：分數歸零 (Game Over / 離場)

- **觸發條件**：遊戲機台內部分數從大於 0 變為 0 的那一瞬間（代表單局結束、玩家離場）。
- **端點規範**：POST https://signal.tg25.win/api/v9/signal-hub/inbound/session-end
- **Request Payload**：
```json
{
  "chip_id": "C8F09E010004",
  "machine_number": "M001",
  "event": "session_end",
  "reason": "points_cleared_to_zero",
  "last_played_duration_seconds": 348,
  "occurred_at": "2026-09-08T11:45:00+08:00"
}
```
