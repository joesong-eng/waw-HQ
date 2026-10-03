# REPORT：Alliance Phase 1 安全與 Quick UX 修復 — 完工回報

- **報告時間**：2026-09-20 21:00 (+0800)
- **回報者**：Allie (Alliance Lead)
- **工單**：`TASK_20260920_ALLIE_SECURITY_AND_QUICK_UX_FIXES`（優先級 High）
- **來源計畫**：`PROJECT/Alliance/docs/ALLIANCE_SITE_IMPROVEMENT_PLAN.md`（僅核准第一波）
- **完整報告**：`.taskflow/alliance/outbox/REPORT_20260920_ALLIE_SECURITY_AND_QUICK_UX_FIXES.md`
- **狀態**：✅ **全數完工、已部署、線上驗收通過**

---

## 一、本波核准項目完成率：7 / 7 = 100%

| 編號 | 項目 | 檔案 | Commit | 狀態 |
|:---|:---|:---|:---|:---|
| 1.1 | 移除登入頁測試帳密 | `auth/login.blade.php` | `75e2726` | ✅ |
| 1.2 | 移除無效「忘記密碼？」連結 | `auth/login.blade.php` | `75e2726` | ✅ |
| 1.3 | `POST /login` 加 `throttle:5,1` | `routes/web.php` | `75e2726` | ✅ |
| 3.1 | 訂單列表顯示真實單號 | `orders/index.blade.php` | (更早已完成) | ✅ 已驗證 |
| 3.3 | Dashboard 收益/訂單預設展開 | `dashboard/index.blade.php` | `97987c0` | ✅ |
| 4.1 | 側邊欄「出貨整理」圖示去重 📦→🚚 | `layouts/app.blade.php` | `97987c0` | ✅ |
| 4.2 | 刪除孤立檔 `welcome.blade.php` | `resources/views/welcome.blade.php` | `97987c0` | ✅ |

**Commit**：`75e2726` → `97987c0`，已推送 `origin/main`；本地 / 遠端 / origin 三方一致。

---

## 二、部署與線上驗收（https://ali.tg25.win）

遠端 `137.131.50.16:/www/wwwroot/ali.tg25.win` HEAD = `97987c0`，工作區乾淨。
已執行 `view:clear` / `cache:clear` / `config:clear` / `route:clear` 並重新 `config:cache` / `view:cache` / `route:cache`（全部成功）。

| 驗收項 | 結果 |
|:---|:---|
| `GET /login` 無測試帳密、無 `password123`、無 `@alliance.com` | ✅ |
| `GET /login` 無「忘記密碼？」連結 | ✅ |
| 訂單列表真實單號（DB 5 筆全數命中，無 `ORD-` fallback） | ✅ |
| Dashboard revenue/orders 無 `collapsed`；disputes 保持 `collapsed` | ✅ |
| 側邊欄「出貨整理」= 🚚 | ✅ |
| `GET /welcome` → 404（檔案已刪） | ✅ |
| `GET /`、`GET /profile` 未登入 → 302 → `/login` | ✅ |
| **連續錯誤登入第 6 次 → 429**（`x-ratelimit-limit: 5`、`retry-after: 5`） | ✅ |

---

## 三、⚠️ 需 HQ 裁定之兩項風險（誠實回報）

### 🔴 R1：`throttle:5,1` 以 Cloudflare 邊緣 IP 為鍵，非真實客戶端 IP
- 站點位於 Cloudflare 之後，nginx 未設 `set_real_ip_from`/`real_ip_header`（已查 `nginx.conf` 與 vhost），且 Laravel 未配置 `TrustProxies`（無 `config/trustedproxy.php`，`bootstrap/app.php` 未呼叫 `trustProxies()`）。
- 因此 `$request->ip()` 實為 **CF 邊緣節點 IP**（access log 為 `162.158.243.x`）。以不同 `X-Forwarded-For` 測試仍得 429，證實額度是「每個 CF 邊緣節點共享」。
- **後果**：同一 CF 節點後的多位合法使用者共用 5 次/分額度，可能誤傷正常登入。
- **建議**：另開工單，於 nginx 還原 CF 真實 IP 或於 Laravel 配置 `TrustProxies` 信任 Cloudflare 網段；或改「每 email+IP」複合鍵。
- 本波任務要求「5 次後出現 429」**已達成**，故未擅自擴大修改範圍。

### 🟠 R2：Migration 帳本漂移（既有問題，非本次造成）
- `migrations` 表僅 9 筆，但 `ali_orders`、`ali_products`、`ali_settlements`、`ali_device_bindings` 等表皆已存在；`migrate:status` 顯示多筆 Pending（含 `2026_06_18_200000_create_alliance_db_schema`）。
- **風險**：`waw_ops.sh deploy alliance` 內含 `php artisan migrate --force`，若執行可能重跑建表/資料遷移而破壞現有資料。
- **Allie 處置**：**主動停用標準 deploy 指令**，改以手動確認 pull 狀態 + 精準清快取完成部署。
- **建議**：由 Infra 端先比對 schema 與遷移帳本、補記已執行之遷移，再恢復標準部署流程。

---

## 四、未動項目（維持原狀，未越權）

3.2 Dashboard 進度地圖、3.4 客戶頁 Tailwind、3.5 已結案訂單燒錄入口（程式已有狀態判斷，待人工目視複核）、4.3~4.7，以及第二波 CSS 大一統與 `burning.blade.php` 拆分，**全數未動**。

---

## 五、結論

第一波核准之 7 項**全數完成、已部署並線上驗收通過**。
節流 429 功能正常，惟存在 CF/TrustProxies 未配置真實 IP 之副作用，已列後續工單建議。
`welcome.blade.php` 刪除後 `/welcome` 回 404，首頁與登入流程不受影響。

**待 HQ 指示**：是否核准 R1（TrustProxies/真實 IP）與 R2（遷移帳本校正）另開工單。

---
**回報者**：Allie (Alliance Lead)
**回報時間**：2026-09-20 21:00 (+0800)
