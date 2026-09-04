# CLI Agent 派工架構設計

> **建立日期**：2026-08-01
> **作者**：HQ
> **狀態**：✅ 設計基準 — 取代舊有 Pub/Sub + 常駐 Agent 設計
> **適用範圍**：所有 Codex CLI Agent（Sophie、Mina、Ina、Allie、Hubie、Fio、Coli）

---

## 一、核心認知

### 1.1 Codex CLI Agent 的本質

Codex CLI Agent **是對話驅動（conversation-driven），不是常駐 daemon**。

| 過去的錯誤假設 | 正確認知 |
|-------------|---------|
| Agent 需要常駐，隨時等待接收任務 | Agent 按需啟動，做完即結束 |
| Redis Pub/Sub 可以「驅動」Agent | Pub/Sub 是 fire-and-forget，沒人訂閱就消失 |
| HQ session 和 Agent session 可以互通 | 不同 CLI session 之間沒有隱性記憶共享 |
| Sophie 要記得「上次的對話」 | Sophie 的記憶來自**專案檔案**，不是 session |

### 1.2 「不常駐」正是優點

- Sophie 的 CLI session 是**一次性**：任務進來 → 讀取規範 → 做事 → 回報 → 結束
- 同一時間可有多個 Agent 各自執行任務，互不干擾
- 無需維護 Agent 的 session 狀態，系統更乾淨

### 1.3 HQ 桌面 session 同樣不常駐

- Joe 在 HQ session 下派工指令
- 派工完成後，HQ session 可以結束，不需要等待
- Agent 做完時，由 **Telegram Bot 通知 Joe**
- Joe 收到通知後，重新開啟 HQ session 繼續對話

---

## 二、完整流程圖

```
Joe (HQ 桌面 session)
  │
  │  發出「諮詢」任務（不得直接要求修改）
  ▼
Consultation CLI session（一次性）
  ├─ 讀取該 Agent 專案現況、規範與限制
  ├─ 回覆可行性、風險、影響檔案、替代方案與驗證計畫
  └─ 寫入 consultation report；status = "awaiting_approval"
              │
              │  Telegram 通知 Joe：有方案待審核
              │
              ▼
Joe（重新開啟 HQ 桌面 session）
  ├─ 審閱 Agent 方案與證據
  ├─ 補充需求／要求修訂，或明確核准 execution plan
  └─ HQ 發出「執行」任務（使用同一 thread_id，增加 execution_id）
              │
              ▼
Execution CLI session（新的一次性 CLI session）
  工作目錄：/Users/ilawusong/Documents/WaW/Owner
  啟動時 Prompt：
  ┌──────────────────────────────────────────┐
  │  你是 Sophie。                            │
  │  依序讀取：                               │
  │    1. AGENTS.md（專案規範）               │
  │    2. _agent/IDENTITY.md（身份規範）      │
  │    3. .taskbox/inbox/<task_id>.json（任務） │
  │  完成後寫入：                             │
  │    .taskbox/outbox/<task_id>_report.json   │
  │  並執行回報腳本通知 HQ。                  │
  └──────────────────────────────────────────┘
              │
              ▼
Sophie 執行任務
  ├─ 讀取上述規範與任務檔（任務自足，不依賴前一 session）
  ├─ 在 Owner 專案內完成指定工作
  ├─ 將結果寫入 .taskbox/outbox/<task_id>_report.json
  └─ 執行回報腳本
              │
              ▼
agent_report_to_hq.sh（回報腳本）
  ├─ 寫入 WHQ/.taskbox/inbox/<task_id>_report.json
  ├─ 更新 Redis：hq:thread:<task_id>:status = "done"
  └─ 呼叫 hq_tg_notifier.py 發送 Telegram 通知
              │
              ▼
Telegram Bot 通知 Joe
  ✅ 「Sophie 已完成任務 TASK_241
      結果：.taskbox/inbox/TASK_241_report.json
      重大決策：需要你審核 XXX 設計」
              │
              ▼
Joe 重開 HQ session，閱讀回報，繼續決策
```

---

## 三、設計原則

### 3.1 兩階段派工（強制）

所有可能修改程式、建立資料表、改變部署、調整 API 或跨專案協作的工作，**必須先諮詢，後執行**。HQ 不可僅憑自身假設直接下修改命令。

