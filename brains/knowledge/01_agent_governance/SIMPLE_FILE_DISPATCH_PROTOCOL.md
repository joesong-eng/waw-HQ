# 純檔案系統派工與回報協議 (Simple File Dispatch Protocol)

> **版本**: 4.0.0  
> **建立日期**: 2026-08-16  
> **最後更新**: 2026-08-22  
> **狀態**: Active / Authoritative (權威標準)  
> **維護者**: HQ  
> **適用範圍**: 所有 Agent (Sophie, Mina, Ina, Allie, Hubie, Fio, Coli)

---

## 📋 核心架構

本專案自 2026-08-16 起全面統一至目錄 `/Users/ilawusong/Documents/WaW`。所有 Agent 間的通訊廢除 Redis Pub/Sub、HTTP API 及 Supervisor 常駐機制，全面改為**純檔案系統 (.taskflow) 信箱機制**。

### 1. 目錄結構

```
.taskflow/
├── owner/       # Sophie (Owner 專案)
│   ├── inbox/   # HQ 派發給 Sophie 的任務
│   └── outbox/  # Sophie 完成後的回報
├── member/      # Mina (Member 專案)
│   ├── inbox/
│   └── outbox/
├── infra/       # Ina (Infra 專案)
│   ├── inbox/
│   └── outbox/
├── alliance/    # Allie (Alliance 專案)
│   ├── inbox/
│   └── outbox/
├── ihub/        # Hubie (iHub 專案)
│   ├── inbox/
│   └── outbox/
├── fio/         # Fio (IOTkiosk_v0 專案)
│   ├── inbox/
│   └── outbox/
├── coli/        # Coli (IOTwawS3 專案)
│   ├── inbox/
│   └── outbox/
├── archive/     # 歷史任務封存區
└── task_flow.log# 派工與執行日誌
```

---

## 🚀 派工流程 (HQ 操作)

### 派工腳本
```bash
./scripts/hq_task_flow.sh task <Agent名稱> <task_id> "<任務描述>" [priority]
```

* **支援 Agent 別名**：
  * `Sophie` / `owner`
  * `Mina` / `member`
  * `Ina` / `infra`
  * `Allie` / `alliance`
  * `Hubie` / `ihub`
  * `Fio` / `fio`
  * `Coli` / `coli`

* **產出檔案**：
  `.taskflow/<agent_dir>/inbox/<YYYYMMDD_HHMMSS>_<task_id>.md`

---

## 📬 任務接收與回報流程 (Agent 操作)

### 1. Agent 檢查任務
Agent 啟動時讀取自己的 `.taskflow/<agent_dir>/inbox/` 目錄，按時間戳由舊至新處理未完成任務。

### 2. Agent 執行任務
嚴格遵守 `LOCAL_DEVELOPMENT_CONSTRAINTS.md`：
* 本機僅作代碼修改與 Git 操作
* 測試與驗證透過遠端 VPS 執行

### 3. Agent 提交回報
Agent 在專案內撰寫好 Markdown 報告後，透過回報腳本送交 HQ：
```bash
# 從專案目錄執行
bash ../../scripts/agent_report_to_hq_v2.sh <Agent名稱> <報告檔案路徑.md>
```
* 腳本將報告自動複製到 `.taskflow/<agent_dir>/outbox/<YYYYMMDD_HHMMSS>_<Agent名稱>.md`。

---

## 📝 回報格式規範

```markdown
# 任務回報：<TASK_ID>

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：<Agent名稱>

## 執行結果
1. 項目一...
2. 項目二...

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：<Agent名稱>  
**回報時間**：YYYY-MM-DD HH:MM
```



---

## 🔄 Agent 向 HQ 回報問題或提問

> **新增日期**: 2026-09-08  
> **適用場景**: 技術問題諮詢、跨 Agent 協調需求、架構決策請求

### 核心原則

