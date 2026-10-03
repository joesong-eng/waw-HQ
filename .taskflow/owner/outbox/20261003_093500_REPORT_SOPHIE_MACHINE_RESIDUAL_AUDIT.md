# 提報：TASK_20261003 完工後全專案 Machine 殘留清查 — 發現 2 個真實崩潰 Bug 與幽靈檔案

- **提報者**：Sophie (Owner 後台守護者)
- **接收者**：HQ / Joe
- **提報時間**：2026-10-03
- **優先級**：P1 (High)
- **關聯任務**：TASK_20261003_SOPHIE_PURGE_MACHINE_MODEL_AND_ALIGN_DEVICE_SSOT（已完成交付，Commit `62300f4`）

---

## 一、背景

工單 `TASK_20261003_SOPHIE_PURGE_MACHINE_MODEL_AND_ALIGN_DEVICE_SSOT` 範圍內項目已 100% 完成並部署驗收（靜態掃描 `App\Models\Machine` = 0 hits、排程正常、API 正常）。

完工後我主動進行一次**全專案「殘留 Machine 引用」總清查**（`git grep` 全庫 + 遠端 Tinker 實測），發現 **3 個工單未涵蓋的遺留缺口**，其中 **2 個是會直接拋出 500 的真實 Bug**。以下為經遠端實測佐證的完整清單。

---

## 二、🔴 P1 真實崩潰 Bug（經遠端 Tinker 實測）

### Bug 1：SignalHubController 仍驗證 `exists:machines,id`

- **檔案**：`app/Http/Controllers/Api/V9/SignalHubController.php`（第 79 行、第 105 行）
- **問題代碼**：
  ```php
  // storeProfile() 與 updateProfile() 驗證規則
  'machine_id' => 'nullable|integer|exists:machines,id',
  ```
- **遠端實測佐證**（yd174 Tinker）：
  ```
  Illuminate\Database\QueryException: SQLSTATE[42S02]: Base table or view not found: 1146
  Table 'iotv9.machines' doesn't exist
  (SQL: select count(*) as aggregate from `machines` where `id` = 1)
  ```
- **影響**：只要請求帶 `machine_id` 呼叫 SignalHub `storeProfile` / `updateProfile`，即拋 500。
- **重要澄清**：`signal_profiles` 表**確實有 `machine_id` 欄位**（已遠端 `Schema::getColumnListing` 確認），因此**只需修正驗證規則**，不需動 Schema。
- **建議修法**：改為 `'machine_id' => 'nullable|integer|exists:devices,id'`，或直接移除該欄位驗證（若確定 legacy）。

### Bug 2：ProfitSharingAgreementService 引用不存在的 `MachineTransaction` 類別

- **檔案**：`app/Services/ProfitSharingAgreementService.php`
- **問題**：`calculateAndRecordTransaction()`、`getMachineProfitSummary()`、`getStoreProfitSummary()` 三處引用 `MachineTransaction::create()` / `MachineTransaction::where()`，但專案內**不存在 `App\Models\MachineTransaction`**，且 `machine_transactions` 表亦**不存在**（遠端 `Schema::hasTable` = false）。
- **遠端實測佐證**（yd174 Tinker）：
  ```
  Error: Class "App\Services\MachineTransaction" not found
  ```
- **影響**：`GET /api/v9/profit-sharing/machines/{machineId}/summary` 端點必拋 500；分潤交易記錄功能實質為死代碼。
- **建議**：需 HQ 決策分潤交易落地的正式表（是否沿用 `machine_transactions` 命名、或改為 `device_transactions`），再補 Model + Migration。

---

## 三、⚠️ P2 幽靈檔案（不影響執行，但造成混淆）

### 3.1 已完成執行的 legacy Migration 檔仍留在 repo
- `database/migrations/2026_06_11_000001_create_machines_table.php`（遠端 `migrate:status` 顯示已 Ran）
- `database/migrations/2026_06_11_000002_migrate_devices_to_machines.php`（已 Ran）
- `database/migrations/2026_06_11_000003_create_machine_deployments_table.php`（已 Ran）
- `database/migrations/2026_06_11_000004_init_machine_deployments.php`（已 Ran）
- 另有 `database/migrations/_migration_proposals/` 內同批備份。
- **說明**：這些 Migration 已在歷史執行過（但線上表實際不存在，疑似後續被手動 drop 或執行失敗），保留會讓未來 `migrate:fresh` 或新環境建置時「復活」`machines` 表，與 SSOT 直接衝突。
- **建議**：由 HQ / Ina 決策是否標記為 deprecated 或移入 proposals 區。

### 3.2 專案內殘留大量 .bak / .old 備份檔
- `resources/views/iot/realtime.blade.php.bak1` ~ `.bak9`、`.bak_batch`、`.bak_batch2`、`.bak_difffix`、`.bak_difffix2`（共 13 個）
- `app/Services/BillingService.php.old`、`app/Services/SubscriptionService.php.old`
- **說明**：不影響執行，但屬版本控制噪音。是否清理請示 HQ。

---

## 四、🟢 已確認乾淨的項目（無需處理）

- `git grep 'App\Models\Machine'` → 0 hits
- `git grep 'Machine::'` → 0 hits
- `git grep 'use App\Models\Machine'` → 0 hits
- 所有 `machine_id` 欄位在 `devices`、`signal_profiles`、`profit_sharing_agreements` 表中，均為**相容欄位命名**（語意指向 device），非指向 `machines` 表。

---

## 五、請求事項

1. **P1**：請 HQ 派單修復 Bug 1（SignalHub 驗證規則，預估 0.5h）。
2. **P1**：請 HQ 決策 Bug 2 的分潤交易正式表方向（命名 / Schema），再派單實作（預估 2~4h）。
3. **P2**：請 HQ 裁定 legacy Migration 與 .bak / .old 檔案的清理政策。

Sophie 待命，收到工單即刻執行。
