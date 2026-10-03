# 回報：TASK_20260920_SOPHIE_FIX_TECHNICIAN_LOGIN_LOOP

**回報時間**：2026-09-21
**執行者**：Sophie
**狀態**：✅ commit + push 完成，等 HQ deploy 後遠端驗證

---

## Commit

```
9e8845e  fix(auth): block technician at login + logout before redirect
```

Push 到 `origin/main` 成功。

---

## 根因分析

| 步驟 | 問題 |
|---|---|
| login 成功 → `redirect()->intended(portal)` | technician 被放進去 |
| portal 在 `iot.access` | EnsureIotAccess 觸發 |
| 舊版：`redirect()->route('login')->with('error')` | 沒有 logout，session 仍有 auth |
| `login` 在 `guest`，已登入 → `redirectUsersTo('/portal')` | 無限 302 |
| login 頁只讀 `$errors`，不讀 `session('error')` | 說明文案永遠不顯示 |

---

## 修法

### Authv9Controller::login
`isExpired()` 之後立即檢查 role：
```php
if ($loggedUser->role === 'technician') {
    Auth::logout();
    $request->session()->invalidate();
    $request->session()->regenerateToken();
    return back()->withErrors([
        'email' => '此帳號僅供技術對接，請前往 signal.tg25.win 進行機台訊號設定。',
    ])->onlyInput('email');
}
```
technician **永遠進不了** `redirect()->intended(portal)`。

### EnsureIotAccess（防禦層）
Web 分支先 logout 再 redirect，改用 withErrors：
```php
Auth::logout();
$request->session()->invalidate();
$request->session()->regenerateToken();
return redirect()->route('login')->withErrors([
    'email' => '此帳號僅供技術對接，請前往 signal.tg25.win 進行機台訊號設定。',
]);
```

---

## 驗證（deploy 後需遠端確認）

工單要求的 3 項驗證，deploy 後透過 tinker 建測試帳再確認：

1. technician POST /login → 停在 login，`$errors->first('email')` 含 signal.tg25.win，不 302 到 portal
2. 若人工 Auth::login 再 GET /portal → logout → 停在 login（無限 302 不再發生）
3. 過期帳仍失敗「帳號已過期，請聯絡機台主重新開立。」

---

## 注意

- 仍未 deploy（等 HQ 開燈）
- technician 不在白名單，EnsureIotAccess 防禦層保留（萬一繞過 login 直接有 session 時仍會擋）

