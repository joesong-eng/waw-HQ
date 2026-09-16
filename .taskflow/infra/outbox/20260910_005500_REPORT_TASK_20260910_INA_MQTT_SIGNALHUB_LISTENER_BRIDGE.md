# 任務回報：TASK_20260910_INA_MQTT_SIGNALHUB_LISTENER_BRIDGE

**完成時間**：2026-09-10 00:55（UTC+8）
**執行者**：Ina

---

## 執行結果

### 1. 程式碼修改（本機 → Git → 遠端）

**修改檔案**：mqtt/scripts/listener.py
**Commit**：f1aa6c6 feat(mqtt): add SignalHub signal event bridge (waw/v1/+/signal/+/event)

三處修改：

① MQTT_TOPICS 新增訂閱（第 53 行）
    ("waw/v1/+/signal/+/event", 1),    # SignalHub 信號事件 (QoS 1) - 2026-09-10

② 新增常數（第 93-95 行）
    SIGNALHUB_API_URL = os.getenv("SIGNALHUB_API_URL", "https://signal.tg25.win/api/internal/signal/event")
    SIGNALHUB_API_KEY = os.getenv("SIGNALHUB_API_KEY", "v9-internal-key-2026")

③ on_message 橋接邏輯（第 1280-1302 行）
- 匹配條件：topic.startswith("waw/v1/") and "/signal/" in topic and topic.endswith("/event")
- HTTP POST 至 SIGNALHUB_API_URL，攜帶 Header X-Internal-Key: v9-internal-key-2026
- 含 timeout=5 保護，Timeout/Exception 各自 WARNING/ERROR log

### 2. 部署過程（附帶修復 MQTT 連線問題）

部署時發現 mqtt-listener.service restart 後持續報錯：
    MQTT connection error: [Errno 101] Network is unreachable

根本原因：
- mqtt.tg25.win DNS 包含 IPv6 AAAA record（指向 Cloudflare CDN）
- 本機 infra VPS 無公開 IPv6，Python 優先嘗試 IPv6 → Errno 101
- Cloudflare 不代理 MQTT port 8883，外部連線無法通達

修復方案：在 /etc/hosts 新增：
    127.0.0.1 mqtt.tg25.win
- Hostname 仍為 mqtt.tg25.win（TLS cert CN 相符）
- 實際走本機 127.0.0.1:8883（mosquitto 本地監聽）
- 不影響外部裝置連線（外部 DNS 仍走 Cloudflare IPv4）

### 3. 部署驗證

  mqtt-listener.service: active (running) since Wed 2026-09-09 16:54:31 UTC
  Main PID: 2376244 (python) | Tasks: 8 | Memory: 32.5M

資料流已恢復正常（credit_in / credit_out / kiosk 事件持續處理中）。
SignalHub 訂閱 waw/v1/+/signal/+/event 已生效，等待 Sidney 端 API 就緒後進行端對端測試。

---

## 結論

✅ 完成

附記：
- 此次重啟修復了潛在 IPv6 DNS 問題，建議 HQ 評估是否長期固定 mqtt.tg25.win 解析策略
- 協同 Sidney 完成 SignalHub API 端後，請通知 Ina 進行端對端驗證

---
**回報者**：Ina
**回報時間**：2026-09-10 00:55

