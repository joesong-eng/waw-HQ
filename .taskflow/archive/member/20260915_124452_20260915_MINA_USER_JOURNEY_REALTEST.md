# 任務：20260915_MINA_USER_JOURNEY_REALTEST

**派發時間**：2026-09-15 12:44  
**優先級**：high  
**負責人**：mina

---

## 📋 任務內容

[🎯 驗收] 以使用者路徑做一次完整真實回測

## 優先級：HIGH（緊急-1 和 緊急-2 完成後立刻做）
## 前置條件：Header injection 500 和 SSL CA bundle 都修好了再做

## 重要原則
不要再看 php -l 或 commit log。
用真實的 HTTP 請求（curl 或瀏覽器），模擬玩家、店家、營運商的完整操作路徑。

---

## 路徑一：玩家掃碼進場
1. curl https://win.tg25.win/ → 200？頁面有正常 HTML 內容？Vue app 有渲染？
2. 未登入狀態直接訪問 /m/play → 應該導向登入（302）還是顯示頁面？記錄實際行為
3. 未登入訪問 /venue/billing → 應該 302 redirect，不是 500
4. LINE 登入流程：/auth/line/redirect → 能正常跳轉到 LINE OAuth？redirect_uri 是否正確？

## 路徑二：開分 / 遊戲中
5. /api/device/{chip_id}/check-session → 回應正常？不報 SSL 錯？
6. fetchDeviceActiveStatus() 能成功打到 Infra API？
   測試：curl -H "X-Internal-Key: v9-internal-key-2026" https://api.tg25.win/api/device/SR9ADYXPDYT1TUF7/active-status
   → 應回 JSON，不是 cURL error 60
7. WebSocket /broadcasting/auth → Private Channel 授權正常？（已登入狀態）

## 路徑三：洗分 / 離場
8. 洗分 callback 端點是否正常接收？
9. CheckOfflineSessions cron：php artisan check:offline-sessions → 正常執行？不報 SSL 錯？

## 路徑四：Venue 營運商頁面
10. 已登入（如果有帳號）訪問 /venue/devices → 200？
11. 已登入訪問 /venue/billing → 200？且銀行帳號已遮罩？
12. 已登入訪問 /venue/subscriptions → 200？

---

## 回報格式
每一步回報：
- 端點 URL
- HTTP Status Code
- 關鍵 response 內容（截取前 200 字元）
- ✅ 正常 / ❌ 異常 + 異常描述

若有任何一步失敗，**立刻停止回測，先回報問題給 HQ**，不要繼續往下走。

---
**派發者**：HQ
**優先級**：HIGH — 緊急-1 和 緊急-2 完成後立即執行

---

## 📝 回報格式

```markdown
# 任務回報：20260915_MINA_USER_JOURNEY_REALTEST

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：mina

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：mina  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-09-15 12:44
