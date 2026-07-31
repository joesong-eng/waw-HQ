# Chat Bridge 廢棄公告

> **狀態**：❌ 已完全棄用  
> **廢棄日期**：2026-06-06  
> **替代方案**：HQ Message Hub

---

## ⚠️ 重要通知

**Chat Bridge (MCP ai-chat-bridge) 已於 2026-06-06 完全棄用，請所有 Agent 立即停止使用。**

---

## 為何棄用？

### 1. 通訊不可靠
- ❌ 訊息經常遺失或延遲
- ❌ 無法保證訊息送達
- ❌ 缺乏錯誤處理機制

### 2. 依賴外部服務
- ❌ 依賴 MCP 外部服務
- ❌ 配置複雜且容易失效
- ❌ 無法本地除錯

### 3. 缺乏記錄與追蹤
- ❌ 沒有訊息歷史記錄
- ❌ 無法追蹤任務狀態
- ❌ 出問題時難以除錯

---

## ✅ 替代方案：HQ Message Hub

### 核心優勢

| 特性 | Chat Bridge | HQ Message Hub |
|------|-------------|----------------|
| 可靠性 | ❌ 不穩定 | ✅ 100% 可靠 |
| 自動化 | ❌ 手動通知 | ✅ 完全自動 |
| 追蹤性 | ❌ 訊息遺失 | ✅ 完整記錄 |
| 除錯性 | ❌ 困難 | ✅ 檔案系統可見 |
| 依賴性 | ⚠️ 外部 MCP | ✅ 本地服務 |

### 服務架構

```
HQ Message Hub
├── HTTP 服務：localhost:8899
├── 收件匣：_agent/inbox/
├── 發件匣：_agent/outbox/
└── 歷史：_agent/archive/
```

---

## 🔄 遷移指南

### HQ（協調者）

**舊方式**（已廢棄）：
```
透過 Chat Bridge 發送：@AgentName <訊息>
```

**新方式**（推薦）：
```bash
./scripts/hq_send_task_via_hub.sh <agent> <task_id> <description> [priority]
```

**範例**：
```bash
./scripts/hq_send_task_via_hub.sh sophie TASK_001 "實作新 API" high
```

### Agent（執行者）

**舊方式**（已廢棄）：
```
被動等待 Chat Bridge 訊息
```

**新方式**（自動化）：
```bash
# 啟動時自動檢查（已安裝 hooks）
# 或手動檢查
./scripts/agent_check_hq.sh <agent_name>

# 完成後回報
./scripts/agent_report_to_hq.sh <agent_name> <report_file>
```

---

## 📖 使用文檔

### HQ 端
- `../../../README_MESSAGE_HUB.md` - 完整使用說明
- `../../../QUICKSTART_MESSAGE_HUB.md` - 快速開始
- `MESSAGE_HUB_PROTOCOL.md` - 協定規範

### Agent 端
- `../../../SHARED_MESSAGE_HUB_GUIDE.md` - Agent 通訊指南（公用）
- `.kiro/hooks/on_start.sh` - 自動檢查機制

---

## ⚠️ 重要提醒

1. **立即停止使用 Chat Bridge**
   - 所有通訊必須透過 HQ Message Hub
   - 不要再嘗試連接 MCP ai-chat-bridge

2. **刪除舊的配置**
   - 移除 MCP chat-bridge 配置
   - 清理相關的環境變數

3. **安裝新的 Hooks**
   - 執行 `./scripts/install_agent_hooks.sh`（在 HQ 目錄）
   - 確保 Agent 啟動時自動檢查任務

---

## 🆘 需要幫助？

1. 查看 HQ Message Hub 文檔：`README_MESSAGE_HUB.md`
2. 執行幫助命令：`./scripts/hq_help.sh`
3. 聯絡 Joe 或 HQ

---

**廢棄日期**：2026-06-06  
**生效日期**：立即生效  
**維護者**：HQ (Hera)
