# HQ 派工使用說明書 (.taskflow)

> **版本**: 2026-10-03 v2.0
> **維護者**: HQ
> **適用對象**: 所有 Agent (Sophie / Mina / Ina / Allie / Hubie / Fio / Coli / Sidney)

---

## 1. 派工管道總覽

本系統唯一派工管道為 **`.taskflow` 純檔案信箱**。

> ⛔ 舊版 `core/hq_task_flow.sh`、Redis Pub/Sub、`.taskbox/*.json`、`_agent/inbox` 已全面廢除。

```
Joe（使用者）
  ↓ 指令 / 截圖 / 問題描述
HQ（協調者）
  ↓ ./dev_tools/waw_ops.sh task <agent> <task_id> --file <工單.md> [priority]
  ↓
  └─ 寫入 .taskflow/<agent>/inbox/YYYYMMDD_HHMMSS_<task_id>.md
         ↓
     Agent 讀取 inbox → 執行 → 回報至 .taskflow/<agent>/outbox/
```

---

## 2. 目錄結構

```
.taskflow/
├── <agent>/          # owner / member / infra / alliance / ihub / fio / coli / signalhub
│   ├── inbox/        # HQ 派發給 Agent 的任務 (.md)
│   └── outbox/       # Agent 回報給 HQ 的結果 (.md)
├── archive/          # 封存區
└── task_flow.log     # 派工操作日誌
```

---

## 3. HQ 派發任務

```bash
cd /Users/ilawusong/Documents/WaW

# 短任務（指令列）
./dev_tools/waw_ops.sh task <Agent名稱> <task_id> "<描述>" [priority]

# 完整工單檔案（強烈推薦，防截斷）
./dev_tools/waw_ops.sh task <Agent名稱> <task_id> --file <工單檔案路徑> [priority]
```

**範例**：

```bash
./dev_tools/waw_ops.sh task Sophie TASK_20261003_FIX_LOGIN --file /tmp/task.md P1
```

---

## 4. Agent 回報任務

```bash
bash ../../dev_tools/agent_report_to_hq_v2.sh <Agent名稱> <回報檔案.md>
```

回報會被複製到 `.taskflow/<agent>/outbox/YYYYMMDD_HHMMSS_<Agent>.md`。

---

## 5. 相關權威文檔

- 派工協議：`brains/knowledge/01_agent_governance/SIMPLE_FILE_DISPATCH_PROTOCOL.md`
- 啟動協議：`brains/knowledge/01_agent_governance/AGENT_STARTUP_PROTOCOL.md`
- 快速指南：`brains/knowledge/01_agent_governance/TASKFLOW_QUICK_GUIDE.md`
- 目錄說明：`.taskflow/README.md`

---

**最後更新**：2026-10-03
