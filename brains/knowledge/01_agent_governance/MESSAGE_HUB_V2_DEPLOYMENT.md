# Message Hub 部署報告（歷史文件）

> ⛔ **注意**：「HQ 發任務」的使用方式區段已過時。現行唯一正確指令請見 `MESSAGE_HUB_PROTOCOL.md`。
> 本文件保留部署細節（launchd、agents_supervisor 設定）供維運參考。

> **完成日期**：2026-06-07
> **最後更新**：2026-06-09（架構演進：各自 plist → supervisor 統一管理）
> **部署方式**：macOS launchd 服務（`com.hq.agents.supervisor`）
> **狀態**：✅ 基礎設施仍在運行；發任務流程見 `MESSAGE_HUB_PROTOCOL.md` v3.0

---

## 🎯 部署成果

### HQ 端
- ✅ Message Hub v2.0 運行中 (`localhost:8899`)
- ✅ Redis 監聽已啟用 (`redis_enabled: true`)
- ✅ HTTP API 正常
- ✅ 虛擬環境 (`.venv` + redis==8.0.0)

### Agent 端
> ⚠️ **架構更新（2026-06-09）**：各 Agent 不再各自使用獨立 plist，改由 `com.hq.agents.supervisor` 單一進程統一管理。

- ✅ 所有 Agent（hq/ina/sophie/mina/allie/hubie/coli/fio）- 由 `agents_supervisor` 統一管理，Redis 已連線

---

## 📊 功能驗證

**Redis Pub/Sub 測試**：
- ✅ HQ 發布任務 → Redis → Agent 即時接收
- ✅ 訂閱模式：`agent/<agent_name>/*`
- ✅ 自動儲存任務到 `_agent/REDIS_*.json`

**launchd 服務**：
- ✅ 開機自動啟動（`com.hq.agents.supervisor`）
- ✅ 程序崩潰自動重啟（`KeepAlive: true`）
- ✅ 日誌輸出到 `HQ/logs/agents_supervisor.out.log`

---

## 🗂️ 檔案清單

### HQ 專案
- `scripts/message_hub_v2/` - Message Hub v2.0 核心模組
  - `__init__.py` (23 行)
  - `config.py` (63 行)
  - `router.py` (97 行)
  - `task_manager.py` (188 行)
  - `redis_listener.py` (184 行)
  - `http_server.py` (203 行)
  - `__main__.py` (146 行)
- `scripts/agent_redis_listener.py` (166 行)
- `scripts/hq_start_v2_venv.sh` (54 行)
- `.venv/` - 虛擬環境

### Agent 專案（現行架構：supervisor 統一管理）

> 各 Agent 專案仍保有 `.venv/` 與 `scripts/agent_redis_listener.py`（備用），但**不再各自載入獨立 launchd plist**。

**統一管理進程**：
- `HQ/scripts/agents_supervisor.py` — 單一進程訂閱所有 Agent Redis 頻道
- `~/Library/LaunchAgents/com.hq.agents.supervisor.plist` — 唯一的 launchd 常駐設定

**各 Agent 專案**（.venv 仍需存在供 supervisor 呼叫）：
- wawOwner (Sophie)：`.venv/bin/python3` ✅
- tg25-infra (Ina)：`.venv/bin/python3` ✅
- Member (Mina)：`.venv/bin/python3` ✅
- Alliance (Allie)：`.venv/bin/python3` ✅
- iHub (Hubie)：`.venv/bin/python3` ✅
- IOTwawS3 (Coli)：`.venv/bin/python3` ✅
- IOTkiosk_v0 (Fio)：`.venv/bin/python3` ✅

~~`~/Library/LaunchAgents/com.hq.agent.*.plist`~~ — ❌ 已廢棄，不再使用

---

## 🚀 使用方式

### HQ 發布任務（唯一正確方式）

> ⛔ 以下「方式 1」舊腳本已廢棄，**禁止使用**。

~~**方式 1（廢棄）**: `hq_send_task_via_hub.sh`~~ — 只寫檔案，不觸發 Redis

**唯一正確方式：`hq_task_flow.sh`**
```bash
./scripts/hq_task_flow.sh task sophie TASK_001 "任務描述" high
```
此腳本同時寫入 outbox 並觸發 `redis-cli PUBLISH agent/sophie/task`。

### Agent 自動接收

**Agent 監聽器統一由 `agents_supervisor` 管理**：
- 開機自動啟動（`com.hq.agents.supervisor` launchd）
- Supervisor 崩潰自動重啟（`KeepAlive: true`）
- 即時接收 HQ 發布的任務（Redis psubscribe）
- 自動儲存到各 Agent 的 `_agent/REDIS_*.json`

### 服務管理

**檢查服務狀態**：
```bash
launchctl list | grep com.hq
```

**查看日誌**：
```bash
tail -f /Users/ilawusong/Documents/sysWawIot/HQ/logs/agents_supervisor.out.log
tail -f /Users/ilawusong/Documents/sysWawIot/HQ/logs/agents_supervisor.err.log
```

**停止服務**：
```bash
launchctl unload ~/Library/LaunchAgents/com.hq.agents.supervisor.plist
```

**啟動服務**：
```bash
launchctl load ~/Library/LaunchAgents/com.hq.agents.supervisor.plist
```


---

## 🔧 技術細節

### Redis Pub/Sub 訂閱模式
- `agent/<agent_name>/*` - Agent 專屬頻道
- `hq/events/agent/<agent_name>/*` - HQ 事件頻道

### 訂閱確認機制
監聽器腳本使用訂閱確認迴圈確保 Redis 訂閱成功：
```python
self.pubsub.psubscribe(*self.channels)

# 等待訂閱確認
for message in self.pubsub.listen():
    if message["type"] == "psubscribe":
        break
```

### launchd 配置要點
- `RunAtLoad: true` - 開機自動啟動
- `KeepAlive: true` - 程序崩潰自動重啟
- `StandardOutPath` - 標準輸出日誌路徑
- `StandardErrorPath` - 錯誤日誌路徑

---

## 🎯 部署檢查清單

### HQ 端
- [ ] Message Hub v2.0 運行中
- [ ] Redis 服務運行中
- [ ] 虛擬環境已建立
- [ ] Redis 套件已安裝

### Agent 端（統一由 supervisor 管理）
- [ ] 各 Agent 專案 `.venv/` 已建立
- [ ] 各 Agent 專案 redis 套件已安裝（`.venv/bin/pip install redis`）
- [ ] `com.hq.agents.supervisor.plist` 已載入並運行
- [ ] `launchctl list | grep com.hq.agents.supervisor` 顯示 PID

---

## 📚 相關文檔

- ~~**設計文檔**：`.kiro/specs/MESSAGE_HUB_V2_DESIGN.md`~~ （已刪除，v2.0 廢棄）
- **v1.0 文檔**：`README_MESSAGE_HUB.md`
- **協定規範**：`MESSAGE_HUB_PROTOCOL.md`
- **Agent 使用指南**：`../SHARED_MESSAGE_HUB_GUIDE.md`
- **統一監聽器**：`scripts/agents_supervisor.py`（管理所有 Agent）

---

**維護者**：HQ (Hera)  
**完成日期**：2026-06-07  
**狀態**：✅ 生產就緒
