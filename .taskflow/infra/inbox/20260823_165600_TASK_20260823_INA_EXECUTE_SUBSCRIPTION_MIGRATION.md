# 任務：TASK_20260823_INA_EXECUTE_SUBSCRIPTION_MIGRATION

**派發時間**：2026-08-23 16:56  
**優先級**：high  
**負責人**：Ina

---

## 📋 任務內容

### 【正式執行工單】執行 WAW 2.0 訂閱與雙所有權 DB Migration 及程式碼適配

HQ 與 Joe 已正式核准 Ina 的評估報告與執行方案。請 Ina 依規劃執行下列工作：

---

### 一、任務步驟

#### 1. 程式碼適配（優先執行，確保相容）
- 修改 `profit_sharing_service.py` 中的 `get_machine_info` 查詢：
  - 改為：`COALESCE(d.machine_owner_id, d.owner_id) as machine_owner_id, d.collector_owner_id`
  - 保證在 Migration 執行前、中、後均能平滑過渡且讀取到正確的分潤接收人。

#### 2. 建立 Migration SQL 腳本
- 於 `PROJECT/Infra/db/migrations/` 建立 Migration 檔案（如 `20260823_waw2_subscription_and_dual_ownership.sql`）：
  - **Step A**: `devices` 表新增 `collector_owner_id` 與 `machine_owner_id` 欄位及對應索引。
  - **Step B**: 安全回填資料：將現有 16 筆記錄之 `collector_owner_id` 與 `machine_owner_id` 設為 `owner_id`。
  - **Step C**: 建立 `subscriptions` 表（支援多態 target_id、自選 JSON 清單、級距碼 tier_code）。
  - **Step D**: 建立 `billing_cycles` 表（支援按日折算月結明細、寬限期、外鍵關聯 subscriptions）。
  - **Step E**: 擴充 `billing_requests` 表（新增 service_type, target_ids, target_started_ats, tier_code, unit_price, quantity 等欄位）。

#### 3. 執行 Migration 並驗證
- 在生產環境 / 遠端 VPS 執行該 Migration。
- 驗證資料庫結構與回填資料（16 筆 devices 是否正確賦值）。
- 驗證 `subscriptions`、`billing_cycles`、`billing_requests` 表結構與索引狀態。

#### 4. 更新 DB_MANIFEST.md
- 更新 `PROJECT/Infra/DB_MANIFEST.md`，記載本次新增的資料表、欄位與 Migration 歷史。

---

### 二、產出要求
- 完成後透過 `agent_report_to_hq_v2.sh` 提交完整回報。
- 回報內請附上 Migration 執行日誌、回填筆數確認及各表 DESCRIBE / SHOW CREATE TABLE 摘要。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260823_INA_EXECUTE_SUBSCRIPTION_MIGRATION

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：Ina

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：Ina  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-08-23 16:56