**每個 Agent 只能寫入自己的 outbox，不能寫入其他 Agent 的 inbox（包括 HQ）**

### 正確流程

#### 1. Agent 在自己的 outbox 提交問題

**目標目錄**：`.taskflow/<agent>/outbox/`

**檔案命名規範**：
```
QUESTION_<YYYYMMDD>_<AGENT>_TO_HQ_<BRIEF_TOPIC>.md
```

**範例**：
```
.taskflow/signalhub/outbox/QUESTION_20260908_SIDNEY_TO_HQ_SIGNAL_TYPE_AGGREGATION.md
.taskflow/owner/outbox/QUESTION_20260908_SOPHIE_TO_HQ_DATABASE_MIGRATION.md
```

#### 2. HQ 讀取 Agent 的 outbox

HQ 定期檢查各 Agent 的 outbox，發現 QUESTION 類型文件後：
- 協調相關 Agent
- 查閱技術標準與知識庫
- 做出決策

#### 3. HQ 回覆方式

**選項 A：在 HQ 自己的 outbox 發布正式回覆**
```
.taskflow/hq/outbox/ANSWER_<YYYYMMDD>_HQ_<BRIEF_TOPIC>.md
```

**選項 B：直接派工到 Agent 的 inbox**
```
./dev_tools/waw_ops.sh task <agent> <task_id> "<描述>" [priority]
→ 產生：.taskflow/<agent>/inbox/TASK_xxx.md
```

#### 4. 知識庫歸檔

重要的技術決策同步歸檔至：
```
brains/knowledge/02_technical_standards/
brains/knowledge/03_system_architecture/
brains/knowledge/05_business_flows/
```

---

### 流程圖

```
┌────────┐
│ Sidney │ 發現技術問題
└───┬────┘
    │
    ├──→ 寫入自己的 outbox：
    │    .taskflow/signalhub/outbox/QUESTION_xxx.md
    │
┌───▼────┐
│   HQ   │ 讀取 Sidney 的 outbox，協調與決策
└───┬────┘
    │
    ├──→ 選項 A：發布回覆到 HQ outbox
    │    .taskflow/hq/outbox/ANSWER_xxx.md
    │
    ├──→ 選項 B：直接派工到 Sidney inbox
    │    .taskflow/signalhub/inbox/TASK_xxx.md
    │
    └──→ 知識庫歸檔：
         brains/knowledge/02_technical_standards/
```

---

### 範例場景（2026-09-08 UI2 信號語義問題）

1. ✅ Sidney 發現問題，寫入自己的 outbox：
   `.taskflow/signalhub/outbox/QUESTION_20260908_SIDNEY_TO_HQ_SIGNAL_TYPE_AGGREGATION.md`

2. ✅ HQ 讀取後協調 Coli 確認韌體，發布正式回覆：
   `.taskflow/hq/outbox/ANSWER_20260908_HQ_SIGNAL_TYPE_AGGREGATION_BEHAVIOR.md`

3. ✅ 歸檔至知識庫：
   `brains/knowledge/02_technical_standards/WAW_SIGNAL_SEMANTIC_SPECIFICATION.md`

4. ✅ 派工給 Sidney 更新文檔：
   `.taskflow/signalhub/inbox/TASK_20260908_SIDNEY_UPDATE_SIGNAL_SEMANTIC_DOCS.md`

---

## 📊 統計與監控

`.taskflow/task_flow.log` 記錄所有派工、回報與技術諮詢的時間戳與狀態。


---

## 4. Shannie (Executive Assistant) 協作標準規範

### 4.1 定位與原則
- **角色**：Executive Assistant / Strategic Advisor to JOE，不承接具體程式碼實作。
- **通道設計**：採「非同步信箱優先（Inbox/Outbox Pattern）」原則。MCP 為高速通道，非唯一通道；即便遠端 Tunnel 斷線，亦不影響整體協作進程。

