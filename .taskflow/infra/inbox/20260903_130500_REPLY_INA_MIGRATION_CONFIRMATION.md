
# 任務回覆與啟動授權：TASK_20260903_INA_SIGNALHUB_SCHEMA_AND_LOG_MAINTENANCE

**發送時間**：2026-09-03 13:05  
**回覆者**：HQ  
**對象**：Ina (Infra Database Lead)

---

## 📋 HQ 決策與指令

1. **確認雙表同時加（冗餘加速）**：
   - `devices` 表：新增 `machine_number` VARCHAR(64) NULL, `machine_name` VARCHAR(128) NULL。
   - `signal_profiles` 表：新增 `machine_number` VARCHAR(64) NULL, `machine_name` VARCHAR(128) NULL, `serial_enabled` BOOLEAN DEFAULT TRUE。
   - 皆設為 **NULLABLE**。

2. **點數與脈衝欄位型態（嚴格純整數，無小數點）**：
   - `cleared_points`：使用 **`BIGINT UNSIGNED NULL DEFAULT NULL`**（支援百萬/千萬級大點數遊戲機，無小數點）。
   - `raw_value`：**`BIGINT UNSIGNED DEFAULT 0`**（64-bit 總里程數，純整數）。
   - `delta_value`：**`INT UNSIGNED DEFAULT 1`**（脈衝觸發一次就是 1，純整數，無小數點）。

3. **正式授權**：
   - ✅ **已確認無誤，正式授權「啟動」**。
   - 請撰寫標準 Laravel Migration 檔案，依 WAW SOP 執行並回報。

