# 工單：清理 OwnerSubscription 引用（修訂版）

## 任務 ID
TASK_20261004_SOPHIE_CLEANUP_OWNER_SUBSCRIPTION_REFS

## 優先級
P1

## 架構依據
ADR-003_SUBSCRIPTION_TABLE_UNIFICATION.md（已修訂）

## 背景
Ina 實測發現：
- subscriptions 表已有 subscriber_id=12 的記錄（id=30/31），資料早已遷移
- owner_subscriptions 表尚未 DROP，需先改代碼再 DROP
- subscription_audit_logs 保留不動（是 subscriptions 的稽核表）

## 你的任務（僅改代碼，不碰 DB）

### 需清理的引用清單（Ina 盤點）
1. app/Models/OwnerSubscription.php -> 刪除或改寫
2. app/Services/SubscriptionService.php -> 確認使用 Subscription（非 OwnerSubscription）
3. app/Console/Commands/CheckSubscriptionExpiry.php -> 改用 Subscription Model
4. app/Http/Controllers/OtaController.php -> 改用 Subscription Model
5. app/Models/User.php hasOne(OwnerSubscription) -> 改為 Subscription
6. app/Services/NotificationService.php -> 改用 Subscription
7. app/Events/SubscriptionExpired.php / SubscriptionExtended.php / RenewalReminderNeeded.php -> 改用 Subscription

### 步驟
1. grep -rn 'OwnerSubscription' app/ routes/ config/ -> 確認所有引用
2. 逐一改用 Subscription Model
3. 確認 routes/api.php 無 owner_subscriptions 殘留路由
4. 部署到遠端
5. 確認站點功能正常

## 驗收指標
1. grep -rn 'OwnerSubscription' app/ routes/ config/ = 0 hits
2. Owner 後台訂閱管理功能正常
3. curl -sI https://iot.tg25.win/ = HTTP 200

## 回報位置
.taskflow/owner/outbox/
