# REPORT — TASK_20261004_SIDNEY_SWITCH_TO_SUBSCRIPTION_MODEL

- **任務 ID**：TASK_20261004_SIDNEY_SWITCH_TO_SUBSCRIPTION_MODEL（Model 切換 OwnerSubscription → Subscription，修訂版）
- **執行者**：Sidney（SignalHub 負責人）
- **完成時間**：2026-10-04 02:56 (Asia/Taipei)
- **架構依據**：ADR-003_SUBSCRIPTION_TABLE_UNIFICATION.md（已修訂）
- **遠端主機**：129.153.116.174:/www/wwwroot/signal.tg25.win
- **Repo**：https://github.com/joesong-eng/signal-hub-standalone.git

---

## Commit
```
2f6e8bd refactor(signalhub): switch OwnerSubscription to unified Subscription model (ADR-003)
(main) 5 files changed, 69 insertions(+), 27 deletions(-)
rename app/Models/{OwnerSubscription.php => Subscription.php} (67%)
```
**Push 結果**：`4445a3f..2f6e8bd  main -> main`（成功）

---

## 執行內容（僅改代碼，未碰 DB）

| 步驟 | 內容 | 檔案 |
|------|------|------|
| 1 | 刪除舊 Model | `app/Models/OwnerSubscription.php`（刪除） |
| 2 | 新增 Subscription Model | `app/Models/Subscription.php`（新增） |
| 3 | Middleware 改用 Subscription | `app/Http/Middleware/EnsureSubscriptionActive.php` |
| 4 | status API 改用 Subscription | `app/Http/Controllers/Api/V9/SignalHubController.php` |
| 5 | 前端橫幅（資料源不變，更新依據註解） | `resources/views/signal-hub/partials/subscription-banner.blade.php` |
| 6 | User.php 關聯改指向 Subscription | `app/Models/User.php` |
| 7 | 部署到遠端 | `waw_ops.sh deploy sidney` |

### 對齊遠端實際 schema
`subscriptions` 表實際欄位（以遠端 iotv9 為準，Ina 實測）：
```
id, subscriber_id, service_type, target_id, tier_code, quota_limit,
selected_target_ids, status, started_at, expires_at, billing_request_id
```
- `Subscription` Model：`protected $table = 'subscriptions'`，fillable 依上列 11 欄。
- `belongsTo(User::class, 'subscriber_id')`。
- 保留 scopes：`active` / `expiringWithinDays` / `expiredWithGrace`（並保留 `expired`）。
- 新增 `resolveFor(int $subscriberId)`：因 subscriptions 同一 subscriber 可能有多筆歷史紀錄，
  依「可寫入(active/grace) 優先，其次 expires_at 最新」解析當前有效訂閱。
- `User::subscription()` 改用 `hasOne(Subscription::class, 'subscriber_id')->latestOfMany('expires_at')`。
- `plan_tier` accessor：`tier_code ?: service_type`（遠端 tier_code 為 null，故回退 service_type）。

> 註：未建立 subscriptions 表、未執行任何 migration/DDL（符合「僅改代碼，不碰 DB」）。

---

## 驗收指標

### 1. grep -rn 'OwnerSubscription' app/ = 0 hits ✅
```
（本機）grep -rn 'OwnerSubscription' app/ routes/ resources/ config/ bootstrap/  → 0 hits = PASS
（遠端）grep -rn 'OwnerSubscription' app/ routes/ resources/                      → 0 hits = PASS
```

### 2. Tinker: new App\Models\Subscription() 可載入 ✅
```
model_class=App\Models\Subscription
table=subscriptions
enforce_flag=false
user12.subscription=id=31 status=active plan_tier=device end=2027-12-31 23:59:59
user1.subscription=exists
```

### 3. GET /api/v9/subscription/status 200 JSON ✅
```
GET /api/v9/subscription/status (owner 12，有效訂閱)
HTTP 200
{"status":"active","plan_tier":"device","service_type":"device","start_date":"2026-09-15",
 "end_date":"2027-12-31","days_remaining":454,"is_expired":false,"in_grace":false}

GET /api/v9/subscription/status (admin 1，歷史訂閱已過期)
HTTP 200
{"status":"expired","plan_tier":"device","service_type":"device","start_date":"2026-06-17",
 "end_date":"2026-08-23","days_remaining":0,"is_expired":true,"in_grace":false}
```
（admin1 現於 subscriptions 表有歷史紀錄 → 正確回傳 expired，非 none；資料源切換生效。）

### 4. curl -sI https://signal.tg25.win/ HTTP 200 ✅
```
curl -sI https://signal.tg25.win/       → HTTP/2 302 (導向 /login，未登入正常)
curl -sI https://signal.tg25.win/login  → HTTP/2 200
```
（`/` 為 302 屬正常導向行為；站點存活驗證以 `/login` 之 HTTP/2 200 佐證。）

---

## 附加驗證（回歸）

### Middleware 行為（真實 HTTP Kernel 派發）
```
flag=false POST /api/v9/signal-hub/profiles (admin1): HTTP 422  ← 未攔截，正常進入驗證
flag=true  POST /api/v9/signal-hub/profiles (admin1): HTTP 403  ← 寫入封鎖
   {"success":false,"code":403,"status":"expired","message":"訂閱已過期或尚未訂閱，請續約後再使用此功能。"}
flag=true  GET  /api/v9/signal-hub/deliveries(admin1): HTTP 200  ← 唯讀放行
```

### 前端橫幅（真實渲染 HTML）
```
GET /signal-hub/profiles (owner12): HTTP 200
banner_div=YES        (id="subscription-banner")
status_api_call=YES   (fetch /api/v9/subscription/status)
```

### 部署輸出
```
./dev_tools/waw_ops.sh deploy sidney
→ git pull origin main (4445a3f..2f6e8bd, 5 files changed, 69 insertions(+), 27 deletions(-))
→ php artisan migrate --force → INFO Nothing to migrate.
→ view:clear / config:cache / cache:clear 全部成功
→ ✅ sidney (signalhub) 部署完成！
```

---

## 結論
✅ **完成**（代碼切換 + 遠端部署 + 全項驗收通過）

- 刪除 `OwnerSubscription`、新增 `Subscription`（指向 `subscriptions` 表），全站引用歸零。
- 未觸碰 DB、未執行 migration；`owner_subscriptions` 表 DROP 由後續作業處理。
- 攔截 Middleware 維持**預設停用**（`enforce=false`）。
- 橫幅與 status API 端點與回傳欄位相容（新增 `service_type`）。

> 待 HQ 指示：`owner_subscriptions` 表已無代碼引用，可於確認後安排 DROP。

