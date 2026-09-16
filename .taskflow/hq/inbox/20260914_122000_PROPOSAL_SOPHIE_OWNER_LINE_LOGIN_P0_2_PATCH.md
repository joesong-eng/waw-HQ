# 主動建議：Owner 端 LINE Login P0-2 修法 Patch 草案

**提出時間**：2026-09-14 12:20
**提出者**：Sophie (Owner)
**對應派工單**：`TASK_20260914_SOPHIE_LINE_SECRET_ROTATION`（中途發現的盲點）
**狀態**：🟡 待 HQ 裁決是否派工執行

---

## 一、背景

在執行 `TASK_20260914_SOPHIE_LINE_SECRET_ROTATION` 的盤點過程中，發現 Owner 後台 `app/Http/Controllers/Iot/LineLoginController.php` 與 Member 端有**完全相同**的 P0-2 漏洞：

- `LINE_CLIENT_ID = '2009625522'` 硬編碼
- `LINE_CLIENT_SECRET = '20f443a0498bcdbfb1e24906f40704e3'` 硬編碼（與 Member 同一個 Secret）
- `LINE_REDIRECT_URI = 'https://iot.tg25.win/auth/line/callback'` 硬編碼

**這是派工單的盲點**——目前派工只 rotate Channel Secret，但 Owner 端一旦 Secret 被 rotate，**LINE 登入會立即壞掉**。

---

## 二、建議修法（與 Mina 端 commit `75cd01c` 對齊）

### 2.1 `config/services.php` 改動

**檔案**：`/Users/ilawusong/Documents/WaW/PROJECT/Owner/config/services.php`

在 `'line'` 段落（行 53-58）**新增 OAuth 登入用 sub-array**：

```php
'line' => [
    // 通知服務（既有）
    'api_url' => env('LINE_SERVICE_URL'),
    'api_key' => env('LINE_SERVICE_API_KEY'),
    'timeout' => env('LINE_SERVICE_TIMEOUT', 30),
    'webhook_secret' => env('LINE_WEBHOOK_SECRET'),
    // OAuth Login（新增，P0-2）
    'login' => [
        'client_id'     => env('LINE_LOGIN_CLIENT_ID'),
        'client_secret' => env('LINE_LOGIN_CLIENT_SECRET'),
        'redirect_uri'  => env('LINE_LOGIN_REDIRECT_URI', 'https://iot.tg25.win/auth/line/callback'),
    ],
],
```

**為何用 `login` 子段落**：避免與既有 `LINE_SERVICE_*` 命名空間衝突。

---

### 2.2 `app/Http/Controllers/Iot/LineLoginController.php` 改動

**檔案**：`/Users/ilawusong/Documents/WaW/PROJECT/Owner/app/Http/Controllers/Iot/LineLoginController.php`

#### 改動 A：行 15-19 移除硬編碼常數

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
private function lineClientId(): string
{
    return config('services.line.login.client_id', '');
}

private function lineClientSecret(): string
{
    return config('services.line.login.client_secret', '');
}

private function lineRedirectUri(): string
{
    return config('services.line.login.redirect_uri', 'https://iot.tg25.win/auth/line/callback');
}
```

#### 改動 B：所有 `self::LINE_CLIENT_ID` → `$this->lineClientId()`

搜尋並替換（建議 4 處）：
- 行 32：`'client_id' => self::LINE_CLIENT_ID,` → `'client_id' => $this->lineClientId(),`
- 行 61：`'client_id' => self::LINE_CLIENT_ID,` → `'client_id' => $this->lineClientId(),`

#### 改動 C：所有 `self::LINE_REDIRECT_URI` → `$this->lineRedirectUri()`

搜尋並替換（2 處）：
- 行 33：`'redirect_uri' => self::LINE_REDIRECT_URI,` → `'redirect_uri' => $this->lineRedirectUri(),`
- 行 60：`'redirect_uri' => self::LINE_REDIRECT_URI,` → `'redirect_uri' => $this->lineRedirectUri(),`

#### 改動 D：所有 `self::LINE_CLIENT_SECRET` → `$this->lineClientSecret()`

- 行 62：`'client_secret' => self::LINE_CLIENT_SECRET,` → `'client_secret' => $this->lineClientSecret(),`

---

### 2.3 `.env.example` 改動

**檔案**：`/Users/ilawusong/Documents/WaW/PROJECT/Owner/.env.example`

**新增**：
```bash
#############################################
# LINE Login (OAuth) 設定
#############################################
LINE_LOGIN_CLIENT_ID=
LINE_LOGIN_CLIENT_SECRET=
LINE_LOGIN_REDIRECT_URI=https://iot.tg25.win/auth/line/callback
```

---

### 2.4 `.env`（**不**直接寫入 Secret 值）

`.env` 應由 **HQ 在 rotate 完成後手動填入**新 Secret 值。Sophie 不在 `.env` 內寫入任何 Secret。

建議 HQ 在 rotate 完後用以下流程：
1. `ssh yd174` 進 Owner VPS
2. `cd /www/wwwroot/iot.tg25.win`
3. `vim .env`（這是 AGENTS.md 允許的例外）
4. 新增 `LINE_LOGIN_CLIENT_SECRET=<新值>` 與 `LINE_LOGIN_CLIENT_ID=2009625522`
5. `php artisan config:clear`

**或者 HQ 透過 `waw_ops.sh` 注入**：
```bash
../../dev_tools/waw_ops.sh remote owner "cd /www/wwwroot/iot.tg25.win && sed -i '/^LINE_LOGIN_CLIENT_SECRET=/d' .env && echo 'LINE_LOGIN_CLIENT_SECRET=<值>' >> .env && php artisan config:clear"
```

（具體指令由 HQ 裁決）

---

## 三、驗證計畫

1. 本機 `php artisan config:clear`
2. 本機啟動測試（不建議，違反 AGENTS.md「本機代碼純淨」）；改用**直接部署到 yd174 驗證**
3. `../../dev_tools/waw_ops.sh deploy owner`
4. 瀏覽器打開 `https://iot.tg25.win/login`
5. 點 LINE 登入，確認 redirect 到 `https://access.line.me/oauth2/v2.1/authorize?...`
6. 完成授權後確認 callback 成功（用 `/auth/line/callback` 路徑）

---

## 四、依賴關係

| 前置 | 狀態 |
|---|---|
| Channel Secret 已 rotate | ⏸️ 等 HQ |
| Mina 已修 Member 端 | ✅ commit `75cd01c` |
| 此 patch 套用 | ⏸️ 等 HQ 派工 |
| `.env` 填入新值 | ⏸️ 等 HQ rotate 後 |

---

## 五、HQ 需裁決的選項

請 HQ 從以下選一個：

1. **派工給 Sophie 執行本提案**：本提案完整可直接採用，預估 15 分鐘
2. **派工給 Mina 跨域執行**：Mina 已有 config 模式經驗（commit `75cd01c`）
3. **HQ 自行執行**：本提案可直接套用
4. **接受 Owner 端中斷**：rotate 後 Owner LINE 登入暫時壞掉，後續再修

---

**提案者**：Sophie (Owner)
**提案時間**：2026-09-14 12:20
