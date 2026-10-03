# 工單：Model 切換 — OwnerSubscription 改為 Subscription（修訂版）

## 任務 ID
TASK_20261004_SIDNEY_SWITCH_TO_SUBSCRIPTION_MODEL

## 優先級
P1

## 架構依據
ADR-003_SUBSCRIPTION_TABLE_UNIFICATION.md（已修訂）

## 背景
Ina 實測發現：
- subscriptions 表已有 subscriber_id=12 的記錄，資料早已遷移
- owner_subscriptions 表尚未 DROP，需先改代碼再 DROP
- subscriptions 表實際 schema：service_type enum('device','venue'), target_id NOT NULL, tier_code varchar, started_at/expires_at datetime

## 你的任務（僅改代碼，不碰 DB）

### 步驟
1. 刪除 app/Models/OwnerSubscription.php
2. 新增 app/Models/Subscription.php：
   - table = subscriptions
   - fillable: subscriber_id, service_type, target_id, tier_code, quota_limit, selected_target_ids, status, started_at, expires_at, billing_request_id
   - belongsTo(User::class, 'subscriber_id')
   - 保留 scopes: active, expiringWithinDays, expiredWithGrace
3. 更新 EnsureSubscriptionActive middleware：
   - use App\Models\Subscription
   - 查詢改為 Subscription::where('subscriber_id', ->id)
4. 更新 SignalHubController subscriptionStatus()：
   - 改用 Subscription Model
5. 更新前端橫幅 API 資料來源
6. User.php 關聯改指向 Subscription
7. 部署到遠端

## 驗收指標
1. grep -rn 'OwnerSubscription' app/ = 0 hits
2. Tinker: new App\Models\Subscription() 可載入
3. GET /api/v9/subscription/status = 200 JSON
4. enforce=false 站點功能不受影響
5. curl -sI https://signal.tg25.win/ = HTTP 200

## 回報位置
.taskflow/signalhub/outbox/
