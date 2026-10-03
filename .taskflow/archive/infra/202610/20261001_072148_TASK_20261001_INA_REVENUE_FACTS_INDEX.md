# 任務：TASK_20261001_INA_REVENUE_FACTS_INDEX

**派發時間**：2026-10-01
**優先級**：P1
**負責人**：Ina (Infra)
**關聯模組**：Infra / iotv9 資料庫 (141.148.165.50)

---

## 任務背景與目的
營運後台「營運看板」(/statistics/dashboard) 載入遲緩。經 Sophie 定位，主要瓶頸為百萬級交易資料表 `iotv9.revenue_facts` 缺乏場地複合索引，導致範圍查詢與聚合計算引發嚴重慢查詢。

---

## 具體執行項目
1. **建立複合索引**：
   在 `iotv9.revenue_facts` 建立索引：
   ```sql
   CREATE INDEX idx_venue_valid_ts ON revenue_facts (venue_id, is_valid, event_ts);
   ```
   *(注意線上 DDL 執行效率與連線健康)*

2. **驗收標準**：
   - `SHOW INDEX FROM revenue_facts;` 確認包含 `idx_venue_valid_ts`。
   - 執行 `EXPLAIN` 驗證典型查詢（如 `WHERE venue_id IN (1) AND is_valid = 1 AND event_ts BETWEEN ...`）確實命中此索引，rows 顯著下降。
   - 記錄 DDL 耗時與驗證結果。

3. **版本控管與同步**：
   - 將對應 migration 或腳本紀錄納入 `PROJECT/Infra` 倉庫。
   - 完成後回報至 `.taskflow/infra/outbox/`。
