# 任務工單：TASK_20260930_SOPHIE_FIX_M7_ROUTES_AND_M6_SECURITY

**派發時間**：2026-09-30 01:50 (台北時間)  
**優先級**：P0 (緊急安全與功能修復)  
**指派對象**：Sophie (Owner Agent)  
**驗收人**：HQ / Joe

---

## 🎯 任務目標

根據 2026-09-30 模組完成度審核結果，修復 Owner 後台 (iot.tg25.win) 兩大實質 P0 缺陷：
1. **M7 對帳結算**：補齊 `routes/api.php` 缺漏的 8 條 Settlement API 路由，打通前端與 `SettlementController`。
2. **M6 報表鎖定**：於 `ReportController::lockAll()` 實裝 Admin 權限門禁，防止非管理者非法觸發。

---

## 📋 具體實作要求

### 一、M7 Settlement 路由掛載 (`routes/api.php`)
在 `routes/api.php` 的 `auth:sanctum` (或系統對應認證中間件分組) 下掛載以下端點，直接對接 `App\Http\Controllers\Api\V9\SettlementController`：

1. `GET /api/v9/settlements` ➔ `index`
2. `GET /api/v9/settlements/{id}` ➔ `show`
3. `POST /api/v9/settlements/{id}/confirm` ➔ `confirm`
4. `POST /api/v9/settlements/{id}/approve` ➔ `approve`
5. `POST /api/v9/settlements/{id}/dispute` ➔ `dispute`
6. `POST /api/v9/settlements/{id}/resolve-dispute` ➔ `resolveDispute`
7. `GET /api/v9/settlements/{id}/download-pdf` ➔ `downloadPdf`
8. `POST /api/v9/settlements/generate` ➔ `generate`

**注意**：確認路由名、參數名稱與 `resources/views/iot/modules/m7/` 前端 `fetch` 呼叫完全一致。

### 二、M6 日報鎖定權限檢查 (`app/Http/Controllers/Api/ReportController.php`)
在 `lockAll()` 方法中加入嚴格權限防護：
- 檢查當前登入者：`auth()->user()->role === 'admin'`（或系統 Admin 判斷標準）。
- 若非 Admin，直接回傳 HTTP 403：
  ```json
  {
      "message": "權限不足，僅系統管理者可執行每日結算鎖定"
  }
  ```

---

## 📦 驗收標準 (Acceptance Criteria)

1. **代碼與測試**：
   - 執行 `php artisan route:list | grep settlements`，確認 8 條路由全部成功載入且無命名衝突。
   - 語法檢查通過（無 PHP 語法錯誤）。
2. **Git 與遠端部署**：
   - Commit message 格式：`fix(m6/m7): mount settlement routes and enforce lockAll admin authorization`
   - Push 至遠端 main 分支。
   - 使用 `./dev_tools/waw_ops.sh deploy owner` 部署至生產環境 (`iot.tg25.win`)。
3. **回報格式**：
   - 依據 `SIMPLE_FILE_DISPATCH_PROTOCOL.md` 格式將回報寫入 `.taskflow/owner/outbox/`。
   - **強制要求檢附遠端證據**：
     - `route:list` 截圖或文字輸出。
     - 非 Admin 打 `lock-all` 回傳 403 之 curl 證據。

---
**派發者**：HQ  

