# REPORT_20260805_085750_TASK_20260805_INFRA_REVERB_SERVICE

## 任務資訊
- **任務 ID**：TASK_20260805_INFRA_REVERB_SERVICE
- **身分**：Ina (Infra)
- **狀態**：completed

## 執行摘要
本任務已成功在 VPS 啟動 Laravel Reverb 服務 (Port 6009) 並設定與驗證 Nginx WebSocket 反向代理。主要執行內容包含：
1. **修復與重啟 Owner VPS (`yd174`, `iot.tg25.win`) 的 Reverb 服務**：
   - 發現原 Supervisor 設定檔 `/etc/supervisor/conf.d/wawv9-reverb.conf` 所指向的專案路徑為舊有的 `/www/wwwroot/iot.tg25.win/wawv9`（該路徑已不存在），導致服務失效且無法正常重啟。
   - 更新 Supervisor 設定，將 `command`、`directory`、`stdout_logfile` 修改為當前正確路徑 `/www/wwwroot/iot.tg25.win`。
   - 執行 `reread` 與 `update` 重啟 `wawv9-reverb` 服務，確認 Reverb 成功於 Port 6009 監聽啟動。
2. **驗證 Owner VPS 反向代理與 WebSocket 連線**：
   - 檢查 `iot.tg25.win` 的 Nginx 配置檔，確認 `/app/` 與 `/apps/` 區段皆已設定 WebSocket 反向代理至 `http://127.0.0.1:6009`。
   - 於外部發起加密 WebSocket 握手請求 (`wss://iot.tg25.win/app/iot-9-key`)，順利通過 Cloudflare 及 Nginx 代理，取得 `HTTP/1.1 101 Switching Protocols` 及 `X-Powered-By: Laravel Reverb` 回應，連線建立成功。
3. **核對與確認 Infra VPS (`infra`, `api.tg25.win`) 的 Reverb 狀態**：
   - 確認 `infra` VPS 上 `/var/www/waw-iot/` 的 Reverb 服務已正常運行於 `127.0.0.1:6009`。
   - 確認 `/etc/nginx/sites-enabled/iot.tg25.win` 已配置 WebSocket 代理將 `/app` 轉發至 `http://127.0.0.1:6009`。

## 證明
### 1. Owner VPS (yd174) 服務運行狀態
執行 `sudo supervisorctl status`：
```
wawv9-reverb:wawv9-reverb_00   RUNNING   pid 909378, uptime 0:00:05
```
執行 `sudo ss -tlnp | grep 6009` 確認監聽於 0.0.0.0:6009：
```
LISTEN 0      511          0.0.0.0:6009       0.0.0.0:*    users:(("php",pid=909378,fd=5))
```
檢視 `/www/wwwroot/iot.tg25.win/storage/logs/reverb.log` 啟動日誌：
```
   INFO  Starting server on 0.0.0.0:6009 (127.0.0.1).
```

### 2. Nginx WebSocket 連線測試 (以 Python 手動握手測試)
連線至 `wss://iot.tg25.win/app/iot-9-key`（經由 Nginx 代理），成功返回 101 狀態碼並順利升級協議：
```http
HTTP/1.1 101 Switching Protocols
Date: Wed, 05 Aug 2026 01:06:33 GMT
Connection: upgrade
Server: cloudflare
Upgrade: websocket
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
X-Powered-By: Laravel Reverb
```

### 3. Infra VPS (infra) 服務運行狀態
執行 `ps -ef | grep reverb`：
```
ubuntu   2096560       1  1 01:04 ?        00:00:01 /usr/bin/php8.5 /var/www/waw-iot/artisan reverb:start --host=127.0.0.1 --port=6009
```
執行 `curl` 測試本地 Reverb 回應，成功升級協議（出現 Pusher App 錯誤係因 Key 不同，屬預期行為）：
```
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
X-Powered-By: Laravel Reverb
{"event":"pusher:error","data":"{\"code\":4001,\"message\":\"Application does not exist\"}"}
```

## 後續風險
1. **日誌容量監控**：Supervisor 的 stdout 日誌上限設定為 10MB，但仍需注意儲存空間狀況，建議定期清理或安排 logrotate。
2. **重啟連線瞬斷**：若未來需要更新 Reverb 或重開服務，WebSocket 客戶端需具備自動斷線重連機制。
