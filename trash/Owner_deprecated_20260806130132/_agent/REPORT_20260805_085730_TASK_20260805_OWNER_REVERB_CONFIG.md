# REPORT_20260805_085730_TASK_20260805_OWNER_REVERB_CONFIG

## 任務資訊
- **任務 ID**：TASK_20260805_OWNER_REVERB_CONFIG
- **身分**：Sophie (Owner)
- **狀態**：completed

## 執行摘要
本任務已將 Owner 專案廣播設定改為 Reverb，並確認前端即時頁面的 Reverb 連線配置以支援自動更新。具體執行內容包括：
1. **驗證廣播設定**：確認 `wawOwner` 的 `.env` 與 Laravel 執行期預設 `BROADCAST_CONNECTION` 設定為 `reverb`。
2. **修復前端連線 Bug**：在 `resources/js/echo.js` 中，原本 `forceTLS` 連線判定僅在 `VITE_REVERB_SCHEME` 為 `'https'` 時為真；現修正為當 scheme 為 `'https'` 或 `'wss'` 時皆為真（`true`），解決生產環境下使用 `wss` 會被判定為 `forceTLS: false` 而遭瀏覽器阻擋未加密 WebSocket 連線的 Bug。
3. **修復警報模組頻道 Bug**：在 `resources/views/iot/modules/m9/alerts.blade.php` 中，原本誤用 `.private('realtime')`，但 `DeviceUpdated` 廣播事件是在公開頻道 `realtime` 發佈，且專案中未實作私有頻道授權。已將其更正為 `.channel('realtime')` 以確保警報能正確接收推播更新。
4. **前端編譯資產**：執行 `pnpm run build` 重新編譯產出最新的前端資產 `app-BINpg08h.js`，並確認包含正確的連線設定。

## 證明
### 1. Laravel Broadcasting 預設設定
執行 `php artisan tinker` 確認預設 connection 為 `reverb`：
```
>>> config('broadcasting.default')
=> "reverb"
```

### 2. 前端已編譯資產之連線設定 (forceTLS: true)
在產出的 `public/build/assets/app-BINpg08h.js` 中，已成功寫入 `forceTLS:!0`（即 `true`）的連線設定，且使用 Reverb 客戶端：
```
aster:"reverb",key:"iot-9-key",wsHost:"iot.tg25.win",wsPort:"443",wssPort:"443",forceTLS:!0,enabledTransports:["ws","wss"]
```

### 3. Git 變更清單
```
M resources/js/echo.js
M resources/views/iot/modules/m9/alerts.blade.php
```

## 後續風險
1. **Reverb 伺服器狀態**：生產環境需要確認 Reverb 服務是否有背景常駐執行（如使用 Supervisor 監管 `php artisan reverb:start`）。
2. **Vite 環境變數配置**：在部署至伺服器時，請務必確認 `.env` 中的 `VITE_REVERB_HOST`、`VITE_REVERB_PORT` 和 `VITE_REVERB_SCHEME` 已配置為對應的生產域名與 TLS 設定，以供編譯後的 JS 連線使用。
