# 任務工單：徹底清理 legacy Machine 模型，全面對齊 devices 實體表 SSOT

**工單編號**：TASK_20261003_SOPHIE_PURGE_MACHINE_MODEL_AND_ALIGN_DEVICE_SSOT  
**派發時間**：2026-10-03  
**負責人**：Sophie (Owner 後台守護者)  
**優先級**：P1 (High)  
**關聯模組**：Owner (iot.tg25.win / yd174)

---

## 🎯 背景與目標

1. **背景**：
   - 2026-09-16 HQ & Joe 架構審查已正式拍板：**終止換表、固化 `iotv9.devices` 為永久唯一硬體與營運 SSOT**。
   - 線上 MySQL 資料庫（`iotv9`）只有 `devices` 表（21 台在線設備、35 個欄位），**從未存在 `machines` 表**。
   - 今晨排程 `machines:check-pending` 報錯 `SQLSTATE[42S02]: Table 'iotv9.machines' doesn't exist`。
   - 審查發現 Owner 代碼庫仍殘留 2026 年 6 月時建立的 `App\Models\Machine`、`MachineController`、`MachineObserver` 等死代碼，嚴重造成混淆與排程崩潰。

2. **目標**：
   - 全面拔除所有指向 `machines` 表的查詢與模型。
   - 所有實體設備與營運邏輯 100% 收斂至 `App\Models\Device`。
   - 刪除幽靈檔案，全專案 `grep -rn "App\\Models\\Machine" app/` 歸零。
   - 通過本機/遠端真實指令驗收並部署上線。

---

## 📋 具體實作項目與規範

### 項目 1：修復排程指令 `CheckPendingMachines.php`
- **檔案**：`app/Console/Commands/CheckPendingMachines.php`
- **調整**：
  1. 引用改為 `use App\Models\Device;`。
  2. 查詢對齊：
     ```php
     $devices = Device::where('status', 'pending_setup')
         ->where('created_at', '<', now()->subDays($days))
         ->where(function ($q) {
             $q->whereNotNull('machine_owner_id')
               ->orWhereNotNull('owner_id');
         })
         ->with('owner')
         ->get();
     ```
  3. 負責人 ID 取值：`$ownerId = $device->machine_owner_id ?? $device->owner_id;`
  4. 警報發送與跳過檢查對齊 `$device->id` 與 `$device->name`。
  5. 驗證：指令執行 `php artisan machines:check-pending --dry-run` 必須正常輸出無任何 SQL 錯誤。

### 項目 2：重構 `RevenueController.php`
- **檔案**：`app/Http/Controllers/Api/V9/RevenueController.php`
- **調整**：
  1. 移除驗證規則中 `'machine_id' => 'sometimes|integer|exists:machines,id'`（避免觸發 SQL 1146）。
  2. 移除對 `App\Models\Machine` 的直接依賴，改用 `Device`。
  3. `resolveMachine` 重構為 `resolveDevice`，統一查 `Device::where('chip_id', ...)->first()` 或 `Device::find($deviceId)`。
  4. 若需 `calculateRevenue`，可將所需邏輯整併至 `Device` 或 Service。

### 項目 3：重構 `MachineController.php`
- **檔案**：`app/Http/Controllers/Api/V9/MachineController.php`
- **調整**：
  1. 將內部 `Machine::with(['currentDeployment.store'])` 改為 `Device::with('venue')`。
  2. 關聯店面改為 `$device->venue?->name`。
  3. 確保 `GET /api/v9/machine/machine_info/{chip_id}` 查詢能正確回傳 `devices` 表之設備數據。

### 項目 4：適配 `SignalProfile.php`
- **檔案**：`app/Models/SignalProfile.php`
- **調整**：
  1. 將 `public function machine(): BelongsTo` 改為指向 `Device::class, 'device_id'`（或標記 deprecated 並安全回傳 `device()`），防止外部呼叫時拋錯。

### 項目 5：重構 Observer 與 Providers
- **檔案**：
  - `app/Observers/MachineObserver.php`（可改名為 `DeviceObserver.php` 或在原檔內改監聽 `Device $device`）
  - `app/Providers/AppServiceProvider.php`
  - `app/Providers/AuthServiceProvider.php`
- **調整**：
  1. Observer 監聽類型改為 `Device $device`。
  2. 監聽條件：當 `$device->wasChanged('status') && $device->status === 'active' && $device->getOriginal('status') === 'pending_setup'` 時，執行 `dismissDeviceAlerts($device->id)`。
  3. `AppServiceProvider.php` 註冊改為：`\App\Models\Device::observe(\App\Observers\DeviceObserver::class);`。
  4. `AuthServiceProvider.php` 移除 `Machine::class => MachinePolicy::class`。

### 項目 6：刪除 Obsolete 檔案
- 移除以下歷史未生效/幽靈檔案：
  - `app/Models/Machine.php`
  - `app/Models/MachineDeployment.php`
  - `app/Models/MachineExtensions.php`
  - `app/Policies/MachinePolicy.php`

### 項目 7：修正測試代碼
- 檢視 `tests/Feature/ProfitSharingAgreementTest.php` 與 `tests/Feature/RevenueControllerRefactorTest.php`，移除對 `Machine` 的引用，改測 `Device`。

---

## 🔍 驗收指標 (Acceptance Criteria)

1. **靜態檢查**：
   - 執行 `git grep -n "App\\Models\\Machine" app/` 必須無任何結果（0 hits）。
2. **排程驗收**：
   - 於遠端 `yd174` 執行 `php artisan machines:check-pending --dry-run`，無 QueryException，正常顯示掃描結果。
3. **單元/功能測試**：
   - 遠端執行 `php artisan test` 全數通過。
4. **部屬上線**：
   - Commit 並 Push，透過 `waw_ops.sh deploy owner` 部署至 `yd174`。
   - 產出標準回報單至 `.taskflow/owner/outbox/`。

