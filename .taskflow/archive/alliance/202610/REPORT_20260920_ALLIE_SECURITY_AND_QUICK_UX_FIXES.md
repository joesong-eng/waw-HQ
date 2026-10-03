# 任務回報：TASK_20260920_ALLIE_SECURITY_AND_QUICK_UX_FIXES

- **完成時間**：2026-09-20 16:35 (+0800)
- **執行者**：Allie (Alliance Lead)
- **派發來源**：HQ `TASK_20260920_ALLIE_SECURITY_AND_QUICK_UX_FIXES`
- **來源計畫**：`PROJECT/Alliance/docs/ALLIANCE_SITE_IMPROVEMENT_PLAN.md`（僅第一波 1.1/1.2/1.3、3.1、3.3、4.1、4.2）
- **狀態**：✅ 已完工並遠端驗收通過

---

## 一、實作內容與變更清單

本波嚴格遵守「高收益、低風險、非破壞性」，未動 `burning.blade.php` 拆分，亦未做全站 CSS 大一統。

### 1. 登入安全修復（1.1 / 1.2 / 1.3）
- `resources/views/auth/login.blade.php`
  - 移除底部 `<div class="test-accounts">` 測試帳密區塊（含 `boss@alliance.com` / `partner@alliance.com` / `password123`）。
  - 同步移除殘留的 `.test-accounts` CSS 規則。
  - 移除無效的「忘記密碼？」`href="#"` 連結（採任務允許之「暫時隱藏」）。
- `routes/web.php`
  - `Route::post('/login', ...)->middleware('throttle:5,1');`

### 2. 訂單號與 Dashboard UX（3.1 / 3.3）
- `resources/views/orders/index.blade.php`
  - 訂單列表改顯示真實單號：`{{ $order->order_no ?? 'ORD-'.$order->id }}`。
- `resources/views/dashboard/index.blade.php`
  - 「📈 聯盟收益趨勢」與「最新訂單動態」移除 `collapsed` → **預設展開**。
  - 「待處理爭議結算單」**保持折疊**（符合計畫指定）。

### 3. 清理與細節修飾（4.1 / 4.2）
- `resources/views/layouts/app.blade.php`
  - 「出貨整理」圖示 📦 → 🚚，消除與「產品管理」📦 的重複。
- `resources/views/welcome.blade.php`
  - 刪除（無路由、無引用之孤立佔位檔）。

### Git Commit
| Commit | 說明 | 變更 |
|---|---|---|
| `75e2726` | security: Phase 1 安全修復 | login.blade.php, routes/web.php |
| `97987c0` | feat(ux): Dashboard 預設展開、出貨圖示改為卡車、移除孤立檔 | dashboard/index.blade.php, layouts/app.blade.php, welcome.blade.php (D) |

`main` 已推送，本地 / `origin/main` / 遠端 HEAD 三方一致於 `97987c0`。

---

## 二、部署與清除快取

遠端 `/www/wwwroot/ali.tg25.win`（`137.131.50.16`）`git log` 已為 `97987c0`，工作區乾淨（僅忽略之 `.bak` 檔）。

執行：
```
php artisan view:clear   → Compiled views cleared successfully.
php artisan cache:clear  → Application cache cleared successfully.
php artisan config:clear → Configuration cache cleared successfully.
php artisan route:clear  → Route cache cleared successfully.
php artisan config:cache / view:cache / route:cache → 皆成功
```

> ⚠️ 注意：專案 `storage/`、`bootstrap/cache/` 擁有者為 `www:www`，SSH 使用者 `ubuntu` 直跑 `php artisan cache:clear` 會出現 "Failed to clear cache" 權限錯誤；已改用 `sudo -n php artisan ...` 成功清除。此為環境既有特性，非本次變更造成。

**未執行** `waw_ops.sh deploy alliance`：因該指令含 `php artisan migrate --force`，而本專案存在遷移帳本漂移（見第四節風險），在未經 HQ 核准下執行恐有破壞性後果，故改以手動 pull 狀態確認 + 精準清快取部署。

---

## 三、線上驗收結果（https://ali.tg25.win）

