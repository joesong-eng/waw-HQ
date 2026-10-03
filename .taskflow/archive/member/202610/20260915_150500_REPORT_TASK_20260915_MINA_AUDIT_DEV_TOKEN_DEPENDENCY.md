# 任務回報：TASK_20260915_MINA_AUDIT_DEV_TOKEN_DEPENDENCY

**完成時間**：2026-09-15 15:05  
**執行者**：mina

## 調查結果

### 1. /api/dev/token 引用清單

| 位置 | 說明 |
|:---|:---|
| `routes/api.php:9-30` | 路由定義，已有 `app()->environment('production')` 守衛，production 下回傳 403 |
| `storage/framework/views/0450d...57.php:640` | **已過期的 Blade 快取**，原始 blade 模板（`welcome.blade.php`）中已無此引用 |

**結論**：前端原始碼（`resources/views/`、`resources/js/`）**零引用** `/api/dev/token`。快取檔是舊版殘留，部署時 `php artisan view:clear` 會清掉。

### 2. TEST_MODE 後門引用清單

| 位置 | 行號 | 說明 |
|:---|:---|:---|
| `app/Http/Controllers/Api/AuthController.php` | L31-33 | `TEST_MODE_886937271782` 後門，受 `app()->environment('local', 'staging')` 守衛 |

**結論**：只在 AuthController 一處，且已有 environment 守衛。**前端無任何地方傳送此 token**，僅供 Postman 手動測試用。切 production 後此後門自動失效。

### 3. APP_ENV=production 影響評估

切換後會**關閉**的功能：

| 功能 | 檔案 | 影響 |
|:---|:---|:---|
| `GET /api/dev/token` 測試取 token | `routes/api.php:9-30` | 回傳 403。**前端不依賴**，無影響 |
| `TEST_MODE_886937271782` 後門登入 | `AuthController.php:33` | 自動失效。**前端不依賴**，無影響 |
| `POST /api/engineering/kiosk/cmd` | `EngineeringController.php:135` | 回傳 403。工程面板 kiosk 指令（OTA/Reboot）被封鎖 |

**不受影響**的功能：
- ✅ LINE OAuth 登入流程（`LineLoginController`）— 無 environment 守衛
- ✅ Firebase 簡訊登入正常流程 — 走 Firebase SDK 驗證，不依賴後門
- ✅ 錢包 API（balance/history）
- ✅ 機台綁定/投幣/結算/解綁（`DeviceController`）
- ✅ Infra callback 端點（credit/settle/kiosk-event）
- ✅ 工程面板查詢類 API（bindings/tablet-status/session-status）— 僅 `kiosk/cmd` 被封
- ✅ Kiosk 內部 webhook（`/internal/` 路由）

### 4. 結論

✅ **可安全切換 `APP_ENV=production`**

被關閉的三個功能（dev/token、TEST_MODE 後門、engineering kiosk cmd）均為開發/測試專用，**前端無任何依賴**，線上用戶不受影響。

唯一需注意：若工程團隊仍需透過面板遠端下達 Kiosk OTA/Reboot 指令，需另開白名單或移除 `EngineeringController` 的 production 守衛。

**目前遠端 APP_ENV**：`local`（尚未切換）

---
**回報者**：mina  
**回報時間**：2026-09-15 15:05

