# Design Document: HQ Gateway

> **建立日期**：2026-06-10
> **版本**：1.0
> **實作代碼位置**：`HQ/scripts/hq_gateway.py`

---

## 實作前必讀

- 任務流程協定：`brains/knowledge/01_agent_governance/MESSAGE_HUB_PROTOCOL.md`
- context store 設計：`brains/knowledge/01_agent_governance/AUTOFLOW_CONTEXT_STORE_DESIGN.md`
- 現有 supervisor 代碼：`scripts/agents_supervisor.py`（參考 AgentThread 和 HQReportThread 的實作）
- LLM API 設定：`config/api_config.py`

---

## 架構總覽

```
Redis
 ├─ agent/*/task          ←── hq_task_flow.sh 發任務
 ├─ agent/*/consultation  ←── hq_task_flow.sh consult
 ├─ agent/*/report        ←── agent_report_to_hq_v2.sh 回報
 └─ agent/*/supplement    ←── hq_task_flow.sh supplement

          ↓ 全部訂閱

┌─────────────────────────────────────────────┐
│              HQ Gateway                      │
│                                             │
│  GatewayListener（主監聽迴圈）               │
│   ├─ on_task()        → 觸發 codex exec     │
│   ├─ on_consultation()→ 記錄 context store  │
│   └─ on_report()      → 呼叫 DecisionEngine │
│                              ↓              │
│         DecisionEngine（AI 決策核心）        │
│          ├─ 讀 context store（完整歷史）     │
│          ├─ 讀回報檔案（完整內容）           │
│          ├─ 組 prompt                       │
│          ├─ POST localhost:8000/v1/...      │
│          └─ 解析決策 → 執行對應動作         │
│                                             │
│  ContextStore（Redis 讀寫封裝）              │
│   ├─ read_thread()                         │
│   └─ append_history()                      │
└─────────────────────────────────────────────┘
```

---

## 模組設計

### 檔案結構

```
HQ/scripts/hq_gateway.py        ← 單一檔案，< 350 行
```

單一檔案，三個 class：

---

### Class 1：`ContextStore`

Redis context store 的讀寫封裝。

```python
class ContextStore:
    def __init__(self, redis_client):
        self.r = redis_client

    def read_thread(self, thread_id: str) -> dict:
        """
        回傳：
        {
            "status": "consulting" | "pending" | "redo_requested" | ...,
            "round": 3,
            "agent": "sophie",
            "description": "原始任務描述",
            "history": [
                {"round": 0, "from": "HQ", "action": "consult_issued", ...},
                {"round": 1, "from": "Sophie", "action": "report", "file": "...路徑...", "summary": "..."},
                ...
            ]
        }
        """

    def append_history(self, thread_id: str, entry: dict):
        """
        追加一筆 history，並更新 round 和 status（如果 entry 有帶的話）。
        entry 格式：
        {
            "round": <int>,
            "from": "Gateway" | "HQ" | "<agent_name>",
            "action": "llm_decision" | "task_triggered" | ...,
            "decision": "<選填>",
            "summary": "<摘要>",
            "file": "<選填，完整回報的檔案路徑>",
            "ts": "<ISO8601>"
        }
        """
```

---

### Class 2：`DecisionEngine`

呼叫 LLM 判斷並執行決策。

```python
class DecisionEngine:
    LLM_URL = "http://localhost:8000/v1/chat/completions"
    LLM_MODEL = "ag/claude-sonnet-4-6"  # 可由環境變數 GATEWAY_MODEL 覆寫

    def __init__(self, hq_path: Path, context_store: ContextStore):
        ...

    def decide(self, thread_id: str, from_agent: str, inbox_file: Path) -> str:
        """
        主入口。
        1. 讀 context store
        2. 讀回報檔案全文
        3. 組 prompt
        4. 呼叫 LLM
        5. 解析決策
        6. 執行動作
        7. 寫回 context store
        回傳：決策字串（'approved' | 'task:...' | 'redo:...' | 'escalate:...'）
        """

    def _build_prompt(self, thread: dict, report_content: str, status: str) -> str:
        """
        組裝完整 prompt，包含：
        - 系統角色
        - 任務背景（agent、描述）
        - 完整 history（每筆都展開）
        - 本次回報全文
        - 根據 status 給不同的判斷指令
        """

    def _call_llm(self, prompt: str) -> str:
        """
        POST localhost:8000/v1/chat/completions
        回傳 LLM 的原始回覆文字。
        timeout: 60s
        """

    def _parse_decision(self, llm_response: str) -> tuple[str, str]:
        """
        解析 LLM 回覆，找出決策類型和內容。
        LLM 必須在回覆中包含以下其中一個標記行：
          DECISION: approved
          DECISION: task:<任務描述>
          DECISION: redo:<原因>
          DECISION: supplement:<補充內容>
          DECISION: escalate:<原因>
        找不到標記 → 預設 escalate
        回傳：(decision_type, decision_content)
        """

    def _execute_decision(self, decision_type: str, content: str,
                          agent: str, thread_id: str):
        """
        根據決策呼叫對應腳本：
        - approved   → hq_task_flow.sh approve <agent> <thread_id>
        - task       → hq_task_flow.sh task <agent> <new_task_id> "<content>" high
        - redo       → hq_task_flow.sh redo <agent> <thread_id> "<content>"
        - supplement → hq_task_flow.sh supplement <agent> <thread_id> "<content>"
        - escalate   → 寫入 _agent/HQ_ESCALATE_<thread_id>.md
        """
```