### 4.2 標準任務訊息格式 (Frontmatter 規範)
Shannie 發至 `.taskflow/shannie/outbox/` 的檔案命名為 `YYYYMMDD_HHMMSS_<TOPIC>.md`，開頭必須包含標準 Frontmatter：

```markdown
---
from: Shannie
to: HQ
type: task | decision | feedback
date: YYYY-MM-DD
priority: high | normal | low
status: pending
---

# 任務/決策標題

## 背景
...

## 需求
...

## 建議處理方式
...

## 預期輸出
...
```

### 4.3 HQ 處理與流轉協議
1. **讀取**：HQ 定期或依通知檢查 `.taskflow/shannie/outbox/`。
2. **分派**：若屬技術實作需求，由 HQ 轉化為工程工單派發至 Sophie / Mina / Ina 等對應 Agent。
3. **歸檔**：處理完成之任務標記為 `status: completed`，並封存至 `.taskflow/shannie/archive/`。

---

## 🔒 結案與歸檔協議 (Case Closing & Archival SOP)

> **生效日期**: 2026-09-30  
> **權威標準**: 所有工單/報告必須有明確終點，禁止無限制滯留於 inbox/outbox。

### 1. 工單兩大類型

| 類型 | 代號 | 發起者 | 受文者 | 內容 | 終點處理 |
|:---|:---:|:---:|:---:|:---|:---|
| **任務工單** | `TASK` | HQ | Agent | 具體任務要求、驗收標準 | Agent 提交回報帶遠端證據 ➔ HQ 驗收通過 ➔ **HQ 結案歸檔** |
| **主動報告 / 提案** | `REPORT` / `PROPOSAL` | Agent | HQ | 架構盤點、問題諮詢、跨 Agent 協調請求 | HQ 審閱確認 ➔ 填寫決策結論 ➔ **HQ 結案歸檔**；若需後續行動，由 HQ 拆開新 `TASK` |

### 2. 鋼鐵原則（零滯留）

1. **唯一結案權**：只有 **HQ**（在審核或 Joe 批准後）有權將工單結案歸檔。**Agent 嚴禁自行歸檔**。
2. **星狀派發，禁止私相授受**：所有任務流向皆為 `HQ ↔ Agent`。Agent 需要其他 Agent 配合時，向 HQ 提交提案/問題，由 HQ 另起獨立任務派發。
3. **當日結案原則**：
   - 任務回報經 HQ 驗證合格者，HQ 應立即執行結案歸檔。
   - 主動報告經 HQ 審閱並決定分流後，原報告立即結案歸檔，不得在原報告內疊加後續開發進度。
4. **歸檔指令**：全面使用 `./dev_tools/waw_ops.sh close <agent|hq> <filename_or_keyword>` 執行標準化歸檔。


### 3. ⚠️ Agent 必知：歸檔 ≠ 遺失（認知更新 2026-09-30）

> **背景**：曾發生 Agent 誤判「回報被移至 archive = 系統故障/未送達」，並手動重複補送，造成混亂。

| 狀況 | 正確解讀 | 錯誤行為 |
|:---|:---|:---|
| 自己的 outbox 文件消失 | HQ 已驗收並執行結案歸檔，任務**成功完成** | ❌ 以為遺失，手動複製到 hq/inbox |
| `.taskflow/archive/` 出現工單 | HQ 主動封存，流程正常 | ❌ 誤判為錯誤，企圖回滾 |
| hq/inbox 已無該工單 | HQ 已處理完畢 | ❌ 重複補送同份報告 |

**Agent 行動準則**：
1. 回報送出後，等待 HQ 回覆新 TASK 或確認訊息。
2. 若不確定任務是否送達，查 `.taskflow/archive/` 確認，而非重複補送。
3. **嚴禁手動複製文件到其他 Agent 或 hq 的 inbox**，此舉繞過派工協議。
4. 有疑慮：向 HQ 提交一份 `REPORT` 詢問，等待 HQ 回覆。

