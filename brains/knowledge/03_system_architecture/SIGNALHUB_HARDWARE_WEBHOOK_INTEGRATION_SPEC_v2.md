# WAW SignalHub 採集卡對接、現場開洗分與通訊系統設計文檔 (System Architecture & Specification)

- **文檔版本**：v2.5 (整合金融級端到端防盜、mTLS 硬體認證與動態 IP 網路規範)
- **發布日期**：2026-09-03
- **主管單位**：WAW HQ
- **適用對象**：HQ 協調員、Sidney (SignalHub 前端/API)、Coli (IOTwawS3 韌體)、Ina (Infra 資料庫)、第三方開發工程師 (小猴)

---

## 1. 業務場景與市場定位邊界

### 1.1 兩種現場模式定位
1. **模式一：已有 POS 系統的場館**
   - 現場已有成熟收銀 POS 系統，不需要額外裝採集卡做開洗分收銀。
   - 小猴等第三方開發者可透過 **WAW 主動上報 API**，將機台狀態與大數據同步至 WAW 雲端產生高階分析報表。
2. **模式二：無 POS 系統的中小型/傳統場地（WAW 核心賦能）**
   - 現場無電腦與 POS 系統，安裝 **WAW ESP32-S3 採集卡** 連接實體開洗分按鈕。
   - 由採集卡充當收銀結算中樞，精準完成每次開洗分上報、10 秒定案與統計。

---

## 2. 採集卡開洗分雙軌輸出與回覆標準 (無 POS 場地)

### 2.1 採集卡輸出 Payload (Serial & Webhook 相同)
{"delivery_id":982341,"event":"credit_in","chip_id":"df1e4c4b1105","machine_number":"M001","machine_name":"街機拳王","pin_code":"UI1","raw_value":10582,"delta_value":1,"occurred_at":"2026-09-03T11:30:00+08:00"}

### 2.2 小猴回覆規範 (3 秒內回傳實際點數 actual_points)
- **開分回覆 (credit_in)**：{"status":"success","delivery_id":982341,"actual_points":500}
- **洗分回覆 (credit_out)**：{"status":"success","delivery_id":982341,"actual_points":3250}

---

## 3. 小猴遊戲主板主動通知 API：分數歸零 (Game Over / 離場)

- **觸發條件**：遊戲機台內部分數從大於 0 變為 0 的那一瞬間。
- **端點規範**：POST https://signal.tg25.win/api/v9/signal-hub/inbound/session-end
- **Request Payload**：
{
  "chip_id": "df1e4c4b1105",
  "machine_number": "M001",
  "event": "session_end",
  "reason": "points_cleared_to_zero",
  "last_played_duration_seconds": 348,
  "occurred_at": "2026-09-03T11:45:00+08:00"
}

---

## 4. 端到端防盜與安全機制架構 (End-to-End Security)

### 4.1 採集卡 -> WAW Server (硬體上報防盜 4 重防線)
1. **mTLS 雙向硬體證書認證 (8883 端口)**：
   - 採集卡出廠內嵌晶片私鑰 (client.crt / client.key)，非授權 ESP32 設備根本無法連上 MQTT Broker。
2. **現場動態/浮動 IP 適配 (零白名單阻礙)**：
   - 釣蝦場、遊樂場現場 Wi-Fi / 4G 網卡為動態 DHCP 浮動 IP。採集卡採主動對外連線 (Outbound mTLS)，**伺服器端無須設置現場 IP 白名單**，現場隨插即用、秒連不掉線。
3. **64-bit 單調遞增里程數 (raw_value)**：
   - 物理計數只能變大不能變小，Server 檢驗若收到小於或等於歷史值的里程數，直接判定作弊攔截。
4. **動態流水號 (msg_id) + 毫秒時間戳**：
   - 杜絕網路抓包重放攻擊 (Anti-Replay Attack)，超過 30 秒或重複單號自動作廢。

### 4.2 WAW Server -> 小猴伺服器 (雲端 Webhook 防偽 4 重防線)
1. **HMAC-SHA256 數位簽名**：
   - Header 帶入 X-WAW-Signature = HMAC_SHA256(secret_key, raw_body)。小猴端驗簽失敗直接 401 拒絕，外人無法偽造假開分。
2. **時間戳時效檢查 (X-WAW-Timestamp)**：
   - 超過 5 分鐘的請求直接作廢，防範中間人重放。
3. **delivery_id 唯一冪等性校驗**：
   - 小猴資料庫以 delivery_id 為 Unique Key，已入帳單號自動去重，絕不重複給分。
4. **WAW Server 固定出站 IP 白名單 (選用)**：
   - 小猴端防火牆可設定僅允許 WAW 官方固定伺服器 IP 請求。

---

## 5. 10 秒極速定案與 0.6MB/2天日誌規範
- 10 秒超時判定失敗，立即觸發 LINE/TG/站內告警。
- 日誌單檔超過 0.6MB 自動切換新檔，僅保留 2 天。
