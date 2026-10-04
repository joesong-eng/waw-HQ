
# 任務：TASK_20260903_SIDNEY_SIGNALHUB_WIZARD_AND_DELIVERIES

**派發時間**：2026-09-03 12:47  
**優先級**：High  
**負責人**：Sidney (SignalHub 前端與 API Lead)

---

## 📋 任務核心要求

1. **三步極速設置精靈 (UI)**：
   - 參考 `iot.tg25.win/devices` 暗色風格，在 `signal.tg25.win` 首頁呈現「待設置設備」卡片。
   - 實作 3 步設置對話框：機台編號/名稱 ➔ 腳位定義 ➔ 通道選擇 (USB/Webhook)。
2. **10 秒極速定案與重試機制**：
   - 實作 Webhook 發送第 1 次 (0s)、第 2 次 (3s)、第 3 次 (6s)，10 秒超時判定。
   - 超時立即呼叫 NotificationService 觸發 LINE / TG / 站內彈窗告警。
3. **洗分回覆與營運報表入庫**：
   - 解析小猴 Webhook 回覆中的 `cleared_points` 與 `remaining_balance`，寫入洗分報表資料表。
4. **0.6MB / 2 天滾動日誌系統**：
   - 實作 `storage/logs/signal_events/` 自動切檔與 48 小時過期清理排程。

