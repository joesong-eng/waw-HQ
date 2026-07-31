# 自動化工具設計共識（2026-06-08）

> 這份文件記錄 Joe 與 HQ 經過完整一個工作天討論後達成的共識。
> 下一個 Session 啟動前必須讀這份文件，否則不要開口。
> **最後更新**：2026-06-09（確認為現行架構）

---

## 一、HQ 發任務給 Agent 的唯一正確流程

```bash
./scripts/hq_task_flow.sh task <agent> <task_id> "<描述>" [priority]
```

| 步驟 | 事件 |
|------|------|
| 1 | `hq_task_flow.sh` 寫 outbox + `redis-cli PUBLISH agent/<agent>/task` |
| 2 | `agents_supervisor.py`（`com.hq.agents.supervisor` launchd 常駐）接收，存 `REDIS_*.json` |
| 3 | 自動觸發 `codex exec` 執行任務 |
| 4 | Agent 用 `agent_report_to_hq_v2.sh` 回報 HQ |

**禁止：**
- ❌ `hq_send_task_via_hub.sh` — 只寫檔案，不觸發 Redis
- ❌ `hq_publish_and_trigger.sh` — 繞過 Redis
- ❌ 手動呼叫 `codex exec`

**Agent 回報（正確）**：
```bash
bash ../HQ/scripts/agent_report_to_hq_v2.sh <agent> _agent/LATEST_REPORT.md ../HQ
```

---

## 二、四個平行世界的架構

```
Joe
 │
 ▼
HQ（我，手動 Session）
 │  redis-cli PUBLISH agent/ina/task
 ▼
Message Hub（localhost:8899）
 │
 ▼
Ina 分身（launchd PID 常駐，agent_redis_listener.py）
 │  自動 codex exec
 ▼
執行任務 → agent_report_to_hq_v2.sh → HQ/_agent/inbox/
```

- **我（HQ Session）** = 發令 + 被動讀結果，不監控
- **Ina 分身** = 自動執行，無人值守
- **共同記憶** = 檔案系統 + Redis

---

## 三、分身 vs 子代理

| | 分身 | 子代理（Sub-agent） |
|--|------|-------------------|
| 身份 | 同一個 Agent，不同 Session | 父 Agent 臨時生出的執行者 |
| 觸發 | launchd + Redis 被動等待 | 父 Agent 主動派發 |
| 回報對象 | HQ | 父 Agent |
| 生命週期 | 常駐 | 任務完成即消失 |
| 目前狀態 | ✅ 已實現 | ❌ 尚未實現 |

---

## 四、目前缺口（待實現）

### 1. HQ 缺分身
- Ina 有 `agent_redis_listener.py`（launchd 常駐）
- HQ 缺對應的 `hq_redis_listener.py`
- 缺了這個，HQ 收到 Ina 回報後無法自動反應，需要 Joe 手動來問

### 2. 缺 context store（跨 Session 記憶池）
- 每個 codex exec Session 天生失憶
- 多輪對話（問題1→解決→問題2→解決）無法連貫
- 解決方案：Redis context store

```
Redis key 設計：
hq:thread:<task_id>:status   → pending / awaiting_reply / resolved
hq:thread:<task_id>:round    → 第幾輪
hq:thread:<task_id>:history  → JSON list，完整對話紀錄
hq:thread:<task_id>:requires_review → true/false，是否需要人工審核（設計型諮詢）
```

- 每個分身啟動時先讀這些 key，結束時更新
- 這樣不管開幾個 Session，都知道對話在第幾輪

### 3. agent_redis_listener.py prompt 已修正
- 已加入角色文件強制載入（AI_CONTEXT.md、GEMINI.md、DB_MANIFEST.md）
- 分身啟動後會先鎖定角色再執行任務
- **注意**：修改後需重啟 launchd 才生效

---

## 五、為什麼不用現有框架

| 框架 | 問題 |
|------|------|
| LangGraph | 綁死 LangChain，為同 process 設計 |
| AutoGen | async 框架，需換底層 |
| CrewAI | 角色模型不同 |
| Swarm | 無 context store |

**結論**：這些框架都是為同一 process 內的 Agent 設計，不支援跨 Session、跨 process、launchd 常駐的架構。自己補 context store 那一塊即可，不需要換框架。

---

## 六、你的架構跟別人的本質差異

別人：同一個 AI 用 prompt 切換角色（戴帽子貼鬍子）
你的：真正獨立的 Workspace + Process，透過 Redis + Message Hub 穿線

