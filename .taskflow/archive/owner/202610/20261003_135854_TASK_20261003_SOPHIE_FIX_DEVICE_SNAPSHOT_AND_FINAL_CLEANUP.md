# 任務工單：收尾修復 DeviceSnapshot 幽靈引用與殘留 .old 檔案清理

**工單編號**：TASK_20261003_SOPHIE_FIX_DEVICE_SNAPSHOT_AND_FINAL_CLEANUP
**派發時間**：2026-10-03
**負責人**：Sophie (Owner 後台守護者)
**優先級**：P1 (High)
**關聯模組**：Owner (iot.tg25.win / yd174)
**前置工單**：TASK_20261003_SOPHIE_PURGE_MACHINE_MODEL_AND_ALIGN_DEVICE_SSOT、TASK_20261003_SOPHIE_FIX_SIGNALHUB_VALIDATION_AND_PURGE_LEGACY_TRANSACTIONS

---

## 🎯 背景

前兩輪清理已修復主要 Bug，但第三輪有界審查提報之殘留項尚未派工處理。經 HQ 遠端實測確認，以下兩項仍為**真實存在的缺陷**：

1. `php artisan mock:snapshots` 遠端實測**直接崩潰**：
   ```
   In GenerateMockSnapshots.php line 111:
   Class "App\Models\DeviceSnapshot" not found
   ```
   資料庫 **確有 `device_snapshots` 表**（8 欄位：id, chip_id, lifetime_credit_in, lifetime_credit_out, snapshot_at, executed_at, created_at, updated_at），但缺少對應 Model。

2. 殘留 `.old` 檔尚未清除（前次僅清了 BillingService / SubscriptionService）。

---

## 📋 具體實作項目

### 項目 1：補建 DeviceSnapshot Model

- **新增檔案**：`app/Models/DeviceSnapshot.php`
- **對齊實際表結構**（遠端 `db:table` 實測欄位）：
  ```php
  <?php

  namespace App\Models;

  use Illuminate\Database\Eloquent\Model;
  use Illuminate\Database\Eloquent\Relations\BelongsTo;

  /**
   * DeviceSnapshot - 機台快照日誌
   *
   * 對應 device_snapshots 表（iotv9），記錄設備每小時累計入金/出金快照。
   * 用於營收趨勢分析與即時監控歷史回補。
   */
  class DeviceSnapshot extends Model
  {
      protected $table = 'device_snapshots';

      protected $fillable = [
          'chip_id',
          'lifetime_credit_in',
          'lifetime_credit_out',
          'snapshot_at',
          'executed_at',
      ];

      protected $casts = [
          'lifetime_credit_in'  => 'integer',
          'lifetime_credit_out' => 'integer',
          'snapshot_at'         => 'datetime',
          'executed_at'         => 'datetime',
      ];

      /**
       * 關聯設備（透過 chip_id）
       */
      public function device(): BelongsTo
      {
          return $this->belongsTo(Device::class, 'chip_id', 'chip_id');
      }
  }
  ```

- **驗收**：遠端 `php artisan mock:snapshots` 能正常執行不再拋 Class not found（可先跑 `--dry-run` 或小範圍測試，避免灌入大量 mock 資料；若指令無 dry-run 選項，請先備份或用 transaction 測試後 rollback，避免污染正式庫）。

> ⚠️ **重要**：`mock:snapshots` 會寫入大量 mock 資料（21 台設備 × 1273 筆 ≈ 2.6 萬筆）。**請勿直接對正式庫執行完整寫入**。驗收方式改為：
> - 方式 A：Tinker 中 `new App\Models\DeviceSnapshot();` 確認類別可載入。
> - 方式 B：`DB::table('device_snapshots')->count()` 確認表可讀。
> - 方式 C：手動構造單筆 `DeviceSnapshot::create([...])` 後刪除。
> 任一方式通過即視為 Model 修復成功。

### 項目 2：清理殘留 .old 檔案

- 刪除：
  - `app/Http/Middleware/EnsureSubscriptionActive.php.old`
  - `config/subscription.php.old`
- 刪除前確認正式版本（無 .old）存在且功能完整：
  - `app/Http/Middleware/EnsureSubscriptionActive.php` 是否存在？
  - `config/subscription.php` 是否存在？
  - 若正式版不存在，**不可直接刪除 .old**，需先與 HQ 確認。

### 項目 3：移除 routes/api.php 無用 import

- `routes/api.php:6` 的 `use App\Models\DeviceSnapshot;` 在路由檔中未被使用。
- 補建 Model 後此 import 仍屬無用（路由檔不直接調用 Model），可移除；或確認有路由使用後保留。

---

## 🔍 驗收指標

1. `git grep 'App\\Models\\DeviceSnapshot'` 引用之 Model 檔案確實存在。
2. 遠端 Tinker：`new App\Models\DeviceSnapshot();` 無 Class not found。
3. `ls app/Http/Middleware/*.old config/*.old` 結果歸零。
4. `php artisan test` 通過。
5. 部署至遠端 `yd174`，站點 `https://iot.tg25.win/login` 回傳 HTTP/2 200。
6. 回報至 `.taskflow/owner/outbox/`。

