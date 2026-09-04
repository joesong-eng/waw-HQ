# HQ 決策與授權指令：Ina 資料庫 Schema 遷移細節確認

- **任務 ID**：TASK_20260903_INA_SIGNALHUB_SCHEMA_AND_LOG_MAINTENANCE
- **決策者**：HQ
- **日期**：2026-09-03

## 1. 欄位架構確認
1. **機台編號與名稱**：
   - `devices` 表（實體設備）：新增 `machine_number` VARCHAR(64) NULL, `machine_name` VARCHAR(128) NULL。
   - `signal_profiles` 表（推播與業務）：新增 `machine_number` VARCHAR(64) NULL, `machine_name` VARCHAR(128) NULL, `serial_enabled` BOOLEAN DEFAULT TRUE。
   - 皆設為 **NULLABLE**，確保既有設備相容。

2. **點數與脈衝型態（純整數，無小數點）**：
   - `cleared_points`：使用 **`BIGINT UNSIGNED NULL DEFAULT NULL`**（支援千萬級大點數，無小數點）。
   - `raw_value`：**`BIGINT UNSIGNED DEFAULT 0`**（64-bit 總里程數，純整數）。
   - `delta_value`：**`INT UNSIGNED DEFAULT 1`**（觸發一次就是 1，無小數點）。

3. **授權狀態**：
   - ✅ **正式授權啟動**：請 Ina 依上述規格撰寫標準 Laravel Migration 檔案，並依照 WAW SOP 進行預審查與部署回報。
