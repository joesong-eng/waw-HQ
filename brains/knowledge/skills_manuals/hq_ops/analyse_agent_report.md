# Skill: analyse_agent_report — ⛔ DEPRECATED（整條自動化鏈已廢除）

> **狀態**：已廢棄。原自動判斷鏈（`scripts/hq_gateway.py` 的 `DecisionEngine`）已於 2026-10-03 隨舊派工系統一併刪除。
> **廢棄日期**：2026-06-10（自動化廢除）／2026-10-03（`hq_gateway.py` 實體刪除）

---

## 現在 HQ 如何分析 Agent 回報

改為**人工**在 HQ session 內執行：

1. **全量讀取**回報：`.taskflow/<agent>/outbox/*.md`（禁止切片，整檔讀取）
2. 以實證驗收：指令輸出、HTTP 回應、SQL SELECT、git commit hash
3. 判斷：
   - ✅ 通過 → `./dev_tools/waw_ops.sh close <agent> <key>` 結案歸檔
   - 🔄 需補 → 重新派工，帶具體問題描述
   - ❌ 阻塞 → 評估是否調整設計或改派

## 取代者

- **派工/結案工具**：`dev_tools/waw_ops.sh`（`.taskflow` 純檔案系統）
- **回報工具**：`dev_tools/agent_report_to_hq_v2.sh`
- **派工協議（權威）**：`../../01_agent_governance/SIMPLE_FILE_DISPATCH_PROTOCOL.md`
- **協調流程**：`task_orchestration.md`

> ⛔ 不再有 `scripts/hq_gateway.py`、`DecisionEngine`、`.taskbox/`、`_agent/HQ_ESCALATE_*.md`。
