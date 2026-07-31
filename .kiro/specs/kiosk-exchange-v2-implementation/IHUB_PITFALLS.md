# iHub 坑記錄與經驗總結

> **最後更新**：2026-05-09 UTC+8  
> **目的**：記錄 iHub 開發過程中踩過的所有坑，重寫前必讀，不得重蹈覆轍。  
> **適用對象**：Hubie（iHub 開發）、HQ（審核）

---

## 🔴 現有 Bug（重寫時必須修正）

### Bug 1：`/api/kiosk/complete` 傳錯欄位

**現象**：點擊「確認完成」或「強制結束」按鈕，session 無法結束，API 回 422。

**根本原因**：
- iHub 發送：`{ kiosk_id: "kiosk_000", reason: "..." }`
- Member `complete()` 驗證：`$request->validate(['session_id' => 'required|integer'])`
- 欄位名稱完全不對，Member 要的是 `session_id`（整數），不是 `kiosk_id`（字串）

**正確做法**：
```javascript
body: JSON.stringify({
    session_id: currentSessionId,  // 從 .MemberBoundToKiosk 事件取得
    reason: reason === 'manual' ? 'ihub_force_ended' : 'ihub_timeout'
})
```

**注意**：`currentSessionId` 必須在 `.MemberBoundToKiosk` 事件中儲存：`currentSessionId = e.session_id`

---

### Bug 2：`KioskSessionUpdated` 事件欄位讀錯

**現象**：入帳後餘額不更新，動畫顯示的 token 數量為 undefined。

**根本原因**：
- iHub 讀：`e.balance`、`e.amount`
- 實際 payload（`KioskSessionUpdated::broadcastWith()`）：

| iHub 讀的欄位 | 實際欄位名稱 |
|-------------|------------|
| `e.balance` | `e.member_balance` |
| `e.amount` | `e.tokens_credited` |

**正確做法**：
```javascript
channel.listen('.KioskSessionUpdated', (e) => {
    memberBalance = e.member_balance;       // 不是 e.balance
    lastDepositedAmount = e.total_deposited;
    const tokensThisRound = e.tokens_credited; // 不是 e.amount
    // ...
});
```

完整 payload 欄位見 `design.md` 第 10.6 章。

---

### Bug 3：QR Code 內容格式不符規範

**現象**：Member 手機掃碼後可能解析失敗（取決於 Member bind 端點的解析邏輯）。

**根本原因**：
- iHub 生成：`https://win.tg25.win/kiosk?token={token}&kiosk={kiosk_id}`（URL 格式）
- 規範格式：`KIOSK:{kiosk_id}:TOKEN:{token}`（純字串）

**正確做法**：
```javascript
await generateQR(`KIOSK:${KIOSK_ID}:TOKEN:${data.token}`);
```

**確認**：Member `bind()` 端點解析的是純字串格式，不是 URL。

---

## 🟡 歷史坑（已修正，但原因要記住）

### 坑 1：WebSocket 頻道大小寫不一致

**發生日期**：2026-04-30  
**現象**：掃碼成功後 iHub 畫面不跳轉。  
**根本原因**：Member 廣播用小寫 `kiosk.kiosk_001`，iHub 訂閱用大寫 `kiosk.KIOSK_001`。  
**規則**：WebSocket 頻道名稱**永遠小寫**，訂閱時加 `.toLowerCase()`。

```javascript
// ✅ 正確
const channel = window.Echo.channel(`kiosk.${KIOSK_ID.toLowerCase()}`);
```

---

### 坑 2：`.MemberBoundToKiosk` 檢查錯誤欄位

**發生日期**：2026-05-08  
**現象**：收到事件但 `result=undefined`，畫面不跳轉。  
**根本原因**：設計文件寫錯，iHub 檢查 `event.result === 'success'`，實際欄位是 `event.status === 'bound'`。  
**規則**：

```javascript
// ✅ 正確
channel.listen('.MemberBoundToKiosk', (e) => {
    if (e.status === 'bound') {  // 不是 e.result
        // ...
    }
});
```

---

### 坑 3：sim-bill 加了一半的功能（heartbeat 405）

**發生日期**：2026-05-08  
**現象**：sim-bill 顯示「💔 心跳發送失敗」。  
**根本原因**：Hubie 在 sim-bill 加了 heartbeat 功能（前端 + server/index.js 路由），但沒有在 nginx 加對應的 proxy_pass。  
**規則**：新增任何 API 路由，必須同時確認 nginx 有對應的 proxy 設定。新功能清單：前端 + 後端 + nginx + 驗證，缺一不可。

---

### 坑 4：QR Code token 每次心跳都換

**發生日期**：2026-04-30  
**現象**：掃碼後出現「QR Code 已過期或無效」。  
**根本原因**：`refreshToken()` 每次 iHub 心跳都換新 token，但 QR Code 顯示的是舊 token。  
**修復**：token 只有過期才換，不是每次心跳都換。  
**規則**：QR Code token 的生命週期由 Member 管理，iHub 只是顯示，不要自己管理 token 更新邏輯。

---

### 坑 5：bind 成功但瞬間顯示錯誤 modal（競態條件）

