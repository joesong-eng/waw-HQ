# Member 專案審查修復狀態總驗報告

**執行時間**：2026-09-14 14:00
**負責人**：Mina (Member)
**關聯報告**：
- `20260914_093000_REPORT_MEMBER_FULL_CODE_AUDIT.md`（代碼安全審查，25 項）
- `20260914_100000_REPORT_MEMBER_FRONTEND_UX_AUDIT.md`（前端 UX 審查，35 項）
**目的**：HQ 裁勘兩份審查報告中各項問題的修復狀態，確認是否達標、是否有遺漏

---

## 一、總體修復率

| 類別 | 總數 | 已修復 | 未修復 | 修復率 |
|:---|:---|:---|:---|:---|
| 🔴 P0 嚴重安全漏洞 | 6 | 6 | 0 | **100%** ✅ |
| 🟠 P1 邏輯與架構錯誤 | 7 | 6 | 1 | **86%** ⚠️ |
| 🟡 P2 代碼品質 | 8 | 0 | 8 | **0%** ❌ |
| 📋 P3 設定與部署 | 4 | 0 | 4 | **0%** ❌ |
| 🎨 UX P0+P1 | 14 | 13 | 1 | **93%** ✅ |
| **合計** | **39** | **25** | **14** | **64%** |

---

## 二、已修復項目一覽（25 頭）

### 🔴 P0 安全漏洞（6/6 全部修復）

| # | 問題 | Commit | 修復方式 |
|:---|:---|:---|:---|
| P0-1 | AuthController 後門無環境守衛 | `6822776` | 加 `app()->environment('local','staging')` 守衛，production 環境跳過後門 |
| P0-2 | LINE 憑證硬編碼 | `75cd01c` | 移至 `config/services.php` 讀 `env('LINE_CLIENT_ID/SECRET')`，Controller 改用 `config()` |
| P0-3 | WebSocket 全為 Public Channel | `b263c6c` | 全部 13 個 Event 類別改為 `PrivateChannel`，`channels.php` 加授權邏輯 |
| P0-4 | Engineering 指令端點無認證 | `601ad8a` | 路由加 `throttle:10,1` middleware，Controller 加 production 403 守衛 |
| P0-5 | SSL verify 關閉 | `92503bb` | DeviceController + KioskController 改為 `'verify' => true` |
| P0-6 | === 時序攻擊 | `c90f3dc` | 全部 4 個 Controller 替換為 `hash_equals()`，共 10 處 |

### 🟠 P1 邏輯錯誤（6/7 修復）

| # | 問題 | Commit | 修復方式 |
|:---|:---|:---|:---|
| P1-1 | 幣別常數不一致 | `b263c6c` | 全部 `'POINT'`/`'TOKEN'`/`'CASH'` 硬編碼替換為 `MemberWallet::CURRENCY_COIN/TICKET` |
| P1-2 | MemberController 越權查詢 | `da1048f` | 改用 `$request->user()->id` 取代前端傳入的 `member_id` |
| P1-3 | CheckOfflineSessions 60s≠3min | `2173d2e` | 改為 `config('services.kiosk.offline_threshold_seconds', 180)`，預設 180 秒 |
| P1-4 | CallbackController settle NPE | `99f9c81` | 加 null guard，$wallet 為 null 時 throw Exception |
| P1-6 | KioskController 殭屍 Session | `2877b73` | sessionStatus 僅在有 member_id 時更新 last_active_at |
| P1-7 | database.sqlite 進 Git | `f19ec19` | `git rm --cached`，.gitignore 加 `database/*.sqlite` |

### 🎨 UX P0+P1（13/14 修復）

| # | 問題 | Commit | 修復方式 |
|:---|:---|:---|:---|
| UX-P0-1 | LINE URL 帶明文 Token | `c11a78f` | 改用 HttpOnly Cookie 傳遞 Token |
| UX-P0-2 | WS PrivateChannel（前端配合） | `b263c6c` | channels.php + echo.js 配合 PrivateChannel |
| UX-P0-3 | console.log 洩露 ID | `b263c6c` | 移除暴露 session/kiosk ID 的 log |
| UX-P0-4 | 手動輸入框預填真實 chip_id | `b263c6c` | 預設值改為空字串 |
| UX-P1-1 | 開分無二次確認 | `674c254` | 加確認 Modal |
| UX-P1-2 | 洗分用原生 confirm() | `7380f8c` | 改為自訂 Modal |
| UX-P1-3 | 洗分後無進度反饋 | `2b097e1` | 加 30s WS 超時處理 + 進度動畫 |
| UX-P1-4 | 超時踢人可能誤殺 | `e56390d` | 整合 Infra active-status API，機台仍在活動則延長 |
| UX-P1-5 | Kiosk 初始 60s 太短 | `76db3bc` | 改為 120 秒 |
| UX-P1-6 | Escrow 確認 15s 太短 | `5965378` | 改為 30 秒 |
| UX-P1-7 | Exchange 無退鈔通知 | `9ec3e5d` | 加 KioskRejected listener |
| UX-P1-8 | 隱私權 Modal 內容損壞 | `b263c6c` | 修復文字 |
| UX-P1-9 | Dev login 殘留 | `b263c6c` | 移除，改為 LINE 登入 |

