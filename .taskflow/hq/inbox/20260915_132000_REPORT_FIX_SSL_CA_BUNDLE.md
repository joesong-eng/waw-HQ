# 任務回報：20260915_MINA_FIX_SSL_CA_BUNDLE

**完成時間**：2026-09-15 13:20
**執行者**：mina

## 執行結果

### 排查結果
1. **CA bundle 已存在**：`/etc/ssl/certs/ca-certificates.crt` (182KB, 2026-07-07)
2. **PHP ini 已正確設定**：
   - `openssl.cafile = /etc/ssl/certs/ca-certificates.crt`
   - `curl.cainfo = /etc/ssl/certs/ca-certificates.crt`
   - 在 `/www/server/php/82/etc/php.ini` 中已配置
3. **curl CLI 驗證**：`curl https://api.tg25.win/` → SSL certificate verify ok → 200 ✅
4. **Guzzle 驗證**：`new GuzzleHttp\Client(['verify' => true])->get('https://api.tg25.win/')` → 200 ✅
5. **Laravel HTTP 驗證**：`Http::withOptions(['verify' => true])->get(...)` → 200 ✅
   - 回傳：`{"chip_id":"SR9ADYXPDYT1TUF7","status":"offline","is_active":false}`

### 根因判斷
之前的 cURL error 60 錯誤已不再出現。可能原因：
- PHP-FPM 需要重啟才能讀取更新後的 php.ini（已在本次操作中重啟）
- config:cache 之前可能快取了舊的設定值

### 已執行操作
1. `php artisan config:cache` — 重建設定快取 ✅
2. `service php-8.2 restart` — 重啟 PHP-FPM ✅
3. 清除路由快取 `php artisan route:clear` ✅

### 驗收結果
| 項目 | 結果 |
|:---|:---|
| `curl https://api.tg25.win/` | 200, SSL verify ok ✅ |
| Laravel Http::get verify=true | 200, 正確回傳 JSON ✅ |
| 新日誌無 cURL error 60 | ✅ |
| 首頁 / | 200 ✅ |
| /m/play | 200 ✅ |
| /venue/billing | 302 redirect ✅ |

## 結論
✅ 完成（SSL CA bundle 已正常工作，Infra API 通訊恢復）

---
**回報者**：mina
**回報時間**：2026-09-15 13:20