| | 戴帽子做法 | Joe 的做法 |
|--|-----------|-----------|
| 隔離性 | 無 | 真實隔離 |
| 可靠性 | 容易角色混亂 | 角色鎖定 |
| 平行執行 | 不行 | 真正並行 |
| context 問題 | 不存在 | 真實存在，需要解決 |

---

## 七、下一步（已確認待做）

1. 實作 `hq_redis_listener.py`（HQ 分身機制）
2. 實作 Redis context store（跨 Session 記憶池）
3. 修改 `hq_redis_listener.py` 和 `agent_redis_listener.py` 支援 context store
4. 重啟 Ina launchd 載入新 prompt

---

**記錄時間**：2026-06-08  
**記錄者**：HQ  
**狀態**：共識已達成，待實作

---

## 八、四個平行世界（最終定案）

每個 Agent 交辦時有兩個 Session：**你**（手動）和**你的分身**（自動）。

```
Joe
 │
 ▼
HQ 你（手動 Session）         HQ 分身（hq_redis_listener，待實作）
 │  發令、讀結果               │  自動收 Ina 回報、自動反應
 │                             │
 └──────── Redis / Message Hub ────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
Ina 你（手動 Session）     Ina 分身（launchd PID 常駐）
  Joe @Ina 喚醒               agent_redis_listener.py
  即時對話                     自動執行、自動回報
```

**四個世界：**

| # | 世界 | 觸發方式 | 狀態 |
|---|------|---------|------|
| 1 | HQ 你 | Joe 手動喚醒 | ✅ 現在這個 |
| 2 | HQ 分身 | 收到 Agent 回報自動觸發 | ❌ 待實作 |
| 3 | Ina 你 | Joe 手動喚醒 | ✅ 已有 |
| 4 | Ina 分身 | Redis launchd 自動觸發 | ✅ 已有 |

**核心原則**：每個 Agent 都是「你 + 分身」一對，共享同一個文件記憶池。HQ 也不例外。

---

## 九、Context Store 設計規格

### 問題
每個 codex exec Session 天生失憶。多輪對話（HQ↔Ina 來回問答）無法連貫，分身不知道上一輪發生了什麼。

### 解決方案：Redis Context Store

每一個任務執行緒，在 Redis 維護一組 key：

```
hq:thread:<task_id>:status   → pending / awaiting_reply / resolved
hq:thread:<task_id>:round    → 第幾輪（integer）
hq:thread:<task_id>:history  → JSON list，完整對話紀錄
hq:thread:<task_id>:issue    → 當前待解決的問題描述
hq:thread:<task_id>:requires_review → true/false，是否需要人工審核（設計型諮詢）
```

### 每個分身的 SOP

```
分身啟動
  │
  ▼
1. 讀 hq:thread:<task_id>:* → 知道目前第幾輪、問題是什麼
  │
  ▼
2. 執行當前任務
  │
  ▼
3. 把結果寫回 Redis（更新 status、round、history）
  │
  ▼
4. 發下一個訊息（給 Ina 或給 HQ）
  │
  ▼
5. 關閉 Session
```

### 多輪閉環範例

```
round 1: HQ 發諮詢給 Ina
          → redis: status=awaiting_reply, round=1, issue=""

round 2: Ina 分身回「問題1待解決」
          → redis: status=awaiting_reply, round=2, issue="問題1"

round 3: HQ 分身讀到 round=2, issue="問題1"
          → 產出解決方法，發回 Ina
          → redis: status=awaiting_reply, round=3

round 4: Ina 分身讀到 round=3
          → 執行解決方法，回「問題2待解決」
          → redis: round=4, issue="問題2"

...直到 status=resolved
```

### 需修改的檔案

| 檔案 | 修改內容 |
|------|---------|
| `tg25-infra/scripts/agent_redis_listener.py` | 啟動時讀 context store，結束時寫回 |
| `HQ/scripts/hq_redis_listener.py` | 待實作，同上 |
| `HQ/scripts/hq_task_flow.sh` | 發任務時初始化 context store key |

---

**記錄時間**：2026-06-08 補充  
**狀態**：設計完成，待實作

---

## 十、HQ 等待機制（取代 HQ 分身的更優方案）

### 核心想法
HQ 發任務後，**同一個 Session 繼續等待 Ina 回報**，不需要：
- 另開 HQ 分身（launchd）
- Joe 再次手動觸發
- context store 跨 Session 傳遞

同一個 Session 天然有上下文，閉環自動完成。

### 流程

