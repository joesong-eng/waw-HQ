# 任務提報：營運看板（statistics.dashboard）載入遲緩根本原因與跨組優化協調

**提報日期**：2026-10-01
**提報者**：Sophie (Owner 後台守護者)
**接收者**：HQ / 協同人員 (Ina, Sophie)
**優先級**：P1 (影響日常營運體驗)
**關聯模組**：Owner (iot.tg25.win), Infra (iotv9 / 141.148.165.50)

---

## 一、問題現象
營運商反饋：點擊「營運看板」(`/statistics/dashboard`) 頁面響應極為遲緩，出現長時間白屏才載入完成。

---

## 二、技術定位與根本原因

1. **資料庫層（Ina 權責）：巨量資料表缺乏場地複合索引（最大瓶頸）**
   - 資料表：`iotv9.revenue_facts`（原始脈衝交易流水，逾 130 萬筆）。
   - 現況：現有唯一複合索引為 `idx_device_ts_type (device_id, event_ts, transaction_type, is_valid)`。
   - 衝突：營運看板核心查詢全部為 `WHERE venue_id IN (...) AND is_valid = 1 AND event_ts BETWEEN ...`。
   - 後果：目前僅能走單欄 `venue_id` 或 `event_ts` 索引，在百萬級資料量下進行範圍過濾與聚合計算，引發大量磁碟 I/O 與慢查詢。

2. **應用層（Sophie 權責）：跨主機串行查詢 + 脫靶查詢**
   - 跨主機 RTT 累積：Web 主機在 `yd174`，資料庫在 `infra` (141.148.165.50)。快取失效時，單一請求串行執行多達 8~10 次跨網 SQL 查詢。
   - 脫靶未快取查詢：`StatisticsController.php` 中 `countTodayTransactions()` 寫在 `getDashboardData()` 快取閉包外，即使看板其餘資料已有快取，每次重新整理仍強制全表掃描 `revenue_facts`。

3. **前端層（Sophie 權責）：同步 SSR + 外部阻塞資源**
   - 頁面未採用骨架屏（Skeleton）， Controller 必須同步等所有 SQL 算完才回傳 HTML。
   - `dashboard.blade.php` 內存在 `@import url('https://fonts.googleapis.com/...');` 外部阻塞下載。

---

## 三、人員分工與派工建議

### 1. Ina (Infra) — 資料庫複合索引建立
- **任務 ID**：`TASK_20261001_INA_REVENUE_FACTS_INDEX`
- **執行內容**：
  在 `iotv9.revenue_facts` 上建立複合索引：
  ```sql
  CREATE INDEX idx_venue_valid_ts ON revenue_facts (venue_id, is_valid, event_ts);
  ```
- **驗收標準**：
  - `SHOW INDEX FROM revenue_facts;` 確認包含 `idx_venue_valid_ts`。
  - `EXPLAIN SELECT ... FROM revenue_facts WHERE venue_id IN (1) AND is_valid = 1 AND event_ts BETWEEN ...` 確認命中該索引且 rows 大幅下降。

### 2. Sophie (Owner) — 程式碼與架構優化
- **任務 ID**：`TASK_20261001_SOPHIE_OPTIMIZE_DASHBOARD_PERF`
- **執行內容**：
  1. **收斂重複查詢**：移除 `countTodayTransactions()` 額外 SQL，直接複用 `today` 統計中已計算好的 `transaction_count`，並納入快取。
  2. **消除前端阻塞**：移除 `@import` Google Fonts，改為本地字體或非阻塞載入。
  3. **非同步架構升級**：比照 `quick-dashboard` 模式，將全量報表改為骨架屏 + Ajax 異步載入，徹底解決白屏體驗。

---

請 HQ 審閱並批准派工。

