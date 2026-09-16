# 主動建議：Owner 端 LINE Login P0-2 修法 Patch 草案（v2，與 Mina 風格對齊）

**提出時間**：2026-09-14 12:30
**提出者**：Sophie (Owner)
**對應派工單**：`TASK_20260914_SOPHIE_LINE_SECRET_ROTATION`（中途發現的盲點）
**狀態**：🟡 待 HQ 裁決是否派工執行
**v2 改動**：根據 Mina (Member) 的 commit `75cd01c` 風格重新設計 config key

---

## 一、背景

在執行 `TASK_20260914_SOPHIE_LINE_SECRET_ROTATION` 的盤點過程中，發現 Owner 後台 `app/Http/Controllers/Iot/LineLoginController.php` 與 Member 端有**完全相同**的 P0-2 漏洞：

- `LINE_CLIENT_ID = '2009625522'` 硬編碼
- `LINE_CLIENT_SECRET = '20f443a0498bcdbfb1e24906f40704e3'` 硬編碼（與 Member 同一個 Secret）
- `LINE_REDIRECT_URI = 'https://iot.tg25.win/auth/line/callback'` 硬編碼

**這是派工單的盲點**——目前派工只 rotate Channel Secret，但 Owner 端一旦 Secret 被 rotate，**LINE 登入會立即壞掉**。

---

## 二、與 Mina 風格對齊

Mina 在 Member 端 `75cd01c` commit 採用的模式：
- 註解：`// P0-2: Credentials moved to config/services.php (loaded from .env)`
- 方法命名：簡短 `clientId()` / `clientSecret()` / `redirectUri()`
- config key：扁平化 `services.line.client_id` / `client_secret` / `redirect_uri`

**Owner 端挑戰**：既有 `config/services.php` 的 `'line'` 段落已是**通知服務**（`api_url` / `api_key` / `webhook_secret`），不能直接覆寫。v2 採**子段落 `login`** 隔離：

```php
'line' => [
    // 通知服務（既有，不動）
    'api_url' => env('LINE_SERVICE_URL'),
    'api_key' => env('LINE_SERVICE_API_KEY'),
    'timeout' => env('LINE_SERVICE_TIMEOUT', 30),
    'webhook_secret' => env('LINE_WEBHOOK_SECRET'),
    // OAuth Login（新增 P0-2，子段落隔離避免命名衝突）
    'login' => [
        'client_id'     => env('LINE_LOGIN_CLIENT_ID'),
        'client_secret' => env('LINE_LOGIN_CLIENT_SECRET'),
        'redirect_uri'  => env('LINE_LOGIN_REDIRECT_URI', 'https://iot.tg25.win/auth/line/callback'),
    ],
],
```

**Controller 方法命名對齊 Mina 風格**：

```php
// P0-2: Credentials moved to config/services.php (loaded from .env)
private function loginClientId(): string
{
    return config('services.line.login.client_id', '');
}

private function loginClientSecret(): string
{
    return config('services.line.login.client_secret', '');
}

private function loginRedirectUri(): string
{
    return config('services.line.login.redirect_uri', 'https://iot.tg25.win/auth/line/callback');
}
```

（加上 `login` 前綴避免與既有 `LINE_SERVICE_*` 概念混淆）

---

## 三、完整改動清單

### 3.1 `config/services.php`（行 53-58）

**Before**：
```php
'line' => [
    'api_url' => env('LINE_SERVICE_URL'),
    'api_key' => env('LINE_SERVICE_API_KEY'),
    'timeout' => env('LINE_SERVICE_TIMEOUT', 30),
    'webhook_secret' => env('LINE_WEBHOOK_SECRET'),
],
```

**After**：
```php
'line' => [
    'api_url' => env('LINE_SERVICE_URL'),
    'api_key' => env('LINE_SERVICE_API_KEY'),
    'timeout' => env('LINE_SERVICE_TIMEOUT', 30),
    'webhook_secret' => env('LINE_WEBHOOK_SECRET'),
    'login' => [
        'client_id'     => env('LINE_LOGIN_CLIENT_ID'),
        'client_secret' => env('LINE_LOGIN_CLIENT_SECRET'),
        'redirect_uri'  => env('LINE_LOGIN_REDIRECT_URI', 'https://iot.tg25.win/auth/line/callback'),
    ],
],
```

