# 任務回報：TASK_20261001_SOPHIE_FIX_SETTLEMENTS_CONTROLLER_500

**完成時間**：2026-10-01 18:58
**執行者**：Sophie (Owner)
**關聯 commit**：`6345583` (fix(m7/m6): 修正 Laravel 11 Controller middleware() 未定義導致 500)
**部署狀態**：✅ 已推送 origin/main 並完成 waw_ops.sh deploy owner（yd174 / iot.tg25.win）

---

## 一、根因確認
Laravel 11 已移除基礎 Illuminate\Routing\Controller 的 middleware() 方法，
專案基底 app/Http/Controllers/Controller.php 亦未提供該方法，
導致下列兩個 Controller 在建構子階段即丟出 Fatal Error，整個 Controller 無法初始化 → HTTP 500：

| 檔案 | 行 | 原錯誤語法 |
| :--- | :--- | :--- |
| app/Http/Controllers/Api/V9/SettlementController.php | 20 | $this->middleware('check.arrears')->only(['confirm','approve','downloadPdf']); |
| app/Http/Controllers/Api/ReportController.php | 26 | $this->middleware('check.arrears')->only(['trend']); |

遠端日誌（修復前）：
    production.ERROR: Call to undefined method App\Http\Controllers\Api\V9\SettlementController::middleware()
    at .../SettlementController.php:20

## 二、修復方案（採 Laravel 11 標準做法：HasMiddleware 介面）
未改動任何路由語意，僅將「建構子內動態呼叫」改為「靜態宣告」，語意等價：

    use Illuminate\Routing\Controllers\HasMiddleware;
    use Illuminate\Routing\Controllers\Middleware;

    class SettlementController extends Controller implements HasMiddleware
    {
        public function __construct(
            private SettlementService $settlementService,
            private SettlementPdfGenerator $pdfGenerator
        ) {}

        public static function middleware(): array
        {
            return [
                new Middleware('check.arrears', only: ['confirm', 'approve', 'downloadPdf']),
            ];
        }
    }

ReportController 同法處理，套用範圍維持 only: ['trend']。

> 選擇 HasMiddleware（而非在 routes/api.php 掛載）之理由：可精準對應 action 層級（only），
> 避免在 routes 端新增額外 group 造成路由結構膨脹，且與 Laravel 11 官方標準一致。

## 三、驗收結果

### 1. 語法檢查（本機）
    php -l app/Http/Controllers/Api/V9/SettlementController.php  -> No syntax errors detected
    php -l app/Http/Controllers/Api/ReportController.php         -> No syntax errors detected

### 2. 遠端部署
    ../../dev_tools/waw_ops.sh deploy owner
    -> vite build OK, built in 18.54s
    -> migrate: Nothing migrate
    -> cache:clear / config:cache / view:clear 完成
    -> owner (owner) 部署完成！
    遠端 HEAD = 6345583

### 3. 端點實測（修復前 500 → 修復後已非 500）
    curl -H "Host: iot.tg25.win" -H "Accept: application/json" https://127.0.0.1/api/v9/settlements
      -> settlements_api=401   （未帶登入態，正確回 401，非 500）

    curl ... /api/v9/reports/trend
      -> reports_trend=401     （同上，非 500）

    curl -H "Host: iot.tg25.win" https://127.0.0.1/settlements/statements
      -> statements_page=302   （導向登入頁，非 500）

### 4. 中介層掛載驗證（php artisan route:list -v）
確認 CheckArrearsStatus 精準掛載於目標 action，且未誤掛其他 action：

| 路由 | check.arrears |
| :--- | :--- |
| POST api/v9/settlements/{id}/confirm | 已掛載 |
| POST api/v9/settlements/{id}/approve | 已掛載 |
| GET  api/v9/settlements/{id}/download-pdf | 已掛載 |
| GET  api/v9/settlements (index) | 未掛載（符合原設計） |
| POST api/v9/settlements/generate | 未掛載（符合原設計） |
| GET  api/v9/reports/trend | 已掛載 |
| GET  api/v9/reports/daily | 未掛載（符合原設計） |

### 5. 錯誤日誌（部署後）
    grep 'undefined method' laravel-2026-10-01.log | tail -1
    -> [2026-10-01 05:06:08]   （最後一筆為修復前的舊錯誤）
    部署後（18:30 之後）undefined method 錯誤筆數 = 0

## 四、待補驗證（需登入態）
/settlements/statements 頁面前端需登入方能存取（瀏覽器開啟會 302 導向 /login），
故「頁面內彈窗是否消失」此項未能以匿名瀏覽器目視驗證。
惟該彈窗之觸發來源即 /api/v9/settlements 的 500，該端點已由 500 -> 401（通過 Controller 初始化），
且錯誤日誌已歸零，技術上已排除原錯誤。
建議：由 JOE 以 owner 帳號登入後開一次 /settlements/statements 做最終目視確認。

## 結論
✅ 完成（P0 修復已上線；唯一待補為需登入態的頁面目視確認）

