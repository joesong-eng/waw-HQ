# 任務：TASK_20261005_SOPHIE_PURGE_SYSWAWIOT_REFS

**派發時間**：2026-10-05
**優先級**：medium
**負責人**：Sophie (Owner)
**性質**：殘留清理 + 提交（Joe 指示：`sysWawIot/` 都是舊的）

---

## 背景

舊根目錄 `/Users/ilawusong/Documents/sysWawIot/` 已遷移為 `/Users/ilawusong/Documents/WaW/`。
Joe 指示：凡引用 `sysWawIot/` 的都是舊的，一律更新或刪除。

**HQ 已代為修正你的專案內 3 個 `.kiro` 檔**（路徑更新 + 修復斷鏈守則），現工作區有待提交變更：

```
 M .kiro/memory/sophie_rules.md          (舊路徑 → 新知識庫路徑)
 M .kiro/steering/agent-execution-rules.md (原指向失效路徑，已重寫為 Owner 專用守則 + 回報鐵律)
 M .kiro/steering/v9-knowledge.md        (舊 HQ 路徑 → 新根目錄)
```

## 任務

1. 確認這 3 檔 diff 無誤。
2. **重點**：`.kiro/steering/agent-execution-rules.md` 已重寫，**請務必閱讀並遵守**（內含「完成回報鐵律」：任務完成後必寫 outbox，否則視為未完成）。
3. 檢查專案內是否還有其他 `sysWawIot` 殘留（`dev-start.sh` 亦有）：
   ```bash
   grep -rn 'sysWawIot' PROJECT/Owner --include='*.sh' --include='*.md' --include='*.json' \
     | grep -v 'storage/' | grep -v '.venv'
   ```
   - `dev-start.sh`（`cd /Users/.../sysWawIot/waw-core`）→ 更新為新路徑。
4. commit + push。
   - 建議 message：`chore(owner): purge stale sysWawIot paths; adopt rewritten agent rules`

## 驗收指標

1. `git -C PROJECT/Owner status --porcelain` → 空
2. `git -C PROJECT/Owner log origin/main..HEAD` → 0
3. `grep -rn 'sysWawIot' PROJECT/Owner --include='*.sh' --include='*.md' --include='*.json' | grep -v storage/ | grep -v .venv` → 僅剩 `agent-execution-rules.md` 的「已失效」說明
4. 站點存活：`curl -sI https://iot.tg25.win/login` → 200

## 禁止

- 不改任何程式邏輯
- 不動 `.kiro`/`dev-start.sh` 以外的檔案

## 完成定義

commit + push 完成，**並務必寫 outbox 回報**（`.taskflow/owner/outbox/`）——這是新守則的第一個考驗。
