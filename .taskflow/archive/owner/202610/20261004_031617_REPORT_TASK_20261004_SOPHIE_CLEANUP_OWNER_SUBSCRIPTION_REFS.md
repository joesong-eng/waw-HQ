# 回報：清理 OwnerSubscription 引用（統一改用 Subscription Model）

## 任務 ID
TASK_20261004_SOPHIE_CLEANUP_OWNER_SUBSCRIPTION_REFS

## 執行者
Sophie（Owner / wawOwner, iot.tg25.win）

## 完成時間
2026-10-04 03:16 (Asia/Taipei)

## 結論
- ✅ 代碼去引用完成並已部署，驗收指標 1、3 通過
- ⚠️ **驗收指標 2 發現既有缺陷（非本次引入）**：`SubscriptionService` 有 4 個被呼叫但不存在的方法，其中 `initializeSubscription` 會導致「新增 owner 帳號」拋錯。詳見第四節，待 HQ 裁定。

---

## 一、執行結果

| 項目 | 值 |
|------|-----|
| Commit | `6a2d53d74e1d3d86c46c7c1348fc6565a7bbeb0b` |
| Commit message | `refactor(subscription): unify on Subscription model, remove OwnerSubscription refs (ADR-003)` |
| Push | `7a8df8b..6a2d53d  main -> main`（github.com/joesong-eng/waw-business.git） |
| 遠端部署 | `waw_ops.sh deploy owner` 成功；遠端 HEAD = `6a2d53d` |
| Diff | 9 files changed, 50 insertions(+), 122 deletions(-) |

### 修改檔案清單
```
D  app/Models/OwnerSubscription.php                 (刪除)
M  app/Models/User.php                              subscription() -> hasOne(Subscription, subscriber_id)
M  app/Console/Commands/CheckSubscriptionExpiry.php 改用 Subscription + logAudit
M  app/Http/Controllers/Api/V9/OtaController.php    owner_id->subscriber_id, plan_tier->tier_code
M  app/Services/NotificationService.php             owner->subscriber, plan_tier->tier_code, end_date->expires_at
M  app/Events/SubscriptionExpired.php               型別 -> Subscription
M  app/Events/SubscriptionExtended.php              型別 -> Subscription
M  app/Events/RenewalReminderNeeded.php             型別 -> Subscription
M  resources/views/iot/modules/m3/devices.blade.php subscription?->tier_code
```

### 欄位映射（owner_subscriptions → subscriptions，依 ADR-003 / Ina 實測 schema）
| 舊欄位 | 新欄位 |
|--------|--------|
| owner_id | subscriber_id |
| plan_tier / plan_name | tier_code |
| end_date | expires_at |
| start_date | started_at |

> 註：`SubscriptionService.php` 原本即已使用 `Subscription`（未變更，符合工單第 2 點）。

---

## 二、驗收佐證

### 指標 1：grep OwnerSubscription app/ routes/ config/ = 0 hits ✅
```
$ grep -rn 'OwnerSubscription' app/ routes/ config/
(0 hits)
$ grep -rn 'owner_subscriptions' routes/ app/ config/
(0 hits)
```

### 指標 3：curl -sI https://iot.tg25.win/ ✅
```
$ curl -sI https://iot.tg25.win/
HTTP/2 302  (redirect -> /login，未登入正常行為)
$ curl -sIL https://iot.tg25.win/
final HTTP 200  url=https://iot.tg25.win/login
$ curl -sI https://iot.tg25.win/login
HTTP/2 200
```

### 遠端部署驗證
```
remote HEAD: 6a2d53d refactor(subscription): unify on Subscription model...
remote grep OwnerSubscription app/ routes/ config/ -> 0 hits
app/Models/OwnerSubscription.php -> No such file or directory
bootstrap/cache/config.php -> rebuilt (03:13)
```

### 瀏覽器真實驗證（截圖）
已開啟 https://iot.tg25.win/login，頁面正常渲染（WAW CORE 登入頁），HTTP 200。詳見對話中之截圖。

### Tinker 功能驗證（遠端實跑）
```
user12->subscription = id=31 subscriber_id=12 tier_code=NULL status=active   ← 關聯正常
admin list count = 35                                                        ← Owner 後台訂閱管理正常
summary owner12: devices=1 venues=0 device_subs=1                            ← 訂閱摘要正常
Blade view:cache -> Blade templates cached successfully (無編譯錯誤)
```

