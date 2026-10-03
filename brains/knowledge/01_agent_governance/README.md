# Agent 治理規則

此目錄包含所有 Agent 必須遵守的協作與執行規範。

## 📋 目錄

### 核心協定
- `SIMPLE_FILE_DISPATCH_PROTOCOL.md` - 純檔案派工協定（✅ 現行唯一派工體系）
- `AGENT_COLLABORATION_PROTOCOL.md` - Agent 協作規範與通訊方式
- `AGENT_STARTUP_PROTOCOL.md` - Agent 啟動協議
- `AGENT_EXECUTION_PROTOCOL.md` - Agent 執行與任務規範
- `TASKFLOW_QUICK_GUIDE.md` - Taskflow 快速參考指南

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

## ⚠️ 已棄用的通訊／派工方式

❌ **Redis Pub/Sub、HQ Message Hub、`hq_gateway.py`（launchd 常駐）、`.taskbox/*.json`、`_agent/inbox`**
已於 2026 全面廢除。相關文件（`MESSAGE_HUB_*.md`、`AUTOFLOW_CONTEXT_STORE_DESIGN.md`、`CLI_AGENT_DISPATCH_DESIGN.md` 等）僅為歷史存檔，**不可作為現行指引**。

❌ **Chat Bridge**（已於 2026-06-06 棄用）

---

## ✅ 現行唯一派工體系

**`.taskflow` 純檔案信箱機制**

- HQ 派工：`./dev_tools/waw_ops.sh task <agent> <task_id> --file <工單.md> [priority]`
- Agent 回報：`bash ../../dev_tools/agent_report_to_hq_v2.sh <agent> <回報.md>`
- 協定規範：`SIMPLE_FILE_DISPATCH_PROTOCOL.md`
- 目錄說明：`.taskflow/README.md`

---

**維護者**：HQ
**最後更新**：2026-10-03
