# 任務：通知系統建置 Phase A - 接通事件鏈

**任務 ID**: TASK_20260828_SOPHIE_NOTIFICATION_SYSTEM_PHASE_A
**優先級**: high
**派發時間**: 2026-08-28
**派發者**: HQ

---

## 背景

通知系統的 Service / Listener / Event 類別已存在，但事件從未被觸發，且 EventServiceProvider 未被註冊。本任務補齊三個關鍵缺口，讓訂閱通知流程正式接通。

---

## 工作範圍

### A1. 建立並註冊 EventServiceProvider

新增 `PROJECT/Owner/app/Providers/EventServiceProvider.php`，內容如下：

```php
<?php

namespace AppProviders;

use IlluminateFoundationSupportProvidersEventServiceProvider as ServiceProvider;

class EventServiceProvider extends ServiceProvider
{
    protected $listen = [
        AppEventsBillingRequestSubmitted::class => [
            AppListenersSendBillingRequestNotification::class,
        ],
        AppEventsBillingRequestReviewed::class => [
            AppListenersSendBillingReviewNotification::class,
        ],
        AppEventsRenewalReminderNeeded::class => [
            AppListenersSendRenewalReminderNotification::class,
        ],
        AppEventsSubscriptionExpired::class => [
            AppListenersSendSubscriptionExpiredNotification::class,
        ],
    ];
}
```

在 `PROJECT/Owner/bootstrap/providers.php` 的 return 陣列中加入：
`AppProvidersEventServiceProvider::class`

---

### A2. BillingService 加入 event() dispatch

檔案：`PROJECT/Owner/app/Services/BillingService.php`

1. **submitBatchRequest()**：在 `return $request;` 之前加入：
   ```php
   event(new AppEventsBillingRequestSubmitted($request));
   ```

2. **approveRequest()**：在 DB::transaction 結束後（`}); // end transaction` 之後）加入：
   ```php
   $request->refresh();
   event(new AppEventsBillingRequestReviewed($request, true));
   ```

3. **rejectRequest()**：在 `$request->save();` 之後加入：
   ```php
   event(new AppEventsBillingRequestReviewed($request, false));
   ```

---

### A3. routes/console.php 加入 renewal reminder 排程

在既有排程區塊末尾加入：

```php
// 每日 09:30 發送訂閱即將到期提醒
Schedule::command('subscription:send-reminders')
    ->dailyAt('09:30')
    ->timezone('Asia/Taipei')
    ->withoutOverlapping()
    ->onOneServer();
```

---

## 完成標準

1. 所有修改本機 commit + push（建議分兩個 commit：A1/A2 一個，A3 一個）
2. 執行 `waw_ops.sh deploy sophie` 部署到遠端
3. 回報中列出：
   - 各修改檔案清單
   - commit hash（兩個）
   - deploy 結果
4. **注意**：不需驗證通知實際送達（LINE API key 正式值待 HQ 確認）；只需確認事件鏈程式碼正確接通、無 PHP 語法錯誤

---

**完成後請執行回報腳本**：
```bash
bash ../../dev_tools/agent_report_to_hq_v2.sh sophie _agent/REPORT_<YYYYMMDD>_<HHMMSS>_TASK_20260828_SOPHIE_NOTIFICATION_SYSTEM_PHASE_A.md
```
