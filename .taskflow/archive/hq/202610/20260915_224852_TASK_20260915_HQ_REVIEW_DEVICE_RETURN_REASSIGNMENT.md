# 任務：TASK_20260915_HQ_REVIEW_DEVICE_RETURN_REASSIGNMENT

**派發時間**：2026-09-15 22:48  
**優先級**：critical  
**負責人**：hq

---

## 📋 任務內容

審核重大跨廠商設備交接修改方案：以本次 device 43 / chip_id 3c0f02d42720 為例，老李舊歸屬與家寶新歸屬不可混合。請核定：1) 新增 device_assignments 作設備交接與歷史所有權 SSOT；2) signal_events 與 signal_webhook_deliveries 寫入 owner_id、assignment_id、order_id 歷史快照與索引；3) 退貨為 transaction 解綁與封存，清空 device 現役 owner/order/machine，但永不刪 event、delivery、profile、webhook 歷史；4) 新出貨限 device 無 owner、無 active assignment/profile 後才可綁新廠商；5) 廠商查詢、權限、統計採 owner_id+assignment_id，禁止依現況 device owner 或單一 chip_id 推斷歷史；6) 退貨後設備上報，建議建立未歸屬稽核、HTTP 202、不發任何廠商 webhook；7) 授權後由 Sidney 實作 migration、交易服務、後台解綁 UI、查詢改造與老李/退貨/家寶實機驗收。補充：本次老李 profile 34 資料按前一指令已被刪除，正式 DB 無該 136 event/delivery，需 HQ 決定是否由備份或合作端紀錄嘗試復原。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260915_HQ_REVIEW_DEVICE_RETURN_REASSIGNMENT

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：hq

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：hq  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-09-15 22:48
