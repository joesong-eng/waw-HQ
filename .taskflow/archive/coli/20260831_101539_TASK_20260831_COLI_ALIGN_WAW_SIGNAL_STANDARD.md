# 任務：TASK_20260831_COLI_ALIGN_WAW_SIGNAL_STANDARD

**派發時間**：2026-08-31 10:15  
**優先級**：1  
**負責人**：coli

---

## 📋 任務內容

請依據 PROJECT/SignalHub/docs/WAW_SIGNAL_STANDARD_v1.0.md 規範進行 IOTwawS3 韌體標準化對齊：1. 保持實體 GPIO 腳位不變（UI1~UI4=13,14,1,2; UO1~UO4=45,46,47,48）。2. 統一採用 64-bit 單調遞增里程表 raw_value 上報，移除僅依賴 Delta 的邏輯。3. 對齊標準 MQTT Topic (waw/v1/{site_id}/signal/{chip_id}/event) 與 JSON Payload (signals 物件)。4. 同步更新 IOTwawS3 專案內所有相關設計文件、架構說明與 Markdown 文檔。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260831_COLI_ALIGN_WAW_SIGNAL_STANDARD

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：coli

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：coli  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-08-31 10:15
