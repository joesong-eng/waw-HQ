# 任務回報：TASK_20261003_SOPHIE_FIX_SIGNALHUB_VALIDATION_AND_PURGE_LEGACY_TRANSACTIONS

- **任務 ID**：TASK_20261003_SOPHIE_FIX_SIGNALHUB_VALIDATION_AND_PURGE_LEGACY_TRANSACTIONS
- **執行者**：Sophie (Owner 後台守護者)
- **完成時間**：2026-10-03
- **狀態**：✅ 完成 (Completed)

---

## 1. 執行項目與修復內容

### 1.1 修復 SignalHubController 驗證規則（Bug 1）
- **檔案**：`app/Http/Controllers/Api/V9/SignalHubController.php`
- **修正**：第 79 行（`storeProfile`）與第 105 行（`updateProfile`）：
  ```diff
  - 'machine_id' => 'nullable|integer|exists:machines,id',
  + 'machine_id' => 'nullable|integer|exists:devices,id',
  ```
- **說明**：`signal_profiles.machine_id` 欄位保留（欄位確實存在），僅將驗證目標由幽靈 `machines` 表改為正式 `devices` 表，杜絕 SQL 1146。

### 1.2 重構 ProfitSharingAgreementService，移除 MachineTransaction（Bug 2）
- **檔案**：`app/Services/ProfitSharingAgreementService.php`（整檔重構）
- **修正**：
  1. **徹底移除**對幽靈類別 `MachineTransaction` 的所有引用與寫入。
  2. `getMachineProfitSummary(int $deviceId, ...)`：改由 `DailyRevenueReport::where('device_id', $deviceId)` 查詢與彙總；依設備當前協議比例拆帳；無報表時回傳結構安全之 0 統計陣列（**嚴禁拋 500**）。
  3. `getStoreProfitSummary(int $venueId, ...)`：改由 `DailyRevenueReport::where('venue_id', $venueId)` 查詢；依各設備協議比例加總拆帳；同樣保證無 500。
  4. `calculateAndRecordTransaction()`：標註 `@deprecated`，改為**純計算**（回傳 array，不再寫入任何不存在的表），並將回傳 `status` 由 `'completed'` 改為 `'computed'` 以區隔「未落表」。
- **架構對齊**：分潤與營收統計唯一真理收斂至 `daily_revenue_reports`，與 `SettlementService` 一致。

### 1.3 順帶修復 ProfitSharingAgreementController 未定義變數
- **檔案**：`app/Http/Controllers/Api/V9/ProfitSharingAgreementController.php`
- **問題**：`machineSummary()` 第 228/231 行先前重構殘留 `$machine = Device::findOrFail(...)` 但下一行卻讀取未定義的 `$device->owner_id`，權限檢查會拋 Warning 並誤判 403。
- **修正**：統一為 `$device`，權限判斷正確。

### 1.4 歷史 Migration 歸檔與冗餘檔案清理
- **Migration 隔離**：移除正式 migrations 目錄下 4 支 legacy 檔（`2026_06_11_000001` ~ `000004`），避免未來 `migrate:fresh` 重造 `machines` 表。已確認 `_migration_proposals/` 內保有完全相同的備份（`diff` 驗證 IDENTICAL）。
- **清理冗餘備份檔**：
  - `resources/views/iot/realtime.blade.php.bak1` ~ `.bak9`、`.bak_batch`、`.bak_batch2`、`.bak_difffix`、`.bak_difffix2`（共 13 檔）
  - `app/Services/BillingService.php.old`、`app/Services/SubscriptionService.php.old`
- **測試適配**：`tests/Feature/ProfitSharingAgreementTest.php` 之 `test_calculate_transaction` 由驗證 Model 屬性改為驗證純計算 array 回傳。

---

## 2. 驗收指標比對（遠端 yd174 實測）

| # | 驗收項 | 實測方式 | 結果 | 判定 |
|:--|:---|:---|:---|:---:|
| 1 | SignalHub 驗證 | Tinker `Validator::make(['machine_id' => 合法設備ID], ['machine_id' => 'exists:devices,id'])` | `passes() = true`、errors `[]`；非法 ID `passes() = false` | ✅ |
| 1b | SignalHub 端到端 | Tinker 實呼 `storeProfile`（帶 `machine_id`） | **HTTP 201**，成功建立 profile（id=44），**無 SQL 1146**（已清理測試資料） | ✅ |
| 2 | 分潤摘要 API | Tinker 實呼 `machineSummary(req, 1)`（admin 登入） | **HTTP 200**，`{"total_amount":15653,"transaction_count":19,...}`，**無 Class not found** | ✅ |
| 2b | 場地分潤統計 | Tinker `getStoreProfitSummary(1)` | 正常回傳 `total_amount: 308987, report_count: 130` | ✅ |
| 2c | 無資料安全 | `getMachineProfitSummary` 對無報表設備 | 回傳 0 統計陣列，無例外 | ✅ |
| 3 | 靜態殘留 | `git grep 'MachineTransaction' / 'exists:machines'` | app/ 內 **0 hits** | ✅ |
| 4 | 站點存活 | `curl -sI https://iot.tg25.win/login` | **HTTP/2 200** | ✅ |
| 5 | 日誌無新錯誤 | 遠端 `laravel-2026-10-03.log` 檢查 | 部署後（01:31）**無新增 ERROR** | ✅ |

**生產環境清理**：SignalHub 端到端測試建立之 `__verify_tmp` profile 已刪除（含 pin mappings），殘留數 = **0**。

---

## 3. Git 版本與部署記錄

- **Git Commit**：`5901134` - `fix(device): SignalHub 驗證對齊 devices、分潤統計改用 daily_revenue_reports、清理 legacy 幽靈檔案`
- **變更規模**：23 files changed, 136 insertions(+), 11596 deletions(-)
- **推送**：`origin/main`（`62300f4..5901134`）
- **遠端部署**：`../../dev_tools/waw_ops.sh deploy owner` → `yd174` (`/www/wwwroot/iot.tg25.win`)
- **遠端 HEAD**：`590113435c8ee6c0f2baa765c1a246b0ca75904d`

---

## 4. 結論

✅ **完成交付**。兩個真實崩潰 Bug（SignalHub `exists:machines` 驗證、分潤統計 `MachineTransaction` 類別缺失）均已修復並通過遠端實測；分潤統計正式收斂至 `daily_revenue_reports` SSOT；歷史幽靈 Migration 與 .bak / .old 噪音檔已清除。全專案 `machines` 相關殘留歸零。
