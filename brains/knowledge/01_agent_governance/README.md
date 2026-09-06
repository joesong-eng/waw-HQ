# Agent 治理規則

此目錄包含所有 Agent 必須遵守的協作與執行規範。

## 📋 目錄

### 核心協定
- `AGENT_COLLABORATION_PROTOCOL.md` - Agent 協作規範與通訊方式
- `MESSAGE_HUB_PROTOCOL.md` - HQ Message Hub 通訊協定（✅ 啟用中）
- `AGENT_EXECUTION_PROTOCOL.md` - Agent 執行與任務規範

### 工作流程
- `DB_MIGRATION_WORKFLOW.md` - 資料庫變更流程
- `TASK_ROUTING_AND_COMPLETION.md` - 任務路由與完成標準

### 文件管理
- `FILE_REGISTRATION_SYSTEM.md` - 文件註冊系統
- `DOCUMENT_CONSISTENCY_RULES.md` - 文件一致性規則

### 邊界與常識
- `AGENT_RESPONSIBILITY_BOUNDARIES.md` - Agent 職責邊界
- `INTERACTION_COMMON_SENSE.md` - 互動常識

---

## ⚠️ 已棄用的通訊方式

### ❌ Chat Bridge（已於 2026-06-06 棄用）

**為何棄用？**
- 通訊不穩定，訊息經常遺失
- 依賴外部 MCP 服務
- 缺乏訊息追蹤與歷史記錄

**替代方案**：
✅ **HQ Message Hub v3.0**（Redis Pub/Sub + hq_gateway.py）
- 100% 可靠的本地 HTTP 服務
- 自動化通訊機制
- 完整的訊息記錄

**使用說明**：
- HQ 端：`../../../README_MESSAGE_HUB.md`
- Agent 端：`../../../SHARED_MESSAGE_HUB_GUIDE.md`
- 協定規範：`MESSAGE_HUB_PROTOCOL.md`

---

**維護者**：HQ  
**最後更新**：2026-06-06
