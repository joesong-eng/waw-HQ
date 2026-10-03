# 任務：TASK_20261001_SOPHIE_OPTIMIZE_DASHBOARD_PERF

**派發時間**：2026-10-01
**優先級**：P1
**負責人**：Sophie (Owner)
**關聯模組**：Owner (iot.tg25.win / yd174)

---

## 任務背景與目的
配合 Ina 建立 `revenue_facts` 複合索引，進行後台應用層與前端渲染優化，徹底消除營運看板載入慢與白屏問題。

---

## 具體執行項目
1. **收斂脫靶與重複查詢**：
   - 檢查 `StatisticsController.php`，移除快取閉包外的 `countTodayTransactions()` 額外 SQL。
   - 複用 `today` 統計已計算之 `transaction_count`，統一納入快取保護。
2. **消除外部阻塞資源**：
   - 檢查 `dashboard.blade.php`，移除 `@import` Google Fonts 外部阻塞，改為本地字體或非阻塞載入。
3. **架構升級（骨架屏 + 異步載入）**：
   - 比照 `quick-dashboard` 模式，改為先渲染骨架屏（Skeleton），再由 Ajax/Fetch 異步載入數據填入圖表與數據卡，防止長時間白屏。
4. **部署與驗證**：
   - 本地 Commit 並推送。
   - 遠端 `yd174` 更新並清快取，驗證 HTTP 響應時間與介面渲染正常。
   - 完成後回報至 `.taskflow/owner/outbox/`。
