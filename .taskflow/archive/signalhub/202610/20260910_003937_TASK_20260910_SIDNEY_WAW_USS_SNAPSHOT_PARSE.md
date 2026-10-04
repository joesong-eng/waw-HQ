# 任務：TASK_20260910_SIDNEY_WAW_USS_SNAPSHOT_PARSE

**派發時間**：2026-09-10 00:39  
**優先級**：critical  
**負責人**：signalhub

---

## 📋 任務內容

【MQTT 鏈路修復】SignalHub 適配 WAW-USS 全腳位快照格式解析。背景：ESP32-S3 採集卡發送的 MQTT Payload 為全腳位快照格式（約400 bytes，包含 signals 字典），現有 storeEvent 介面需擴充以原生支援此格式。必做項目（修改 PROJECT/SignalHub/app/Http/Controllers/Api/SignalHubApiController.php）：1. storeEvent 新增快照格式判斷：若 request body 包含 signals 字典（WAW-USS 快照），遍歷每個腳位：查最新 raw_value、若本次 raw_value > last_raw_value 計算 delta 並寫入 signal_events 觸發 Webhook；若為單一事件格式則維持原有邏輯；2. 提交 Git、Push；3. 遠端部署 signal.tg25.win、清除快取、重啟服務；4. 回報 API 路由確認。協同：Ina 同步執行任務 A，待兩端就緒後進行端對端測試。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260910_SIDNEY_WAW_USS_SNAPSHOT_PARSE

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：signalhub

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：signalhub  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-09-10 00:39
