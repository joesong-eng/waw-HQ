# Requirements: HQ Gateway

> **建立日期**：2026-06-10
> **狀態**：✅ 已確認
> **背景**：取代 agents_supervisor 的 HQReportThread，成為統一的任務流程決策中心

---

## 問題陳述

現行架構有兩個缺口：

1. **諮詢（consult）回覆後，沒有自動決策機制**
   HQ 發出 consult 後，Agent 回覆可行性，但沒有任何程序自動判斷「夠不夠好、要不要發正式任務」，全靠 Joe 人工看。

2. **context store 只記錄 task 階段，consult 往來沒有記錄**
   分身在分析回報時，看不到完整的對話歷史，判斷缺乏背景。

---

## 需求清單

### R1：統一監聽所有 Agent 頻道

Gateway 常駐，訂閱 Redis：
- `agent/*/report` — Agent 回報（諮詢回覆 + 實作回報）
- `agent/*/task` — HQ 發出的任務（用於同步 context store）
- `agent/*/consultation` — HQ 發出的諮詢（用於同步 context store）

### R2：根據 context store 判斷當前階段

收到回報時，先讀 `hq:thread:<id>:status`：

| status | 代表 | Gateway 動作 |
|--------|------|-------------|
| `consulting` | 諮詢階段，等 Agent 回覆可行性 | 呼叫 LLM 判斷是否推進到 task |
| `pending` | 已發正式任務，等實作完成 | 呼叫 LLM 判斷是否通過驗收 |
| `redo_requested` | 要求重做，等 Agent 再次回報 | 呼叫 LLM 重新判斷 |

### R3：呼叫 LLM 時帶完整上下文

Prompt 組成：
1. 系統角色說明（HQ 協調者）
2. 任務背景（task_id、agent、原始描述）
3. 完整 history（從 Redis 讀出，包含所有輪次）
4. 本次回報全文（從 inbox 檔案讀取，不截斷）
5. 判斷指令（根據當前 status 給不同指令）

LLM endpoint：`http://localhost:8000/v1/chat/completions`
Model：`ag/claude-sonnet-4-6`（從 config 讀取，可覆寫）

### R4：LLM 決策結果對應動作

| LLM 回傳 | Gateway 動作 |
|---------|-------------|
| `approved` | 呼叫 `hq_task_flow.sh approve` |
| `task:<描述>` | 呼叫 `hq_task_flow.sh task`，發正式任務 |
| `redo:<原因>` | 呼叫 `hq_task_flow.sh redo` |
| `supplement:<補充內容>` | 呼叫 `hq_task_flow.sh supplement` |
| `escalate:<原因>` | 寫入 `_agent/HQ_ESCALATE_<task_id>.md`，等 Joe 人工介入 |

### R5：所有往來都寫進 context store

每一個動作（HQ 發出 / Agent 回報 / LLM 決策）都要追加到：
`hq:thread:<id>:history`

格式：
```json
{
  "round": 3,
  "from": "Gateway",
  "action": "llm_decision",
  "decision": "task",
  "summary": "LLM 判斷諮詢回覆可行，發出正式任務",
  "ts": "2026-06-10T00:00:00Z"
}
```

history 同時記錄完整回報的**檔案路徑**，供需要細節時讀取。

### R6：agents_supervisor 的任務觸發邏輯整合進 Gateway

Gateway 同時負責原本 supervisor 做的事：
收到 `agent/*/task` → 觸發 `codex exec` 在對應 Agent 專案執行

`agents_supervisor.py` 的 `AgentThread` 邏輯直接搬入 Gateway。

### R7：Gateway 本身不取代 agents_supervisor 進程管理

agents_supervisor 的 launchd 設定（`com.hq.agents.supervisor`）不動，
只是把 Gateway 的程式碼整合進去，或另起一個進程由 launchd 管理。

---

## 不在範圍內

- Gateway 不直接修改任何 Agent 的業務程式碼
- Gateway 不存取生產環境資料庫
- Gateway 不取代 Joe 對「架構變更」的最終決策權（escalate 就是邊界）
