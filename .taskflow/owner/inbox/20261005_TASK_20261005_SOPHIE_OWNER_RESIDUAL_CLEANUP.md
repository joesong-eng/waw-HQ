# 任務：TASK_20261005_SOPHIE_OWNER_RESIDUAL_CLEANUP

**派發時間**：2026-10-05
**優先級**：high
**負責人**：Sophie (Owner)
**性質**：收尾清理（程式碼已於 ADR-003 落地，本單只做「殘留歸零 + 版控收斂」）

---

## 背景

HQ 全系統盤點發現：Owner 是**唯一仍有未提交檔案**的專案（其餘 7 專案 dirty=0）。
ADR-003「訂閱表統一為 `subscriptions`、廢除 `owner_subscriptions`」在 Owner 只做了一半：
程式碼已 commit（`6a2d53d`），但文件替換改完**未提交**，且 `.kiro/` 代理記憶仍指向已廢除模型。

---

## 任務 1：提交 Owner 未提交的 2 個檔案

現況（`git status --porcelain`）：
```
 M README.md
 M docs/TEST_PLAN.md
```

內容皆為 `OwnerSubscription` → `Subscription` 的文案替換（未動程式碼）。

**動作**：確認 diff 無誤後 commit + push。

- 建議 commit message：`docs(subscription): finish OwnerSubscription -> Subscription rename in README/TEST_PLAN (ADR-003)`
- push：`git push origin main`

---

## 任務 2：清除 `.kiro/` 內已廢除的 `OwnerSubscription` 引用

ADR-003 已廢除 `OwnerSubscription`，但 Owner 專案 `.kiro/` 代理技能/記憶檔仍殘留舊模型引用：

```
.kiro/agents/accessops.md:28,39,41
.kiro/skills/subscription-logic.md:13
.kiro/steering/kiro-access-ops-memory.md:12
.kiro/steering/known-bugs.md:109,143
```

**動作**：將上述文件中「現行規則/技能」語意下的 `OwnerSubscription` 改為 `Subscription`
（指向 `subscriptions` 表）。

**注意（歷史記憶豁免）**：
- `.kiro/steering/kiro-access-ops-memory.md` 與 `known-bugs.md` 中**明確標記為歷史事件紀錄**（例如 `[2026-04-15]` 的審核紀錄）的段落，
  **保留原文**，僅在該段落末尾加註「（該模型已於 ADR-003 廢除，現行為 `Subscription`）」。
- 其餘描述「現行查詢規則、模型路徑」者一律更正為 `Subscription`。

---

## 驗收指標（每項附實際指令與輸出）

1. `git status --porcelain` → **空**（dirty=0）
2. `git log origin/main..HEAD` → **0**（已 push）
3. `grep -rn 'OwnerSubscription' .kiro/` → 僅剩**歷史紀錄段落的加註行**，且不含「現行模型路徑」語意
4. `grep -rn 'OwnerSubscription' app/ routes/ resources/` → **0 hits**（維持 ADR-003 歸零）
5. `curl -sI https://iot.tg25.win/login` → HTTP 200（站點存活）

---

## 禁止

- 不改任何程式邏輯（本單純文件/記憶清理）
- 不動 `.kiro/` 以外的非 Owner 專案
- 未確認 diff 前不得 commit

## 完成定義

任務 1、2 完成，5 項驗收皆有實際輸出佐證，回報寫入 `.taskflow/owner/outbox/`。
