# 任務工單：TASK_20260930_SOPHIE_FIX_M6_KPI_TODAY_TRANSACTIONS

**派發時間**：2026-09-30 04:05 (台北時間)  
**優先級**：P2 (修正 M6 儀表板關鍵指標「今日交易筆數」假數據)  
**指派對象**：Sophie (Owner Agent)  
**驗收人**：HQ / Joe

---

## 🎯 任務目標

在 `PROJECT/Owner/app/Http/Controllers/Iot/StatisticsController.php` 中，現有儀表板 (`dashboard`) 頁面回傳的 `todayTransactions` 存在嚴重邏輯缺陷：
```php
'todayTransactions' => $dashboardData->kpis['today_revenue']['value'] > 0 ?
    $dashboardData->deviceStats->total : 0,
```
此邏輯在今日有營收時，直接把「設備總台數」當成「交易筆數」回傳給前端，極度荒謬且數據不真實。

**本次任務目標**：
將 `todayTransactions` 重構為真正的 `RevenueFact` 交易筆數統計，呈現真實的「今日投幣/開分次數」。

---

## 📋 具體實作要求

### 一、真實筆數計算 (`app/Http/Controllers/Iot/StatisticsController.php`)
參考 `VenueController.php:349` 的標準實作，依照當前選定的場地（或用戶名下所有可見場地/設備）：
1. 查詢 `RevenueFact`：
   - 篩選條件：
     - `transaction_type = 'credit_in'`
     - `event_ts >= 今日 00:00:00 (依照用戶或場地時區)`
     - `is_valid = 1`
     - 若有 `venue_id` 則過濾該場地；若無則過濾用戶所屬場地/設備集合。
   - 執行 `->count()` 取得真正的交易筆數。
2. 替換掉原本把 `deviceStats->total` 充當筆數的錯誤代碼。

### 二、KPI 與格式統一
確保傳遞給 Blade 視圖的 `todayTransactions` 以及 KPI 卡片內的 `transactions` 為整數真實值，若今日無交易則正確顯示 `0`。

---

## 📦 驗收標準 (Acceptance Criteria)

1. **語法與邏輯檢查**：
   - `php -l app/Http/Controllers/Iot/StatisticsController.php` 無錯誤。
   - 時區判斷與過濾條件正確，利用既有的 `idx_device_ts_type` 索引，避免全表掃描。
2. **Git 與遠端部署**：
   - Commit message 格式：`fix(m6): calculate real todayTransactions count from revenue_facts`
   - Push 至遠端 main 分支並完成 `waw_ops.sh deploy owner`。
3. **回報格式**：
   - 依據 `SIMPLE_FILE_DISPATCH_PROTOCOL.md` 將回報送達 `.taskflow/owner/outbox/`。
   - 附上代碼變更說明與遠端部署成功之 git log。

---
**派發者**：HQ  