---

### Class 3：`GatewayListener`

Redis 監聽主迴圈，整合 agents_supervisor 的 AgentThread 邏輯。

```python
class GatewayListener:
    PATTERNS = [
        'agent/*/task',
        'agent/*/consultation',
        'agent/*/report',
        'agent/*/supplement',
        'agent/*/redo',
        'agent/*/approval',
    ]

    AGENTS = {
        # 從 agents_supervisor.py 搬過來，保持一致
        'sophie': {'work_dir': '/Users/ilawusong/Documents/sysWawIot/wawOwner', ...},
        'ina':    {'work_dir': '/Users/ilawusong/Documents/sysWawIot/tg25-infra', ...},
        # ... 其餘 Agent
    }

    def on_task(self, agent: str, payload: dict):
        """
        觸發 codex exec（從 agents_supervisor.py 的 execute_task 搬過來）
        同時在 context store 追加 task_triggered 記錄。
        """

    def on_consultation(self, agent: str, payload: dict):
        """
        context store 已由 hq_task_flow.sh 初始化，
        這裡只追加 Gateway 收到諮詢的確認記錄。
        """

    def on_report(self, agent: str, payload: dict, inbox_file: Path):
        """
        呼叫 DecisionEngine.decide()
        """

    def run(self):
        """
        psubscribe 所有 PATTERNS，永久迴圈。
        收到訊息 → 解析 agent 和類型 → 分派到對應 on_* 方法。
        每個 on_* 都在獨立 thread 執行，不阻塞主監聽迴圈。
        """
```

---

## Prompt 設計（關鍵）

### 系統 prompt
```
你是 HQ，wawIoT 遊藝場管理系統的協調者。
你的任務是判斷 Agent 的回報是否達到要求，並決定下一步行動。
判斷必須嚴格、客觀，不接受模糊的口頭承諾，需要實際證明（log、截圖、API 回傳）。
```

### 依 status 給不同指令

**status = `consulting`**
```
目前處於諮詢階段。你詢問了 Agent 的可行性評估。
請判斷 Agent 的回覆是否：
1. 確認可行，且提供了足夠的實作步驟 → DECISION: task:<具體任務描述>
2. 表示不可行或有重大風險 → DECISION: escalate:<原因>
3. 回覆不夠完整，需要補充 → DECISION: supplement:<需要補充的問題>
```

**status = `pending`**
```
目前處於實作驗收階段。你要驗收 Agent 的實作成果。
請判斷 Agent 的回報是否：
1. 提供了實際證明（log/截圖/API/grep），且內容符合任務要求 → DECISION: approved
2. 有部分問題或缺少證明 → DECISION: redo:<具體指出哪裡不對>
3. 遇到超出能力範圍的問題 → DECISION: escalate:<原因>
```

---

## context store history 格式（完整定義）

每筆 history entry：
```json
{
  "round": 1,
  "from": "HQ | Gateway | <agent_name>",
  "action": "consult_issued | task_issued | supplement | report | llm_decision | task_triggered | approved | redo | escalate",
  "summary": "< 200字摘要>",
  "file": "/絕對路徑/到/完整回報.md（選填）",
  "decision": "approved | task | redo | escalate（選填，只有 llm_decision 時有）",
  "ts": "2026-06-10T00:00:00Z"
}
```

---

## 與 agents_supervisor.py 的關係

| 功能 | 現在在哪 | 搬到哪 |
|------|---------|-------|
| Agent task 觸發 codex exec | `AgentThread` | `GatewayListener.on_task()` |
| HQ 分身收 report | `HQReportThread` | `GatewayListener.on_report()` |
| context store tick | `HQReportThread._tick_context()` | `ContextStore.append_history()` |
| 子代理分析回報 | `HQReportThread._spawn_subagent()` | `DecisionEngine.decide()` |

**移轉策略**：
1. 先寫 `hq_gateway.py`，測試通過
2. 從 `agents_supervisor.py` 移除 `HQReportThread` 和 `AgentThread`
3. 用 launchd 同時跑 gateway（或整合進 supervisor 的 main()）

---

## 錯誤處理

| 情況 | 處理方式 |
|------|---------|
| Redis 斷線 | 5 秒後重試，永久迴圈 |
| LLM API 無回應（timeout 60s） | 寫入 escalate，通知 Joe |
| LLM 回覆沒有 DECISION 標記 | 預設 escalate，附上原始回覆 |
| inbox 檔案不存在 | log 警告，跳過，不 crash |
| hq_task_flow.sh 執行失敗 | log 錯誤，寫入 escalate |
