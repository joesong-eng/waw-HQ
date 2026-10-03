# 回報：TASK_20260920_SOPHIE_FIX_TECHNICIAN_LOGIN_LOOP（遠端證據補交）

**回報時間**：2026-09-21
**執行者**：Sophie
**狀態**：✅ 已 deploy（9e8845e）+ 三項遠端驗證全過

---

## 遠端現況

```
遠端 git log:
9e8845e fix(auth): block technician at login + logout before redirect
bfb7b48 feat(users): technician account management
749ca95 fix: make technician migration idempotent
```

Deploy 由 Sophie 自行執行 `waw_ops.sh deploy owner`，遠端已到 9e8845e。

---

## 三項遠端證據

### ✅ 驗證 1：technician POST /login → Location 鏈

**做法**：tinker 建 technician 測試帳（techtest@tg25.win, id=14, role=technician, expires_at=null），curl POST /login。

```
HTTP/2 302
location: https://iot.tg25.win/login
```

login 頁渲染：
```
此帳號僅供技術對接，請前往 signal.tg25.win 進行機台訊號設定。
```

**結論**：302 回 /login（不是 /portal），無迴圈，$errors->first('email') 有文案。

---

### ✅ 驗證 2：人工 session 打 /portal

**做法**：owner 登入取得 session → tinker 將 role 改 technician → 用同一 session cookie GET /portal。

```
HTTP/2 302
location: https://iot.tg25.win/login
```

login 頁渲染：
```
此帳號僅供技術對接，請前往 signal.tg25.win 進行機台訊號設定。
```

**結論**：EnsureIotAccess 對 technician 先 Auth::logout + invalidate + regenerateToken，再 redirect /login。無限 302 迴圈不再發生。

---

### ✅ 驗證 3：過期帳文案

**做法**：tinker 設 technician expires_at=2026-09-19（昨天），curl POST /login。

```
HTTP/2 302
location: https://iot.tg25.win/login
```

login 頁渲染：
```
帳號已過期，請聯絡機台主重新開立。
```

**結論**：isExpired() 在 session regenerate 前攔截，logout + withErrors，文案正確。

---

## 清理

- techtest@tg25.win (id=14) 已硬刪
- owner id=2 role 已恢復 owner
- 遠端 /tmp 測試 PHP 已清

---

## 防禦層次

| 層 | 位置 | 行為 |
|---|---|---|
| 第一層 | Authv9Controller::login | isExpired() 後查 role=technician → logout + withErrors |
| 第二層 | EnsureIotAccess | 萬一有 session 繞過 login → logout + redirect /login withErrors |
| 第三層 | CheckUserManagementAccess | technician 無法進 /users 管理頁 |

technician 從碼上、從行為上，都進不了營運後台。

