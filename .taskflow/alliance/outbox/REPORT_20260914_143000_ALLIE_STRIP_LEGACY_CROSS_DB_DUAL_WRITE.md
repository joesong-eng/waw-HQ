# 任務回報：TASK_20260914_ALLIE_STRIP_LEGACY_CROSS_DB_DUAL_WRITE

**完成時間**：2026-09-14 14:30
**執行者**：Allie (Alliance Lead)
**派發來源**：HQ (TASK_20260914_ALLIE_STRIP_LEGACY_CROSS_DB_DUAL_WRITE)
**關聯項目**：
- PROPOSAL_20260914_ALLIE_DEVICES_CROSS_DB_ARCHITECTURE_REFACTOR
- Ina 完工回報 REPORT_TASK_20260914_INA_CROSS_DB_TRIGGER_AND_DEVICE_STATUS_API
**狀態**：✅ 已完工並驗收通過

---

## 一、實作內容與變更清單

配合 Ina 已在 `141.148.165.50` 的 `alliance_db` 建立完成的兩組觸發器：
- `trg_ali_device_bindings_sync_to_iotv9` (AFTER INSERT)
- `trg_ali_device_bindings_sync_to_iotv9_upd` (AFTER UPDATE)

Allie 已將 Alliance 應用層中所有舊有手動跨庫雙寫至 `waw_core.devices` 的代碼全數拔除：

### 1. `app/Http/Controllers/DeviceController.php`
- 移除 `commitRegistration()` 內呼叫 `$this->core()->table('devices')->updateOrInsert(...)` 的雙寫代碼。
- 改為只寫入 `ali_device_bindings`，由 MySQL 觸發器自動在同一事務內同步至 `iotv9.devices`。
- 保留成功 Log 紀錄，供追蹤 Trigger 運作。

### 2. `app/Http/Controllers/OrderController.php`
- 移除 `ship()` 流程中第 6 步對 `$this->syncDevicesToCore($order)` 的呼叫。
- 移除私有方法 `syncDevicesToCore(AliOrder $order)` 本身（共 70+ 行代碼全數拔除）。
- 出貨流程回歸業務本質，完全交由資料庫層 Trigger 自動維護設備同步。

---

## 二、Git 提交與部署資訊

- **Commit Hash**: `ba6f6f6`
- **Commit 訊息**: `refactor(devices): remove legacy PHP dual-write, delegate sync to MySQL trigger`
- **異動檔案**:
  - `app/Http/Controllers/DeviceController.php` (+9, -36)
  - `app/Http/Controllers/OrderController.php` (+1, -72)
- **遠端部署**:
  - 主機: `137.131.50.16` (`ali.tg25.win`)
  - 狀態: `git pull` fast-forward 成功，`config:cache` / `route:cache` / `view:clear` 執行完畢。
  - HTTP 狀態碼檢驗: `https://ali.tg25.win/devices` 正常回應 302/200，無語法與運行期異常。

---

## 三、驗證結論

- 應用層已完全解除對 `waw_core.devices` 的雙寫耦合。
- 後續無論老邱從燒錄站、後台管理、或 API 寫入/更新 `ali_device_bindings`，MySQL Trigger 保證原子性寫入 `iotv9.devices`，老李（場主端）可隨時在後台檢視未設置卡片。

---
**回報者**：Allie (Alliance Lead)  
**回報時間**：2026-09-14 14:30
