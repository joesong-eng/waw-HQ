# 任務：TASK_20261001_SOPHIE_FIX_SETTLEMENTS_CONTROLLER_500

**派發時間**：2026-10-01
**優先級**：P0
**負責人**：Sophie (Owner)
**關聯模組**：Owner (iot.tg25.win / yd174)

---

## 一、問題現象與根因定位
在 `/settlements/statements` 頁面彈出警告「載入結算單失敗：Server Error」。

經查遠端 yd174 `storage/logs/laravel-2026-10-01.log`，真正錯誤為：
```
production.ERROR: Call to undefined method App\Http\Controllers\Api\V9\SettlementController::middleware() at /www/wwwroot/iot.tg25.win/app/Http/Controllers/Api/V9/SettlementController.php:20
```

**根本原因**：
Laravel 11 取消了基礎 Controller 的 `middleware()` 方法。
- `SettlementController::__construct()` 內使用了：
  ```php
  $this->middleware('check.arrears')->only(['confirm', 'approve', 'downloadPdf']);
  ```
- 同樣地，`ReportController::__construct()`（`app/Http/Controllers/Api/ReportController.php:26`）也有同款語法：
  ```php
  $this->middleware('check.arrears')->only(['trend']);
  ```
導致 Controller 初始化直接 Fatal Error 500。

---

## 二、修復方案
1. **移除 Controller 建構子中的 `$this->middleware()` 呼叫**。
2. **改為在 Route 定義上套用 middleware**，或實作 `HasMiddleware` 介面（Laravel 11 標準做法）：
   - 方式 A（推薦，最簡短俐落）：在 `routes/api.php` 對特定路由套用 `check.arrears`，或針對 group 設定。
   - 方式 B：Controller `implements HasMiddleware` 並實作 `middleware()` 靜態方法。
3. 一併檢查並修復 `ReportController.php` 中的同款問題。

---

## 三、驗收標準
1. 本地 commit 並推送到 main。
2. `waw_ops.sh deploy owner` 部署至 yd174。
3. 遠端實測 `curl -i -s -k -H "Host: iot.tg25.win" https://127.0.0.1/api/v9/settlements` 或直接在瀏覽器開啟 `/settlements/statements`，不再報 500 / Server Error。
4. 回報至 `.taskflow/owner/outbox/`。
