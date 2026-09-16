# 任務：20260915_MINA_FIX_AUTH_REDIRECT_HEADER

**派發時間**：2026-09-15 12:42  
**優先級**：high  
**負責人**：mina

---

## 📋 任務內容

[🚨 緊急-1] 修復 auth:sanctum 未認證 redirect 的 Header injection 500 錯誤

## 優先級：最高（使用者正在看到 500 崩潰畫面）

## 問題描述
加了 auth:sanctum 後，未認證使用者訪問受保護路由（/venue/*）回傳 HTTP 500 而非 302 redirect。
錯誤訊息：Header may not contain more than a single header, new line detected。
根因：session cookie 或 response header 中包含換行符（\n 或 \r\n），導致 PHP header() 函式拒絕發送。

## 預期結果（使用者視角）
未登入使用者點進 /venue/billing → 平順 302 redirect 到登入頁面（或首頁），不是 500。

## 排查方向
1. 檢查 bootstrap/app.php 中 redirectGuestsTo 的值是否含換行符
2. 檢查 config/session.php 的 domain / path / same_site 設定是否有異常字元
3. 檢查 .env 中 APP_URL、SESSION_DOMAIN、SANCTUM_STATEFUL_DOMAINS 是否含尾部空白或換行
4. 檢查是否有 middleware 在 response header 中注入含換行的值
5. 嘗試在 routes/web.php 用簡單的 return redirect("/") 測試是否也觸發同樣錯誤
6. 檢查 PHP 版本是否為 8.x（header injection protection 在 8.x 更嚴格）

## 修復後驗證（必做）
1. curl -I https://win.tg25.win/venue/billing → 應回 302（不是 500）
2. curl -I https://win.tg25.win/venue/devices → 應回 302
3. curl -I https://win.tg25.win/venue/subscriptions → 應回 302
4. 首頁 https://win.tg25.win/ → 200
5. play 頁 https://win.tg25.win/m/play → 200（確保修改不影響既有功能）

## 交付
- Commit 訊息：fix(auth): resolve header injection error in unauthenticated redirect
- 推送 origin/main
- 部署至 129.146.103.177
- 回報 curl 驗證結果至 outbox

---
**派發者**：HQ
**優先級**：CRITICAL — 立即執行，不要先做其他任務

---

## 📝 回報格式

```markdown
# 任務回報：20260915_MINA_FIX_AUTH_REDIRECT_HEADER

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
**派發時間**：2026-09-15 12:42
