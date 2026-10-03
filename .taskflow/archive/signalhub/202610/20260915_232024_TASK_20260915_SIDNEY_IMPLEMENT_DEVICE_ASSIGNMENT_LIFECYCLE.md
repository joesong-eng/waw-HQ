# 任務：TASK_20260915_SIDNEY_IMPLEMENT_DEVICE_ASSIGNMENT_LIFECYCLE

**派發時間**：2026-09-15 23:20  
**優先級**：critical  
**負責人**：sidney

---

## 📋 任務內容

HQ 已核准跨廠商設備交接架構：1) 建立 device_assignments 表作為所有權 SSOT；2) signal_events 與 deliveries 補齊 owner_id, assignment_id 快照；3) 實作退貨/解綁事務與出貨前防呆校驗；4) 改造廠商查詢權限隔離；5) 未歸屬設備上報回 HTTP 202 且不發 Webhook。請建立 migration、服務邏輯與相關測試。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260915_SIDNEY_IMPLEMENT_DEVICE_ASSIGNMENT_LIFECYCLE

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
**派發時間**：2026-09-15 23:20
