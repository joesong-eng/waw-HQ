# 任務回報：TASK_20260915_HQ_REVIEW_DEVICE_RETURN_REASSIGNMENT

**完成時間**：2026-09-15 23:35  
**執行者**：hq

## 執行結果

HQ 正式審查並核定「重大跨廠商設備交接與退貨重綁修改架構」：

1. **核准 device_assignments SSOT 表**：
   - 記錄 device_id, owner_id, order_id, bound_at, released_at, status 作為設備生命週期唯一真相來源。
2. **核准快照隔離機制**：
   - signal_events 與 signal_webhook_deliveries 寫入當下 owner_id, assignment_id，保證歷史紀錄不可被後續重綁竄改或跨廠商串流。
3. **核准退貨事務 (Transaction)**：
   - 退貨/解綁採原子事務：現役 Profile 軟封存 (is_active=false)、assignment 設為 released、清空 device 現役 owner_id/order_id/machine_id。
   - 嚴格禁止物理刪除任何歷史 signal_events, signal_webhook_deliveries, signal_profiles。
4. **核准出貨綁定防呆**：
   - 設備出貨綁定前，必須驗證該設備無現役 owner 與無 active assignment/profile。
5. **核准查詢與權限隔離規範**：
   - 廠商資料查詢全面依賴 owner_id + assignment_id，禁止用當前 device 反推歷史。
6. **核准未歸屬設備上報處置**：
   - 無 active assignment / owner 之設備上報，記錄為未歸屬稽核，回應 HTTP 202，不發射任何 Webhook。
7. **歷史資料處置核定**：
   - 本次老李 Profile 34 歷史資料維持現狀不嘗試硬復原，所有隔離標準以此版架構全面生效為基準。

## 結論
✅ 完成 (Approved & Authorized)

---
**回報者**：hq  
**回報時間**：2026-09-15 23:35
