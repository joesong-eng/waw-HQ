# HQ 技能與手冊索引 (Skills & Manuals Index)

> **最後更新**：2026-10-05
> **狀態**：已對齊 `.taskflow` 純檔案派工體系

---

## 1. 現行技能與工具 (Active)

| 項目 | 位置 |
|------|------|
| **派工系統** | `dev_tools/waw_ops.sh`（`.taskflow` 純檔案系統） |
| **回報工具** | `dev_tools/agent_report_to_hq_v2.sh` |
| **任務協調 Skill** | `hq_ops/task_orchestration.md` |
| **部署指南** | `brains/knowledge/04_deployment_operations/DEPLOYMENT_GUIDE.md` |
| **本機限制規範** | `brains/knowledge/04_deployment_operations/LOCAL_DEVELOPMENT_CONSTRAINTS.md` |
| **派工協議（權威）** | `brains/knowledge/01_agent_governance/SIMPLE_FILE_DISPATCH_PROTOCOL.md` |

---

## 2. 歷史手冊（已廢棄，僅供參考）

| 項目 | 說明 |
|------|------|
| `hq_ops/message_hub_operations.md` | Redis / Message Hub v3.0 時代操作（已廢除） |
| `hq_ops/init_thread.md` | 舊派工/自動化機制（已廢除） |
| `hq_ops/analyse_agent_report.md` | 原 `hq_gateway.py DecisionEngine` 自動判斷鏈（已廢除） |
| `ait/` | 早期 AIT 部署腳本手冊（歷史參考） |
| `owner_ops/` | 早期 Owner 部署範例 |
| `common/` | 早期通用派工/部署範例 |

> ⛔ 上述已廢棄機制包含：Redis Pub/Sub、Message Hub、`hq_gateway.py`、`core/`、`.taskbox`、`_agent/`。
> 現行唯一派工體系為 `.taskflow`。

---

*維護者：HQ*
