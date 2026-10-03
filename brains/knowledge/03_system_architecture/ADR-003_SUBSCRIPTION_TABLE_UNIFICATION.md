# ADR-003：訂閱表統一為 subscriptions，廢除 owner_subscriptions

> **文件類型**：Architecture Decision Record
> **決策者**：JOE
> **建立日期**：2026-10-04
> **狀態**：Accepted（已修訂）
> **Supersedes**：ADR-001 決策一（owner_subscriptions 為 SSOT 部分）
> **修訂記錄**：2026-10-04 Ina 實測後修正 Schema 描述與執行順序

---

## 1. 背景

Sophie 在 SOPHIE_CONSOLIDATED 階段三驗證中發現雙軌表並存問題。
Ina 實測後進一步發現：

| 問題 | 說明 |
|------|------|
| 雙軌表並存 | iotv9 同時存在 owner_subscriptions（2 筆）與 subscriptions（35 筆） |
| 資料已遷移 | subscriptions.id=30/31 的 subscriber_id=12 與 owner_subscriptions.id=1 的 started_at/expires_at 完全一致，資料早已搬過 |
| 孤兒記錄 | owner_subscriptions.owner_id=11 無對應 users |
| audit_logs 歸屬錯誤 | subscription_audit_logs 實際是 subscriptions 的稽核表（無 FK 指向 owner_subscriptions），不應 drop |

## 2. 決策

保留 subscriptions 表為唯一訂閱 SSOT，廢除 owner_subscriptions 表。

### 修正事項
1. 資料遷移步驟省略（subscriptions 已有 subscriber_id=12 的記錄）
2. subscription_audit_logs 保留（非 owner_subscriptions 子表，是 subscriptions 現行稽核表）
3. 執行順序反轉：先改代碼並部署，後 DROP 表

## 3. 修訂後執行順序

### 步驟 1：Sophie + Sidney 並行改代碼（不依賴 DB 變更）

#### Sophie (Owner) — 清理 OwnerSubscription 引用
1. 刪除或改寫 app/Models/OwnerSubscription.php
2. CheckSubscriptionExpiry.php 改用 Subscription Model
3. OtaController.php 改用 Subscription Model
4. User.php hasOne(OwnerSubscription) 改為 Subscription
5. NotificationService.php + Events 改用 Subscription
6. 部署到遠端

#### Sidney (SignalHub) — 切換 Model
1. 刪除 app/Models/OwnerSubscription.php
2. 新增 app/Models/Subscription.php（指向 subscriptions 表）
3. EnsureSubscriptionActive middleware 改用 Subscription
4. SignalHubController subscriptionStatus 改用 Subscription
5. User.php 關聯改指向 Subscription
6. 部署到遠端

### 步驟 2：Ina 確認代碼去引用完成後執行 DROP

1. 確認 Sophie + Sidney 已部署且站點正常
2. DROP TABLE owner_subscriptions（僅此一表）
3. 不 DROP subscription_audit_logs（保留）

## 4. subscriptions 表實際 schema（Ina 實測）

service_type enum('device','venue') NOT NULL
target_id bigint unsigned NOT NULL
tier_code varchar(50) NULL
subscriber_id (FK 到 users.id)
started_at datetime NOT NULL
expires_at datetime NOT NULL
quota_limit, selected_target_ids, status, billing_request_id

## 5. 驗收指標

1. Owner: grep -rn OwnerSubscription app/ routes/ = 0 hits
2. SignalHub: grep -rn OwnerSubscription app/ = 0 hits
3. 兩站站點存活 + 訂閱功能正常
4. Ina 確認代碼去引用後 DROP owner_subscriptions
5. subscription_audit_logs 保留不動
