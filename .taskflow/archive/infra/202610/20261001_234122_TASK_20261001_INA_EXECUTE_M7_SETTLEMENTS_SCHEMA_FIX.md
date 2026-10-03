# 任務：TASK_20261001_INA_EXECUTE_M7_SETTLEMENTS_SCHEMA_FIX

**派發時間**：2026-10-01 23:41
**優先級**：P0 / Critical（解除 M7 月結算阻斷）
**負責人**：Ina (Infra)
**關聯模組**：Central DB iotv9 (VPS infra / 141.148.165.50) / Owner M7 / Infra _agent 治理

---

## 📌 任務背景與 HQ 裁示

依據 Ina 於 2026-10-01 回報之唯讀稽核報告（`20261001_220500_REPORT_TASK_20261001_INA_EVALUATE_M7_SETTLEMENTS_SCHEMA.md`）及過期治理文件清理提案（`PROPOSAL_20261001_INA_TO_HQ_CLEANUP_STALE_AGENT_DOCS.md`），HQ (Joe) 已正式核准並裁示如下：

1. **核准方案 A（三表對齊 M7 原始設計）**：一次性解決 settlements / settlement_logs / daily_revenue_reports 結構脫節。
2. **欄位依 Ina 建議處理**：
   - 舊版廢棄欄位（owner_id, amount, method, completed_at, reference）**確認丟棄**。
   - `outstanding_deducted` 與 `effective_payment` **確認保留**（Model $fillable 依賴）。
   - 財務表外鍵約束**嚴格遵循鐵律：禁用 ON DELETE CASCADE，改用 RESTRICT 或 SET NULL**。
   - `ali_settlements` 表為 Alliance 獨立業務表，**維持現狀不更動**。
3. **治理文件處置**：
   - `PROJECT/Infra/_agent/` 之過期治理文件採**加註廢棄（DEPRECATED）標頭**處置，保留歷史可追溯性。
   - 2026-08 歷史回報文件歸檔至 `_agent/archive/`。

---

## 📋 第一部分：M7 三表 Schema 升級修復（P0）

### 1.1 執行目標與庫別
- **目標庫**：Central DB `iotv9`（VPS infra / 141.148.165.50）
- 目前 `settlements`、`settlement_logs`、`daily_revenue_reports` 三表確認均為 **0 筆資料**，具備乾淨升級條件。

### 1.2 具體表結構定義規格

#### (A) `settlements` 表
- **操作**：處理 `data_anomalies` 之關聯後，採 `DROP TABLE IF EXISTS settlements` 並以完整 M7 規格重建。
- **必要欄位清單**：
  - `id` bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY
  - `settlement_number` varchar(50) NOT NULL UNIQUE COMMENT '結算單號'
  - `venue_id` bigint unsigned NOT NULL COMMENT '場地 ID (FK -> venues.id)'
  - `device_owner_id` bigint unsigned NOT NULL COMMENT '機台主 ID (FK -> users.id)'
  - `venue_owner_id` bigint unsigned NOT NULL COMMENT '場地主 ID (FK -> users.id)'
  - `period_start` date NOT NULL COMMENT '結算週期開始'
  - `period_end` date NOT NULL COMMENT '結算週期結束'
  - `total_revenue` decimal(12,2) NOT NULL DEFAULT 0.00 COMMENT '總營收'
  - `pre_tax_expenses` decimal(12,2) NOT NULL DEFAULT 0.00 COMMENT '稅前支出'
  - `taxable_revenue` decimal(12,2) NOT NULL DEFAULT 0.00 COMMENT '應稅營收'
  - `device_breakdown` json NULL COMMENT '設備營收明細快照'
  - `device_owner_amount` decimal(12,2) NOT NULL DEFAULT 0.00 COMMENT '機台主分潤金額'
  - `venue_owner_amount` decimal(12,2) NOT NULL DEFAULT 0.00 COMMENT '場地主分潤金額'
  - `device_owner_share` decimal(5,2) NOT NULL DEFAULT 0.00 COMMENT '機台主分潤比例%'
  - `venue_owner_share` decimal(5,2) NOT NULL DEFAULT 0.00 COMMENT '場地主分潤比例%'
  - `outstanding_deducted` decimal(12,2) NULL DEFAULT 0.00 COMMENT '扣除欠款'
  - `effective_payment` decimal(12,2) NULL DEFAULT 0.00 COMMENT '實際撥款'
  - `status` enum('created','confirmed','paid','closed','disputed') NOT NULL DEFAULT 'created' COMMENT '結算狀態'
  - `confirmed_at` timestamp NULL DEFAULT NULL
  - `paid_at` timestamp NULL DEFAULT NULL
  - `closed_at` timestamp NULL DEFAULT NULL
  - `disputed_at` timestamp NULL DEFAULT NULL
  - `dispute_reason` text NULL
  - `dispute_resolution` text NULL
  - `payment_proof_url` varchar(255) NULL
  - `created_at` timestamp NULL DEFAULT NULL
  - `updated_at` timestamp NULL DEFAULT NULL
- **索引與約束**：
  - UNIQUE KEY `settlements_settlement_number_unique` (`settlement_number`)
  - KEY `settlements_venue_id_index` (`venue_id`)
  - KEY `settlements_device_owner_id_index` (`device_owner_id`)
  - KEY `settlements_venue_owner_id_index` (`venue_owner_id`)
  - KEY `settlements_period_index` (`period_start`, `period_end`)
  - KEY `settlements_status_index` (`status`)
  - FK `venue_id` -> `venues.id` (ON DELETE RESTRICT)
  - FK `device_owner_id` -> `users.id` (ON DELETE RESTRICT)
  - FK `venue_owner_id` -> `users.id` (ON DELETE RESTRICT)

