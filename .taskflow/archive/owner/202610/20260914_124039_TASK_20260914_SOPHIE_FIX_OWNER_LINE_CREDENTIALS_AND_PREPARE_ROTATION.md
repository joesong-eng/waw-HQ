# 任務：TASK_20260914_SOPHIE_FIX_OWNER_LINE_CREDENTIALS_AND_PREPARE_ROTATION
**派發時間**：2026-09-14 13:45
**優先級**：🔴 CRITICAL（緊急安全修復）
**負責人**：Sophie (Owner)
**來源**：Sophie 回報 20260914_121635_Sophie.md 裁決

## 一、HQ 對 4 個問題的正式裁決

### Q1 & Q2. LINE Console 登入與 Secret Rotation
- **裁決**：由 **Joe 親自登入 LINE Developers Console 進行 Secret Rotation**。
- 你不需要登入 LINE Console。
- 當你完成 Owner 程式碼修改並部署後，HQ 會請 Joe 點擊 Reissue Secret，並由 HQ 同步更新 Member 與 Owner 伺服器的 `.env`。

### Q3. Owner 端硬編碼處置
- **裁決**：**採納你的警告，先修復 Owner 端硬編碼，再進行 Rotate**。
- 請立即將 Owner 端的 LINE 憑證改為讀取 `.env` + `config/services.php`。

### Q4. Callback URL 確認
- **裁決**：**完全同意你的指正**，Callback 路徑無 `/api` 前綴。
- LINE Developers Console 將確保登記以下兩個 URL：
  1. `https://win.tg25.win/auth/line/callback` (Member)
  2. `https://iot.tg25.win/auth/line/callback` (Owner)

---

## 二、本次任務具體執行項目

### 1. 修改 Owner 後台 LINE Login 憑證
- **檔案**：`PROJECT/Owner/app/Http/Controllers/Iot/LineLoginController.php`
- 移除類別中寫死的常數：
  ```php
  // 移除以下寫死常數：
  // private const LINE_CLIENT_ID     = '2009625522';
  // private const LINE_CLIENT_SECRET = '20f443a0498bcdbfb1e24906f40704e3';
  // private const LINE_REDIRECT_URI  = 'https://iot.tg25.win/auth/line/callback';
  ```
- 改為透過 `config('services.line.client_id')`、`config('services.line.client_secret')`、`config('services.line.redirect')` 讀取。

### 2. 更新 config/services.php 與 .env.example
- 在 `config/services.php` 新增 `line` 設定段落：
  ```php
  'line' => [
      'client_id'     => env('LINE_CLIENT_ID'),
      'client_secret' => env('LINE_CLIENT_SECRET'),
      'redirect'      => env('LINE_REDIRECT_URI', 'https://iot.tg25.win/auth/line/callback'),
  ],
  ```
- 在 `.env.example` 補充上述三個環境變數說明。
- 檢查本機 `.env`，填入現有（尚未 rotate 的）憑證，確保本地不中斷。

### 3. 本地測試、Commit 與標準部署
- 執行語法檢查 `php -l`。
- Commit 訊息格式：`fix(security): P0-2 move LINE credentials to .env and services config`
- Push 至 `origin/main`。
- 透過 `dev_tools/waw_ops.sh deploy sophie` 部署至 `129.153.116.174` (`iot.tg25.win`)。
- 在遠端伺服器 `.env` 確保已設置 `LINE_CLIENT_ID`、`LINE_CLIENT_SECRET`、`LINE_REDIRECT_URI`（目前仍先維持現有值）。

---

## 三、回報要求
完成後將報告寫入 `.taskflow/owner/outbox/`：
1. Commit hash
2. 修改檔案清單
3. 遠端部署與 `config:cache` 狀態
4. 確認「隨時可接受 Secret Rotation」

---
**派發者**：HQ  
**派發時間**：2026-09-14 13:45
