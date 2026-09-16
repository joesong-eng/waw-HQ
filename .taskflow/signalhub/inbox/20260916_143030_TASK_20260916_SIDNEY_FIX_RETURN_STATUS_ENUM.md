# 任務：TASK_20260916_SIDNEY_FIX_RETURN_STATUS_ENUM

**派發時間**：2026-09-16 14:30  
**優先級**：critical  
**負責人**：sidney

---

## 📋 任務內容

E2E 驗收第二次中斷：devices.status 為 enum('pending_setup','active','maintenance','lost')，DeviceAssignmentService::return 執行 ->update(['owner_id' => null, 'status' => 'returned']) 觸發 SQLSTATE[01000] Data truncated for column 'status' at row 1。請立即修復：1) 若退貨設備回歸待設置，status 應設為 'pending_setup' 或 'maintenance'；或 2) migration 擴充 enum 支援 'returned'。修復後部署以完成驗收。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260916_SIDNEY_FIX_RETURN_STATUS_ENUM

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
**派發時間**：2026-09-16 14:30
