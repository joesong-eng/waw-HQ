# Skill: message_hub_operations

## 描述

HQ 透過 Message Hub（v3.0 Redis Pub/Sub 架構）與所有 Agent 通訊的完整操作技能。
涵蓋：發任務、補充、諮詢、重做、確認通過、查看回報、服務管理。

**適用對象**：HQ（`codex exec` CLI 模式）
**不適用**：Qoder（IDE 助手不可執行任何發任務腳本）

---

## 系統架構概覽

```
Joe
 │
 ▼
hq_task_flow.sh          ← HQ 唯一發令入口
 ├─→ .taskbox/outbox/to_<Agent>.json    （備份存檔）
 └─→ redis-cli PUBLISH agent/<agent>/task <payload>
           │
           ▼
   hq_gateway.py
   （com.hq.agents.supervisor，launchd 常駐）
   ├─ 訂閱 agent/<name>/*（任務、諮詢、回報、補充）
   ├─ 存 _agent/REDIS_<ts>_<task_id>.json
   ├─ 自動觸發 codex exec 執行任務
   └─ 收到 report → DecisionEngine 自動決策
           │
           ▼
   Agent 執行完成
   └─→ agent_report_to_hq_v2.sh
       └─→ .taskbox/inbox/<ts>_<agent>.json
```

---

## 前置確認（每次操作前）

```bash
# 1. Redis 在線？
redis-cli ping                          # 應回 PONG

# 2. agents_supervisor 在跑？
launchctl list | grep com.hq.agents.supervisor   # 應有 PID

# 3. 當前系統狀態
./scripts/hq_status.sh
```

若 Redis 未啟動：
```bash
redis-server --daemonize yes
```

若 supervisor 未啟動：
```bash
launchctl load ~/Library/LaunchAgents/com.hq.agents.supervisor.plist
```

---

## 操作一：發正式任務

### 指令
```bash
./scripts/hq_task_flow.sh task <agent> <task_id> "<描述>" [priority]
```

### 參數說明
| 參數 | 說明 | 範例 |
|------|------|------|
| `agent` | Agent 名稱（小寫） | `sophie` |
| `task_id` | 任務 ID（建議格式：`TASK_YYYYMMDD_XXX`） | `TASK_20260609_001` |
| `描述` | 任務說明（加引號） | `"實作分潤 API"` |
| `priority` | 優先級（選填） | `high` / `normal`（預設）/ `low` |

### 範例
```bash
# 發任務給 Sophie
./scripts/hq_task_flow.sh task sophie TASK_20260609_001 "實作 /api/v1/profit-sharing 端點" high

# 發任務給 Ina
./scripts/hq_task_flow.sh task ina TASK_20260609_002 "執行 devices 表補欄位 migration" high

# 發任務給 Coli
./scripts/hq_task_flow.sh task coli TASK_20260609_003 "更新 OTA 邏輯至 v1.0.27" normal
```

### 發出後發生的事
1. `.taskbox/outbox/to_<Agent>.json` 被寫入（備份）
2. `redis-cli PUBLISH agent/<agent>/task <payload>` 推送
3. `hq_gateway` 收到 → 存 `_agent/REDIS_<ts>_<task_id>.json`
4. 自動觸發 `codex exec` 在對應 Agent 專案執行任務
5. Redis context store 初始化（`hq:thread:<task_id>:*`）

---

## 操作二：發諮詢

任務正式執行前，先詢問 Agent 方案、可行性。

```bash
./scripts/hq_task_flow.sh consult <agent> <consult_id> "<問題描述>"
```

### 範例
```bash
./scripts/hq_task_flow.sh consult ina CONS_20260609_001 "請評估 devices 表加欄位的 migration 風險與步驟"
```

---

## 操作三：補充資訊

已發出任務或諮詢後，補充額外說明。

```bash
./scripts/hq_task_flow.sh supplement <agent> <原始id> "<補充內容>"
```

### 範例
```bash
./scripts/hq_task_flow.sh supplement ina CONS_20260609_001 "欄位清單：chip_id, pulse_to_token, pulse_to_display, firmware_version"
```

---

## 操作四：要求重做

Agent 回報結果不符合要求時。

```bash
./scripts/hq_task_flow.sh redo <agent> <task_id> "<重做原因>"
```

### 範例
```bash
./scripts/hq_task_flow.sh redo sophie TASK_20260609_001 "回傳格式不符，profit_ratio 應為整數非浮點數"
```

---

## 操作五：確認通過

審核 Agent 回報後，正式結案。

```bash
./scripts/hq_task_flow.sh approve <agent> <task_id>
```

### 範例
```bash
./scripts/hq_task_flow.sh approve sophie TASK_20260609_001
```

---

## 操作六：查看 Agent 回報

### 列出最新回報
```bash
ls -lht .taskbox/inbox/ | head -10
```

### 讀取特定回報
```bash
cat .taskbox/inbox/<檔名>.json | python3 -m json.tool
```