### 路由殘留檢查
`owner_subscriptions` 表相關路由 = 0 hits。
`routes/api.php` 之 `/internal/alliance/owner-subscription(s)` 為 Alliance 代理商端點，讀取來源為 `BillingRequest`（非 OwnerSubscription 表），非本次殘留，未變更。

---

## 三、部署後功能狀態
- 站點存活：✅ HTTP 200
- Owner 後台訂閱管理（`/api/v9/admin/subscription/list|extend|audit`）：✅ 運作
- `User::subscription` 關聯：✅ 指向 subscriptions 表
- 部署後 laravel log：✅ 無新錯誤

---

## 四、⚠️ 重大發現：既有缺陷（非本次引入，待 HQ 裁定）

清理過程中發現：**`SubscriptionService` 缺少 4 個被程式呼叫的方法**，此缺陷早於本次任務即存在（2026-08-23 雙軌重構時遺失），**遠端部署版本（ce76cb3）同樣缺少**，非本次改動造成。

### 缺失方法與呼叫者
| 缺失方法 | 呼叫者 | 影響 |
|----------|--------|------|
| `initializeSubscription()` | `app/Observers/UserObserver.php:21`（User::created 時對 owner 呼叫） | 🔴 **新增 owner 帳號會拋錯** |
| `isSubscriptionActive()` | `app/Http/Middleware/EnsureProSubscription.php:43` | 使用 `pro` middleware 時拋錯 |
| `getSubscriptionStatus()` | `app/Http/Middleware/EnsureProSubscription.php:51` | 同上 |
| `expireSubscription()` | `app/Console/Commands/CheckSubscriptionExpiry.php`（本次已改寫為直接 update，不再呼叫） | 已由本次修正解除 |

### 實測佐證（在**現行部署**程式上，交易內測試後 rollback，未寫入 DB）
```
$ php artisan tinker  (DB::beginTransaction ... User::create role=owner ... DB::rollBack)
CREATE_THROWS: Error: Call to undefined method App\Services\SubscriptionService::initializeSubscription()
rolled back
```
```
method_exists(SubscriptionService, 'initializeSubscription') = NO
method_exists(SubscriptionService, 'isSubscriptionActive')   = NO
method_exists(SubscriptionService, 'getSubscriptionStatus')  = NO
method_exists(SubscriptionService, 'expireSubscription')     = NO
```
> 舊版實作仍存於 `trash/Owner_obsolete/app/Services/SubscriptionService.php`（基於 OwnerSubscription），可作修復參考。

### 影響範圍評估
- `UserObserver` 已於 `AppServiceProvider::boot()` 註冊，任何 `role=owner` 的 `User::create`（自助註冊 `Authv9Controller::register`、LINE 登入建帳 `LineLoginController`、`UserManagementController`）都會觸發。
- `EnsureProSubscription`（別名 `pro`）目前未見於任何路由掛載，風險較低但仍是地雷。
- 現有生產用戶未受影響（建立於缺陷之前）。

### 建議（待 HQ 裁定，我未擅自實作以免臆測業務邏輯）
1. 由 HQ 指示是否補回這 4 個方法（以 `subscriptions` 表為基礎重寫）；`initializeSubscription` 涉及「新 owner 預設訂閱」之業務規則（舊版為 plan=basic、有效期 100 年），屬商業決策，建議明確定義後再實作。
2. 或移除 `UserObserver` 對 `initializeSubscription` 的呼叫，改由帳務流程建立訂閱（與 ADR-003「以帳務流程為準」一致）。

---

## 五、給 Ina 的 DROP 前置確認
- Sophie（Owner）去引用 + 部署：✅ 完成（commit 6a2d53d）
- Sidney（SignalHub）：另案，待其完成
- 兩者完成且站點正常後，Ina 即可執行 `DROP TABLE owner_subscriptions`（依 ADR-003 步驟 2）
- Owner 端已無任何 `owner_subscriptions` 表依賴（grep = 0 hits）

---

## 六、結論
- ✅ 任務主體（清理 OwnerSubscription 引用、統一改用 Subscription Model）完成並部署，驗收指標 1、3 通過；指標 2 之訂閱管理功能正常。
- ⚠️ 額外發現既有缺陷（4 個缺失的 SubscriptionService 方法，含影響新帳號註冊的 `initializeSubscription`），已如實回報，**未擅自變更業務邏輯**，待 HQ 裁定後處理。

## 執行者簽章
Sophie（Owner）