**發生日期**：2026-04-30  
**現象**：bind 成功，但同時出現「儲值機連線失敗」錯誤畫面。  
**根本原因**：`bindToKiosk` 的 `finally` 區塊將 `loadingKiosk = false`，Vue 重新渲染時 `kioskBindResult` 是 null，`v-else` 瞬間顯示錯誤畫面（競態條件）。  
**規則**：bind 成功後立刻關閉 modal，不要等 `finally`。

---

### 坑 6：Laravel Scheduler 未設定，殭屍 session 累積

**發生日期**：2026-04-30  
**現象**：每次掃碼成功後 session 60 秒就被殺，紙鈔機退鈔。  
**根本原因**：yd47 沒有設定 crontab，`closeIdleSessions` 從未執行，殭屍 session 累積，下次掃碼被 409 擋。  
**修復**：yd47 已加入 crontab：`* * * * * cd /www/wwwroot/win.tg25.win && php artisan schedule:run >> /dev/null 2>&1`  
**規則**：這是 Member 端的問題，但 iHub 遇到 409 時要顯示清楚的錯誤訊息，不要讓用戶看到空白或無意義的錯誤。

---

### 坑 7：node-id API 422（deviceId 為空）

**發生日期**：tasks 14.4d  
**現象**：`GET /api/kiosk/node-id` 回 422。  
**根本原因**：`deviceId` 是 `undefined` 或空字串時，API 被呼叫但 `screen_mac` 參數為空。  
**規則**：呼叫 node-id API 前必須確認 `deviceId` 非空，否則顯示錯誤而非呼叫 API。

```javascript
if (!deviceId) throw new Error('無法讀取設備識別碼');
```

---

### 坑 8：錯誤畫面 landscape 版面溢出

**發生日期**：tasks 14.4e  
**現象**：橫屏時錯誤畫面文字溢出螢幕。  
**根本原因**：`showErrorScreen()` 使用硬編碼 px 尺寸，橫屏時 viewport 高度不夠。  
**規則**：所有尺寸使用 `clamp()` 或 `vw/vh`，不要硬編碼 px。

---

### 坑 9：idle countdown 初始值顯示錯誤

**發生日期**：tasks 14.4c  
**現象**：idle 倒數顯示 60 秒，但實際是 300 秒。  
**根本原因**：HTML 初始值硬編碼為 `60`，但 `resetIdleTimer(300)` 設定 300 秒。  
**規則**：HTML 初始值要跟 JS 邏輯一致，或者由 JS 在初始化時設定，不要在 HTML 硬編碼。

---

## 📋 重寫 iHub 前的檢查清單

重寫 `main.js` 前，對照以下清單確認每一項：

### API 呼叫
- [ ] `/api/kiosk/token`：body `{ kiosk_id }` ✅
- [ ] `/api/kiosk/complete`：body `{ session_id, reason }` ← **Bug 1，必須用 session_id**
- [ ] `/api/kiosk/escrow/confirm`：body `{ kiosk_id }` ✅
- [ ] `/api/kiosk/escrow/reject`：body `{ kiosk_id }` ✅
- [ ] 所有 API 都帶 `X-Internal-Key` header ✅

### WebSocket 事件
- [ ] 訂閱頻道：`kiosk.${KIOSK_ID.toLowerCase()}` ✅
- [ ] `.MemberBoundToKiosk`：檢查 `e.status === 'bound'`，不是 `e.result` ✅
- [ ] `.KioskEscrowPending`：payload 欄位 `e.amount`、`e.tokens`、`e.member.name`、`e.member.phone` ✅
- [ ] `.KioskSessionUpdated`：用 `e.member_balance`（不是 `e.balance`）、`e.tokens_credited`（不是 `e.amount`）← **Bug 2**
- [ ] `.KioskSessionEnded`：收到後轉 completed 狀態 ✅

### Session 管理
- [ ] `.MemberBoundToKiosk` 時儲存 `currentSessionId = e.session_id` ✅
- [ ] complete 時傳 `session_id`，不是 `kiosk_id` ← **Bug 1**
- [ ] reason 值：`ihub_force_ended`（手動）、`ihub_timeout`（超時）✅

### QR Code
- [ ] 格式：`KIOSK:${KIOSK_ID}:TOKEN:${token}` ← **Bug 3，不是 URL 格式**
- [ ] token 只有過期才換，不是每次心跳都換 ✅

### UI
- [ ] 所有尺寸用 `clamp()` 或 `vw/vh`，不硬編碼 px ✅
- [ ] 倒數初始值由 JS 設定，不在 HTML 硬編碼 ✅
- [ ] 新增 API 路由時同步確認 nginx proxy ✅

### 接口對照
- [ ] 所有 payload 欄位名稱對照 `design.md` 第 10 章，不猜測 ✅

---

## 📌 重寫原則

1. **先讀 design.md 第 10 章**，所有接口欄位名稱以那裡為準，不猜測
2. **每個 API 呼叫都要有 error handling**，失敗時顯示清楚的錯誤訊息
3. **新增功能前列出完整清單**：前端 + 後端 + nginx + 驗證，缺一不可
4. **不要在 HTML 硬編碼動態數值**，由 JS 初始化時設定
5. **WebSocket 頻道名稱永遠小寫**
6. **完成後 HQ 親自 curl 驗證**，不接受口頭回報
