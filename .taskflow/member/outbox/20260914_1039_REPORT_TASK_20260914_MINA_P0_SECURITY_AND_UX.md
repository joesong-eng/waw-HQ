# 回報：TASK_20260914_MINA_P0_BACKEND_SECURITY + TASK_20260914_MINA_P0_FRONTEND_UX

**完成時間**：2026-09-14 10:39
**負責人**：Mina (Member)
**來源任務**：TASK_20260914_MINA_P0_BACKEND_SECURITY + TASK_20260914_MINA_P0_FRONTEND_UX

---

## 後端安全任務完成清單

### P0 後端安全漏洞（6/6 完成）

| 項目 | Commit Hash | 修改檔案 | 說明 |
| :--- | :--- | :--- | :--- |
| P0-1 | `6822776` | AuthController.php | 測試後門加入 `app()->environment('local','staging')` 守衛；移除 CASH 錢包，改用 TICKET 常數 |
| P0-2 | `75cd01c` | LineLoginController.php, config/services.php | LINE clientId/clientSecret 從硬編碼移至 `.env` + `config/services.php` line 段落 |
| P0-3 | `f581eaa` | 11 個 Event 檔案, routes/channels.php, routes/web.php, resources/js/echo.js, welcome.blade.php, play.blade.php | 全部 Public Channel → PrivateChannel；channels.php 加入授權回調；echo.js 加入 Sanctum Bearer authorizer；前端 `.channel()` → `.private()`；web.php 加入 /broadcasting/auth 路由 |
| P0-4 | `601ad8a` | routes/api.php, EngineeringController.php | Engineering 路由加入 `auth:sanctum` middleware + `throttle:10,1`；kioskCommand 方法內加 production 環境守衛 |
| P0-5 | `92503bb` | DeviceController.php, KioskController.php | `'verify' => false` → `'verify' => true`，啟用 SSL 驗證防止 MITM |
| P0-6 | `c90f3dc` | DeviceController.php, KioskController.php, CallbackController.php, EngineeringController.php | 所有 `===` 金鑰比對改為 `hash_equals()` 時間安全比較 |

### P1 安全相關邏輯修復（5/5 完成）

| 項目 | Commit Hash | 修改檔案 | 說明 |
| :--- | :--- | :--- | :--- |
| P1-1 | `68cb58c` | KioskSessionUpdated.php, MemberBoundToKiosk.php, MemberPointsUpdated.php, BillAcceptorService.php, routes/api.php | 統一幣別常數：移除所有 'POINT'、'TOKEN'、'CASH' 硬編碼，改用 MemberWallet::CURRENCY_COIN / CURRENCY_TICKET |
| P1-2 | `da1048f` | MemberController.php, routes/web.php | transactions() 改用 `$request->user()->id` 取代 query param，防止 IDOR；路由加 `auth:sanctum` |
| P1-3 | `2173d2e` | CheckOfflineSessions.php | 硬編碼 60s 改為 `config('services.kiosk.offline_threshold_seconds', 180)`，預設 180 秒 |
| P1-4 | `99f9c81` | CallbackController.php | settle() 方法在 $wallet->increment() 前加入 null check NPE 防護 |
| P1-6 | `2877b73` | KioskController.php | sessionStatus() 移除 orderByRaw + 'TOKEN'/'POINT' 字串，改用 MemberWallet 常數；$member->name 加 null safe operator |
| P1-7 | `f19ec19` | .gitignore | 加入 `database/*.sqlite` 和 `database/*.sqlite-journal` 模式 |

---

## 前端 UX 任務完成清單

### 第一階段 P0 緊急修復（4/4 完成）

| 項目 | Commit Hash | 修改檔案 | 說明 |
| :--- | :--- | :--- | :--- |
| UX-P0-1 | `c11a78f` | LineLoginController.php, routes/web.php, welcome.blade.php | LINE 回調改用 HttpOnly Cookie 傳遞 Token，新增 /api/auth/line/exchange 端點；前端偵測 ?line_auth=1 自動交換 |
| UX-P0-2 | `0f7ea6f` | welcome.blade.php | manualChipId 預設值從真實 chip_id `'sr9adyxpdyt1tuf7'` 改為空字串 `''` |
| UX-P0-3 | `4e58fca` | welcome.blade.php | 清理 10+ 條 console.log，將敏感 ID/Token/SessionID 替換為 [REDACTED] |
| UX-P0-4 | `a9efcc2` | routes/web.php | Venue 路由 (/subscriptions, /devices, /billing) 加入 `auth:sanctum` middleware |

### P1 邏輯/體驗修復（9/9 完成）

| 項目 | Commit Hash | 修改檔案 | 說明 |
| :--- | :--- | :--- | :--- |
| UX-P1-1 | `674c254` | play.blade.php | 開分加入自訂確認 Modal（含選擇金額/消耗代幣顯示） |
| UX-P1-2 | `7380f8c` | play.blade.php | 洗分原生 confirm() 改為自訂 Modal |
| UX-P1-3 | `2b097e1` | play.blade.php | 洗分加入進度 Modal（pending→success/timeout），30 秒超時處理 |
| UX-P1-4 | `2b097e1` | DeviceController.php, play.blade.php | 超時從 120s→180s，標注 TODO 待 Ina 提供 MQTT heartbeat topic |
| UX-P1-5 | `76db3bc` | welcome.blade.php | Kiosk Exchange Countdown 60s→120s |
| UX-P1-6 | `5965378` | welcome.blade.php | Escrow Confirm Countdown 15s→30s |
| UX-P1-7 | `9ec3e5d` | welcome.blade.php | Kiosk 頻道加入 KioskRejected 事件監聽，投幣被退時即時通知玩家 |
| UX-P1-8 | `4ab0ebf` | welcome.blade.php | 移除登入成功後 Toast 顯示 Token 的程式碼 |
| UX-P1-9 | `b263c6c` | welcome.blade.php | 移除 Dev Login 代碼（/api/dev/token 呼叫），改為導向 LINE Login |

---

## 遠端部署與驗證

- **部署指令**：`../../dev_tools/waw_ops.sh deploy mina` ✅ 成功
- **Git Push**：`e6cff92..c11a78f main -> main` ✅ 成功
- **首頁驗證**：`https://win.tg25.win/` → 200 ✅
- **Play 頁驗證**：`https://win.tg25.win/m/play` → 200 ✅
- **Broadcasting Auth**：`/broadcasting/auth` → 403 (未授權正確拒絕) ✅
- **LINE Exchange**：`/api/auth/line/exchange` → 200 ✅
- **Engineering 路由**：`/api/engineering/bindings` → 已加 auth:sanctum ✅

## 待 HQ 協調事項

1. **LINE Secret rotation**：LINE clientId/clientSecret 已從程式碼移至 .env，但歷史 commit 中的密鑰需要 GitHub history 清理 + LINE Console Secret rotation（HQ 協調 Owner）
2. **Reverb 設定**：PrivateChannel 需要 Reverb 正確運行，相關 .env 設定不在本任務範圍
3. **APP_ENV**：遠端目前 APP_ENV=local，建議設為 production 以啟用環境守衛
4. **UX-P1-4 MQTT heartbeat**：需與 Ina 確認 MQTT heartbeat topic+field，目前用 180s 超時作為過渡方案

---

**回報人**：Mina
**回報時間**：2026-09-14 10:39

