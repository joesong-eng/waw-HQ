# 任務：老李端開立／刪除技術工程師帳號

**派工時間**：2026-09-20
**派工者**：HQ
**執行者**：Sophie
**優先級**：high
**前置**：Ina 已完成。`iotv9.users.role` 已含 `technician`，`expires_at` datetime NULL 已存在。Laravel migrations 已冪等且帳本 batch=19。本單**禁止**再寫 migration、禁止改 ENUM。

**關聯**：Sophie 自己的規格回報 `20260920_REPORT_TECH_OPERATOR_ROLE_SEPARATION_SPEC.md`

---

## 產品邊界（對使用者說話用正式詞，不要寫小猴）

兩個地方，兩種設定，不要混：

| 系統 | 誰用 | 設什麼 |
|---|---|---|
| `iot.tg25.win`（本單） | 機台主 | 場地、一分多少錢、開分上限、分潤。開／停／刪「技術工程師」帳號 |
| `signal.tg25.win`（**下一張 Sidney，本單不做**） | 技術工程師 | GPIO、Webhook、Callback、模擬器 |

機台主可開臨時技術帳給裝機人員。設完可刪。沒有外包人員時，機台主自己登 SignalHub 即可。技術帳**不准**看營收、分潤、銀行、訂閱。

UI 文案用「技術工程師」，不要用人名、不要內部暱稱。

---

## 現況（HQ 已核程式，不要重盤成另一套）

- `UserManagementController::store()` **寫死** `role = 'sub_agent'`，沒有 role 欄、沒有 `expires_at`
- `getUsersForRole()` owner 只看 `staff`, `sub_agent`，看不到 technician
- 無 `DELETE /users/{id}`
- `users.blade.php` 新增 Modal 只有姓名／信箱／密碼，無角色、無效期、無刪除
- `CheckUserManagementAccess` 只擋 `staff`, `sub_agent`
- `EnsureIotAccess` 白名單：`admin, owner, staff, sub_agent`。technician 現在會 403，這方向對，但要改成可讀提示並導去 SignalHub，不要空白 403
- `User::isExpired()` 已存在（Ina 加的），登入要接上

---

## 必做

### 1. 建立帳號 `POST /users`

- 新增驗證：`role` required，`in:staff,sub_agent,technician`
- 新增驗證：`expires_at` nullable，date，且必須 `>= now()`（或當天）。**僅 `role=technician` 允許填**；`staff` / `sub_agent` 送來 `expires_at` 直接忽略或 422
- `root_id`：owner 建帳 = 自己 id；admin 建帳仍要指定 `root_id`（維持現況）
- **禁止**再寫死 `sub_agent`
- 回傳 data 含 `role`, `expires_at`, `root_id`, `status`

### 2. 列表

- owner：`root_id = 自己` 且 role in `staff, sub_agent, technician`
- admin：維持看全部
- technician / staff / sub_agent：不可進 `/users`

### 3. 刪除 `DELETE /users/{id}`

- 僅允許刪 `role=technician`
- owner 只能刪 `root_id = 自己` 的帳
- 禁止刪自己、禁止刪 owner/admin/staff/sub_agent（那些繼續用既有啟用／停用）
- 有銀行資料也不准當擋刪理由——技術帳本來就不該有財務；若意外有 bankProfile，仍可刪帳，但**不要級聯亂刪財務表**。本單只刪 `users` 該列（或 status=0 + 軟刪，二選一；若軟刪必須讓同一 email 能再開新帳）
- 回傳 200 + 被刪 id

路由加在現有 `check.user.management.access` 群組：

```
Route::delete('users/{id}', [UserManagementController::class, 'destroy'])->name('users.destroy');
```

### 4. 更新（可選但建議）

- technician 允許改 `expires_at`（可清空=永不過期）
- 仍禁止改 `role`, `root_id`

### 5. 擋技術帳進營運後台

- `EnsureIotAccess`：**不要**把 technician 加進白名單
- technician 已登入打 `iot.tg25.win` 任何需 `iot.access` 的頁：redirect 到一個極簡說明頁（或 login 頁 flash），文案大意：「此帳號僅供技術對接，請前往 signal.tg25.win」。JSON 請求回 403
- `CheckUserManagementAccess` 把 `technician` 加入阻擋清單
- `index()` 現在只 redirect staff，一併擋 technician

### 6. 過期帳號不可登入

- Owner `Authv9Controller::login`：`isExpired()` 為 true 則失敗，錯誤「帳號已過期」
- 不要在本單改 SignalHub 登入（Sidney）

### 7. `users.blade.php` UI（大字、高對比、間距緊、標籤照下面）

新增 Modal 加：

- 角色下拉：**員工** / **子代理** / **技術工程師**。預設員工
- 選「技術工程師」才顯示效期日期（可空白=永不過期）與一句說明：「此帳號只能設定機台訊號對接，看不到營業與分潤。設定完成後可刪除。」
- Legend 加技術工程師色點（不要跟既有 admin/owner/staff/sub_agent 撞色）
- 表格姓名色碼：`technician` 用新色
- technician 列提供 **刪除**（二次確認：「確定刪除此技術工程師帳號？」）。員工／子代理不要出現刪除
- 可顯示效期；空白顯示「永久」

---

## 不做

- 不改 SignalHub、不做 SSO、不發 Token 跳轉
- 不改設備 setup 彈窗（一分多少錢仍是機台主的事）
- 不新 migration、不改 `users.role` ENUM
- 不在本機跑 php artisan / 測 DB
- 不自己 production migrate（已做完）

---

## 驗證（遠端，回報必須貼輸出／截圖）

1. owner 登入 `/users`，新增「技術工程師」成功。DB：`role=technician`, `root_id=該 owner`, `expires_at` 符合表單
2. 同一 owner 再新增員工，角色必須是 `staff` 或所選值，**不再默默變成 sub_agent**
3. 列表看得到技術工程師；刪除後該列消失，`users` 無此 id（或軟刪後無法再登入且 email 可重用，需在回報寫清選了哪種）
4. 用該技術帳登 `iot.tg25.win`：進不了 dashboard／users／營收。有導向說明，不是裸 403 空白
5. 把 `expires_at` 設成過去時間，Owner 登入失敗
6. owner 不能刪別人的 technician；不能刪 staff
7. commit + push Owner。**先不要 deploy**，等 HQ 核過再部署（deploy 會 migrate --force，Ina 已收口，但仍由 HQ 開燈）

回報含：改動檔案、commit hash、上述 1–6 的遠端證據。
