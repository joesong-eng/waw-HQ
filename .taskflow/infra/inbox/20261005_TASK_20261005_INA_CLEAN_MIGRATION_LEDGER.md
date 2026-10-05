# 任務：TASK_20261005_INA_CLEAN_MIGRATION_LEDGER

**派發時間**：2026-10-05
**優先級**：low
**負責人**：Ina (Infra / DB)
**性質**：殘留清理（Joe 裁定）
**關聯**：`TASK_20261005_MINA_DELETE_MACHINE_SESSIONS_MIGRATION`

---

## 背景

Mina 已刪除 Member 的 `2026_03_23_024700_create_machine_sessions_table.php`（該表從未在生產建立，程式碼 0 引用）。

但遠端 **Member 生產 DB 的 `migrations` 帳本仍有一筆殘列**：
```
2026_03_23_024700_create_machine_sessions_table .... Ran
```

這筆記錄指向已刪除的 migration 檔。`migrate:status` 會持續顯示它（但因檔案不存在，實際不會再被執行）。

**Joe 裁定：清理此殘列。**

---

## 任務

### 步驟 1：確認（唯讀）
- 到 Member 生產 DB（`waw_member_production` @ yd177，依你前單查核的正確連線）。
- 查：
  ```sql
  SELECT * FROM migrations WHERE migration LIKE '%machine_sessions%';
  ```
- 確認 `machine_sessions` 表確實不存在。

### 步驟 2：清理帳本殘列
- **先備份**該列（記錄 SELECT 輸出即可）。
- 刪除該列：
  ```sql
  DELETE FROM migrations WHERE migration = '2026_03_23_024700_create_machine_sessions_table';
  ```

### 步驟 3：驗證
- `php artisan migrate:status | grep machine` → 應無輸出。
- `php artisan migrate:status` → 其餘 migration 狀態正常（無異常）。
- 站點：`curl -sI https://win.tg25.win/` → 200。

---

## 驗收指標（附實際輸出）

1. 刪除前 SELECT 結果（備份）
2. 刪除後 `migrate:status | grep machine` → 空
3. `migrate:status` 整體正常
4. 站點 200

---

## 禁止

- 不動其他 migration 帳本記錄
- 不動任何業務資料表
- 不執行任何業務 DDL

## 完成定義

帳本殘列清除，4 項驗收有輸出，回報寫入 `.taskflow/infra/outbox/`。
