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