```
HQ Session（同一個，不關閉）
  │
  ▼
1. 發任務給 Ina（hq_task_flow.sh）
  │
  ▼
2. 訂閱等待 Ina 回報
   redis-cli SUBSCRIBE agent/ina/report
  │
  ▼
3. 收到回報 → 讀取分析
  │
  ├── 問題解決 → 發下一個任務 → 回到步驟 2
  │
  └── 全部完成 → status=resolved → 結束 Session，通知 Joe
```

### 實作方式

```bash
# hq_task_flow.sh 加入 --wait 參數
./scripts/hq_task_flow.sh task ina "TASK_XXX" "描述" normal --wait

# --wait 觸發後：
# 1. 發任務（redis PUBLISH）
# 2. 訂閱等待（redis SUBSCRIBE agent/ina/report）
# 3. 收到回報自動處理
# 4. 需要反應則再發，繼續等
# 5. resolved 才結束
```

### 對四個平行世界的影響

原本設計：
- HQ 分身需要獨立 launchd 常駐 ❌ 複雜

新設計：
- HQ 你（同一 Session）發任務後等待 ✅ 簡單
- HQ 分身不需要實作了

| # | 世界 | 狀態 |
|---|------|------|
| 1 | HQ 你（發令+等待） | ✅ 實作後完整 |
| 2 | HQ 分身 | ✅ 不需要了 |
| 3 | Ina 你 | ✅ 已有 |
| 4 | Ina 分身 | ✅ 已有 |

### context store 影響
同一個 Session 等待，上下文天然連貫。
Redis context store 仍保留作為**持久化備份**，Session 意外中斷時可以恢復。

---

**記錄時間**：2026-06-08 補充
**狀態**：設計完成，待實作
**優先級**：高（這是最簡單優雅的方案）

---

## 十一、最終定案（2026-06-08）

### 四個平行世界，永久定案

| # | 世界 | 角色 | 狀態 |
|---|------|------|------|
| 1 | HQ 你 | 發令、跟 Joe 對話、隨時可用 | ✅ 現在這個 |
| 2 | HQ 分身 | launchd 常駐、收 Ina 回報、派子代理處理 | ❌ 待實作 |
| 3 | Ina 你 | Joe 手動喚醒、即時對話 | ✅ 已有 |
| 4 | Ina 分身 | launchd 常駐、自動執行任務、自動回報 | ✅ 已有 |

### 分工

```
Joe
 │
 ▼
HQ 你（永遠空著，隨時對話）
 │ 發任務
 ▼
HQ 分身（launchd 常駐，輕量監聽）
 │ 收到 Ina 回報
 ▼
子代理（臨時 Session，分析決策回覆）
 │ 發回給 Ina
 ▼
Ina 分身（launchd 常駐，執行任務）
 │ 完成回報
 ▼
HQ 分身（收到，再派子代理...直到 resolved）
```

### 為什麼不能少於四個

- HQ 你不能等待 → Joe 會被卡住
- 子代理不能取代 HQ 分身 → HQ 你還是要等子代理
- HQ 分身是唯一讓 Joe 永遠自由的方案

### 待實作清單

1. `HQ/scripts/hq_redis_listener.py` — HQ 分身監聽器
2. `~/Library/LaunchAgents/com.hq.agent.hq.plist` — HQ 分身 launchd
3. `HQ/scripts/hq_task_flow.sh` — 發任務時初始化 context store
4. context store 讀寫整合進 HQ 分身和 Ina 分身

---

**最終定案時間**：2026-06-08  
**狀態**：設計完成，待實作

---

## 十二、架構演進記錄（2026-06-09）

> 本章修正十一章「最終定案」中已過時的內容，記錄實際落地後的架構變化。

### 架構變更：從各自 plist → supervisor 統一管理

**原設計（十一章）**：每個 Agent 分身 + HQ 分身各自有獨立 launchd plist 常駐。

**實際落地**：廢棄獨立 plist 方案，改由 `com.hq.agents.supervisor`（`agents_supervisor.py`）單一進程統一管理所有 Agent 的 Redis 訂閱與 codex 觸發。

#### 變更原因

1. **TCC 權限問題**：`com.hq.all_agents.plist` 透過 `/bin/bash` 呼叫 shell，被 macOS 沙盒擋住（狀態碼 126，`Operation not permitted`）。
2. **架構簡化**：單一 Python supervisor 直接訂閱所有頻道，比多個獨立 plist 更容易維護，且 Python 進程有完整磁碟存取授權。

#### 目前實際運行的 launchd 服務

