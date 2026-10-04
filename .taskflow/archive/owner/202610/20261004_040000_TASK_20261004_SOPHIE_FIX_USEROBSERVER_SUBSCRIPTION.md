# 工單：移除 UserObserver initializeSubscription 呼叫

## 任務 ID
TASK_20261004_SOPHIE_FIX_USEROBSERVER_SUBSCRIPTION

## 優先級
P1（現有 bug：新 owner 帳號無法建立）

## 背景
HQ 裁定選項 (b)：移除 UserObserver 對 initializeSubscription 的呼叫。
理由：現無收費機制，訂閱由帳務流程手動建立，不自動化。

## 修改內容

### 1. app/Observers/UserObserver.php
找到 created() 方法中呼叫 initializeSubscription 的那一行，移除或註解掉。

### 2. app/Http/Middleware/EnsureProSubscription.php
確認 isSubscriptionActive / getSubscriptionStatus 是否無定義。
若此 middleware 無任何路由掛載，直接刪除整個檔案。
若有路由掛載，移除那兩行呼叫並改為直接查 Subscription Model。

## 驗收指標
1. Tinker: User::create(role=owner) 不拋錯
2. grep -rn 'initializeSubscription' app/ = 0 hits
3. grep -rn 'isSubscriptionActive' app/ = 0 hits
4. curl -sI https://iot.tg25.win/ = HTTP 200
5. 部署到遠端

## 回報位置
.taskflow/owner/outbox/
