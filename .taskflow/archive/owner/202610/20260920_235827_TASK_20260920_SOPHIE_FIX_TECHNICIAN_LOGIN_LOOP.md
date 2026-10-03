# 補單：技術工程師登 iot.tg25.win 會 login↔portal 迴圈，先修再開燈

**派工時間**：2026-09-20
**派工者**：HQ
**執行者**：Sophie
**優先級**：high
**前置**：`bfb7b48` 功能碼 HQ 已讀。**禁止 deploy。**

---

## HQ 審核結論

CRUD / 角色下拉 / 刪除 / `expires_at` / 不再寫死 `sub_agent`：**通過（碼審）**。  
遠端行為 1–6：**未驗**（你也寫等 HQ deploy）。  
**開燈條件未過**，因為擋營運後台這段會自己打轉。

---

## 必現路徑（不要辯）

1. `Authv9Controller::login` 成功後 `redirect()->intended(route('portal'))`
2. `portal` 在 `auth` + `iot.access`
3. `EnsureIotAccess` 對 technician：`redirect()->route('login')->with('error', '...')` **沒有 logout**
4. `login` 在 `guest`；`bootstrap/app.php` `redirectUsersTo('/portal')`
5. 已登入 technician 打 `/login` → 被丟回 `/portal` → 再被丟 `/login` → 迴圈

附加：login 頁只渲染 `$errors`，**不讀** `session('error')`。就算沒迴圈，說明文案也不會出現。工單要的是「有導向說明，不是裸 403 空白」，現況兩邊都不成立。

---

## 必改（最小）

### 1. 登入當下就擋，不要先放進 portal

`Authv9Controller::login`：`isExpired()` 之後立刻查 role。

- `role === 'technician'`：logout + invalidate session + regenerateToken，`back()->withErrors(['email' => '此帳號僅供技術對接，請前往 signal.tg25.win 進行機台訊號設定。'])`
- **不要** `intended('portal')`

過期帳現有文案保留。

### 2. 中介層先登出，再去 login

`EnsureIotAccess` technician 分支：

- JSON：維持 403 現有訊息
- Web：`Auth::logout()`、`session()->invalidate()`、`regenerateToken()`，然後 `redirect()->route('login')->withErrors(['email' => '此帳號僅供技術對接，請前往 signal.tg25.win 進行機台訊號設定。'])`
- 禁止再用 `with('error')`（login 頁吃不到）
- 仍**不要**把 technician 加進白名單

### 3. 驗證（遠端，本單仍先不要 HQ 全站 deploy）

你可在遠端用 tinker 建一個測試 technician（`root_id` 指向既有 owner，`status=1`，`expires_at=null`），**不要**對 production 亂開真帳。

必貼：

1. 該帳 POST `/login`：停在 login，錯誤含 `signal.tg25.win`，**不會** 302 到 portal
2. 若先人工 `Auth::login` 再 GET `/portal`：最終停在 login（guest），不是無限 302
3. 過期帳仍失敗「帳號已過期」
4. commit + push。**仍不要**跑 `waw_ops.sh deploy`

測完刪掉測試帳（硬刪即可）。回報含 commit hash 與 curl/log 證據（Location 鏈、最終 URL、錯誤字串）。
