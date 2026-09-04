# 任務：TASK_20260831_SIDNEY_SIGNAL_STANDARD_DOCS

**派發時間**：2026-08-31
**優先級**：high
**負責人**：Sidney (SignalHub)
**派發者**：HQ

---

## 任務背景
signal.tg25.win 域名已正式綁定生效，並直通 SignalHub 信號設定模組。
現在需要 Sidney 開始撰寫 WAW 對外開放的《ESP32 信號採集開放標準規格書 (v1.0)》與《第三方 API / Webhook 接入指南》。

## 任務內容
1. 在 PROJECT/SignalHub/docs/ 下建立 WAW_SIGNAL_STANDARD_v1.0.md：
   - 定義 8 腳位標準 (UI1~UI4 / UO1~UO4)
   - 定義 PCNT 硬體計數與里程表模式 (Cumulative Meter)
   - 定義 MQTT 主題規範與 JSON Payload 格式
2. 在 PROJECT/SignalHub/docs/ 下建立 THIRD_PARTY_INTEGRATION_GUIDE.md：
   - 說明如何透過 Webhook 接收信號
   - 附上 Python 與 Node.js 的 HMAC-SHA256 驗簽範例代碼
3. 完成後於 .taskflow/sidney/outbox/ 提交回報。
