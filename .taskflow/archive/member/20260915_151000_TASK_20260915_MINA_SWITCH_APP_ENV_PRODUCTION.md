# 任務：TASK_20260915_MINA_SWITCH_APP_ENV_PRODUCTION

**派發時間**：2026-09-15 15:10  
**優先級**：P0  
**負責人**：Mina (Member)

---

## 📋 任務內容

將 win.tg25.win 正式環境切換為 production 模式。

### 執行步驟

1. SSH 進遠端 `yd177`，進入 `/www/wwwroot/win.tg25.win`
2. 修改 `.env`：
   - `APP_ENV=production`
   - `APP_DEBUG=false`
3. 清除快取：
   - `php artisan config:clear`
   - `php artisan cache:clear`
   - `php artisan view:clear`
   - `php artisan route:clear`
4. 重建快取：
   - `php artisan config:cache`
   - `php artisan route:cache`
5. 驗證：
   - `curl` 呼叫 `/api/dev/token` → 應回 403
   - 首頁 `/` → 應回 200
   - `/api/auth/line/login-url` → 應回 200
   - 故意觸發錯誤 → 不應洩露 stack trace
   - 確認遠端 `.env` 的 APP_ENV 和 APP_DEBUG 值

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260915_MINA_SWITCH_APP_ENV_PRODUCTION

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：mina

## 執行結果

### .env 修改前後
（貼出修改前後的 APP_ENV / APP_DEBUG 值）

### 驗證結果
| 測試項 | 預期 | 實際 |
|:---|:---|:---|
| GET /api/dev/token | 403 | ? |
| GET / | 200 | ? |
| GET /api/auth/line/login-url | 200 | ? |
| 錯誤頁面是否洩露 stack trace | 否 | ? |

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：mina  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-09-15 15:10

