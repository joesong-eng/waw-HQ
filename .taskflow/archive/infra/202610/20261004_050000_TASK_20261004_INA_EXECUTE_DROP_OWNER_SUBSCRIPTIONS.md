# 工單：DROP TABLE owner_subscriptions

## 任務 ID
TASK_20261004_INA_EXECUTE_DROP_OWNER_SUBSCRIPTIONS

## 優先級
P1

## 前置條件（已確認）
- Sophie commit c1072bc 部署完成，Owner 端 OwnerSubscription 引用 = 0 hits ✅
- Sidney commit 2f6e8bd 部署完成，SignalHub 端 OwnerSubscription 引用 = 0 hits ✅
- 兩站站點存活 HTTP 200 ✅

## 執行步驟

1. 確認無代碼引用（雙保險）：
   - 遠端 Owner：grep -rn 'owner_subscriptions' /www/wwwroot/iot.tg25.win/app/ = 0 hits
   - 遠端 SignalHub：grep -rn 'owner_subscriptions' /www/wwwroot/signal.tg25.win/app/ = 0 hits

2. 執行 DROP（只刪這一張表）：
   DROP TABLE owner_subscriptions;

3. 確認已不存在：
   SHOW TABLES LIKE 'owner_subscriptions'; -> 0 rows

## 注意
- subscription_audit_logs 保留不動，不要 DROP
- subscriptions 表保留不動

## 驗收指標
1. SHOW TABLES LIKE 'owner_subscriptions' = 0 rows
2. SHOW TABLES LIKE 'subscription_audit_logs' = 1 row（確認保留）
3. 兩站站點存活 HTTP 200

## 回報位置
.taskflow/infra/outbox/
