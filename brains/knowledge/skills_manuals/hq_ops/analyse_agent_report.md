# ~~Skill: analyse_agent_report~~ — ⚠️ DEPRECATED

> **狀態**：已由 `scripts/hq_gateway.py` 的 `DecisionEngine` 自動接管，本文件不再使用。
> **廢棄日期**：2026-06-10
> **取代者**：`scripts/hq_gateway.py` → `class DecisionEngine`

## 為什麼廢棄

原本這個 skill 是給 HQ 子代理（codex exec）讀的執行手冊，
收到 Agent 回報後 spawn 一個子代理、讀這份 md、照步驟判斷。

現在 `hq_gateway.py` 的 `DecisionEngine.decide()` 直接呼叫 LLM API 完成同樣判斷，
不再需要 spawn 子代理，本文件實質退休。

## 決策邏輯現在在哪裡

`scripts/hq_gateway.py`：
- `DecisionEngine.STATUS_PROMPTS` — 各階段判斷標準（consulting / pending / redo_requested）
- `DecisionEngine.decide()` — 讀 context store → 呼叫 LLM → 解析 DECISION → 執行對應動作
- `DecisionEngine._execute()` — 呼叫 `hq_task_flow.sh` 執行 approved/task/redo/supplement
- `DecisionEngine._escalate()` — 寫入 `_agent/HQ_ESCALATE_*.md` 等待 Joe 介入

## 如需調整判斷邏輯

直接修改 `scripts/hq_gateway.py` 的 `DecisionEngine.STATUS_PROMPTS` 或 `SYSTEM_PROMPT`。
