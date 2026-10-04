# 任務：TASK_20261005_MINA_PURGE_SYSWAWIOT_REFS

**派發時間**：2026-10-05
**優先級**：low
**負責人**：Mina (Member)
**性質**：殘留清理（Joe 指示：`sysWawIot/` 都是舊的，更新或刪除）

---

## 背景

舊根目錄 `/Users/ilawusong/Documents/sysWawIot/` 已遷移為 `/Users/ilawusong/Documents/WaW/`。
Joe 指示：凡引用 `sysWawIot/` 的都是舊的，一律更新或刪除。

**新舊路徑對照**：
| 舊 | 新 |
|----|----|
| `/Users/ilawusong/Documents/sysWawIot/Member` | `/Users/ilawusong/Documents/WaW/PROJECT/Member` |
| `/Users/ilawusong/Documents/sysWawIot/HQ` | `/Users/ilawusong/Documents/WaW` |

---

## 你專案內的殘留（HQ 已定位）

- `PROJECT/Member/docs/TASK_20260514_MINA_FAQ_RESOLUTION.md`（歷史報告，路徑改新）
- `PROJECT/Member/temp_core_remnants/.kiro/steering/*.md`、`.vscode/sftp.json`（暫存殘留目錄）

## 任務

1. `docs/TASK_20260514_MINA_FAQ_RESOLUTION.md`：把 `sysWawIot/Member`、`sysWawIot/HQ` 等路徑更新為新路徑。
2. `temp_core_remnants/`：確認是否為無用暫存；若是，整區刪除；不確定先回報。
3. commit + push。

## 驗收指標

1. `grep -rn 'sysWawIot' PROJECT/Member --include='*.md' --include='*.json'` → 0 hits
2. 若有刪除，列清單
3. commit hash + push 狀態
4. 站點存活：`curl -sI https://win.tg25.win/` → 200

## 禁止

- 不動 `app/`、`routes/`、`resources/` 正式邏輯
- 不確定用途的檔案先保留並改路徑

## 完成定義

殘留處理完畢，驗收有輸出，回報寫入 `.taskflow/member/outbox/`。
