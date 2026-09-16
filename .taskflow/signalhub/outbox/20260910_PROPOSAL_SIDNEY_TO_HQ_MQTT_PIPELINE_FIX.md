# 技術方案與協同請示：20260910_PROPOSAL_SIDNEY_MQTT_PIPELINE_FIX

**提交時間**：2026-09-10 00:45  
**提交者**：Sidney (SignalHub Lead)  
**呈報對象**：HQ (Taskflow 總指揮)  
**協同對象**：Ina (Infra Lead), Coli (Firmware Lead)  
**主旨**：實體採集卡 MQTT 上報至 SignalHub 鏈路中斷原因診斷報告與修復方案請示  
**優先級**：critical  

---

## 1. 問題背景與現象

Boss (Joe) 回報已完成實體 ESP32-S3 採集卡（chip_id: 3c0f02d09118）按鈕接線，硬體端（Coli 韌體監聽）正常輸出：
- MQTT: Publish standard signal event: waw/v1/default/signal/3c0f02d09118/event
- SIGNAL: UI4 +1，64-bit 累計 8
- USB_CDC: USB 輸出成功: {"delivery_id":955606,"event":"pulse","chip_id":"3c0f02d09118","pin":"UI4","raw":8,"delta":1,"ts":1788970360}

但後台及 Mock 接收端（https://signal.tg25.win/mock/callback）未收到任何事件與派送。

---

## 2. 伺服器現場診斷實證（斷點定位）

經過調閱主機日誌與程式碼進行逐層檢驗，已精確鎖定鏈路斷點：

### ① 【正常】硬體 -> Mosquitto Broker（141.148.165.50:8883）
- 伺服器日誌（/var/log/mosquitto/mosquitto.log）：
  - 1788971136: Received PINGREQ from waw-esp32-3c0f02d09118
  - 1788971136: Sending PINGRESP to waw-esp32-3c0f02d09118
  - 1788971139: Received PUBLISH from waw-esp32-3c0f02d09118 (d0, q1, r0, m29284, 'waw/v1/default/signal/3c0f02d09118/event', ... (400 bytes))
  - 1788971139: Sending PUBACK to waw-esp32-3c0f02d09118 (m29284, rc0)
- 結論：硬體 mTLS 憑證通過、心跳正常、Publish 成功，Broker 已正確回覆 PUBACK。

### ② 【斷點】Mosquitto Broker -> 0 訂閱者（丟棄訊息）
- 對比傳統機台主題（如 device/+/data/credit_in）會立即出現 Sending PUBLISH to C7FA3667...。
- 本次硬體發布 waw/v1/default/signal/3c0f02d09118/event 時，Broker 日誌沒有任何發送給訂閱者的記錄，表示目前沒有任何客戶端訂閱該 Topic。

### ③ 【斷點核心】Infra 中繼監聽器（listener.py）未接入
- 檢閱 /home/ubuntu/tg25-infra/mqtt/scripts/listener.py（Infra 負責）：
  1. 第 46 行 MQTT_TOPICS 僅訂閱 device/+/... 與 kiosk/+/...，未訂閱 waw/v1/+/signal/+/event。
  2. 程式碼中完全沒有 SIGNALHUB_API_URL（即 https://signal.tg25.win/api/internal/signal/event）之定義。
  3. on_message 回調中完全沒有處理 WAW-USS 信號事件之邏輯。

### ④ 【格式需適配】MQTT Payload 數據結構差異
- 檢閱 ESP32-S3 C 語言源碼（IOTwawS3/src/services/mqtt_service.c:220），標準發布為全腳位快照格式（400 bytes），包含 signals 物件。
- SignalHub 現有內部接口需增強以原生支援此快照結構，自動辨別數值變化的腳位。

### ⑤ 【正常】SignalHub 內部事件 -> Webhook 派發
- 已在先前測試驗收通過（Delivery ID 26~29 均為 HTTP 200）。只要數據進入 signal_events，Webhook 派發即刻成功。

---

## 3. 解決方案與協同分工建議

### 【任務 A】Ina (Infra Master) — 修改中央監聽器
1. 修改檔案：PROJECT/Infra/mqtt/scripts/listener.py
2. 新增主題訂閱：MQTT_TOPICS 增加 ("waw/v1/+/signal/+/event", 1)
3. 新增 API 配置：
   - SIGNALHUB_API_URL = "https://signal.tg25.win/api/internal/signal/event"
   - SIGNALHUB_API_KEY = "v9-internal-key-2026"
4. 新增處理邏輯：
   當 Topic 符合 waw/v1/+/signal/+/event 時，將 Payload 攜帶 X-Internal-Key: v9-internal-key-2026 轉打至 SIGNALHUB_API_URL。
5. 部署重啟：systemctl restart mqtt-listener.service

### 【任務 B】Sidney (SignalHub Lead) — 適配快照解析
1. 修改檔案：PROJECT/SignalHub/app/Http/Controllers/Api/SignalHubApiController.php
2. 支援格式：
   storeEvent 增加判斷，若接收到含有 signals 字典的 WAW-USS 快照，自動遍歷各腳位：
   - 讀取資料庫該腳位之最新 raw_value
   - 若本次數值大於歷史值，計算 delta_value = raw_value - last_raw_value
   - 寫入 signal_events 並觸發 Webhook 推送
3. 部署上線：依 SOP 提交 Git、Push、遠端部署並驗證。

---

## 4. 請示事項

請 HQ 審核此排查結果與分工方案：
1. 是否批准由 HQ 向 Ina 派發【任務 A】或授權協同調整 listener.py？
2. 是否批准 Sidney 執行【任務 B】以完整支援 WAW-USS 規範之信號快照？

待 HQ 指示確認無誤後，即刻啟動代碼修改與部署。
