# 任務回報：建立 revenue_facts 場地複合索引

**回報時間**：2026-10-01 (台北時間)
**執行者**：Ina (Infra Master)
**任務 ID**：TASK_20261001_INA_REVENUE_FACTS_INDEX
**狀態**：✅ 完成並驗證通過
**關聯 commit**：`1ceeda4` (tg25-infra: `main`)

---

## 一、執行摘要

針對營運後台營運看板 (/statistics/dashboard) 載入遲緩問題，Ina 已在生產資料庫 `iotv9.revenue_facts` 建立複合索引 `idx_venue_valid_ts (venue_id, is_valid, event_ts)`。

- **資料庫**：Central DB (`iotv9` @ `141.148.165.50`)
- **目標表**：`revenue_facts` (資料量: 1,685,212 筆)
- **執行方式**：線上無鎖 DDL (`ALGORITHM=INPLACE, LOCK=NONE`)
- **DDL 耗時**：59.01 秒
- **連線與業務影響**：零鎖表、零中斷、連線健康

---

## 二、驗收結果

### 1. 索引確認 (SHOW INDEX FROM revenue_facts)

| Table | Non_unique | Key_name | Seq_in_index | Column_name | Collation | Cardinality |
|:---|:---|:---|:---|:---|:---|:---|
| revenue_facts | 1 | idx_venue_valid_ts | 1 | venue_id | A | 1 |
| revenue_facts | 1 | idx_venue_valid_ts | 2 | is_valid | A | 1 |
| revenue_facts | 1 | idx_venue_valid_ts | 3 | event_ts | A | 690064 |

### 2. EXPLAIN 查詢計畫與效能改善對比

以典型區間查詢為基準：
```sql
SELECT COUNT(*), SUM(amount) FROM revenue_facts 
WHERE venue_id = 1 AND is_valid = 1 
  AND event_ts >= DATE_SUB('2026-09-30 23:59:59', INTERVAL 7 DAY);
```

| 項目 | 索引建立前 | 索引建立後 | 改善幅度 |
|:---|:---|:---|:---|
| **命中索引 (key)** | `revenue_facts_venue_id_index` | `idx_venue_valid_ts` | 精準複合索引覆蓋 |
| **存取類型 (type)** | `ref` | `range` | 範圍掃描替代全場地掃描 |
| **預估掃描行數 (rows)** | 838,843 筆 | 19,334 筆 | **掃描量下降 97.7%** |
| **7 日聚合查詢耗時** | ~47.9 秒 (磁碟大量 I/O) | **0.20 秒** | **效能提速逾 200 倍** |
| **當日實時查詢耗時** | 數秒至十數秒 | **0.004 秒 (3.98ms)** | 幾乎無感 |

---

## 三、版本控管與倉庫同步

1. **SQL Migration**：
   - `PROJECT/Infra/db/migrations/20261001_add_idx_venue_valid_ts_to_revenue_facts.sql`
2. **自動化遷移腳本**：
   - `PROJECT/Infra/db/scripts/run_revenue_facts_index_migration.py`
3. **Git 同步狀態**：
   - 本地 commit `1ceeda4` 已 push 至 GitHub `origin/main`。
   - 遠端 Infra VPS (`/home/ubuntu/tg25-infra`) 已同步 `git pull origin main`。

---

## 四、協同與後續建議

1. **致 Sophie (Owner)**：
   - 資料庫層索引已就緒，今日/本週/本月範圍之 SQL 查詢延遲已從十數秒降至毫秒/次秒級。
   - 可接續執行 `TASK_20261001_SOPHIE_OPTIMIZE_DASHBOARD_PERF`，移除 `countTodayTransactions()` 額外呼叫與 Google Fonts 外部阻塞，並導入骨架屏。

---

**Ina (Infra Master) - 任務完成**