### 查看 Redis context store 狀態
```bash
TASK_ID="TASK_20260609_001"
redis-cli GET hq:thread:${TASK_ID}:status    # pending / resolved / blocked / escalated
redis-cli GET hq:thread:${TASK_ID}:round     # 第幾輪
redis-cli LRANGE hq:thread:${TASK_ID}:history 0 -1  # 完整歷史
```

### 收件匣摘要
```bash
./scripts/hq_inbox_summary.sh
```

---

## 操作七：Agent 回報給 HQ（Agent 端執行）

在各 Agent 專案目錄執行：

```bash
bash ../HQ/scripts/agent_report_to_hq_v2.sh <agent> <report_file> ../HQ
```

### 範例
```bash
# Sophie 在 wawOwner/ 目錄
bash ../HQ/scripts/agent_report_to_hq_v2.sh sophie _agent/LATEST_REPORT.md ../HQ

# Ina 在 tg25-infra/ 目錄
bash ../HQ/scripts/agent_report_to_hq_v2.sh ina _agent/LATEST_REPORT.md ../HQ
```

回報機制：
1. `redis-cli PUBLISH agent/<agent>/report <payload>`
2. `hq_gateway.py` 收到後自動存入 `HQ/.taskbox/inbox/` 並觸發 DecisionEngine

---

## Agent 名稱對照表

| 參數（小寫） | outbox 檔案 | 專案目錄 | 職責 |
|------------|------------|---------|------|
| `sophie` | `to_Sophie.json` | `wawOwner/` | Owner 後台、設備管理 |
| `ina` | `to_Ina.json` | `tg25-infra/` | DB、MQTT、Redis、基礎設施 |
| `mina` | `to_Mina.json` | `Member/` | 玩家前端、支付系統 |
| `allie` | `to_Allie.json` | `Alliance/` | 供應商、代理商 |
| `hubie` | `to_Hubie.json` | `iHub/` | Android APK |
| `coli` | `to_Coli.json` | `IOTwawS3/` | 遊戲機韌體（`device/+/`） |
| `fio` | `to_Fio.json` | `IOTkiosk_v0/` | 兌幣機韌體（`kiosk/+/`） |

---

## Payload JSON 格式

### 任務（HQ → Agent）
```json
{
  "type": "task",
  "task_id": "TASK_20260609_001",
  "to_agent": "Sophie",
  "priority": "high",
  "description": "任務描述",
  "published_at": "2026-06-09T00:00:00Z",
  "deadline": "2026-06-10 EOD"
}
```

### 回報（Agent → HQ）
```json
{
  "from_agent": "sophie",
  "timestamp": "2026-06-09T01:23:45Z",
  "report_file": "_agent/LATEST_REPORT.md",
  "report": "完整 Markdown 回報內容"
}
```

---

## 目錄結構

```
HQ/_agent/
├── outbox/
│   └── to_<Agent>.json          # 備份存檔（非觸發信號）
├── inbox/
│   └── YYYYMMDD_HHMMSS_<agent>.json   # Agent 回報
├── REDIS_<ts>_<agent>.json      # Supervisor 接收 Redis 後存檔
└── task_flow.log                # 操作日誌
```

---

## ❌ 絕對禁止

| 禁止動作 | 原因 |
|---------|------|
| 使用已刪除的 `hq_send_task_via_hub.sh` | 已刪除，且只寫檔案不觸發 Redis |
| 使用已刪除的 `hq_publish_and_trigger.sh` | 已刪除，且繞過 Redis |
| 手動 `codex exec` | 破壞架構一致性 |
| Qoder 執行任何發任務腳本 | Qoder 不是 HQ，無發令權 |

---

## 故障排除

### Agent 收不到任務
```bash
# 1. 確認 Redis 收到了嗎？
redis-cli SUBSCRIBE agent/sophie/task   # 手動監聽看有沒有訊息

# 2. Supervisor 有在跑嗎？
launchctl list | grep com.hq.agents.supervisor

# 3. 看 supervisor 日誌
tail -50 /Users/ilawusong/Documents/sysWawIot/HQ/logs/hq_gateway.out.log
```

### Redis 沒回應
```bash
redis-server --daemonize yes
redis-cli ping   # 確認 PONG
```

### 想清除某 Agent 的 outbox
```bash
./scripts/hq_clear_tasks.sh <agent>
```

---

## 相關文件

- **權威協定**：`brains/knowledge/01_agent_governance/MESSAGE_HUB_PROTOCOL.md`
- **禁止行為共識**：`brains/knowledge/01_agent_governance/AUTOFLOW_CONTEXT_STORE_DESIGN.md`
- **HQ Autoflow 完整文件**：`brains/knowledge/01_agent_governance/HQ_AUTOFLOW.md`
- **初始化 thread**：`skills/hq_ops/init_thread.md`

---

*制定者：HQ | 版本：1.0 | 建立日期：2026-06-09*
