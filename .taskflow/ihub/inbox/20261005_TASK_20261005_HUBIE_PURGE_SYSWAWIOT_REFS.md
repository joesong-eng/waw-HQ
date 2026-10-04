# 任務：TASK_20261005_HUBIE_PURGE_SYSWAWIOT_REFS

**派發時間**：2026-10-05
**優先級**：low
**負責人**：Hubie (iHub)
**性質**：殘留清理（Joe 指示：`sysWawIot/` 都是舊的，更新或刪除）

---

## 背景

舊根目錄 `/Users/ilawusong/Documents/sysWawIot/` 已遷移為 `/Users/ilawusong/Documents/WaW/`。
Joe 指示：凡引用 `sysWawIot/` 的都是舊的，一律更新或刪除。

## 你專案內的殘留（HQ 已定位）

- `PROJECT/iHub/Temp/01_agent_governance/`（`README.md`、`AGENT_RESPONSIBILITY_BOUNDARIES.md`、`TASK_ROUTING_AND_COMPLETION.md`）
- `PROJECT/iHub/Temp/kiosk_three_screen_ux_flow.md`

> `Temp/` 疑似為舊文件暫存區。

## 任務

1. 判斷 `Temp/` 是否為無用暫存：
   - 若是 → 整區刪除。
   - 若仍需保留 → 內含路徑更新為新路徑（`sysWawIot/iHub` → `PROJECT/iHub`，`sysWawIot/HQ` → 根目錄）。
2. commit + push（若 `Temp/` 為 untracked 則不需 commit，於回報說明）。

## 驗收指標

1. `grep -rn 'sysWawIot' PROJECT/iHub --include='*.md'` → 0 hits
2. 處理說明（刪除 / 更新）
3. 站點存活：`curl -sI https://ihub.tg25.win/` → 200

## 禁止

- 不動 `src/`、`dist/` 正式邏輯

## 完成定義

殘留處理完畢，回報寫入 `.taskflow/ihub/outbox/`。