| 驗收項 | 方法 | 結果 |
|---|---|---|
| 測試帳密已移除 | `curl GET /login` 掃描 | ✅ `test-accounts`=0、`password123`=0、`@alliance.com`=0 |
| 忘記密碼連結已移除 | 同上 | ✅ `忘記密碼`=0 |
| 登入頁正常 | `GET /login` | ✅ HTTP 200 |
| 訂單列表真實單號 | 遠端 render `orders.index` | ✅ DB 5 筆單號全數出現於 HTML，且無 `ORD-` fallback |
| Dashboard 預設展開 | 遠端 render `DashboardController@index` | ✅ revenue/orders 無 `collapsed`；disputes 帶 `collapsed`（collapsed 計數=1） |
| 側邊欄圖示去重 | 遠端 render layout | ✅ 「出貨整理」=🚚 |
| welcome.blade.php 已刪 | `GET /welcome` | ✅ HTTP 404（檔案不存在） |
| 未登入導向 | `GET /`、`GET /profile` | ✅ HTTP 302 → `/login` |
| **登入節流 429** | `POST /login` 連續錯誤登入 | ✅ 第 1–5 次 302，**第 6 次起 429**，回傳 `x-ratelimit-limit: 5`、`retry-after: 5` |

節流原始日誌（nginx access log）：
```
... "POST /login HTTP/2.0" 302
... "POST /login HTTP/2.0" 302
... "POST /login HTTP/2.0" 302
... "POST /login HTTP/2.0" 302
... "POST /login HTTP/2.0" 302
... "POST /login HTTP/2.0" 429   ← 第 6 次
```

---

## 四、風險與待辦（誠實回報，不在本波授權範圍）

1. **🔴 節流桶以 Cloudflare 邊緣 IP 為鍵，非真實客戶端 IP**
   - 現象：站點位於 Cloudflare 之後，nginx 未設 `set_real_ip_from` / `real_ip_header`（已查 `nginx.conf` 與 `vhost/ali.tg25.win.conf`），且 Laravel 未配置 `TrustProxies`（無 `config/trustedproxy.php`，`bootstrap/app.php` 無 `trustProxies()`）。
   - 後果：`throttle:5,1` 的簽章為 `route domain + $request->ip()`，而 `$request->ip()` 實為 **Cloudflare 邊緣節點 IP**（access log 顯示 `162.158.243.x`）。驗收時以不同 `X-Forwarded-For` 仍拿到 429，證實桶是「每邊緣節點共享」而非「每真實使用者」。
   - 影響：同一 CF 邊緣節點後的多位合法使用者共用 5 次/分額度，可能誤傷正常登入。
   - 建議（需另開工單）：於 nginx 還原 Cloudflare 真實 IP，或於 Laravel 配置 `TrustProxies` 信任 Cloudflare 網段；亦或改用「每 email + IP」複合鍵。
   - 本波任務要求「5 次後出現 429」已達成，故此項列為後續優化，未擅自擴大修改。

2. **🟠 Migration 帳本漂移（既有問題，非本次造成）**
   - `migrations` 表僅 9 筆，但 `ali_orders`、`ali_products`、`ali_settlements`、`ali_device_bindings` 等表皆已存在；`migrate:status` 顯示多筆 Pending（含 `2026_06_18_200000_create_alliance_db_schema`）。
   - 風險：若執行 `php artisan migrate --force`（即 `waw_ops.sh deploy` 內建步驟），可能重跑建表/資料遷移而破壞現有資料。已因此**主動停用 deploy**。
   - 建議：由 Infra 端先行比對 schema 與遷移帳本，補記已執行之遷移後，再恢復標準部署流程。

3. **ℹ️ 計畫書中未授權項目維持原狀**：3.2 Dashboard 進度地圖、3.4 客戶頁 Tailwind、3.5 已結案訂單燒錄入口（程式已具 `@if(!in_array($order->status, ['completed','shipped']))` 判斷，待人工目視確認）、4.3~4.7 及第二波 CSS 大一統，皆**未動**。

---

## 五、結論

第一波核准項目（1.1、1.2、1.3、3.1、3.3、4.1、4.2）**全數完成、已部署並線上驗收通過**。
節流 429 功能正常，惟因 Cloudflare/TrustProxies 未配置真實 IP，存在「跨使用者共享額度」之副作用，已列為後續工單建議。
`welcome.blade.php` 刪除後 `/welcome` 回 404，首頁流程不受影響。

**回報時間**：2026-09-20 16:35 (+0800)
