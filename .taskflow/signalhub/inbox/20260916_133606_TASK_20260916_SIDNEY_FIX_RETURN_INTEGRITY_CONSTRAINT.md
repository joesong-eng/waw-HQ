# 任務：TASK_20260916_SIDNEY_FIX_RETURN_INTEGRITY_CONSTRAINT

**派發時間**：2026-09-16 13:36  
**優先級**：critical  
**負責人**：sidney

---

## 📋 任務內容

E2E 驗收退貨失敗：devices 表的 owner_id 欄位在 DB 為 NOT NULL (bigint unsigned)，DeviceAssignmentService::return 執行 ->update(['owner_id' => null, 'status' => 'returned']) 觸發 SQLSTATE[23000] Column 'owner_id' cannot be null。請立即評估：1) 若退貨清空 owner，需建立 migration 將 devices.owner_id 改為 nullable；或 2) 改以 0 / 系統保留庫存帳號代表已退貨；並修復相關邏輯與部署。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260916_SIDNEY_FIX_RETURN_INTEGRITY_CONSTRAINT

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：sidney

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：sidney  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-09-16 13:36
