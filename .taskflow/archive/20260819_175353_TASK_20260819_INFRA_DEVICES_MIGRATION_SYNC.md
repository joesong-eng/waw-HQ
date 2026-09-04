# 任務：TASK_20260819_INFRA_DEVICES_MIGRATION_SYNC

**派發時間**：2026-08-19 17:53  
**優先級**：high  
**負責人**：Ina

---

## 📋 任務內容

### 1. devices 表 Migration 執行與同步
- 審核 Sophie 先前提出的 devices 表新欄位變更請求，於 tg25-infra 確認/執行 Migration 並同步至生產環境。
- 更新 DB_MANIFEST.md 記錄最新 Schema 變更。

### 2. 欄位更名收尾 (pulse_ratio -> pulse_to_token)
- 將相關 SQL 查詢與 Listener 中殘留的 pulse_ratio 統一變更為 pulse_to_token。
- 解除 WAW 2.0 第一階段的阻塞點。

### 3. 狀態回報
- 回報 Migration 與 SQL 修正的執行結果，以便後續進入 WAW 2.0 第二階段。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260819_INFRA_DEVICES_MIGRATION_SYNC

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：Ina

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：Ina  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-08-19 17:53
