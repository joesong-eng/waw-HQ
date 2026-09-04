# HQ Autoflow — 自動化任務流程服務

> **建立日期**：2026-06-10
> **狀態**：✅ 現役（launchd 常駐）
> **核心檔案**：`scripts/hq_gateway.py`（完整路徑：`/Users/ilawusong/Documents/sysWawIot/HQ/scripts/hq_gateway.py`）

---

## 定位

HQ Autoflow 是一個**常駐自動化服務**，不是 skill，也不是一次性工具。

它在背景持續監聽 Redis，收到事件後自動推進任務流程——從諮詢、回覆、LLM 決策，到發出實作任務或結案，全程無需人工介入。

```
hq_task_flow.sh consult   ←── Joe / HQ 真身發令
        │
        ▼ Redis Pub/Sub
hq_gateway.py（launchd com.hq.agents.supervisor 常駐）
        ├─ GatewayListener  → 監聽所有 agent/* 頻道
        ├─ ContextStore     → Redis hq:thread:<id>:* 讀寫
        └─ DecisionEngine   → LLM 判斷 → hq_task_flow.sh 執行下一步
        │
        ▼
codex exec（Agent 分身執行任務）
        │
        ▼ agent_report_to_hq_v2.sh → Redis PUBLISH agent/<agent>/report
        │
        ▼
DecisionEngine.decide() → DECISION: approved / task / redo / supplement / escalate
```

---

## 完整 SOP 流程

### 階段一：諮詢（consulting）

Joe 發出諮詢，給 Agent 先評估可行性：

```bash
./scripts/hq_task_flow.sh consult <agent> <consult_id> "<問題描述>"
```

**查詢型 vs 設計型諮詢**：
- **查詢型**（`consult`）：查詢現況、確認設定 → LLM 自動決策，可自動結案
- **設計型**（`review`）：設計 schema、撰寫規格 → 永遠 escalate，必須 Joe 審核

```bash
# 查詢型（可自動結案）
./scripts/hq_task_flow.sh consult ina CONS_001 "Redis 版本是多少？"

# 設計型（永遠需審核）
./scripts/hq_task_flow.sh review ina REV_001 "設計玩家錢包 DB schema"
```

- `hq_task_flow.sh` 寫入 context store（status=`consulting`）並 PUBLISH
- Gateway 收到 → `on_consultation()` → 觸發 Agent codex exec
- Agent 回答後 → `agent_report_to_hq_v2.sh` → Redis PUBLISH `agent/<agent>/report`

### 階段二：LLM 決策

Gateway `on_report()` 收到回報：

1. 存入 `.taskbox/inbox/<ts>_<agent>_auto.json`
2. 讀取 context store（含完整歷史）
3. 呼叫 LLM（`localhost:8000/v1/chat/completions`，model: `ag/claude-sonnet-4-6`）
4. 解析 DECISION 標記

| DECISION | 動作 |
|---------|------|
| `approved` | 結案，context store 標記 `resolved` |
| `task:<描述>` | 發正式實作任務給 Agent |
| `redo:<原因>` | 要求 Agent 重做 |
| `supplement:<問題>` | 要求補充資訊 |
| `escalate:<原因>` | 寫入 `HQ_ESCALATE_*.md`，等 Joe 介入 |

### 階段三：實作（pending）

DecisionEngine 決定 `task` 後：

```bash
hq_task_flow.sh task <agent> TASK_<id> "<描述>" high
```

- Agent 收到正式任務 → codex exec 實作
- 實作完成 → `agent_report_to_hq_v2.sh` 回報
- Gateway 再次收到 → DecisionEngine 驗收（status=`pending`）
- 驗收通過 → `approved` → 結案

### 結案條件

context store status 變為 `resolved` 後，後續所有回報自動跳過（`⏭ 已結案`）。

---

## 三個核心 Class

### `ContextStore`

Redis `hq:thread:<id>:*` 的讀寫封裝，TTL 7 天。

```
hq:thread:<id>:status      → consulting / pending / redo_requested / resolved
hq:thread:<id>:round       → 第幾輪（整數）
hq:thread:<id>:agent       → Agent 名稱
hq:thread:<id>:description → 原始描述
hq:thread:<id>:history     → JSON list，每輪完整記錄
```

### `DecisionEngine`

