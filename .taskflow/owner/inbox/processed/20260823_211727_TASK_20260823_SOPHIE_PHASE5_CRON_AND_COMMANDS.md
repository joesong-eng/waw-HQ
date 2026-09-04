# 任務：TASK_20260823_SOPHIE_PHASE5_CRON_AND_COMMANDS

**派發時間**：2026-08-23 21:17  
**優先級**：high  
**負責人**：owner

---

## 📋 任務內容

Sophie，經查證 Phase 1 ~ Phase 4（DB、後端服務、Controller API、前端 Blade/Alpine.js 視圖）均已落實並提交！

現在請執行《WAW IoT 訂閱與定價架構重構執行藍圖》之最後階段【第五階段：排程任務與自動化運維 (Cron & Console Layer)】：

1. T5.1 新建/實作  Command：
   - 運作時機：每月 1 號 00:01 執行。
   - 職責：為所有有效訂閱 (Subscription) 自動產出當期帳單 (BillingCycle)，計算本月使用天數與金額。
2. T5.2 新建/實作  Command：
   - 運作時機：月底前 1 天執行。
   - 職責：發送對帳與即將扣款/繳費提醒通知。
3. T5.3 新建/實作  Command：
   - 運作時機：每月 2 號 00:00 (或寬限期結束時) 執行。
   - 職責：將逾期未繳之訂閱狀態轉為 expired，自動移入灰字折疊區。
4. 於  (或 Laravel 11 routes/console.php) 註冊排程頻率。
5. 進行 PHP 語法檢查與測試，完成後提交 Phase 5 完工回報。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260823_SOPHIE_PHASE5_CRON_AND_COMMANDS

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：owner

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：owner  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-08-23 21:17
