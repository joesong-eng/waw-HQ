# 任務：TASK_20261005_MINA_DELETE_MACHINE_SESSIONS_MIGRATION

**派發時間**：2026-10-05
**優先級**：medium
**負責人**：Mina (Member)
**性質**：殘留清理（Joe 裁定）
**架構依據**：`ADR-002_MEMBER_DEVICE_SESSION_SSOT.md`

---

## 背景（Joe 裁定）

`machine_sessions` 已依 ADR-002 廢除，SSOT 統一為 `device_sessions`。

經 Ina 遠端查核（`TASK_20261005_INA_VERIFY_DEVICE_SESSIONS_SSOT`）確認：
- **`machine_sessions` 表在生產環境根本不存在**（該 migration 從未執行過）。
- `device_sessions` 表**存在且正常運作**（96 筆，4 個 migration 全 Ran）。
- Member 程式碼對 `machine_sessions` / `MachineSession` 引用 = **0**。

唯一殘留是那個從未執行的 migration 檔：
```
PROJECT/Member/database/migrations/2026_03_23_024700_create_machine_sessions_table.php
```

**Joe 裁定：刪除該 migration 檔。**

---

## 任務步驟

1. **確認無引用**：
   ```bash
   grep -rn 'MachineSession\|machine_sessions' app/ routes/ database/ --include='*.php'
   ```
   預期只剩該 migration 檔本身。
2. **刪除** `database/migrations/2026_03_23_024700_create_machine_sessions_table.php`。
3. **確認 migrate 帳本無此檔記錄**（遠端 `migrations` 表不應有 `create_machine_sessions_table`；若有殘列，回報但不自行刪）。
4. commit + push。
   - 建議 message：`chore(member): delete never-run machine_sessions migration (ADR-002 cleanup)`

---

## 驗收指標（附實際佐證）

1. 刪除前 `grep` 結果（確認僅該檔）
2. 刪除後 `ls database/migrations/ | grep machine` → 空
3. `git status` + commit hash + push 狀態
4. 遠端 `php artisan migrate:status | grep machine` → 無此項
5. `curl -sI https://win.tg25.win/` → 200（站點存活）

---

## 禁止

- 不動 `device_sessions` 相關 migration（那是現行 SSOT）
- 不動 production DB 資料
- 不刪遠端 `migrations` 表的任何列（如有殘列，回報 HQ）

## 完成定義

migration 檔刪除並 push，5 項驗收有輸出，回報寫入 `.taskflow/member/outbox/`。
