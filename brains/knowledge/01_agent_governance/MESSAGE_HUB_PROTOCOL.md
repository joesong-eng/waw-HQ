# ~~HQ Message Hub 通訊協定~~ (已廢棄)

> ⛔ **廢棄聲明**：本文件描述 v1.0-v3.0 時期的 Redis Pub/Sub 架構。  
> 自 2026-08 起，派工系統已簡化為**純檔案系統模式**。  
> **當前版本請參閱**：`SIMPLE_FILE_DISPATCH_PROTOCOL.md`

---

## 為什麼廢棄？

**目錄結構變更**：所有專案已整合到統一目錄 `PROJECT/` 下

```
舊架構（分散式）          新架構（統一目錄）
~/wawOwner/          →   ~/Documents/WaW/PROJECT/Owner/
~/tg25-infra/        →   ~/Documents/WaW/PROJECT/Infra/
~/Member/            →   ~/Documents/WaW/PROJECT/Member/
```

由於所有專案在同一父目錄下，不再需要：
- ❌ Redis Pub/Sub 跨進程通訊
- ❌ HTTP API Message Hub
- ❌ agents_supervisor 自動觸發
- ❌ launchd 自動監聽

**檔案系統已足夠快速可靠**。

---

## 當前派工方式

**HQ 派發任務**：
```bash
./scripts/hq_task_flow.sh task <agent> <task_id> "<描述>" [priority]
```

**Agent 回報**：
```bash
bash ../../scripts/agent_report_to_hq_v2.sh <agent_name> <report_file.md>
```

**詳細說明**：請參閱 `SIMPLE_FILE_DISPATCH_PROTOCOL.md`

---

## 歷史參考（v3.0 Redis Pub/Sub 架構）

以下內容僅供歷史參考，已不再使用。



---
---

# HQ Message Hub 通訊協定

> **文件類型**：Agent 協作協議（權威版本）
> **建立日期**：2026-06-06
> **最後更新**：2026-06-09
> **狀態**：✅ 現行版本（v3.0 Redis Pub/Sub 架構）
> **維護者**：HQ

---

## ⚠️ 版本演進說明

| 版本 | 時期 | 核心機制 | 狀態 |
|------|------|---------|------|
| v1.0 | 2026-06-06 | HTTP + 檔案系統 | ❌ 廢棄 |
| v2.0 | 2026-06-07 | HTTP-only + fallback 檔案系統 | ❌ 廢棄 |
| **v3.0** | **2026-06-09** | **Redis Pub/Sub + agents_supervisor** | **✅ 現行** |

---

## 📋 概述

HQ Message Hub v3.0 採用 **Redis Pub/Sub** 作為核心通訊骨幹，由 `hq_gateway.py`（launchd 常駐）統一管理所有 Agent 的任務接收、觸發與自動決策。

### 核心設計原則

1. **Redis 是唯一觸發機制**：任務必須經由 `redis-cli PUBLISH` 推送，才能觸發 Agent 執行
2. **agents_supervisor 統一管理**：所有 Agent 不再各自維護獨立 launchd plist
3. **outbox 為備份存檔**：檔案系統 outbox 僅供人工查閱，不作為觸發信號
4. **hq_task_flow.sh 是唯一入口**：HQ 發任務只能走這個腳本

---

## 🏗️ 系統架構

```
Joe
 │
 │ ./scripts/hq_task_flow.sh task <agent> <task_id> "<描述>" [priority]
 ▼
hq_task_flow.sh
 ├─→ 寫入 .taskbox/outbox/to_<Agent>.json（備份存檔）
 └─→ redis-cli PUBLISH agent/<agent>/task <payload>
           │
           ▼
   hq_gateway.py（com.hq.agents.supervisor，launchd 常駐）
   ├─ 訂閱：agent/<agent_name>/*
   ├─ 接收任務 → 存 _agent/REDIS_<timestamp>.json
   └─ 自動觸發 codex exec 執行任務
           │
           ▼
   Agent 執行完成
   └─→ agent_report_to_hq_v2.sh → HQ/.taskbox/inbox/<timestamp>_<agent>.json
```

---

## 🚨 HQ 發任務唯一正確流程

```bash
./scripts/hq_task_flow.sh task <agent> <task_id> "<描述>" [priority]
```

### 支援的訊息類型

| 子命令 | 用途 | 範例 |
|--------|------|------|
| `task` | 發布正式任務 | `hq_task_flow.sh task sophie TASK_001 "實作 API" high` |
| `consult` | 發送諮詢 | `hq_task_flow.sh consult ina CONS_001 "確認 Redis 版本"` |
| `review` | 發送設計型諮詢（需審核） | `hq_task_flow.sh review ina REV_001 "設計 DB schema"` |
| `supplement` | 補充資訊 | `hq_task_flow.sh supplement sophie CONS_001 "補充說明..."` |
| `redo` | 要求重做 | `hq_task_flow.sh redo sophie TASK_001 "回傳格式不正確"` |
| `approve` | 確認通過 | `hq_task_flow.sh approve sophie TASK_001` |

#### `consult` vs `review` 的區別

| 類型 | 命令 | 適用場景 | 處理方式 |
|------|------|----------|----------|
| **查詢型諮詢** | `consult` | 查詢現況、確認設定、取得資訊 | LLM 自動決策，可自動結案 |
| **設計型諮詢** | `review` | 設計 schema、撰寫規格、產出設計稿 | 永遠 escalate，必須 Joe 審核 |

