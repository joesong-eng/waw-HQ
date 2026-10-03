# 請求：M7 settlements 表 Schema 重建評估（Sophie -> Ina）

**提出時間**：2026-10-01
**提出者**：Sophie (Owner / iot.tg25.win / yd174)
**優先級**：P0 / Critical（財務功能阻塞）
**類型**：DB Schema 變更（依鐵律，由 Ina 執行，Sophie 不自行 Migration）

---

## 一、問題摘要
生產 settlements 表結構與 M7 結算程式碼**完全不符**，導致 M7 月結算功能無法運作。

## 二、現況對照

### 生產 settlements 實際欄位

    id, owner_id, amount, outstanding_deducted, effective_payment,
    method, status, completed_at, reference, created_at, updated_at
    （資料筆數：0）

### M7 程式碼期望欄位

    settlement_number, venue_id, device_owner_id, venue_owner_id,
    period_start, period_end, total_revenue, pre_tax_expenses, taxable_revenue,
    device_breakdown, device_owner_amount, venue_owner_amount,
    device_owner_share, venue_owner_share,
    status(created/confirmed/paid/closed/disputed),
    confirmed_at, paid_at, closed_at, disputed_at, dispute_reason, ...

### 相關表
- settlement_logs：存在，FK -> settlements(settlement_id)
- daily_revenue_reports.settlement_id：存在

## 三、根因線索
- M7 建表 migration 2026_03_11_000001_create_settlements_table.php
  目前位於 database/migrations/_migration_archive/（commit 519cf6f 歸檔）。
- DB migrations 表查無此筆 -> 該 migration **從未對生產庫執行**。
- 現有 settlements 表係由其他（已不在 repo 的）來源建立。
- database/migrations/ 現存 19 檔，DB migrations 表有 62 筆，兩者不對齊。

## 四、請求 Ina 評估與處置
1. 判定現有 settlements（owner_id/amount/method/reference 版）之歸屬：
   - 是否為 legacy 金流／撥款表？是否有模組或外部流程仍在讀寫？
2. 提出遷移方案（二選一或更佳）：
   - (a) 重建 settlements 為 M7 schema（若舊表確認無用）；
   - (b) 將舊表更名保留，另建 M7 專用表（並同步調整 model 的 $table）。
3. 一併檢視 FK 依賴：settlement_logs、daily_revenue_reports.settlement_id。
4. 提供 migration 檔案；Sophie 端負責 Settlement model $table / 程式碼對齊。

## 五、時程影響
- 2026-09 月度結算單已因另一個 bug（已修，ffb5dbb）而未生成；
  但**即使該 bug 修好，本 schema 問題仍會使結算失敗**。
- 故 M7 結算功能在 schema 修復前，實質處於**未上線**狀態。

## 六、附註
Sophie 已完成的部分：
- 修復 SettlementController / ReportController 的 Laravel 11 middleware() 500（commit 6345583）。
- 修復 GenerateMonthlySettlements 傳參型別錯誤（commit ffb5dbb）。
- 未執行任何 Migration、未執行 queue:retry、未觸碰財務資料。

