# 任務：TASK_20261002_SOPHIE_VERIFY_M7_SETTLEMENT_PIPELINE

**派發時間**：2026-10-02
**優先級**：P0 / Critical（財務月結算全流程打通）
**負責人**：Sophie (Owner)
**關聯模組**：Owner (iot.tg25.win / yd174)
**前置條件**：Ina 已完成 Central DB `settlements` / `settlement_logs` / `daily_revenue_reports` 三表 M7 標準 Schema 對齊（Commit `7ae0925`）。

---

## 📌 任務背景與目的
Ina 已於 Central DB 完成 M7 結算三表重建與外鍵規範（RESTRICT/SET NULL）。
Sophie 需接續打通 M7 月結算程式碼邏輯層，修復報表來源與機台分組，並補跑 2026-09 月結算單，完成全流程端到端驗收。

---

## 📋 具體執行項目

### 1. 報表來源與機台級日報對齊（關鍵邏輯層）
- **現狀問題**：
  - M7 `SettlementService::generateMonthlySettlements()` 依賴 `DailyRevenueReport` 的 `groupBy('device_id')` 與機台分潤計算。
  - 目前 `RebuildDailyReports`（`revenue:rebuild-reports`）僅按 `venue_id + local_date` 聚合，未記錄 `device_id`。
- **改善需求**：
  - 調整或擴充 `DailyRevenueReport` 生成機制（或提供帶 `device_id` 的補帳/聚合選項），確保結算週期內的營收日報具備對應機台關聯。
  - 同步確保 venue 級排程（如 nightly 對帳）不受干擾（Ina 已將 `device_id` 設為 nullable）。

### 2. 補跑與驗證 2026-09 月結算單
- **執行方式**：
  - 重試先前失敗的 Queue Job（Job ID: `a67ee6ce-4c7f-4020-b852-81cb38cda689`），或透過 Artisan / 控制台呼叫生成 2026-09 月度結算單。
- **驗證項目**：
  - `settlements` 表成功寫入 2026-09 週期結算單資料（非 0 筆）。
  - `settlement_logs` 表正常記錄狀態流轉與操作日誌。
  - 結算單各項拆帳金額（設備主分潤、場地主分潤、稅前支出）計算無誤。

### 3. 前端介面與端點端到端驗收
- 登入測試驗證 `/settlements/statements` 頁面：
  - 列表正常讀取並渲染結算單數據卡與表格。
  - 原「載入結算單失敗：Server Error」彈窗徹底消除。
- 測試結算單詳情頁與狀態流轉按鈕（如查看、確認等）功能正常。

---

## 🚀 部署與回報標準
1. 代碼修改 Commit 並推送至 `origin/main`。
2. 執行遠端部署（`waw_ops.sh deploy owner`）。
3. 提供實測證據（SQL 查詢結算單筆數、Laravel Log 無錯誤、前端頁面載入正常回應）。
4. 完成後回報至 `.taskflow/owner/outbox/`。

