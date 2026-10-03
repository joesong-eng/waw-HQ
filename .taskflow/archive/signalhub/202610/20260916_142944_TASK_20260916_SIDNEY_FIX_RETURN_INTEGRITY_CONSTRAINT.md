# 任務：TASK_20260916_SIDNEY_FIX_RETURN_INTEGRITY_CONSTRAINT

**派發時間**：2026-09-16 14:29  
**優先級**：critical  
**負責人**：signalhub

---

## 📋 任務內容

回報完成。採方案1: 新 migration 2026_09_16_140000_make_devices_owner_id_nullable 將 devices.owner_id 改 nullable。選擇理由：退貨後 device 真實無歸屬，NULL 語意最正確；偽帳號方案造成外鍵偽關聯與長期查詢複雜度。遠端驗證：HEAD=da65dc5，Batch 16 已執行，SHOW COLUMNS Null=YES，DeviceAssignmentService::return() update owner_id=null 不再觸發 SQLSTATE[23000]。退貨流程 integrity constraint 已解除。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260916_SIDNEY_FIX_RETURN_INTEGRITY_CONSTRAINT

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
**派發時間**：2026-09-16 14:29
