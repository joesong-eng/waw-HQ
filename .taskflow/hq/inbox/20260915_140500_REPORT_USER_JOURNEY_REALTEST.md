# 任務回報：20260915_MINA_USER_JOURNEY_REALTEST

**完成時間**：2026-09-15 14:05
**執行者**：mina

---

## 執行結果

### 路徑一：玩家掃碼進場

| # | 端點 | HTTP Status | 結果 |
|:---|:---|:---|:---|
| 1 | `GET /` 首頁 | 200 | ✅ HTML 35KB，Vue 3 Vite 打包正常 |
| 2 | `GET /m/play` 未登入 | 200 | ✅ 頁面載入正常（前端 JS 處理登入引導） |
| 3 | `GET /venue/billing` 未登入 | 302 → / | ✅ 正確 redirect |
| 4 | `GET /venue/devices` 未登入 | 302 → / | ✅ 正確 redirect |
| 5 | `GET /venue/subscriptions` 未登入 | 302 → / | ✅ 正確 redirect |
| 6 | `GET /api/auth/line/login-url` | 200 | ✅ 回傳 LINE OAuth URL |
| 7 | `GET /auth/line/login` | 302 → LINE OAuth | ✅ 正確跳轉 |

### 路徑二：API 認證保護

| # | 端點 | 未登入 | 已登入 | 結果 |
|:---|:---|:---|:---|:---|
| 8 | `POST /api/device/credit` | 401 | - | ✅ 正確拒絕 |
| 9 | `POST /api/device/settle` | 401 | - | ✅ 正確拒絕 |
| 10 | `POST /api/engineering/kiosk/cmd` | 401 | - | ✅ 正確拒絕 |
| 11 | `GET /api/device/check-session` | 401 | 400 | ✅ 401 正確，400=設備不存在 |
| 12 | `POST /api/device/bind` | - | 400 | ✅ 400=機台不存在或無法連線 |

### 路徑三：已登入使用者

| # | 端點 | HTTP Status | 結果 |
|:---|:---|:---|:---|
| 13 | `GET /api/wallet/balance` | 200 | ✅ 回傳 COIN 餘額 500 |
| 14 | `GET /api/wallet/history` | 200 | ✅ 回傳交易紀錄 |
| 15 | `GET /venue/billing` 已登入 | 200 | ✅ 銀行帳號已遮罩 XXXX-XXXX-XXXX |
| 16 | `GET /venue/devices` 已登入 | 200 | ✅ |
| 17 | `GET /venue/subscriptions` 已登入 | 200 | ✅ |

### 路徑四：Infra API 通訊

| # | 測試 | 結果 |
|:---|:---|:---|
| 18 | `curl → api.tg25.win/device/.../active-status` | 200 ✅ JSON 回傳正常 |
| 19 | 從 VPS curl → Infra API | 200 ✅ |
| 20 | Laravel tinker DeviceController::infraHttp() | 200 ✅ |
| 21 | `app:check-offline-sessions` cron | 正常執行，無 SSL 錯誤 ✅ |
| 22 | 遠端日誌新 cURL error 60 計數 | 0 ✅ |

### 路徑五：WebSocket

| # | 端點 | HTTP Status | 結果 |
|:---|:---|:---|:---|
| 23 | `POST /broadcasting/auth` 未登入 | 403 | ✅ 正確拒絕（需認證） |

---

## 🔴 新發現的問題

### 問題 A：APP_ENV=local 在正式環境（CRITICAL）

遠端 `.env` 中 `APP_ENV=local`，導致：
- `/api/dev/token` 端點可被任何人呼叫（生產環境應 403）
- `TEST_MODE_886937271782` 後門可用
- `APP_DEBUG=true` 在正式環境洩露錯誤細節

**建議**：HQ 需確認是否改為 `APP_ENV=production`。但改為 production 後 dev/token 和測試後門都會關閉，需確認前端沒有依賴這些。

### 問題 B：API 未認證回應之前 500 → 已修復

之前的 `redirectGuestsTo` 回傳 Response 物件被當作 redirect URL，導致整個 HTTP response 嵌入 Location header，觸發 "Header may not contain more than a single header" 500 錯誤。

**已修復**：commit `5ed9d6d` + `b383075`，改用 `$exceptions->render()` 攔截 `AuthenticationException`，對 API 請求回傳 JSON 401。

### 問題 C：broadcasting/auth 回 403 而非 401

WebSocket 認證端點回 403 而非 401。可能影響前端 echo.js 的認證流程。需確認前端是否有對應處理。

---

## 結論

✅ 主要使用者路徑全部通過

但發現 APP_ENV=local 的安全問題需 HQ 裁決。

---
**回報者**：mina
**回報時間**：2026-09-15 14:05