#### (B) `settlement_logs` 表
- **操作**：採 `DROP TABLE IF EXISTS settlement_logs` 並重建。
- **必要欄位清單**：
  - `id` bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY
  - `settlement_id` bigint unsigned NOT NULL COMMENT 'FK -> settlements.id'
  - `user_id` bigint unsigned NULL COMMENT '操作者 ID (FK -> users.id)'
  - `action` varchar(50) NOT NULL COMMENT '操作動作 (created, confirmed, marked_paid, closed, disputed, resolved)'
  - `from_status` varchar(50) NULL COMMENT '原狀態'
  - `to_status` varchar(50) NULL COMMENT '新狀態'
  - `metadata` json NULL COMMENT '變更明細快照'
  - `ip_address` varchar(45) NULL
  - `user_agent` text NULL
  - `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
- **索引與約束**：
  - KEY `settlement_logs_settlement_id_index` (`settlement_id`)
  - KEY `settlement_logs_user_id_index` (`user_id`)
  - FK `settlement_id` -> `settlements.id` (ON DELETE RESTRICT)
  - FK `user_id` -> `users.id` (ON DELETE SET NULL)

#### (C) `daily_revenue_reports` 表
- **操作**：採 `DROP TABLE IF EXISTS daily_revenue_reports` 並依現行 Active migration `2026_06_16_140202` 規格重建。
- **必要欄位清單**：
  - `id` bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY
  - `venue_id` bigint unsigned NOT NULL COMMENT 'FK -> venues.id'
  - `device_id` bigint unsigned NOT NULL COMMENT 'FK -> devices.id (必須補齊，M7 結算依賴)'
  - `report_date` date NOT NULL COMMENT '營業日'
  - `total_pulse` int unsigned NOT NULL DEFAULT 0
  - `total_amount` decimal(12,2) NOT NULL DEFAULT 0.00
  - `is_locked` tinyint(1) NOT NULL DEFAULT 0
  - `settlement_id` bigint unsigned NULL COMMENT '關聯結算單 (FK -> settlements.id)'
  - `created_at` timestamp NULL DEFAULT NULL
  - `updated_at` timestamp NULL DEFAULT NULL
- **索引與約束**：
  - UNIQUE KEY `daily_rev_venue_device_date_unique` (`venue_id`, `device_id`, `report_date`)
  - KEY `daily_revenue_reports_report_date_index` (`report_date`)
  - KEY `daily_revenue_reports_settlement_id_index` (`settlement_id`)
  - FK `venue_id` -> `venues.id` (ON DELETE RESTRICT，嚴禁 CASCADE)
  - FK `device_id` -> `devices.id` (ON DELETE RESTRICT)
  - FK `settlement_id` -> `settlements.id` (ON DELETE SET NULL)

#### (D) 外部表關聯恢復
- `data_anomalies.settlement_id`：重建 FK 關聯至 `settlements.id` (ON DELETE SET NULL)。

### 1.3 遷移腳本與版本控管
1. 將完整遷移 DDL 腳本儲存於 `PROJECT/Infra/db/migrations/v9/` 目錄下（例如 `M7_SETTLEMENTS_SCHEMA_ALIGNMENT.sql` 或 Python migration runner）。
2. 在 VPS infra 實機執行遷移前先建立 database snapshot / backup。
3. 執行後在 VPS 端以腳本或 SQL 驗證：
   - `DESCRIBE settlements;`
   - `DESCRIBE settlement_logs;`
   - `DESCRIBE daily_revenue_reports;`
   - 確認 3 張表的外鍵與約束建立完整。

---

## 📋 第二部分：過期治理文件清理與歸檔（Normal）

依據提案處理 `PROJECT/Infra/_agent/` 文件：

1. **認可處置**：認可 `HQ_COMMUNICATION_SOP.md` 已加註 DEPRECATED 標頭。
2. **加註 DEPRECATED 標頭（保留歷史可追溯）**：
   - `PROJECT/Infra/_agent/DISPATCH_BOARD.md`：頂部加註廢棄警示，說明派工機制已全面升級為 `.taskflow` 檔案模式（依據 `brains/knowledge/01_agent_governance/SIMPLE_FILE_DISPATCH_PROTOCOL.md` v4.0.0）。
   - `PROJECT/Infra/_agent/IDENTITY.md`：頂部加註廢棄警示，說明舊 machines 表已廢止，對齊最新架構。
   - `PROJECT/Infra/_agent/status.md`：頂部加註廢棄或更新為最新狀態。
3. **歷史報告歸檔**：
   - 建立 `PROJECT/Infra/_agent/archive/` 目錄。
   - 將 `_agent/` 根目錄下 7 份 2026-08 的歷史報告（`REPORT_*.md`）移入 `archive/`。

---

## 驗證標準與回報格式

1. 提供 Central DB 執行後三張表之 `DESCRIBE` 或 `SHOW CREATE TABLE` 截圖或文字驗證。
2. 確認外鍵約束中無任何非預期的 `CASCADE`。
3. 回報發布至 `.taskflow/infra/outbox/`。

---

**派發者**：HQ (Joe 裁示)  
**派發時間**：2026-10-01 23:41

