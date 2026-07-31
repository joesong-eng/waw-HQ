# ~~Message Hub v2.0 - 事件驅動架構~~ （已廢棄）

> ⛔ **廢棄聲明**：本文件描述的 v2.0 HTTP-only 架構已於 2026-06-09 廢棄。
> 現行架構請參閱 `MESSAGE_HUB_PROTOCOL.md`（v3.0 Redis Pub/Sub）。

> **版本**：2.0.0（已廢棄）
> **狀態**：❌ 廢棄，請勿使用
> **取代文件**：`MESSAGE_HUB_PROTOCOL.md` v3.0
> **更新日期**：2026-06-06（廢棄日：2026-06-09）
> **維護者**：HQ

---

## 📋 概述

Message Hub v2.0 是 HQ 的核心通訊系統，採用**事件驅動架構**，支援：
- ✅ HTTP API (Agent 查詢/回報)
- ✅ 任務自動管理
- ✅ 事件路由與分派
- 🚧 Redis Pub/Sub 監聽 (預留，未啟用)
- 🚧 WebSocket 監聽 (未來功能)

---

## 🏗️ 架構設計

### 模組結構

```
scripts/message_hub_v2/
├── __init__.py          (23 行) - 模組導出
├── config.py            (63 行) - Agent 路由規則
├── router.py            (97 行) - 事件路由邏輯
├── task_manager.py      (188 行) - 任務產生與管理
├── redis_listener.py    (184 行) - Redis Pub/Sub 監聽
├── http_server.py       (203 行) - HTTP API 伺服器
└── __main__.py          (146 行) - 主程式入口
```

**總計**：904 行，分 7 個模組，遵守 CHUNKED WRITE PROTOCOL (每個 <350 行)

### 資料流程

```
┌─────────────────────────────────────────────────┐
│         HQ Message Hub v2.0                     │
│                                                 │
│  ┌──────────┐                                  │
│  │  HTTP    │  ← Agent 查詢任務                │
│  │ Server   │  → 回傳 JSON                     │
│  │ :8899    │                                  │
│  └────┬─────┘                                  │
│       │                                         │
│       ▼                                         │
│  ┌──────────────┐                              │
│  │Task Manager  │                              │
│  │  - 產生任務  │                              │
│  │  - 路由分派  │                              │
│  │  - 儲存管理  │                              │
│  └──────┬───────┘                              │
│         │                                       │
│         ▼                                       │
│  _agent/outbox/to_<agent>.json                 │
└─────────────────────────────────────────────────┘
```

---

## 📊 Agent 路由規則

> ⚠️ **注意**：Firmware Agent 分工（不可混淆）
> - **Fio** → `IOTkiosk_v0` (kiosk/+) - 兌幣卡韌體（紙鈔機）
> - **Coli** → `IOTwawS3` (device/+) - 通訊卡韌體（遊戲機）

| Agent | 負責範圍 | Redis 頻道 | 關鍵字 |
|-------|---------|------------------|-------|
| Sophie | 設備管理 | `hq/events/device/*` | device, owner, esp32 |
| Ina | 基礎設施 | `hq/events/infra/*` | database, mqtt, redis, postgres |
| Mina | 玩家系統 | `hq/events/member/*` | payment, member, kiosk, redemption |
| **Coli** | **遊戲機韌體** | `hq/events/firmware/wawS3/*` | **IOTwawS3, game_v0** |
| **Fio** | **兌幣機韌體** | `hq/events/firmware/kiosk/*` | **IOTkiosk_v0, kiosk_v0** |
| Allie | 供應商 | `hq/events/alliance/*` | supplier, alliance |
| Hubie | iHub APK | `hq/events/ihub/*` | android, apk, tablet |

---

## 🚀 使用方式

### 啟動服務

```bash
# 方式 1：使用啟動腳本
./scripts/hq_start_v2.sh

# 方式 2：直接執行
python3 -m scripts.message_hub_v2

# 方式 3：背景執行
nohup python3 -m scripts.message_hub_v2 > /tmp/msghub_v2.log 2>&1 &
```

### API 端點

```bash
# 查詢系統狀態
curl http://localhost:8899/status

# Agent 查詢任務
curl http://localhost:8899/tasks/<agent_name>

# Agent 列表
curl http://localhost:8899/agents

# Agent 回報 (POST)
curl -X POST http://localhost:8899/report \
  -H "Content-Type: application/json" \
  -d '{"from_agent":"sophie","status":"completed",...}'
```

---

## 📂 目錄結構

```
_agent/
├── inbox/              # Agent 回報收件匣
│   └── 20260606_120000_sophie.json
├── outbox/             # Agent 待辦任務
│   ├── to_sophie.json
│   ├── to_ina.json
│   └── to_mina.json
└── event_logs/         # 事件處理日誌
    └── 20260606_120000_event.json
```

---

## 🔧 維護與監控

### 檢查服務狀態

```bash
# 查看進程
ps aux | grep message_hub_v2

# 查看 API 狀態
curl http://localhost:8899/status | python3 -m json.tool

# 查看日誌
tail -f /tmp/msghub_v2.log
```

### 停止服務

```bash
# 找到 PID
ps aux | grep message_hub_v2 | grep -v grep

# 停止服務
kill <PID>

# 或強制停止
pkill -f message_hub_v2
```

---

## 🚧 未來擴充

### Phase 2: Redis Pub/Sub 監聽 (預留)

當需要即時事件監聽時：

1. 安裝 Redis Python 套件
   ```bash
   pip install redis
   ```

2. 確認 Redis 服務運行
   ```bash
   redis-cli ping
   ```

3. 重啟 Message Hub，自動啟用 Redis 監聽

4. 其他系統發布事件
   ```bash
   redis-cli PUBLISH "hq/events/device/ESP32_ABC/offline" \
     '{"device_id":"ESP32_ABC","status":"offline"}'
   ```

5. HQ 自動接收並產生任務給對應 Agent

### Phase 3: WebSocket 監聽 (未實作)

- 連接 Owner/Member 後端 WebSocket
- 接收即時事件並路由

---

## 📚 相關文檔

- ~~**設計文檔**：`.kiro/specs/MESSAGE_HUB_V2_DESIGN.md`~~ （已刪除，v2.0 廢棄）
- **v1.0 文檔**：`README_MESSAGE_HUB.md`
- **協定規範**：`MESSAGE_HUB_PROTOCOL.md`
- **Agent 使用指南**：`../SHARED_MESSAGE_HUB_GUIDE.md`

---

## ⚠️ 已知限制

1. **Redis 功能未啟用** - 目前以 HTTP-only 模式運行
2. **Python 版本問題** - 需要 Python 3.9+ 且安裝 redis 套件
3. **向下兼容** - 與 v1.0 HTTP API 完全兼容

---

**維護者**：HQ (Hera)  
**服務地址**：http://localhost:8899  
**版本**：2.0.0  
**最後更新**：2026-06-06