| Label | 程式 | KeepAlive | 職責 |
|-------|------|-----------|------|
| `com.hq.agents.supervisor` | `scripts/agents_supervisor.py` | ✅ | **所有 Agent**（含 HQ）Redis 監聽與 codex 觸發 |
| `com.hq.messagehub.v2` | Message Hub v2 | ✅ | HTTP API 任務分發 |
| `com.hq.redis.keeper` | Redis keeper | ✅ | Redis 健康維護 |
| ~~`com.hq.agent.hq.plist`~~ | — | ❌ | **不需要**，已由 supervisor 接管 |
| ~~`com.hq.all_agents.plist`~~ | — | ❌ | **已廢棄**，TCC 126 問題 |

#### 修正後的四個平行世界

| # | 世界 | 觸發方式 | 狀態 |
|---|------|---------|------|
| 1 | HQ 你 | Joe 手動喚醒 | ✅ 現在這個 |
| 2 | HQ 分身 | `agents_supervisor` 收到 `agent/*/report` 自動觸發 | 🟡 supervisor 已整合 hq，但 report 訂閱待補 |
| 3 | Ina 你 | Joe 手動喚醒 | ✅ 已有 |
| 4 | Ina 分身 | `agents_supervisor` 收到 `agent/ina/task` 自動觸發 | ✅ 已有 |

### 已完成 vs 仍待實作（2026-06-09 更新）

| 項目 | 原狀態 | 現狀態 |
|------|--------|--------|
| `hq_redis_listener.py` | ❌ 待實作 | ✅ 已建立（但尚未整合進 supervisor 的 report 訂閱） |
| `com.hq.agent.hq.plist` | ❌ 待實作 | ✅ 不需要（supervisor 統一管理） |
| `agents_supervisor.py` 訂閱 `agent/*/report` | — | ❌ 待補：收到回報後派子代理分析 |
| `hq_task_flow.sh` 初始化 context store | ❌ 待實作 | ❌ 仍待實作 |
| context store 讀寫整合進 Ina 分身 | ❌ 待實作 | ❌ 仍待實作 |

### 下一步待實作清單（修正版）

1. **`agents_supervisor.py` 補充 report 訂閱**：在 hq 的訂閱頻道加入 `agent/*/report`，收到後派子代理執行 `skills/hq_ops/analyse_agent_report.md`
2. **`hq_task_flow.sh` 初始化 context store**：發任務時寫入 `hq:thread:<task_id>:*` Redis key
3. **context store 讀寫整合**：HQ 分身和 Ina 分身啟動時讀、結束時寫

---

**記錄時間**：2026-06-09  
**記錄者**：HQ  
**狀態**：架構已落地，三項功能待實作

---

## 十三、架構定案（2026-06-10）

> 本章為最終現行架構，取代十一、十二章中所有「待實作」項目。

### 現行運行架構

```
Joe
 │
 ▼
HQ 你（手動 Session，隨時對話）
 │  hq_task_flow.sh consult/task
 ▼
Redis Pub/Sub
 │
 ▼
hq_gateway.py（com.hq.agents.supervisor，launchd 常駐）
 ├─ GatewayListener：訂閱 agent/*/task|consultation|report|supplement|redo|approval
 ├─ ContextStore：讀寫 hq:thread:<id>:* (Redis)
 └─ DecisionEngine：LLM 自動判斷 → hq_task_flow.sh 執行下一步
           │
           ▼
   Agent 分身（codex exec，由 gateway 觸發）
   └─→ agent_report_to_hq_v2.sh → Redis PUBLISH agent/<agent>/report
           │
           ▼
   hq_gateway.py 收到 report → DecisionEngine 自動決策
```

### 已完成 vs 原待實作

| 原待實作項目 | 現狀態 |
|------------|--------|
| `hq_redis_listener.py` | ✅ 不需要，`hq_gateway.py` 統一接管 |
| HQ 分身 launchd | ✅ 由 `com.hq.agents.supervisor` 統一管理 |
| context store 讀寫整合 | ✅ `ContextStore` class 已實作 |
| `hq_task_flow.sh` 初始化 context store | ✅ 已實作（`init_context_store()`） |
| Agent 回報自動決策 | ✅ `DecisionEngine.decide()` + LLM API |
| `analyse_agent_report.md` skill | ✅ 已由 `DecisionEngine` 取代，原 skill 標記 deprecated |

### LLM 端點
- URL：`http://localhost:8000/v1/chat/completions`（9router，本地常駐）
- Model：`ag/claude-sonnet-4-6`（可透過 `GATEWAY_MODEL` 環境變數覆蓋）
- API Key：透過 `GATEWAY_API_KEY` 環境變數注入

---

**記錄時間**：2026-06-10
**狀態**：✅ 架構完整落地
