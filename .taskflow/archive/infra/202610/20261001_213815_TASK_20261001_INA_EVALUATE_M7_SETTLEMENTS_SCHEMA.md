# 任務：TASK_20261001_INA_EVALUATE_M7_SETTLEMENTS_SCHEMA

**派發時間**：2026-10-01
**優先級**：P0 / Critical（財務結算阻斷）
**負責人**：Ina (Infra)
**關聯模組**：Infra / Central DB iotv9 (141.148.165.50) / Owner M7

---

## 📌 任務背景
Sophie 於今日完成 M7 月結算程式碼檢驗後，發現生產資料庫 `iotv9.settlements` 表結構與現行 M7 程式碼完全脫節，導致 9 月份月結算任務生成失敗（結算功能目前實質無法上線）。

### 1. 生產庫現有 `settlements` 表結構（資料筆數：0 筆）
```
id, owner_id, amount, outstanding_deducted, effective_payment, method, status, completed_at, reference, created_at, updated_at
```
*(此結構為舊版金流/撥款表，且 migrations 記錄中無 M7 原始建表紀錄)*

### 2. M7 業務程式碼實際依賴欄位
```
settlement_number, venue_id, device_owner_id, venue_owner_id, period_start, period_end,
total_revenue, pre_tax_expenses, taxable_revenue, device_breakdown, device_owner_amount,
venue_owner_amount, device_owner_share, venue_owner_share, status, confirmed_at, paid_at,
closed_at, disputed_at, dispute_reason, dispute_resolution, payment_proof_url, created_at, updated_at
```

---

## 📋 具體執行項目

1. **現況調查與衝突判定**：
   - 確認現有 `settlements` 表是否仍有其他外部模組、Legacy API 或未記錄流程依賴。
   - 確認外部鍵關聯：`settlement_logs` (FK -> settlements.id) 與 `daily_revenue_reports.settlement_id`。

2. **Schema 遷移方案實施**：
   - 若現有 0 筆資料之 `settlements` 確屬廢棄/未上線定義：
     - 提供並執行遷移腳本，將 `settlements` 表結構升級/重建為 M7 標準 Schema（可參考 `PROJECT/Owner/database/migrations/_migration_archive/2026_03_11_000001_create_settlements_table.php` 及 `2026_03_27_164643_add_pre_tax_expenses_to_settlements_table.php`）。
   - 若舊結構仍有保留必要：
     - 將舊表重新命名備份（如 `legacy_settlements`），另建 M7 標準 `settlements` 表。

3. **版本控管與同步**：
   - 建立正規 DDL migration 腳本並納入 `PROJECT/Infra` 或同步至 `PROJECT/Owner` 倉庫。
   - 在 Central DB 驗證 DDL 正確性 (`DESCRIBE settlements;`)。

4. **回報至 `.taskflow/infra/outbox/`**。

