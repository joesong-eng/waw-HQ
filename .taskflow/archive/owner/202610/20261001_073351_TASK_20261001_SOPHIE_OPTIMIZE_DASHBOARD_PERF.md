# 任務：TASK_20261001_SOPHIE_OPTIMIZE_DASHBOARD_PERF

**派發時間**：2026-10-01
**優先級**：P1 / high
**負責人**：Sophie (Owner)
**來源**：HQ 協調派發（銜接 Ina TASK_20261001_INA_REVENUE_FACTS_INDEX 驗收成果）

---

## 📌 前置狀態確認
- **Ina (Infra)** 已於生產 Central DB (`iotv9.revenue_facts`) 完成無鎖線上建立複合索引 `idx_venue_valid_ts (venue_id, is_valid, event_ts)`（Commit `1ceeda4`）。
- 效能實測：7 日範圍查詢由 47.9s 降至 0.20s（行數掃描降 97.7%），當日查詢僅 3.98ms。資料庫端瓶頸已完全解除。

---

## 📋 任務執行內容

### 1. 收斂重複 SQL 查詢與快取優化
- 檢查 `StatisticsController.php`：
  - 移除位於 `getDashboardData()` 快取閉包外的 `countTodayTransactions()` 額外呼叫。
  - 直接複用 `today` 統計中已計算好的 `transaction_count`，確保不再觸發脫靶的全表掃描。
  - 確認跨日/當日資料快取 TTL 設定合理。

### 2. 消除前端外部資源阻塞
- 檢查 `dashboard.blade.php`：
  - 移除 `@import url('https://fonts.googleapis.com/...');` 外部阻塞下載。
  - 改用系統字型族（system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto 等）或非阻塞非同步加載，避免外部網路延遲導致頁面渲染中斷。

### 3. 非同步骨架屏 (Skeleton) 架構升級
- 比照 `quick-dashboard` 模式：
  - 首屏渲染骨架屏佔位，第一時間呈現框架，杜絕白屏。
  - 圖表與聚合指標改為 Ajax / Fetch 異步載入填充。

---

## 🚀 驗收與部署標準
1. 程式碼修改完成後，以 Git 提交並推送至 GitHub。
2. 執行遠端部署（`yd174` / `iot.tg25.win`），清除應用快取 (`php artisan optimize:clear`)。
3. 驗證 `/statistics/dashboard` 首屏響應時間與網路請求瀑布流，無阻塞外部資源，回報驗收指標。

---

## 📝 回報格式
回報存於 `.taskflow/owner/outbox/`：
```markdown
# 任務回報：TASK_20261001_SOPHIE_OPTIMIZE_DASHBOARD_PERF

**完成時間**：YYYY-MM-DD HH:MM
**執行者**：Sophie
**關聯 commit**：<commit_hash>

## 執行結果
1. SQL 與快取優化
2. 前端字體阻塞移除
3. 骨架屏與 Ajax 異步化
4. 遠端部署與驗證指標

## 結論
✅ 完成
```

