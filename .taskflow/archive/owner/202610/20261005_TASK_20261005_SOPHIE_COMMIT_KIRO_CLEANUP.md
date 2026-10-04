# 任務：TASK_20261005_SOPHIE_COMMIT_KIRO_CLEANUP

**派發時間**：2026-10-05
**優先級**：low
**負責人**：Sophie (Owner)
**性質**：收尾提交（HQ 已代為修正內容，只需 commit + push）
**關聯**：`TASK_20261005_SOPHIE_OWNER_RESIDUAL_CLEANUP`（前單 .kiro 清理未清完全）

---

## 背景

前單 `TASK_20261005_SOPHIE_OWNER_RESIDUAL_CLEANUP` 已將 `.kiro` 的 `OwnerSubscription` 引用改為 `Subscription`（commit `ca50c68` 已 push）。

但 HQ 複核發現**仍有殘留**：`.kiro` 內還提及已於 2026-10-04 刪除的 `EnsureProSubscription` middleware 與 `subscription.pro` 別名，以及從未實作的 `SubscriptionService::isSubscriptionActive()` / `getSubscriptionStatus()`。

**HQ 已直接修正內容**（依「順手補清」指示），現 Owner 工作區有 2 檔待提交：

```
 M .kiro/agents/accessops.md
 M .kiro/skills/subscription-logic.md
```

## 任務

1. 確認這兩檔的 diff 為上述清理（無誤刪）。
2. commit + push。
   - 建議 message：`docs(kiro): purge removed EnsureProSubscription/subscription.pro refs (ADR-003 follow-up)`

---

## 驗收指標

1. `git -C PROJECT/Owner status --porcelain` → **空**
2. `git -C PROJECT/Owner log origin/main..HEAD` → **0**（已 push）
3. `grep -rn 'EnsureProSubscription' PROJECT/Owner/.kiro/` → 僅剩「已刪除」加註行

---

## 禁止

- 不改任何程式邏輯
- 不動 `.kiro` 以外的檔案

## 完成定義

commit + push 完成，3 項驗收有輸出，回報寫入 `.taskflow/owner/outbox/`。

> 註：前單成果經 HQ 實測驗收通過（dirty 歸零、commit ca50c68、站點正常），但**未寫 outbox 回報**，違反回報鐵律。本單請務必留回報。
