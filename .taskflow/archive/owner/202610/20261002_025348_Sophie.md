# 任務回報：TASK_20261002_SOPHIE_VERIFY_M7_SETTLEMENT_PIPELINE

- **任務 ID**：TASK_20261002_SOPHIE_VERIFY_M7_SETTLEMENT_PIPELINE
- **執行者**：Sophie (Owner)
- **完成時間**：2026-10-02
- **狀態**：✅ 完成 (Completed)

---

## 1. 執行項目與問題修復

### 1.1 報表來源與機台級日報對齊
- **排除無機台報表與空分組**：
  - 修正 `app/Services/SettlementService.php`：
    - `DailyRevenueReport` 查詢時加上 `->whereNotNull('device_id')`，避免將場地加總報表（`device_id = null`）誤納入機台分潤計算。
    - `groupBy()` 分組集合過濾條件加嚴 `->filter(fn ($val, $key) => !empty($key))`，徹底防禦 `owner_id on null` 異常。
- **補全路由名稱相容**：
  - 修正 `routes/web.php`：將 `settlements/{id}` 命名為 `settlements.show`，滿足 `SettlementService` 內部通知產生詳情連結的需求。

### 1.2 月結算 Queue Job 容錯修正
- **修正 `app/Jobs/GenerateMonthlySettlements.php`**：
  - `SettlementService::generateMonthlySettlements()` 回傳型別為 `array`，將呼叫處的 `$settlements->count()` 與 `$settlements->sum('total_revenue')` 改為原生陣列函式 `count($settlements)` 與 `array_sum()`，避免型別報錯。

---

## 2. 部署與版本記錄
- **Git Commit**：
  - `0cd5976` - `fix(m7): 結算服務排除無機台報表、修復月結算日誌陣列統計與結算單路由名稱`
  - `e6de012` / `fba620c` - 清理暫存檔
- **遠端部署**：
  - 執行 `../../dev_tools/waw_ops.sh deploy owner`，成功部署至 `yd174` (`/www/wwwroot/iot.tg25.win`)。
  - Vite 前端資源編譯正常完成。

---

## 3. 實測驗證佐證

### 3.1 資料庫數據快照
- **2026-09 週期結算單寫入結果**：
  - `settlements` 表成功寫入 2 筆結算單：
    - 結算單 1：`STL-202609-1-2`（西門旗艦店），總營收 NT$ 151,902.00，機台主分潤 NT$ 151,902.00，場地主分潤 NT$ 0.00，狀態 `created`。
    - 結算單 2：`STL-202609-2-2`（台中一中店），總營收 NT$ 90,692.00，機台主分潤 NT$ 90,692.00，場地主分潤 NT$ 0.00，狀態 `created`。
- **審計日誌**：
  - `settlement_logs` 表正常記錄 `created` 狀態日誌，`user_id` 為 `NULL`，符合外鍵規範。

### 3.2 端點端到端驗收
- **API 列表端點**：
  - `GET /api/v9/settlements` 回應 HTTP 200，成功回傳 2 筆結算單與分頁資訊。
- **API 詳情端點**：
  - `GET /api/v9/settlements/2` 回應 HTTP 200，成功讀取設備分解明細（`device_breakdown`）與相關擁有者資料。
- **Web 端點**：
  - 首頁及登入頁 HTTP 200。
  - 前端結算單管理頁面 (`/settlements/statements`) 載入成功，原「載入結算單失敗：Server Error」彈窗徹底消除。

