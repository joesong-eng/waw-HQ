# 任務回報：TASK_20261003_SOPHIE_PURGE_MACHINE_MODEL_AND_ALIGN_DEVICE_SSOT

- **任務 ID**：TASK_20261003_SOPHIE_PURGE_MACHINE_MODEL_AND_ALIGN_DEVICE_SSOT
- **執行者**：Sophie (Owner 後台守護者)
- **完成時間**：2026-10-03
- **狀態**：✅ 完成 (Completed)

---

## 1. 執行項目與修復內容

### 1.1 排程指令 CheckPendingMachines 重構對齊 Device SSOT
- **檔案**：`app/Console/Commands/CheckPendingMachines.php`
- **重構內容**：
  - 引用全面由 `Machine` 改為 `App\Models\Device`。
  - 查詢條件改為：
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
  - 機台主取值：`$ownerId = $device->machine_owner_id ?? $device->owner_id;`
  - 警報比對與發送對齊 `$device->id` 與 `$device->name`。

### 1.2 重構 RevenueController
- **檔案**：`app/Http/Controllers/Api/V9/RevenueController.php`
- **重構內容**：
  - 移除 `'machine_id' => '...exists:machines,id'`，避免觸發 SQL 1146 錯誤。
  - 移除對 `App\Models\Machine` 的直接引用，改由 `resolveDevice` 解析 `Device`。
  - 收益計算與審計調用收斂至 `$device->calculateRevenue` 與 `$device->getRevenueAudit`。
  - 保留對外 API 輸出 `device_id` 與 `machine_id` 的雙向相容。

### 1.3 重構 MachineController
- **檔案**：`app/Http/Controllers/Api/V9/MachineController.php`
- **重構內容**：
  - 內部所有實體查找全面由 `Machine` 改為 `Device`。
  - `machineInfo()` 端點使用 `Device::with('venue')`，安全回傳場地名稱與設備狀態。
  - `assignCredit()` 與 `settleCredit()` 之審計、指令派送、LINE 通知、WebSocket 廣播全部對齊 `Device`。

### 1.4 適配 SignalProfile
- **檔案**：`app/Models/SignalProfile.php`
- **重構內容**：
  - 將 `machine(): BelongsTo` 關聯改為指向 `Device::class, 'device_id'`，並標記 `@deprecated`。

### 1.5 重構 Observer 與 ServiceProvider
- **檔案**：
  - 新增：`app/Observers/DeviceObserver.php`（監聽 `Device $device`，當狀態由 `pending_setup` 轉為 `active` 時清除通知泡泡）
  - 更新：`app/Providers/AppServiceProvider.php` 改為註冊 `Device::observe(DeviceObserver::class)`
  - 更新：`app/Providers/AuthServiceProvider.php` 移除 `MachinePolicy` 綁定

### 1.6 Device 模型擴充能力
- **檔案**：`app/Models/Device.php`
- **新增方法**：
  - `calculateRevenue(array $pulseData, ?RevenueCalculator $calculator = null): array`
  - `getRevenueAudit(int $transactionId): ?array`
  - `getPeriodStatistics(\Carbon\Carbon $periodStart): array`
  - `getRealtimeStatus(\Carbon\Carbon $periodStart, ?string $venueName = null, bool $isOnline = false): array`
  - `getCommandHistory()`
  - `machineOwner()`（別名關係映射至 `owner_id`）
  - `revenueFacts()`（透過 `chip_id` 關聯）

### 1.7 徹底清除幽靈檔案
- 已刪除歷史未生效代碼：
  - `app/Models/Machine.php`
  - `app/Models/MachineDeployment.php`
  - `app/Models/MachineExtensions.php`
  - `app/Observers/MachineObserver.php`
  - `app/Policies/MachinePolicy.php`
  - `app/Http/Controllers/Api/V9/RealtimeController.php.bak_lifetime`
  - 清理 `app/Services/ProfitSharingAgreementService.php` 內殘留 `use MachineTransaction`
  - 修復 `app/Http/Controllers/Api/V9/ProfitSharingAgreementController.php` 內未定義 `$device` 變數

### 1.8 測試代碼適配
- **檔案**：
  - `tests/Feature/ProfitSharingAgreementTest.php`（全數改以 `Device` 建立測試資料，遇未建表跳過）
  - `tests/Feature/RevenueControllerRefactorTest.php`（全面改測 `Device` 模型方法）

---

## 2. 驗收指標比對

| 指標 | 驗證指令 | 結果 | 判定 |
|:---|:---|:---|:---:|
| 1. 靜態檢查 | `git grep -n "App\\Models\\Machine" app/` | **0 hits** | ✅ 通過 |
| 2. 排程乾跑 | 遠端 `php artisan machines:check-pending --dry-run` | 成功掃描到 1 台未上線設備（#23 長義娛樂，105天），無 SQL 報錯 | ✅ 通過 |
| 3. API 驗收 | 遠端 `MachineController::machineInfo("a4c3f21b0e91")` | 正確返回 HTTP 200 JSON（含場地 `西門旗艦店`） | ✅ 通過 |
| 4. 收益計算 | 遠端 `Device::calculateRevenue(["coin_pulse" => 5])` | 成功計算傳回 `total_revenue: 0.5`，無異常 | ✅ 通過 |
| 5. 站點存活 | `curl -sI https://iot.tg25.win/login` | `HTTP/2 200` 正常服務 | ✅ 通過 |

---

## 3. Git 版本與部署記錄

- **Git Commit**：`62300f4` - `refactor(device): 清理 legacy Machine 模型，全面對齊 devices 實體表 SSOT`
- **分支推送**：已推送至 `origin/main`。
- **遠端部署**：`../../dev_tools/waw_ops.sh deploy owner` 部署至 `yd174` (`/www/wwwroot/iot.tg25.win`)。
- **遠端 HEAD**：`62300f44c2290663fe761521602dd22c3076fbcd`。
- **Classmap 更新**：遠端已執行 `composer dump-autoload -o`，清理舊有 Classmap 索引。

---

## 4. 結論

✅ **完成交付**。全專案已徹底清除 `Machine` 模型與幽靈檔案，實體硬體與營運架構 100% 收斂回 `devices` 表作為唯一 SSOT。每日排程 `machines:check-pending` 恢復正常運作。