| 階段 | 任務類型 | Agent 可做的事 | 產出 | HQ 是否需要介入 |
|------|---------|---------------|------|----------------|
| A | `consultation` | 讀專案、分析需求、查現況、提出方案；不得修改業務程式或基礎設施 | `consultation_report.json` | ✅ 必須審閱 |
| B | `execution` | 只實作 HQ 已核准的方案；遇到範圍外決策即停止並回報 | `report.json`、測試 log、diff | ✅ 以證據驗收 |

**Consultation report 最少須包含：**

```json
{
  "thread_id": "CLI_DISPATCH_PHASE1_INFRA",
  "status": "awaiting_approval",
  "understanding": "Agent 對需求的重述",
  "current_state_evidence": ["實際讀取的檔案、指令輸出與 log"],
  "recommended_plan": ["分步驟方案"],
  "alternatives": ["替代方案及取捨"],
  "affected_files": ["預計修改的檔案"],
  "risks": ["風險與回滾方法"],
  "validation_plan": ["執行後的驗證證據"],
  "questions_for_hq": ["尚需 Joe/HQ 決策的事項"]
}
```

### 3.2 角色隔離與知識優勢

- 每個 Agent 只在其所屬專案的工作目錄中諮詢與執行，避免跨專案上下文污染。
- Agent 比 HQ 更熟悉當前專案的程式碼、相依性、歷史限制與測試方式；其 consultation report 是執行前的必要輸入。
- 跨專案方案須由各涉及 Agent 分別 consultation，再由 HQ 做整合決策；不得由單一 Agent 臆測其他專案的實作。

### 3.3 任務 Payload 必須自足

任務 JSON 需包含 Sophie 啟動後所需的全部上下文，不能依賴前一個 session 的隱性記憶：

```json
{
  "task_id": "TASK_241",
  "to_agent": "Sophie",
  "priority": "high",
  "description": "實作會員分潤 API",
  "acceptance_criteria": [
    "GET /api/v1/member/commission 返回正確分潤金額",
    "有對應 Feature Test",
    "Swagger 已更新"
  ],
  "context_files": [
    "_agent/IDENTITY.md",
    "_agent/DB_MANIFEST.md",
    "brains/knowledge/05_product_and_business_flows/commission_flow.md"
  ],
  "constraints": [
    "不修改現有 migration，新增獨立 migration 檔",
    "遵守 TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md"
  ],
  "report_format": ".taskbox/outbox/TASK_241_report.json",
  "published_at": "2026-08-01T13:15:00+08:00"
}
```

### 3.4 任務持久化原則

| 操作 | 舊方式（問題） | 新方式（正確） |
|-----|-------------|-------------|
| HQ outbox | `to_Sophie.json` 覆蓋 | `to_Sophie_TASK_241.json`（task_id 命名） |
| Agent inbox | 不寫 Agent 專案 | 寫入 `Owner/.taskbox/inbox/TASK_241.json` |
| 任務通道 | Redis Pub/Sub（消失） | Redis Streams（持久，可重試） |
| 任務狀態 | 無追蹤 | `hq:thread:<task_id>:status` 全程更新 |

### 3.5 冪等保護

- `task_id` 作為全局唯一鍵
- `hq_gateway.py` 執行前先檢查：若 `status != "pending"` 則跳過
- 避免重啟後重複執行同一任務

### 3.6 Agent 專案記憶的繼承方式

CLI Agent 每次啟動都是新 session，但可透過以下方式繼承**持久記憶**：

```
繼承的（✅）                  不繼承的（❌）
─────────────────────────   ─────────────────────────
Owner 專案的程式碼            前一個 session 的推理過程
_agent/IDENTITY.md           隱性約定（沒有寫下來的）
_agent/DB_MANIFEST.md        使用者偏好（沒有文件化）
Git 歷史與 commit message
任務 payload 中的上下文
AGENTS.md 的專案規範
```

**結論：關鍵決策必須文件化，隨任務帶入。**

---

## 四、工具選型：Skill-first，MCP 為後續選項

### 4.1 建議：先建立 HQ 派工 Skill

本系統的第一個介面應是 **Skill**，例如 `hq-task-orchestration`。它負責把 HQ 的行為固定成可審計流程：

- 強制先建立 `consultation`，禁止未核准即建立 `execution`
- 產生標準任務 payload、thread_id 與驗收條件
- 呼叫 `hq_task_flow.sh`／讀取回報／檢查 context store
- 指示 HQ 以 Telegram 通知與實際 log 作為驗收證據

Skill 適合承載「決策規則、提示詞、操作 SOP 與防呆」，且不需新增外部服務。

### 4.2 MCP 的定位：不是第一步，但可在流程穩定後補上

