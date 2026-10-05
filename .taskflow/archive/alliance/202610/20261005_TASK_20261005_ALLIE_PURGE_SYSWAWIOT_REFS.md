# 任務：TASK_20261005_ALLIE_PURGE_SYSWAWIOT_REFS

**派發時間**：2026-10-05
**優先級**：medium
**負責人**：Allie (Alliance)
**性質**：殘留清理（Joe 指示：`sysWawIot/` 都是舊的，更新或刪除）

---

## 背景

舊根目錄 `/Users/ilawusong/Documents/sysWawIot/` 已遷移為 `/Users/ilawusong/Documents/WaW/`。
Joe 指示：凡引用 `sysWawIot/` 的都是舊的，一律更新或刪除。

**新舊路徑對照**：
| 舊 | 新 |
|----|----|
| `/Users/ilawusong/Documents/sysWawIot/Alliance` | `/Users/ilawusong/Documents/WaW/PROJECT/Alliance` |
| `~/Documents/sysWawIot/Alliance` | `~/Documents/WaW/PROJECT/Alliance` |

---

## 你專案內的殘留（HQ 已定位）

| 檔案 | 性質 | 建議 |
|------|------|------|
| `update_burning.php` | **一次性臨時腳本**（硬編碼舊路徑改 burning.blade.php） | 已無用 → **刪除** |
| `fix_terminal.php` | 同上（一次性 CSS 修補） | **刪除** |
| `fix_height.php` | 同上 | **刪除** |
| `compress_ui.php` | 同上 | **刪除** |
| `test_result.txt` | 一次性 500 錯誤 log | **刪除** |
| `AI_CONTEXT.md` | 舊路徑索引檔 | 路徑更新為新路徑，或刪除 |
| `_docs_quarantine/.kiro/steering/*.md` | 隔離區舊守則（untracked） | 路徑更新或整區刪除 |

> 這些 `*.php` 是當時用的一次性 patch 腳本，**不是應用程式邏輯**（不在 `app/` 內），刪除不影響站點。

## 任務

1. 逐一確認上述檔案**未被任何程式引用**（`grep -rn 'update_burning\|fix_terminal\|fix_height\|compress_ui' app/ routes/ resources/` → 應為 0）。
2. 一次性腳本與 log → 刪除。
3. `AI_CONTEXT.md` / `_docs_quarantine` → 更新路徑或刪除（不確定先回報）。
4. commit + push。

## 驗收指標

1. `grep -rn 'sysWawIot' PROJECT/Alliance --include='*.php' --include='*.md' --include='*.txt'` → 0 hits（排除 `.kiro/steering/agent-execution-rules.md` 的「已失效」說明）
2. 刪除檔案清單
3. commit hash + push 狀態
4. 站點存活：`curl -sI https://ali.tg25.win/` → 200/302

## 禁止

- 不動 `app/`、`routes/`、`resources/` 的正式邏輯
- 不動 `burning.blade.php`
- 不刪除仍在使用的檔案（不確定先回報）

## 完成定義

殘留處理完畢，驗收有輸出，回報寫入 `.taskflow/alliance/outbox/`。
