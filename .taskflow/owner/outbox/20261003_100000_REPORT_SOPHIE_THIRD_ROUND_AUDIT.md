# 提報：Owner 第三輪收斂式整案檢查 — 發現 1 個真實崩潰 Bug 與 3 項殘留/待決事項

- **提報者**：Sophie (Owner 後台守護者)
- **接收者**：HQ / Joe
- **提報時間**：2026-10-03
- **優先級**：P1（含 1 個真實崩潰 Bug）
- **觸發原因**：Joe 指示「整案再檢查一次」。為節約 Token，採**有界定點掃描**（非全案重讀），針對前兩輪重構後的遺留引用做 5 類驗證。

---

## 一、檢查方法（有界掃描，已避免全專案重讀）

| # | 掃描項 | 方式 |
|:--|:---|:---|
| 1 | 全庫 exists:<table> 驗證規則 | git grep 抽出所有 exists 目標 |
| 2 | 全庫 .bak / .old / .orig 噪音檔 | git ls-files 過濾 |
| 3 | legacy 類別引用 | git grep MachineTransaction / MachineDeployment / App\Models\Machine |
| 4 | 所有 App\Models\* 引用類別是否存在 | 靜態比對 refs vs 實際檔案 |
| 5 | 路由 Controller、排程指令、Jobs 類別 | 靜態比對 + 遠端 route:list / artisan list |

---

## 二、🔴 P1 真實崩潰 Bug（經遠端 Tinker 實測）

### Bug 3：BillAcceptorService 第 43 行 . 誤用（應為 ->）

- **檔案**：`app/Services/BillAcceptorService.php:43`（`handleEscrow` 的「設備不存在」分支）
- **問題代碼**：
```php
$this->mqttService.rejectBill($chipId, $reqId);   // ❌ 應為 ->
```
  同檔其餘 4 處皆正確使用 `$this->mqttService->rejectBill(...)` / `->stackBill(...)`，僅此處筆誤。
- **遠端實測佐證**（yd174 Tinker）：
```
Error: Call to undefined method App\Services\BillAcceptorService::rejectBill()
```
- **影響**：紙鈔機（Kiosk）Escrow 事件在「設備不存在」降級路徑時，**原本應安全回傳錯誤，卻直接拋 500**。此路徑可達：`POST /api/internal/kiosk/event`（verify.internal.key 中介層）。
- **修法**：改為 `->rejectBill(...)`（預估 5 分鐘）。

---

## 三、⚠️ 待決事項（需 HQ 裁定，非崩潰）

### 3.1 App\Models\DeviceSnapshot 類別不存在（幽靈引用）
- **引用位置**：
  - `app/Console/Commands/GenerateMockSnapshots.php`（DeviceSnapshot::insert()）
  - `database/factories/DeviceSnapshotFactory.php`、`database/seeders/DeviceSnapshotSeeder.php`、`routes/api.php:6`（僅 use 匯入，未實際使用）
- **實測**：`app/Models/DeviceSnapshot.php` **不存在**；但 DB 中 device_snapshots 表**存在**（Schema::hasTable = true）。
- **影響**：`php artisan mock:snapshots` 執行即拋 Class not found（該指令仍註冊於 artisan list）。非排程路徑，但屬幽靈引用。
- **建議**：由 HQ 決策補建 DeviceSnapshot Model，或將 mock:snapshots、Factory、Seeder、routes 匯入一併移除（mock 用途，疑似已無需）。

### 3.2 mysql_member 連線缺 .env 設定（跨庫路徑）
- **依賴位置**：`app/Services/BillAcceptorService.php`（4 處）、`app/Console/Commands/NightlyRevenueReconcile.php:81`、對應 `config/database.php:65`。
- **實測**：遠端 .env 查無 MEMBER_DB_* 設定（輸出為空），僅有 config 預設值。
- **影響**：紙鈔機跨庫查 machine_sessions、深夜對帳查 Member 端資料時，可能連線失敗。
- **建議**：請 HQ 確認此跨庫路徑是否仍在使用；若使用，需 Ina 補 .env 連線設定。

### 3.3 殘留 .old 檔與非原始碼噪音目錄
- `app/Http/Middleware/EnsureSubscriptionActive.php.old`、`config/subscription.php.old`（前次已清 BillingService/SubscriptionService 的 .old，此二檔仍在）
- 非版本原始碼噪音：`.kiro/`（19 檔）、`_agent/outbox/`（14 檔）、`README.md:200` 仍描述已刪除的 MachineExtensions.php
- **建議**：請 HQ 裁定是否清除 .old；.kiro/_agent/README 屬文件層，建議一併更新以免誤導。

---

## 四、🟢 已確認乾淨（無需處理）

- 全庫 exists:<table> 目標：device_types, devices, profit_sharing_proposals, signal_profiles, users, venues — **全部指向真實表，0 個 machines**。
- 全庫 legacy 類別引用：App\Models\Machine、Machine::、MachineTransaction、MachineDeployment、MachineExtensions、MachineObserver、MachinePolicy 於 app/ 內 **0 hits**（僅存於 _migration_proposals/ 與 .kiro 文件）。
- 31 個 App\Models\* 引用中，僅 DeviceSnapshot 缺失（見 3.1），其餘 30 個皆存在。
- 路由 31 個 Controller 類別 **全部存在**；217 條路由正常載入。
- 排程 10 條指令：僅 devices:snapshot（已在 console.php 註解停用）無對應類別，其餘皆正常。
- 站點存活：curl -sI https://iot.tg25.win/login → HTTP/2 200。

---

## 五、請求事項

1. **P1**：派單修復 Bug 3（BillAcceptorService 第 43 行 . → ->，預估 5 分鐘）。
2. **P2**：裁定 DeviceSnapshot 幽靈引用處理方式（補 Model 或移除 mock 相關）。
3. **P2**：確認 mysql_member 跨庫路徑是否在用，決定是否補 .env。
4. **P3**：裁定殘留 .old 檔與 .kiro/_agent/README 文件的清理/更新政策。

Sophie 待命，收到工單即刻執行。
