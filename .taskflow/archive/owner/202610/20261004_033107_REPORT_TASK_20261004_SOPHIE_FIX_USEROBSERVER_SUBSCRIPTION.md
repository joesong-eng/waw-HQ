# 回報：移除 UserObserver initializeSubscription 呼叫（HQ 裁定選項 b）

## 任務 ID
TASK_20261004_SOPHIE_FIX_USEROBSERVER_SUBSCRIPTION

## 執行者
Sophie（Owner / wawOwner, iot.tg25.win）

## 完成時間
2026-10-04 03:30 (Asia/Taipei)

## 結論
✅ 完成。已移除 UserObserver 對 initializeSubscription 的呼叫，並整檔刪除無路由掛載的 EnsureProSubscription middleware。部署後 `User::create(role=owner)` 不再拋錯，全數驗收指標通過。

---

## 一、執行結果

| 項目 | 值 |
|------|-----|
| Commit | `c1072bc79c67ede8160c006375f2c73572dd13ee` |
| Commit message | `fix(subscription): stop auto-init on user create; remove unused EnsureProSubscription (HQ option b)` |
| Push | `6a2d53d..c1072bc  main -> main`（github.com/joesong-eng/waw-business.git） |
| 遠端部署 | `waw_ops.sh deploy owner` 成功（fast-forward `6a2d53d..c1072bc`）；遠端 HEAD = `c1072bc` |
| Diff | 3 files changed, 5 insertions(+), 74 deletions(-) |

### 修改檔案清單
```
M  app/Observers/UserObserver.php                  移除 initializeSubscription 呼叫與 SubscriptionService 依賴
D  app/Http/Middleware/EnsureProSubscription.php   整檔刪除（0 路由掛載）
M  bootstrap/app.php                               移除 'pro' middleware 別名（指向已刪除類別）
```

### 決策說明
1. **UserObserver**：依 HQ 裁定 (b)，訂閱不再於帳號建立時自動初始化。目前無收費機制，訂閱一律由帳務流程手動建立。已移除 `created()` 中對 `initializeSubscription()` 的呼叫，並移除不再需要的 `SubscriptionService` 建構子注入。
2. **EnsureProSubscription**：經確認該 middleware 呼叫的 `isSubscriptionActive()` / `getSubscriptionStatus()` **在 SubscriptionService 中無定義**（幽靈呼叫），且**無任何路由掛載** → 依工單「若無路由使用則整個刪除」整檔刪除，並清掉 `bootstrap/app.php` 的 `'pro'` 別名註冊。
3. **EnsureSubscriptionActive**（別名 `subscription.active`）：未在工單範圍內；經查其使用的方法（`canAccessDevice` / `canAccessVenue`）**皆存在**，非缺陷，故保留不動。

---

## 二、驗收佐證

### 指標 1：Tinker User::create(role=owner) 不拋錯 ✅
```
$ php artisan tinker  (DB::beginTransaction ... User::create role=owner ... DB::rollBack)
CREATE_OK id=22
rolled_back
$ probe rows = 0        ← 無殘留測試資料
```
（對照：修復前同一測試為 `CREATE_THROWS: Error: Call to undefined method SubscriptionService::initializeSubscription()`）

### 指標 2：grep -rn 'initializeSubscription' app/ = 0 hits ✅
```
$ grep -rn 'initializeSubscription' app/
(0 hits)
```

### 指標 3：grep -rn 'isSubscriptionActive' app/ = 0 hits ✅
```
$ grep -rn 'isSubscriptionActive' app/
(0 hits)
$ grep -rn 'getSubscriptionStatus' app/     (附帶)
(0 hits)
$ grep -rn 'EnsureProSubscription' app/ bootstrap/ routes/
(0 hits)
```

### 指標 4：curl -sI https://iot.tg25.win/ ✅
```
$ curl -sI https://iot.tg25.win/
HTTP/2 302   (redirect -> /login，未登入正常行為)
$ curl -sI https://iot.tg25.win/login
HTTP/2 200
```

### 指標 5：部署到遠端 ✅
```
remote HEAD: c1072bc fix(subscription): stop auto-init on user create...
app/Http/Middleware/EnsureProSubscription.php -> No such file or directory
composer dump-autoload -o -> vendor/composer/autoload_classmap.php EnsureProSubscription count = 0
config:cache / view:clear -> 完成
```

### 其他完整性驗證（遠端實跑）
```
route:list 載入正常（223 行）
subscription 相關路由 = 13 條（正常）
middleware aliases: pro = NO（已移除）, subscription.active = YES（保留）
class EnsureSubscriptionActive 存在 = YES
class EnsureProSubscription 存在 = NO（已刪除）
今日 laravel log 無 ERROR/Exception
```

### 瀏覽器真實驗證（截圖）
已開啟 https://iot.tg25.win/login，頁面正常渲染（WAW CORE 登入頁），HTTP 200。詳見對話中之截圖。

---

## 三、部署後功能狀態
- 站點存活：✅ HTTP 200
- 新增 owner 帳號：✅ 不再拋錯（先前為 P1 阻斷性 bug）
- 訂閱相關路由（admin list/extend/audit、summary、status、plans）：✅ 全部正常載入
- 部署後 laravel log：✅ 無新錯誤

---

## 四、備註
- 本任務為前一任務（TASK_20261004_SOPHIE_CLEANUP_OWNER_SUBSCRIPTION_REFS）所發現既有缺陷之後續修復，HQ 已裁定採選項 (b)。
- 至此 Owner 端 `SubscriptionService` 的所有幽靈方法呼叫已全數解除（initializeSubscription / isSubscriptionActive / getSubscriptionStatus / expireSubscription 皆已無呼叫者）。
- Ina 之 `DROP TABLE owner_subscriptions` 前置條件（Sophie 端去引用 + 部署）：✅ 已完成。

## 執行者簽章
Sophie（Owner）

