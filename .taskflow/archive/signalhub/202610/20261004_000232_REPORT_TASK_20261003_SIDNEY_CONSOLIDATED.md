# REPORT — TASK_20261003_SIDNEY_CONSOLIDATED

- **任務 ID**：TASK_20261003_SIDNEY_CONSOLIDATED（SignalHub 版控清理 + 訂閱機制落地，合併三任務）
- **執行者**：Sidney（SignalHub 負責人）
- **完成時間**：2026-10-04 00:02 (Asia/Taipei)
- **遠端主機**：129.153.116.174:/www/wwwroot/signal.tg25.win
- **Repo**：https://github.com/joesong-eng/signal-hub-standalone.git

---

## 階段一：版控清理

### Commit
```
4d89e26 chore(signalhub): purge residue backup files and legacy .taskbox symlink
(main) 10 files changed, 1 insertion(+), 1817 deletions(-)
```
**Push 結果**：`d8cff53..4d89e26  main -> main`（成功）

### 執行內容
1a. 已納版控備份檔（git rm，共 8 個）：
- app/Jobs/ProcessWebhookDelivery.php.bak.archive
- app/Models/SignalProfile.php.bak.archive
- app/Services/SignalNotificationService.php.bak.archive
- config/subscription.php.old
- resources/views/signal-hub/profiles.blade.php.bak
- routes/api.php.bak.archive / routes/api.php.bak2 / routes/api.php.bak3

1b. 未納版控殘留檔（unlink，共 8 個；除工單列出 3 個外，另清出 5 個同名家族殘留）：
- app/Http/Controllers/Api/V9/SignalHubController.php.bak
- app/Http/Controllers/Api/V9/SignalHubController.php.backup ←（額外發現）
- resources/views/signal-hub/profiles.blade.php.new_template
- resources/views/signal-hub/profiles.blade.php.backup ←（額外發現）
- resources/views/signal-hub/profiles.blade.php.bak_before_layout ←（額外發現）
- routes/api.php.contaminated / routes/api.php.bak4 / routes/api.php.bak5 ←（額外發現）

1c. 移除 `.taskbox` 舊派工 symlink（git rm，delete mode 120000）。

1d. `.gitignore` 補上缺漏的 `*.new_template`（原僅有 `*.bak*`、`*.old`、`*.contaminated`）。

> 額外清理：部署後於**遠端**發現本機不存在的殘留檔 `resources/views/signal-hub/pins.blade.php.bak`（未納版控、7.7KB，正式版 21.9KB），已一併刪除。

### 驗收指令輸出
```
# [A] git ls-files '.bak|.old|.contaminated|.new_template'  → (empty = PASS)
# [B] find ... -name '*.bak*' -o -name '*.old' -o -name '*.contaminated' -o -name '*.new_template'  → (empty = PASS)
# [C] ls -ld .taskbox  → No such file or directory (PASS)
# [D] 正式檔保留：routes/api.php(6653B) / config/subscription.php(4237B) / profiles.blade.php(15397B)
```
**遠端複核**：`git ls-files` 殘留 = NONE；`find` 殘留 = 空；`.taskbox` 不存在。✅

---

## 階段二：訂閱機制落地（ADR-001_SIGNALHUB_SUBSCRIPTION）

### Commit
```
4445a3f feat(signalhub): implement subscription (model, status API, middleware, banner)
(main) 8 files changed, 353 insertions(+), 2 deletions(-)
```
**Push 結果**：`4d89e26..4445a3f  main -> main`（成功）

### 交付項目
| 項目 | 檔案 | 說明 |
|------|------|------|
| 1. Model | `app/Models/OwnerSubscription.php`（新增） | 複用既有 `owner_subscriptions` 表；修復 `User.php:127` 幽靈引用 |
| 2. Status API | `SignalHubController::subscriptionStatus()` + `GET /api/v9/subscription/status` | 回傳 status / plan_tier / start_date / end_date / days_remaining / is_expired / in_grace |
| 3. Middleware | `app/Http/Middleware/EnsureSubscriptionActive.php`（新增） | alias `subscription.active`；**預設停用** |
| 4. 前端橫幅 | `resources/views/signal-hub/partials/subscription-banner.blade.php`（新增）+ `layouts/app.blade.php` 注入 | 過期/寬限顯示橫幅，**不阻擋瀏覽** |