**實作機制**：
- `consult` 在 JSON payload 中設定 `"requires_review": false`
- `review` 在 JSON payload 中設定 `"requires_review": true`
- `hq_gateway.py` 根據 `requires_review` 旗標決定是否 escalate
- 舊版關鍵詞偵測機制已廢棄（2026-06-10）


### Priority 選項

`high` / `normal`（預設）/ `low`

---

## ❌ 禁止行為（違反直接下線）

| 禁止指令 | 原因 |
|---------|------|
| `hq_send_task_via_hub.sh` | 只寫檔案，**不觸發 Redis**，Agent 不會知道有任務 |
| `hq_publish_and_trigger.sh` | 繞過 Redis，直接 codex exec，破壞架構一致性 |
| 手動 `codex exec` | 同上，非架構內觸發 |

---

## 📂 檔案系統結構

```
HQ/_agent/
├── outbox/                          # HQ 發布的任務（備份存檔，非觸發信號）
│   └── to_<Agent>.json              # 首字母大寫，e.g. to_Sophie.json
├── inbox/                           # Agent 回報收件匣
│   └── YYYYMMDD_HHMMSS_<agent>.json
├── REDIS_<timestamp>_<agent>.json   # agents_supervisor 接收 Redis 訊息後存檔
└── task_flow.log                    # hq_task_flow.sh 操作日誌
```

---

## 📋 JSON Payload 格式規範

### 任務（task）

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
  "report": "完整報告內容（Markdown）"
}
```

---

## 🔄 完整工作流程

### Step 1：HQ 發任務

```bash
cd /Users/ilawusong/Documents/sysWawIot/HQ
./scripts/hq_task_flow.sh task sophie TASK_001 "實作分潤 API" high
```

**發生的事**：
- `.taskbox/outbox/to_Sophie.json` 被寫入（備份）
- `redis-cli PUBLISH agent/sophie/task <payload>` 推送

### Step 2：agents_supervisor 接收

- `com.hq.agents.supervisor`（launchd 常駐）訂閱 `agent/<name>/*`
- 接收訊息 → 存入 `_agent/REDIS_<timestamp>_sophie.json`
- 自動觸發 `codex exec` 在 Sophie 專案執行任務

### Step 3：Agent 執行並回報

```bash
# Agent 完成後（在各自專案目錄執行）
bash ../HQ/scripts/agent_report_to_hq_v2.sh sophie _agent/LATEST_REPORT.md ../HQ
```

**回報方式**：
1. `redis-cli PUBLISH agent/<agent>/report <payload>`
2. `hq_gateway.py` 收到後存入 `HQ/.taskbox/inbox/` 並由 `DecisionEngine` 自動決策

### Step 4：HQ 查看回報

```bash
ls -lht .taskbox/inbox/ | head -10
cat .taskbox/inbox/<最新檔案>.json
```

---

## 🤖 服務管理

### agents_supervisor（統一管理所有 Agent）

```bash
# 查看服務狀態
launchctl list | grep com.hq.agents.supervisor

# 查看日誌
tail -f /Users/ilawusong/Documents/sysWawIot/HQ/logs/agents_supervisor.out.log
tail -f /Users/ilawusong/Documents/sysWawIot/HQ/logs/agents_supervisor.err.log

# 重啟服務
launchctl unload ~/Library/LaunchAgents/com.hq.agents.supervisor.plist
launchctl load ~/Library/LaunchAgents/com.hq.agents.supervisor.plist
```

### Redis 狀態確認

```bash
redis-cli ping          # 應回傳 PONG
redis-cli info server   # 確認版本與狀態
```

---

## 🎯 Agent 名稱對照表

| Agent 名稱（參數小寫） | 檔案名稱（首字母大寫） | 專案目錄 | 職責 |
|----------------------|----------------------|---------|------|
| `sophie` | `to_Sophie.json` | wawOwner | 營運商後台、設備管理 |
| `ina` | `to_Ina.json` | tg25-infra | 資料庫、MQTT、Redis |
| `mina` | `to_Mina.json` | Member | 玩家前端、支付系統 |
| `allie` | `to_Allie.json` | Alliance | 供應商、代理商 |
| `hubie` | `to_Hubie.json` | iHub | Android APK |
| `coli` | `to_Coli.json` | IOTwawS3 | 遊戲機韌體（device/+/） |
| `fio` | `to_Fio.json` | IOTkiosk_v0 | 兌幣機韌體（kiosk/+/） |

---

## 🔗 文件神經連結

### 強關聯（必讀）
> 修改本文件內容前，必須先閱讀以下文件

- `AUTOFLOW_CONTEXT_STORE_DESIGN.md` - 自動化共識，包含 context store 設計與禁止行為
- `CODEX_EXEC_GUIDE.md` - Agent 接收任務後的執行規則

### 中關聯（建議讀）
> 了解完整上下文，建議閱讀

- `MESSAGE_HUB_V2_DEPLOYMENT.md` - 部署細節與 launchd 設定
- `01_agent_governance/AGENT_COLLABORATION_PROTOCOL.md` - 協作規範

### 排除混淆
> 容易混淆但已廢棄，不應再參考

- `MESSAGE_HUB_V2.md` - v2.0 HTTP-only 架構說明，**已廢棄**
- `README_MESSAGE_HUB_COMPLETE.md` - v2.0 使用指南，**已廢棄**

---

*制定者：HQ | 版本：3.0 | 最後更新：2026-06-09*

