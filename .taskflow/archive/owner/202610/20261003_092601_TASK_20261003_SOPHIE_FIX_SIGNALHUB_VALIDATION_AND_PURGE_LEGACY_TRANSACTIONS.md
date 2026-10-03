# 任務工單：修復 SignalHub 驗證規則、重構分潤統計對齊 DailyRevenueReport、清理歷史幽靈檔案

**工單編號**：TASK_20261003_SOPHIE_FIX_SIGNALHUB_VALIDATION_AND_PURGE_LEGACY_TRANSACTIONS  
**派發時間**：2026-10-03  
**負責人**：Sophie (Owner 後台守護者)  
**優先級**：P1 (High)  
**關聯模組**：Owner (iot.tg25.win / yd174)

---

## 🎯 背景與目標

在上一輪 `Machine` 模型清理後，Sophie 延伸清查回報 2 個真實潛在崩潰點與歷史冗餘檔案：
1. `SignalHubController` 驗證規則殘留 `exists:machines,id`，傳入 `machine_id` 時觸發 SQL 1146。
2. `ProfitSharingAgreementService` 調用未建表的幽靈類別 `MachineTransaction`，導致分潤統計端點 500。
3. 2026 年 6 月之 legacy Migration 檔仍存在於正規 migrations 目錄，且專案內有多個 `.bak` / `.old` 噪音檔。

本工單要求徹底修復上述兩處崩潰 Bug，並收斂統計來源至正式資料表（`daily_revenue_reports`），完成幽靈檔案歸檔清理。

---

## 📋 具體實作項目

### 項目 1：修復 SignalHubController 驗證規則
- **檔案**：`app/Http/Controllers/Api/V9/SignalHubController.php`
- **修正**：
  - 第 79 行 (`storeProfile`) 與第 105 行 (`updateProfile`)：
    將 `'machine_id' => 'nullable|integer|exists:machines,id'`
    改為 `'machine_id' => 'nullable|integer|exists:devices,id'`。
  - 確保傳入合法的 `machine_id` (對齊 `devices.id`) 時不會拋出 SQL 1146。

### 項目 2：重構 ProfitSharingAgreementService，移除 MachineTransaction
- **檔案**：`app/Services/ProfitSharingAgreementService.php`
- **架構原則**：
  - WAW 2.0 分潤與營收事實唯一真理為 `revenue_facts` 與每日彙總表 `daily_revenue_reports`。
  - `SettlementService` 亦以 `daily_revenue_reports` 為準。
- **修正**：
  1. 徹底移除對 `MachineTransaction` 的引用與調用。
  2. `getMachineProfitSummary(int $deviceId, ?Carbon $startDate = null, ?Carbon $endDate = null): array`：
     - 改由 `DailyRevenueReport::where('device_id', $deviceId)` 查詢與彙總營收與分成金額。
     - 若無報表記錄，回傳結構安全之預設 0 統計陣列，嚴禁拋 500。
  3. `getStoreProfitSummary(int $venueId, ?Carbon $startDate = null, ?Carbon $endDate = null): array`：
     - 改由 `DailyRevenueReport::where('venue_id', $venueId)` 查詢與彙總。
  4. `calculateAndRecordTransaction`：廢棄或標註 deprecated，避免嘗試寫入不存在的表。

### 項目 3：歷史 Migration 歸檔與冗餘檔案清理
- **Migration 隔離**：
  - 將 `database/migrations/2026_06_11_000001_create_machines_table.php` ~ `000004_init_machine_deployments.php` 四個檔案從正式 migrations 目錄移除，移入 `database/migrations/_migration_proposals/` 或刪除（避免未來 `migrate:fresh` 重造 `machines` 表）。
- **清理冗餘備份檔**：
  - 清理 `resources/views/iot/realtime.blade.php.bak*`。
  - 清理 `app/Services/BillingService.php.old`、`app/Services/SubscriptionService.php.old`。

---

## 🔍 驗收指標

1. **SignalHub 驗證實測**：
   - 透過 Tinker 測試以帶 `machine_id` 的 payload 通過 `SignalHubController` 的 Validator，確認不拋 `exists:machines` 錯誤。
2. **分潤摘要 API 實測**：
   - 呼叫 `GET /api/v9/profit-sharing/machines/{machineId}/summary`（對應已存在設備 ID），確認回傳 HTTP 200 JSON，無 `Class not found` 錯誤。
3. **單元測試與部署**：
   - `php artisan test` 通過。
   - 部署至遠端 `yd174`，驗證網站功能與日誌無相關報錯。
   - 產出標準回報至 `.taskflow/owner/outbox/`。