MCP 適合封裝明確的工具呼叫，例如 `create_consultation`、`approve_execution`、`get_thread_status`、`read_report`。它的價值在於參數驗證、權限控管與結構化 UI，而不是取代 dispatcher。

**現階段不建議先做 MCP**：派工的持久化、Streams consumer group、回報與 Telegram 尚未穩定，先完成底層協議與 Skill SOP；流程驗證後，再把穩定操作封裝成 MCP。

---

## 五、回報通知設計

### 5.1 Telegram 是 HQ 的非同步眼睛

- HQ session 不常駐，無法即時監聽 Redis 回報
- Telegram 是唯一跨 session 的人機通知管道
- 回報訊息需包含足夠資訊，讓 Joe 決定是否需要開 HQ session

### 5.2 回報訊息格式

```
🤖 [Sophie] 任務完成
─────────────────
任務 ID：TASK_241
描述：實作會員分潤 API
狀態：✅ 完成

摘要：
• 新增 GET /api/v1/member/commission
• Migration: 2026_08_01_add_commission_table
• Feature Test: 3 passed

📁 完整回報：WHQ/.taskbox/inbox/TASK_241_report.json
⚠️ 需要審核：分潤計算邏輯請確認（見回報第 3 節）
```

### 5.3 需要 HQ 介入的情況（回報中標示）

- `requires_review: true`：設計決策型問題，需 Joe 確認
- `blocked: true`：任務受阻，需 HQ 補充資訊或介入
- `sub_tasks: [...]`：需要派工給其他 Agent

---

## 六、常駐服務清單（最小化）

| 服務 | 程序 | 角色 | 必要性 |
|-----|------|------|-------|
| Redis | `redis-server` | 任務佇列 + context store | ✅ 必要 |
| redis_keeper | `redis_keeper.py` | 守護 Redis，掛了自動拉起 | ✅ 必要 |
| hq_gateway | `hq_gateway.py` | 消費任務，觸發 codex exec，處理回報 | ✅ 必要 |
| Telegram listener | `telegram_listener.py` | 接收 Telegram 指令（未來擴充） | 🔄 選用 |
| ~~message_hub_v2~~ | ~~`__main__.py`~~ | ~~設備事件路由（與派工架構分離）~~ | ⚠️ 獨立用途 |

**Agent（Sophie、Mina…）均不常駐。**

---

## 七、待實作項目

按優先順序：

1. **新增 consultation / approval / execution 三種任務類型**
   - `consultation` 完成後只能把狀態設為 `awaiting_approval`
   - 只有 HQ 明確 `approve` 後，才可產生關聯的 `execution` 任務
   - `execution` payload 必須帶入已核准 consultation report 的路徑與摘要

2. **修改 `hq_task_flow.sh`**
   - outbox 改為 `to_<Agent>_<task_id>.json`（解決覆蓋問題）
   - 新增：寫入 `<Agent 專案>/.taskbox/inbox/<task_id>.json`
   - 改用 `redis-cli XADD` 取代 `PUBLISH`（Streams 持久化）

3. **修改 `hq_gateway.py`**
   - 改用 `XREAD` 消費 Redis Streams（支援重試）
   - 加入冪等鍵檢查（跳過 `status != pending` 的任務）
   - `codex exec` 的 prompt 帶入任務檔路徑

4. **修改 `agent_report_to_hq.sh`**（或新建）
   - 回報後更新 `hq:thread:<task_id>:status = "done"`
   - 呼叫 Telegram 通知

5. **更新各 Agent 的 `AGENTS.md`**
   - 加一行：啟動後先讀 `.taskbox/inbox/` 中最新任務

---

## 八、相關文件

| 文件 | 說明 |
|-----|------|
| `MESSAGE_HUB_PROTOCOL.md` | 舊版 Pub/Sub 架構（現行已有問題，本文取代） |
| `CODEX_EXEC_GUIDE.md` | `codex exec` 使用方式與軍令 |
| `AUTOFLOW_CONTEXT_STORE_DESIGN.md` | Redis context store 設計 |
| `AGENT_STARTUP_PROTOCOL.md` | Agent 啟動安全協議（禁止遞迴掃描等） |

---

## 🔗 文件神經連結

- **上游**：`01_agent_governance/MESSAGE_HUB_PROTOCOL.md`（取代）
- **下游**：`hq_task_flow.sh`、`hq_gateway.py`、各 Agent `AGENTS.md`
- **觸發更新**：修改任何派工相關腳本時，同步更新本文件的「待實作項目」狀態
