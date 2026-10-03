# 工單：DB 遷移 — 廢除 owner_subscriptions，資料搬到 subscriptions

## 任務 ID
TASK_20261004_INA_DROP_OWNER_SUBSCRIPTIONS

## 優先級
P1

## 架構依據
ADR-003_SUBSCRIPTION_TABLE_UNIFICATION.md

## 背景
JOE 裁定：保留 subscriptions 表為唯一訂閱 SSOT，廢除 owner_subscriptions。
你需要執行 DB 資料搬遷和表刪除。

## 步驟
1. 確認 owner_subscriptions 表內容（應僅 2 筆）
   - owner_id=12（家寶科技，有效）要搬
   - owner_id=11（孤兒，無對應 user）不搬

2. 將 owner_id=12 的記錄搬到 subscriptions 表：
   INSERT INTO subscriptions (subscriber_id, service_type, target_id, tier_code, quota_limit, selected_target_ids, status, started_at, expires_at, billing_request_id, created_at, updated_at)
   SELECT owner_id, 'device_service', NULL, 'basic', NULL, NULL, status, start_date, end_date, NULL, created_at, updated_at
   FROM owner_subscriptions WHERE owner_id = 12;

3. 確認 subscriptions 表新增了這筆記錄

4. DROP TABLE subscription_audit_logs（FK 指向 owner_subscriptions，先刪）

5. DROP TABLE owner_subscriptions

6. 回報 SQL 執行結果 + 驗證截圖

## 驗收指標
1. SELECT * FROM owner_subscriptions -> 表不存在
2. SELECT * FROM subscription_audit_logs -> 表不存在
3. SELECT * FROM subscriptions WHERE subscriber_id=12 -> 有記錄

## 回報位置
.taskflow/infra/outbox/
