# 任務回報：TASK_20260920_INA_AUDIT_ALLIANCE_MIGRATION_DRIFT

**完成時間**：2026-09-20 22:30  
**執行者**：ina (Infra Master)

## 執行結果

### 1. 漂移根本原因分析
- `ali.tg25.win` (137.131.50.16) 的預設資料庫連接為 `alliance`，指向 `infra` (141.148.165.50) 的 `alliance_db`。
- 歷史上 Alliance 資料庫與數據是透過 raw SQL 與遷移腳本一次性初始化建立，但 Laravel `migrations` 帳本僅記錄了 4 個初始遷移以及 2026-09-09 的 4 個遷移，導致歷史的 16 個遷移在帳本中呈現 `Pending`。
- 其中包含 `2026_06_18_210000_migrate_users_to_alliance_db.php`（含數據校驗邏輯，重跑會拋異常中斷）、`create_ali_base_tables` 等。若觸發 `php artisan migrate --force`，部署流程必然中斷或可能破壞結構。

### 2. 安全備份與帳本補齊
- 備份現有 migrations 帳本至 `/home/ubuntu/tg25-infra/backups/alliance_db_migrations_before_audit_20260920.sql`。
- 實地逐表校對 `alliance_db` 現有 Schema（包括 `ali_products`, `ali_orders`, `ali_order_items`, `ali_device_bindings`, `alliance_users`, `ali_product_bundles`, `ali_settlements` 等各欄位與索引），確認所有 16 個 Pending 遷移所定義的表結構與欄位早已完整存在於線上 DB。
- 將 16 個已在線生效的遷移記錄補入 `alliance_db.migrations` 帳本（Batch 1）：
  - `2026_04_23_230204_create_ali_product_bundles_table`
  - `2026_04_24_000001_add_missing_columns_to_ali_tables`
  - `2026_04_24_200001_add_has_firmware_to_ali_products`
  - `2026_04_24_200002_create_ali_product_audit_logs_table`
  - `2026_04_24_210001_update_ali_products_category_enum`
  - `2026_04_25_000001_update_ali_orders_deposit_and_partner`
  - `2026_04_28_063833_add_node_id_to_ali_device_bindings_table`
  - `2026_04_28_182950_add_qr_printed_at_to_ali_device_bindings_table`
  - `2026_04_28_184125_add_firmware_type_to_ali_products_table`
  - `2026_05_05_103806_add_is_test_to_kiosks_table`
  - `2026_05_05_104808_add_name_to_kiosks_table`
  - `2026_05_22_172328_add_owner_id_to_ali_orders_table`
  - `2026_06_17_174850_create_ali_base_tables`
  - `2026_06_18_200000_create_alliance_db_schema`
  - `2026_06_18_210000_migrate_users_to_alliance_db`
  - `2026_09_13_230000_add_public_token_to_ali_device_bindings_table`

### 3. 實機驗證確認
- 執行 `php artisan migrate:status`：所有 24 個遷移檔案全數為 `Ran`，無任何 `Pending`。
- 執行 `php artisan migrate --pretend --force`：輸出 `Nothing to migrate.`
- 執行 `php artisan migrate --force`：輸出 `Nothing to migrate.`，零報錯，零結構變動。
- 未來 `../../dev_tools/waw_ops.sh deploy alliance` 執行時將平滑通過，不再有衝突或中止風險。

## 結論
✅ 完成

---
**回報者**：ina  
**回報時間**：2026-09-20 22:30

