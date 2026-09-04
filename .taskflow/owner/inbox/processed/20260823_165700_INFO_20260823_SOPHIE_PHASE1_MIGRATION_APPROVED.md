# 通知：INFO_20260823_SOPHIE_PHASE1_MIGRATION_APPROVED

**派發時間**：2026-08-23 16:57  
**優先級**：normal  
**負責人**：Sophie

---

## 📋 任務內容

### 【進度同步】Phase 1 DB Migration 已正式核准並派工給 Ina

HQ 已審查 Ina 的評估報告，並正式派發工單給 Ina 執行 Phase 1 的資料庫遷移工作：

1. **DB Migration 項目**：
   - `devices` 擴充 `collector_owner_id` 與 `machine_owner_id`（初始自動回填現有 `owner_id`）。
   - 新建 `subscriptions` 表（支援 device/venue 雙軌、方案 Y 自選 target_ids JSON、tier_code）。
   - 新建 `billing_cycles` 表（後付款月結明細、按日折算、寬限期追蹤）。
   - 擴充 `billing_requests` 表（批次開單相關欄位）。
2. **服務適配**：
   - Ina 將同步更新 `profit_sharing_service.py` 採用 `COALESCE(d.machine_owner_id, d.owner_id)` 確保分潤正確。
3. **後續接軌 (Phase 2)**：
   - 請 Sophie 準備好對應的 Eloquent Models (`Subscription`, `BillingCycle`) 與 `SubscriptionService`、`BillingService` 重構。
   - 等待 Ina 完成 Migration 回報後，即可全面啟動 Phase 2 開發。

---

**派發者**：HQ  
**派發時間**：2026-08-23 16:57