- 路由套用：`v9/signal-hub/*`（寫入群組）與 `v9/signal-hub/inbound/session-end` 掛 `subscription.active`。
- 對齊遠端實際 schema：`id, owner_id, owner_type, plan_name, started_at, expires_at, status`（非舊 migration 的 plan_tier/start_date/end_date）。
- 未建立 owner_subscriptions 表、未建 SubscriptionController / CRUD（符合工單注意事項 1、2）。

### Tinker 實測（遠端）
```
model_class=App\Models\OwnerSubscription
enforce_flag=false            ← 攔截預設停用（證明）
grace_days=3
user1_sub=null                ← User::find(1)->subscription 可載入（admin 無訂閱）
user12_sub_status=active
user12_allowsWrite=true
user12_remaining=454
```

### status API 回傳（真實 HTTP Kernel 派發，session 認證）
```
GET /api/v9/subscription/status  (owner 12，有效訂閱)
HTTP 200
{"status":"active","plan_tier":"device_service","start_date":"2026-09-15",
 "end_date":"2027-12-31","days_remaining":454,"is_expired":false,"in_grace":false}

GET /api/v9/subscription/status  (admin 1，無訂閱)
HTTP 200
{"status":"none","plan_tier":null,"start_date":null,"end_date":null,
 "days_remaining":0,"is_expired":false,"in_grace":false}
```

### 攔截 Middleware 驗證（真實 HTTP Kernel 派發）
```
=== flag=FALSE (預設) ===
B  POST /api/v9/signal-hub/profiles (admin1, 無訂閱): HTTP 422  ← 未攔截，正常進入驗證
=== flag=TRUE (runtime 模擬啟用) ===
C  POST /api/v9/signal-hub/profiles (admin1, 無訂閱): HTTP 403  ← 寫入封鎖
   {"success":false,"code":403,"status":"none","message":"訂閱已過期或尚未訂閱，請續約後再使用此功能。"}
D  POST /api/v9/signal-hub/profiles (owner12, 有效): HTTP 422  ← 有效訂閱放行
E  GET  /api/v9/signal-hub/deliveries      (admin1): HTTP 200  ← 唯讀放行
F  GET  /api/v9/signal-hub/deliveries/stats(admin1): HTTP 200  ← 唯讀放行
G  POST /api/v9/signal-hub/inbound/session-end (admin1): HTTP 403  ← 寫入封鎖
```
**驗收對應**：flag=false 站點功能不受影響 ✅；flag=true 寫入端點回 403 ✅、唯讀端點正常 ✅。

### 攔截 flag 預設值證明
```
config('subscription.enforce') = false
config/subscription.php → 'enforce' => env('SUBSCRIPTION_ENFORCE', false)
```

### 前端橫幅驗證（真實渲染 HTML）
```
GET /signal-hub/profiles (owner12): HTTP 200
has_banner_div=YES        (id="subscription-banner")
has_status_api_call=YES   (fetch /api/v9/subscription/status)
has_expired_text=YES      ("訂閱已過期")
has_grace_text=YES        ("訂閱即將到期")

狀態邏輯（未持久化實例驗證）：
expired → effectiveStatus=expired, isExpired=true,  allowsWrite=false
grace   → effectiveStatus=grace,   in_grace=true,  allowsWrite=true
active  → effectiveStatus=active
```
**驗收對應**：過期狀態下可見橫幅、頁面仍可瀏覽 ✅。

### 站點狀態碼
```
curl -sI https://signal.tg25.win/       → HTTP/2 302 (導向 /login)
curl -sI https://signal.tg25.win/login  → HTTP/2 200
```
（`/` 為 302 屬正常：未登入導向登入頁；站點存活正常。）

### 部署輸出
```
./dev_tools/waw_ops.sh deploy sidney
→ git pull origin main（19 files changed, 380 insertions(+), 1824 deletions(-)）
→ php artisan migrate --force → INFO Nothing to migrate.
→ view:clear / config:cache / cache:clear 全部成功
→ ✅ sidney (signalhub) 部署完成！
```

---

## 結論
✅ **完成**（階段一 + 階段二全數交付並通過遠端驗證）

- 階段一 commit `4d89e26`；階段二 commit `4445a3f`；兩者皆已 push 至 main 並完成遠端部署。
- 訂閱攔截 Middleware 預設停用（`enforce=false`），待 HQ 宣布正式上線再由 env 啟用。
- 遵循 ADR-001：SignalHub 端僅補「讀取 + 攔截 + 橫幅」，未重建資料表、未建帳務 CRUD。

> 備註：工單列出 11 個殘留檔，實際另清出 6 個同家族殘留（本機 5 + 遠端 1），合計 17 個，確保 `find` 驗收歸零。