### 3.2 `app/Http/Controllers/Iot/LineLoginController.php`

**改動 A**：行 15-19 移除硬編碼常數

**Before**：
```php
private const LINE_CLIENT_ID     = '2009625522';
private const LINE_CLIENT_SECRET = '20f443a0498bcdbfb1e24906f40704e3';
private const LINE_REDIRECT_URI  = 'https://iot.tg25.win/auth/line/callback';
private const LINE_TOKEN_URL     = 'https://api.line.me/oauth2/v2.1/token';
private const LINE_PROFILE_URL   = 'https://api.line.me/v2/profile';
```

**After**：
```php
// P0-2: Credentials moved to config/services.php (loaded from .env)
private function loginClientId(): string
{
    return config('services.line.login.client_id', '');
}

private function loginClientSecret(): string
{
    return config('services.line.login.client_secret', '');
}

private function loginRedirectUri(): string
{
    return config('services.line.login.redirect_uri', 'https://iot.tg25.win/auth/line/callback');
}
```

（注意：`LINE_TOKEN_URL` 與 `LINE_PROFILE_URL` 是 LINE 官方 API endpoint，不含憑證，**保留常數**即可）

**改動 B**：5 處 `self::LINE_*` 替換

| 行數 | Before | After |
|---|---|---|
| 32 | `'client_id'     => self::LINE_CLIENT_ID,` | `'client_id'     => $this->loginClientId(),` |
| 33 | `'redirect_uri'  => self::LINE_REDIRECT_URI,` | `'redirect_uri'  => $this->loginRedirectUri(),` |
| 60 | `'redirect_uri'  => self::LINE_REDIRECT_URI,` | `'redirect_uri'  => $this->loginRedirectUri(),` |
| 61 | `'client_id'     => self::LINE_CLIENT_ID,` | `'client_id'     => $this->loginClientId(),` |
| 62 | `'client_secret' => self::LINE_CLIENT_SECRET,` | `'client_secret' => $this->loginClientSecret(),` |

### 3.3 `.env.example`

新增（**不**包含實際 Secret 值）：

```bash
#############################################
# LINE Login (OAuth) 設定
#############################################
LINE_LOGIN_CLIENT_ID=
LINE_LOGIN_CLIENT_SECRET=
LINE_LOGIN_REDIRECT_URI=https://iot.tg25.win/auth/line/callback
```

### 3.4 `.env`（HQ 自行填入，不在 patch 範圍）

`.env` 應由 HQ 在 Channel Secret rotate 完成後**手動填入**新值。**不**在 Sophie patch 範圍。

---

## 四、驗證計畫（套用後）

1. 本機 `php artisan config:clear`（驗證 config 讀取無誤）
2. `../../dev_tools/waw_ops.sh deploy owner` 部署到 yd174
3. 瀏覽器打開 `https://iot.tg25.win/login`
4. 點 LINE 登入按鈕，**不應再呼叫硬編碼的 `2009625522`**
5. 確認 redirect URL 為 `https://iot.tg25.win/auth/line/callback`（無 `/api` 前綴）
6. 完成 LINE 授權流程，確認 callback 成功建立 session

---

## 五、依賴關係

| 前置 | 狀態 |
|---|---|
| HQ 已 rotate Channel Secret | ⏸️ 待 HQ 登入 LINE Console |
| Mina 端已修 Member | ✅ commit `75cd01c` 已上線 |
| 此 Owner patch 套用 | ⏸️ 待 HQ 派工 |
| Owner `.env` 填入新值 | ⏸️ 待 HQ rotate 後填 |

---

## 六、HQ 需裁決的選項

1. **派工給 Sophie 套用本提案**：完整 patch 已就緒，預估 15 分鐘
2. **派工給 Mina 跨域執行**：Mina 已有 config 模式經驗
3. **HQ 自行執行**：本提案可直接套用
4. **接受 Owner 端中斷**：rotate 後 Owner LINE 登入暫時壞掉，後續再修

---

**提案者**：Sophie (Owner)
**提案時間**：2026-09-14 12:30
**v2 變更**：config key 改用 `services.line.login.*` 子段落；方法命名 `loginClientId()` 對齊 Mina 風格
