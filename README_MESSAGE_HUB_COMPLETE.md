# HQ Message Hub 完整使用指南

**更新日期**: 2026-06-09
**狀態**: ✅ v3.0 Redis Pub/Sub 架構
**權威協定文件**: `brains/knowledge/01_agent_governance/MESSAGE_HUB_PROTOCOL.md`

---

## ⚠️ 版本說明

本文件已於 2026-06-09 更新為 **v3.0**（Redis Pub/Sub 架構）。
舊版 v2.0（HTTP-only + 檔案系統 fallback）已廢棄，相關腳本禁止使用。

---

## 系統架構總覽

```
Joe
 │
 │ ./scripts/hq_task_flow.sh task <agent> <task_id> "<描述>" [priority]
 ▼
hq_task_flow.sh
 ├─→ 寫入 _agent/outbox/to_<Agent>.json（備份存檔）
 └─→ redis-cli PUBLISH agent/<agent>/task <payload>
           │
           ▼
   agents_supervisor.py（com.hq.agents.supervisor，launchd 常駐）
   ├─ 訂閱所有 agent/<name>/* 頻道
   ├─ 接收 → 存 _agent/REDIS_<timestamp>_<agent>.json
   └─ 自動觸發 codex exec 執行任務
           │
           ▼
   Agent 執行完成
   └─→ agent_report_to_hq_v2.sh → HQ/_agent/inbox/
```

---

## 🚨 HQ 發任務：唯一正確指令

```bash
./scripts/hq_task_flow.sh task <agent> <task_id> "<描述>" [priority]
```

### 範例

```bash
# 發任務給 Sophie
./scripts/hq_task_flow.sh task sophie TASK_001 "實作分潤 API" high

# 發任務給 Ina
./scripts/hq_task_flow.sh task ina TASK_002 "優化 Redis 連線池" normal

# 發任務給 Coli
./scripts/hq_task_flow.sh task coli TASK_003 "更新韌體 OTA 邏輯" low
```

### 支援的訊息類型

```bash
./scripts/hq_task_flow.sh consult <agent> <id> "<問題>"      # 諮詢
./scripts/hq_task_flow.sh supplement <agent> <id> "<補充>"   # 補充資訊
./scripts/hq_task_flow.sh redo <agent> <task_id> "<原因>"    # 要求重做
./scripts/hq_task_flow.sh approve <agent> <task_id>          # 確認通過
```

### ❌ 禁止使用（已廢棄）

| 禁止指令 | 原因 |
|---------|------|
| `hq_send_task_via_hub.sh` | 只寫檔案，**不觸發 Redis**，Agent 收不到 |
| `hq_publish_and_trigger.sh` | 繞過 Redis，直接 codex exec |
| 手動 `codex exec` | 非架構內觸發 |

---

## Agent 端操作（接收與回報）

### 回報任務完成

在各 Agent 專案目錄執行：

```bash
bash ../HQ/scripts/agent_report_to_hq_v2.sh <agent名稱小寫> <回報檔案> ../HQ
```

**範例**：

```bash
# Sophie 回報（在 wawOwner 目錄）
bash ../HQ/scripts/agent_report_to_hq_v2.sh sophie _agent/LATEST_REPORT.md ../HQ

# Ina 回報（在 tg25-infra 目錄）
bash ../HQ/scripts/agent_report_to_hq_v2.sh ina _agent/LATEST_REPORT.md ../HQ
```

**回報流程**：
1. 優先 HTTP POST → `localhost:8899/report`
2. 失敗則自動 fallback → 直接寫入 `HQ/_agent/inbox/`

---

## HQ 端：查看回報

```bash
# 查看最新回報
ls -lht _agent/inbox/ | head -10

# 讀取特定 Agent 回報
cat _agent/inbox/<最新檔案>.json
```

---

## 服務管理

```bash
# 查看 agents_supervisor 狀態
launchctl list | grep com.hq.agents.supervisor

# 查看日誌
tail -f logs/agents_supervisor.out.log
tail -f logs/agents_supervisor.err.log

# 重啟服務
launchctl unload ~/Library/LaunchAgents/com.hq.agents.supervisor.plist
launchctl load ~/Library/LaunchAgents/com.hq.agents.supervisor.plist

# 確認 Redis 正常
redis-cli ping
```

---

## Agent 名稱對照表

| Agent 名稱（參數） | 檔案名稱 | 專案 | 職責 |
|------------------|---------|------|------|
| `sophie` | `to_Sophie.json` | wawOwner | 營運商後台、設備管理 |
| `ina` | `to_Ina.json` | tg25-infra | 資料庫、MQTT、Redis |
| `mina` | `to_Mina.json` | Member | 玩家前端、支付系統 |
| `allie` | `to_Allie.json` | Alliance | 供應商、代理商 |
| `hubie` | `to_Hubie.json` | iHub | Android APK |
| `coli` | `to_Coli.json` | IOTwawS3 | 遊戲機韌體（`device/+/`） |
| `fio` | `to_Fio.json` | IOTkiosk_v0 | 兌幣機韌體（`kiosk/+/`） |

---

## 目錄結構

```
HQ/_agent/
├── outbox/                          # 任務備份（非觸發信號）
│   └── to_<Agent>.json
├── inbox/                           # Agent 回報收件匣
│   └── YYYYMMDD_HHMMSS_<agent>.json
├── REDIS_<timestamp>_<agent>.json   # Supervisor 接收 Redis 後存檔
└── task_flow.log                    # 操作日誌
```

---

## 快速參考

```bash
# HQ 發任務
./scripts/hq_task_flow.sh task sophie TASK_001 "任務描述" normal

# Agent 回報
bash ../HQ/scripts/agent_report_to_hq_v2.sh sophie _agent/LATEST_REPORT.md ../HQ

# 查看回報
ls -lht _agent/inbox/ && cat _agent/inbox/<最新>.json

# 服務狀態
launchctl list | grep com.hq && redis-cli ping
```

---

**文檔版本**: v3.0
**最後更新**: 2026-06-09
**架構**: Redis Pub/Sub + agents_supervisor（launchd 常駐）
**維護者**: HQ