---

## 三、未修復項目一覽（14 頭）

### 🟠 P1 邏輯錯誤（1 項未修）

| # | 問題 | 當前狀態 | 風險 |
|:---|:---|:---|:---|
| P1-5 | MachineController + MachineSession + 舊路由仍存在 | `MachineController.php`(9.3KB)、`MachineSession.php`、`/api/machine/*` 路由仍在 `routes/api.php` | 低（前端已不使用，但增加攻擊面） |

### 🟡 P2 代碼品質（8 項未修）

| # | 問題 | 當前狀態 |
|:---|:---|:---|
| P2-1 | Vue 從 CDN 載入 | `welcome.blade` 和 `play.blade` 仍 `import from 'https://unpkg.com/vue@3/...'` |
| P2-2 | welcome.blade.php 2500+ 行 | 未拆分 |
| P2-3 | DeviceController 重複代碼 | 未重構 |
| P2-4 | Schema::getColumnListing 濫用 | 仍有 9 處（MemberWallet 2 + DeviceController 7） |
| P2-5 | KioskSession 硬編碼 URL | 仍為 `'https://api.tg25.win/api/internal/mqtt/publish'` |
| P2-6 | PERF 日誌寫死 | CallbackController 仍有 `[PERF]`/`[PERF2]` 的 `Log::info()` |
| P2-7 | BillController 無路由（死代碼） | 仍無路由指向，死代碼狀態 |
| P2-8 | .gitignore 是 Python 模板 | 仍為 `__pycache__/`、`*.pyc` 等 Python 內容 |

### 📋 P3 設定與部署（4 項未修）

| # | 問題 | 當前狀態 |
|:---|:---|:---|
| P3-1 | .env.example 預設值不當 | 仍為 `sqlite`/`log`/`database` |
| P3-2 | config/services.php infra 冗餘 | 仍有 `url`+`base_url`（同讀 INFRA_BASE_URL 但預設值不同）、`key`+`infra_key` 重複 |
| P3-3 | 測試覆蓋率極低 | 仍只有 ExampleTest 空殼 |
| P3-4 | 根目錄雜物堆積 | `pyrefly.toml`、`hq_agent_tools/`、`AGENTS.md.backup`、`public/waw_test.html`、`public/ota/firmware.bin` 仍在 |

### 🎨 UX（1 項未修）

| # | 問題 | 當前狀態 |
|:---|:---|:---|
| UX-P0-4b | Venue 頁面（/devices, /billing, /subscriptions）可能仍無 auth | `routes/web.php` 中三條路由仍為裸 `view()`，無 middleware |

---

## 四、風險評估

### 🔴 仍有風險的項目

1. **UX-P0-4b：Venue 頁面可能仍無認證**
   - `/devices`、`/billing`、`/subscriptions` 三條路由在 `routes/web.php` 中仍為裸 `Route::get(..., fn() => view(...))`，無 auth middleware
   - 雖然頁面內容目前全是假資料（不影響真實資料安全），但帳單頁暴露了銀行帳號（玉山 808 帳號 0123-456-789012），不應對外公開

2. **P1-5：舊版 MachineController 仍在**
   - 前端已切換到 `/api/device/*`，但 `/api/machine/*` 路由仍在
   - 攻擊者可直接呼叫舊路由觸發非預期行為

### 🟡 低風險但應處理的項目

3. **P2-5：KioskSession 硬編碼 URL** — 若 Infra 域名變更需手動改代碼
4. **P2-4：Schema::getColumnListing** — 每次呼叫查 information_schema，效能損耗
5. **P2-1：Vue CDN 依賴** — CDN 不穩定時前端白屏

---

## 五、Mina 申請事項

懇請 HQ 裁勘以下事項：

1. **P0 安全修復是否合格**？6 項 P0 全部修復，請確認修復方式是否達到金融級安全標準。

2. **P1-5 MachineController 是否可安全移除**？需確認無其他系統（Infra / Alliance / iHub）依賴 `/api/machine/*` 路由。若可移除，Mina 可立即執行。

3. **UX-P0-4b Venue 頁面認證**：這三個頁面目前全是假資料，是否：
   - (A) 直接移除路由（功能未上線）
   - (B) 加 auth middleware + 後台管理員權限
   - (C) 暫時保留但加 IP 白名單

4. **P2 代碼品質改善排程**：8 項均未動工，是否分批派工？
   - P2-5（KioskSession URL）和 P2-8（.gitignore）各只需 5 分鐘，可立即修
   - P2-1（Vue CDN → Vite）和 P2-2（拆分 welcome.blade）需較大重構，建議獨立任務

5. **P3 設定部署改善排程**：4 項均未動工，是否列入下次部署前必做清單？

---

**回報人**：Mina (Member)
**回報時間**：2026-09-14 14:00
**狀態**：等待 HQ 裁勘指示
