# Agent 協作協定

> **文件類型**：協作規範  
> **適用範圍**：所有 Agent  
> **維護者**：HQ

---

## 🎯 協作原則

### 1. 專業分工，互不越權
- 每個 Agent 只負責自己專案的代碼
- 需要跨專案協作時，透過 HQ Message Hub 溝通
- 不要擅自修改其他 Agent 的代碼

### 2. 知識共享，統一規範
- 技術標準由 HQ 統一維護
- Agent 需遵守 `brains/knowledge/` 中的所有規範
- 發現規範問題，透過 HQ Message Hub 提出

### 3. 透明溝通，記錄完整
- 所有決策與變更需記錄
- 重要討論需存檔到 `brains/history/`
- 使用 HQ Message Hub 確保訊息可追蹤

---

## 📡 通訊方式

### HQ Message Hub（Redis Pub/Sub，v3.0 現行架構）

**核心機制**：Redis Pub/Sub + `hq_gateway.py`（launchd 常駐）

**優點**：
- ✅ 即時推送，Agent 無需輪詢
- ✅ 自動觸發 `codex exec` 執行任務
- ✅ 有記錄，所有訊息存檔可追蹤

**HQ 發布任務（唯一正確方式）**：
```bash
./scripts/hq_task_flow.sh task <agent> <task_id> "<description>" [priority]
```

> ❌ 禁止使用 `hq_send_task_via_hub.sh`（只寫檔案，不觸發 Redis）
> ❌ 禁止使用 `hq_publish_and_trigger.sh`（繞過 Redis）

**Agent 回報完成**：
```bash
bash ../HQ/scripts/agent_report_to_hq_v2.sh <agent_name> <report_file> ../HQ
```

**詳細文檔**：
- 權威協定：`MESSAGE_HUB_PROTOCOL.md`（v3.0）
- 部署細節：`MESSAGE_HUB_V2_DEPLOYMENT.md`

---

## 🔄 協作流程

### 典型場景 1：跨專案功能開發

**情境**：Sophie 需要 Ina 新增一個 API

1. **Sophie 提需求**
   ```bash
   bash ../HQ/scripts/agent_report_to_hq_v2.sh sophie _agent/API_REQUEST.md ../HQ
   ```

2. **HQ 審核需求**
   - 確認需求合理性
   - 確認資料來源與邊界
   - 分配任務給 Ina

3. **HQ 發布任務給 Ina**
   ```bash
   ./scripts/hq_task_flow.sh task ina TASK_001 "新增 XXX API" high
   ```

4. **Ina 啟動時自動收到任務**
   - 系統自動執行 `agent_check_hq.sh ina`
   - 任務存入 `_agent/INBOX_*.json`

5. **Ina 完成後回報**
   ```bash
   bash ../HQ/scripts/agent_report_to_hq_v2.sh ina _agent/TASK_001_REPORT.md ../HQ
   ```

6. **HQ 通知 Sophie**
   - HQ 查看收件匣
   - 通知 Sophie API 已就緒

### 典型場景 2：資料庫變更

參考 `DB_MIGRATION_WORKFLOW.md`

### 典型場景 3：技術規範更新

**情境**：Coli 發現 MQTT 主題命名有問題

1. **Coli 提出問題**
   ```bash
   bash ../HQ/scripts/agent_report_to_hq_v2.sh coli _agent/MQTT_TOPIC_ISSUE.md ../HQ
   ```

2. **HQ 審核並更新規範**
   - 檢查問題是否影響其他 Agent
   - 更新 `brains/knowledge/02_technical_standards/MQTT_TOPIC_STANDARD.md`
   - 記錄變更歷史

3. **HQ 通知所有相關 Agent**
   ```bash
   ./scripts/hq_task_flow.sh task sophie STANDARD_UPDATE "MQTT 主題規範已更新" normal
   ./scripts/hq_task_flow.sh task ina STANDARD_UPDATE "MQTT 主題規範已更新" normal
   ```

---

## 📋 回報格式

### 任務完成回報

```markdown
# Agent XXX 任務回報

> **任務 ID**：TASK_YYYYMMDD_XXX  
> **回報時間**：YYYY-MM-DD HH:MM  
> **狀態**：已完成 / 進行中 / 遇到問題

## 完成項目
- ✅ 項目 1
- ✅ 項目 2

## 遇到的問題
（如有）

## 需要協助的事項
（如有）

---
*回報人：XXX Agent*
```

### 技術問題回報

```markdown
# 技術問題回報

> **提報者**：XXX Agent  
> **日期**：YYYY-MM-DD  
> **優先級**：High/Normal/Low

## 問題描述
<詳細描述遇到的問題>

## 重現步驟
1. ...
2. ...

## 預期行為
<應該是怎樣的？>

## 實際行為
<現在是怎樣的？>

## 建議解決方案
（如有）
```

---

## ⚠️ 注意事項

1. **不要直接修改知識庫**
   - 只有 HQ 有寫入權限
   - Agent 需透過 HQ Message Hub 提交更新

2. **不要跳過 HQ 直接協作**
   - 避免資訊不同步
   - 確保所有決策有記錄

3. **不要假設其他 Agent 的狀態**
   - 需要確認時，透過 HQ Message Hub 詢問
   - 不要猜測或假設

---

## 🔗 相關文件

- `MESSAGE_HUB_PROTOCOL.md` - HQ Message Hub 協定
- `DB_MIGRATION_WORKFLOW.md` - 資料庫變更流程
- `AGENT_EXECUTION_PROTOCOL.md` - Agent 執行規範
- `../../../README_MESSAGE_HUB.md` - HQ Message Hub 使用說明
- `../../../SHARED_MESSAGE_HUB_GUIDE.md` - Agent 通訊指南（公用）

---

**維護者**：HQ  
**最後更新**：2026-06-09
