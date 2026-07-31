# launchd Agent 架構與 com.hq.all_agents 廢棄記錄

> **最後更新**：2026-06-09  
> **Owner**：HQ (Hera)  
> **狀態**：Active

---

## 背景

wawIoT 系統使用 macOS launchd 管理所有常駐服務。本文記錄 Agent 監聽器的正確架構，以及 `com.hq.all_agents` 的廢棄原因與決策過程。

---

## 現行正確架構

### 核心守護進程：`com.hq.agents.supervisor`

| 項目 | 值 |
|------|-----|
| plist | `~/Library/LaunchAgents/com.hq.agents.supervisor.plist` |
| 執行程式 | `.venv/bin/python3 scripts/hq_gateway.py` |
| KeepAlive | `true`（崩潰自動重啟） |
| RunAtLoad | `true` |
| EnvironmentVariables | PATH、CODEX_BIN、HQ_PATH、AGENT_EXEC_TIMEOUT |

`hq_gateway.py` 用單一 Python 進程同時訂閱所有 Agent 的 Redis 頻道，並整合 LLM 決策引擎：

```
agent/hq/*        agent/ina/*       agent/sophie/*
agent/mina/*      agent/allie/*     agent/hubie/*
agent/coli/*      agent/fio/*
```

收到任務後直接在對應工作目錄觸發 `codex exec`，不需要各自獨立的 listener 進程。

---

## com.hq.all_agents 廢棄記錄

### 廢棄日期
2026-06-09

### 廢棄原因

1. **功能重疊**：`start_all_agents.sh` 啟動各 Agent 的 `agent_redis_listener.py`，但 `agents_supervisor.py` 已統一處理相同工作。
2. **TCC 權限問題（狀態碼 126）**：plist 使用 `/bin/bash` 呼叫 shell 腳本，macOS 沙盒機制（TCC）擋住了 launchd 對 `/bin/bash` 的存取，出現 `Operation not permitted`，腳本無法執行。
3. **根本解法**：launchd 直接呼叫 Python（有授權），不透過 `/bin/bash` 中介，是正確且最小權限的設計。

### 126 狀態碼的意義

macOS launchd 狀態碼 `126` = `Permission denied`（而非找不到程式的 `127`）。  
錯誤訊息：`/bin/bash: .../start_all_agents.sh: Operation not permitted`  
根因：`getcwd` 失敗 + TCC 未授予 `/bin/bash` 完整磁碟存取。

### 廢棄操作

```bash
launchctl unload ~/Library/LaunchAgents/com.hq.all_agents.plist
rm ~/Library/LaunchAgents/com.hq.all_agents.plist
```

---

## launchd plist 設計原則

### ✅ 正確做法

```xml
<key>ProgramArguments</key>
<array>
    <string>/path/to/.venv/bin/python3</string>
    <string>-u</string>
    <string>/path/to/script.py</string>
</array>
<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>HOME</key>
    <string>/Users/ilawusong</string>
</dict>
```

- 直接呼叫 Python 或已授權的執行檔
- 明確設定 `EnvironmentVariables`（launchd 不繼承 shell 環境）
- `KeepAlive true` 給需要常駐的服務

### ❌ 避免做法

```xml
<!-- 避免：透過 /bin/bash 呼叫腳本 -->
<string>/bin/bash</string>
<string>/path/to/script.sh</string>
```

- 透過 `/bin/bash` 中介容易被 TCC 擋住（狀態碼 126）
- Shell 腳本的功能應整合進 Python 或直接由 supervisor 處理

---

## 相關 launchd 服務一覽

| Label | 程式 | KeepAlive | 職責 |
|-------|------|-----------|------|
| `com.hq.agents.supervisor` | `hq_gateway.py` | ✅ | 所有 Agent Redis 監聽、codex 觸發、LLM 自動決策 |
| `com.hq.messagehub.v2` | Message Hub v2 | ✅ | HTTP API 任務分發 |
| `com.hq.redis.keeper` | Redis keeper | ✅ | Redis 健康維護 |
| ~~`com.hq.all_agents`~~ | ~~`start_all_agents.sh`~~ | ❌ | **已廢棄** |

---

## 🔗 文件神經連結

| 關聯文件 | 關係 |
|----------|------|
| `HQ_DEPLOYMENT_SOP.md` | launchd 服務屬於部署範疇，受 SOP 管轄 |
| `LOCAL_DEV_CUSTOMIZATIONS.md` | 本地開發環境相關設定 |
| `01_agent_governance/MESSAGE_HUB_V2_DEPLOYMENT.md` | Message Hub v2 部署細節 |
| `01_agent_governance/AUTOFLOW_CONTEXT_STORE_DESIGN.md` | agents_supervisor 的上層設計背景 |