- LLM URL：`http://localhost:8000/v1/chat/completions`（9router 本地常駐）
- API Key：`GATEWAY_API_KEY` 環境變數（預設從 codex config 讀）
- Model：`GATEWAY_MODEL` 環境變數（預設 `ag/claude-sonnet-4-6`）
- stream：`False`（強制同步回應）

consulting 階段的判斷標準（`STATUS_PROMPTS['consulting']`）：
1. 諮詢問題已完整回答，不需進一步實作 → `approved`
2. 確認可行且需要實作 → `task:<描述>`（嚴格限制在原始描述範圍內）
3. 不可行或有風險 → `escalate:<原因>`
4. 回覆不完整 → `supplement:<問題>`

### `GatewayListener`

訂閱頻道：
```
agent/*/task
agent/*/consultation
agent/*/report
agent/*/supplement
agent/*/redo
agent/*/approval   ← 只記 log，不觸發執行
```

---

## 重要設計決策

### task_id 命名規則
諮詢 ID `CONS_YYYYMMDD_NNN` 衍生為任務 ID `TASK_YYYYMMDD_NNN`（一次性替換，不疊加 `_TASK`）。

### 雙重回報防止
`execute_task()` 結束後統一呼叫 `agent_report_to_hq_v2.sh`，prompt 裡不要求 Agent 自行呼叫。

### approval 事件不觸發執行
`hq_task_flow.sh approve` 發出的 `agent/*/approval` 事件是給人工確認用的，Gateway 只記 log。

### history JSON 格式
`hq_task_flow.sh` 使用 `python3 -c "import json..."` 生成標準 JSON，避免 shell 引號問題造成非法格式。

---

## 已知限制

- 雙重 Redis 訂閱：`approved` 後 `hq_task_flow.sh approve` 會再發一個 `approval` 事件給 Agent，Agent 會再跑一次 codex exec（approve 任務），但因 status=`resolved`，Gateway 收到其回報後會直接跳過，**不影響正確性，只是多跑一次**。
- LLM 端點依賴 9router 本地服務（`localhost:8000`）必須常駐。

---

## 維運指令

```bash
# 查看即時 log
tail -f /Users/ilawusong/Documents/sysWawIot/HQ/logs/hq_gateway.out.log

# 重啟服務
launchctl unload ~/Library/LaunchAgents/com.hq.agents.supervisor.plist
launchctl load  ~/Library/LaunchAgents/com.hq.agents.supervisor.plist

# 查看 context store
redis-cli LRANGE "hq:thread:<id>:history" 0 -1
redis-cli GET "hq:thread:<id>:status"

# 手動結案（緊急）
redis-cli SET "hq:thread:<id>:status" resolved
```

---

## 歷史演進

| 日期 | 事件 |
|------|------|
| 2026-06-06 | Chat Bridge 廢棄，改用 HQ Message Hub v1（HTTP localhost:8899） |
| 2026-06-09 | 升級為 v3.0 Redis Pub/Sub + agents_supervisor.py |
| 2026-06-10 | Qoder 實作 hq_gateway.py（DecisionEngine + ContextStore） |
| 2026-06-10 | Trae 重構：移除 import 耦合，Gateway 完全自包含 |
| 2026-06-10 | 端對端測試：發現並修正 task_id 疊加、consulting 無 approved 選項、雙重回報、approval 重複觸發等問題 |
| 2026-06-10 | agents_supervisor.py 退為純函式庫，Gateway 統一接管所有監聽 |

---

## 相關文件

- `scripts/hq_gateway.py` — 核心實作
- `scripts/hq_task_flow.sh` — HQ 發令唯一入口
- `scripts/agent_report_to_hq_v2.sh` — Agent 回報腳本（Redis PUBLISH）
- `brains/knowledge/01_agent_governance/MESSAGE_HUB_PROTOCOL.md` — 通訊協定
- `brains/knowledge/01_agent_governance/AUTOFLOW_CONTEXT_STORE_DESIGN.md` — 設計演進歷史
- `brains/knowledge/04_ops_and_deployments/LAUNCHD_AGENT_ARCHITECTURE.md` — launchd 架構
- `.kiro/specs/hq-gateway/design.md` — 原始設計規格（Qoder 使用）

---

*制定者：HQ | 版本：1.0 | 建立日期：2026-06-10*
