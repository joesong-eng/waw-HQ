# .taskflow - 派工系統目錄

**建立日期**：2026-08-16  
**維護者**：HQ (Hera)

---

## 目錄結構

```
.taskflow/
├── <agent>/
│   ├── inbox/     # HQ 派發給 Agent 的任務
│   └── outbox/    # Agent 回報給 HQ 的結果
├── archive/       # 封存的舊檔案
└── task_flow.log  # 派工操作日誌
```

---

## Agent 路徑映射

| Agent 名稱 | 目錄名稱 | 專案 |
|-----------|---------|------|
| Sophie | owner | Owner 營運商後台 |
| Mina | member | Member 玩家前端 |
| Ina | infra | Infra 基礎設施 |
| Allie | alliance | Alliance 供應商代理商 |
| Hubie | ihub | iHub Android APK |
| Fio | fio | IOTkiosk_v0 兌幣卡 |
| Coli | coli | IOTwawS3 遊戲採集卡 |

---

## 使用方式

### HQ 派發任務

```bash
cd /Users/ilawusong/Documents/WaW
./scripts/hq_task_flow.sh task <Agent名稱> <task_id> "<描述>" [priority]
```

**範例**：
```bash
./scripts/hq_task_flow.sh task Sophie FIX_BUG_001 "修復登入問題" high
```

任務會被寫入到：`.taskflow/owner/inbox/YYYYMMDD_HHMMSS_FIX_BUG_001.md`

---

### Agent 回報任務

```bash
./scripts/agent_report_to_hq_v2.sh <Agent名稱> <回報檔案.md>
```

**範例**：
```bash
# 1. Agent 先創建回報檔案
cat > /tmp/report.md << 'EOF'
# 任務回報：FIX_BUG_001

**完成時間**：2026-08-16 15:30  
**執行者**：Sophie

## 執行結果
已成功修復登入問題...

## 結論
✅ 完成
EOF

# 2. 使用腳本提交回報
./scripts/agent_report_to_hq_v2.sh Sophie /tmp/report.md
```

回報會被複製到：`.taskflow/owner/outbox/YYYYMMDD_HHMMSS_Sophie.md`

---

## 檔案格式

### 任務檔案 (inbox)

```markdown
# 任務：<task_id>

**派發時間**：YYYY-MM-DD HH:MM  
**優先級**：high/medium/low  
**負責人**：<Agent名稱>

---

## 📋 任務內容

<任務描述>

---

**派發者**：HQ  
**派發時間**：YYYY-MM-DD HH:MM
```

### 回報檔案 (outbox)

```markdown
# 任務回報：<task_id>

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：<Agent名稱>

## 執行結果
<執行內容>

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：<Agent名稱>  
**回報時間**：YYYY-MM-DD HH:MM
```

---

## 日誌檔案

派工操作會記錄到 `task_flow.log`：

```
[2026-08-16 19:03:43] ✅ 任務已派發：Sophie (owner) → /path/to/task.md
```

---

## 封存說明

- `archive/inbox_legacy_20260816/` - 舊 HQ inbox (2026-08-16 前)
- `archive/outbox_legacy_20260816/` - 舊 HQ outbox (2026-08-16 前)
- `archive/test_tasks_20260816/` - 測試任務封存

---

## 相關文檔

- 派工協議：`brains/knowledge/01_agent_governance/SIMPLE_FILE_DISPATCH_PROTOCOL.md`
- 啟動協議：`brains/knowledge/01_agent_governance/AGENT_STARTUP_PROTOCOL.md`
- 測試報告：`TEST_REPORT_20260816.md`

---

**最後更新**：2026-08-16  
**版本**：v2.0 (檔案系統派工)

