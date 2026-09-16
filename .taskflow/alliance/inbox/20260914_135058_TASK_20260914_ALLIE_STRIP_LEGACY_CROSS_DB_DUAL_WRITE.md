# 任務：TASK_20260914_ALLIE_STRIP_LEGACY_CROSS_DB_DUAL_WRITE
**派發時間**：2026-09-14 14:20
**優先級**：HIGH
**負責人**：Allie (Alliance Lead)
**來源**：
- PROPOSAL_20260914_ALLIE_DEVICES_CROSS_DB_ARCHITECTURE_REFACTOR.md
- Ina 完工回報 20260914_134500_REPORT_TASK_20260914_INA_CROSS_DB_TRIGGER_AND_DEVICE_STATUS_API.md

## 一、任務說明
Ina 已於資料庫層（`141.148.165.50` 的 `alliance_db`）部署了兩組觸發器：
- `trg_ali_device_bindings_sync_to_iotv9` (AFTER INSERT)
- `trg_ali_device_bindings_sync_to_iotv9_upd` (AFTER UPDATE)

當 `ali_device_bindings` 有寫入或更新且具備有效 `chip_id` 與 `node_id` 時，MySQL 會自動在同一事務內同步至 `iotv9.devices`。因此，Alliance 應用層原本的跨庫手動雙寫已無存在必要，且容易造成脫鉤。

---

## 二、具體執行項目

### 1. 清理 DeviceController 中的跨庫寫入
- **檔案**：`app/Http/Controllers/DeviceController.php`
- **範圍**：約 200-227 行 `commitRegistration()`（以及 `afterSalePair()` 若有）
- **操作**：拔除手動呼叫 `core()->table('devices')->updateOrInsert(...)` 的代碼，改為單純寫入 `ali_device_bindings`，由 Trigger 自動接手同步。

### 2. 清理 OrderController 中的跨庫寫入
- **檔案**：`app/Http/Controllers/OrderController.php`
- **範圍**：約 604-655 行的 `syncDevicesToCore()` 方法及呼叫處（如 `ship()`）
- **操作**：移除或標記廢棄 `syncDevicesToCore()` 跨庫操作，簡化出貨流程。

### 3. 本地語法驗證、Commit 與部署
- 確保 PHP 語法通過 `php -l`。
- Commit 訊息格式：`refactor(devices): remove legacy PHP dual-write, delegate sync to MySQL trigger`
- 推送至 `origin/main`。
- 使用 `dev_tools/waw_ops.sh deploy allie` 部署至 `137.131.50.16` (`ali.tg25.win`)。

### 4. 驗收方式
- 部署完成後，確認燒錄站（`https://ali.tg25.win/devices`）運行無 PHP 報錯。
- 將 Commit Hash、修改檔案清單與驗證結果回報至 outbox。

---
**派發者**：HQ  
**派發時間**：2026-09-14 14:20
