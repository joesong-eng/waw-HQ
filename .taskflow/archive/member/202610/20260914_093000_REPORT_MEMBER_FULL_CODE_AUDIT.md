# Member 專案全面健康審查報告

**執行時間**：2026-09-14 09:30
**負責人**：Mina (Member)
**審查範圍**：`win.tg25.win` (Member) 全專案原始碼
**審查方法**：全量人工 Code Review（routes、controllers、models、services、events、config、migrations、views、frontend JS）
**狀態**：⚠️ 審查完成，待 HQ 裁決修復優先級與派工

---

## 一、執行摘要

本次對 Member 專案進行了全量代碼審查，涵蓋 20 個 PHP 類（Controller / Model / Service / Event / Command）、4 條路由文件、15 個 Migration、2 個核心 Blade 模板、前端 JS/CSS。

共發現 **25 項問題**，按嚴重程度分級：

| 級別 | 數量 | 概述 |
|:---|:---|:---|
| 🔴 P0 嚴重安全漏洞 | 6 | 憑證外洩、後門無守衛、WebSocket 全公開、指令端點無認證、SSL 關閉、時序攻擊 |
| 🟠 P1 邏輯與架構錯誤 | 7 | 幣別常數不一致導致 Kiosk 餘額顯示為 0、越權查詢、殭屍 Session 等 |
| 🟡 P2 代碼品質問題 | 8 | CDN 依賴、單檔超長、重複代碼、動態欄位查詢等 |
| 📋 P3 設定與部署問題 | 4 | .env 預設值、config 冗餘、測試覆蓋率低、根目錄雜物 |

**最嚴重風險**：LINE Client Secret 已寫死在 Git 中；AuthController 測試後門在 production 仍可繞過 Firebase 驗證；WebSocket 全部使用 Public Channel，任何人可監聽任意會員餘額變動。

---

## 二、🔴 P0 嚴重安全漏洞（必須立即修復）

### P0-1：AuthController 測試後門未受環境保護

**檔案**：`app/Http/Controllers/Api/AuthController.php`
**嚴重性**：🔴 Critical — 可繞過 Firebase 驗證直接登入

```php
if ($idTokenString === 'TEST_MODE_886937271782') {
    $phoneNumber = '+886937271782';
    return $this->loginOrCreateMember($phoneNumber);
}
```

**問題**：此後門**沒有** `app()->environment('production')` 檢查。只要知道 magic string `TEST_MODE_886937271782`，任何人可在 production 環境繞過 Firebase 驗證，以 +886937271782 身份登入並取得 Sanctum Token。與 `/api/dev/token` 不同（該端點有 production 守衛），此後門在所有環境均有效。

**修復方案**：
```php
if (app()->environment('local', 'staging') && $idTokenString === 'TEST_MODE_886937271782') {
    // ...
}
```

**預估工時**：10 分鐘

---

### P0-2：LINE Login 憑證硬編碼在原始碼中

**檔案**：`app/Http/Controllers/Api/LineLoginController.php`
**嚴重性**：🔴 Critical — 憑證已進 Git 版本控制

```php
private $clientId = '2009625522';
private $clientSecret = '20f443a0498bcdbfb1e24906f40704e3';
```

**問題**：LINE Channel Access Token Secret 直接寫死在 Controller 類屬性中，已進 Git 歷史。任何能接觸 repo 的人（含未來新進人員）都能取得此密鑰，可偽造 LINE OAuth 流程。

**修復方案**：
1. 移至 `.env`：`LINE_CLIENT_ID`、`LINE_CLIENT_SECRET`
2. 在 `config/services.php` 新增 `line` 段落讀取
3. Controller 改用 `config('services.line.client_id')`
4. **立即在 LINE Developers Console rotate Secret**
5. 用 `git filter-repo` 或 BFG 清除 Git 歷史中的密鑰

**預估工時**：30 分鐘（不含 Git 歷史清理）

---

### P0-3：WebSocket 頻道全為 Public Channel

**檔案**：`app/Events/MemberPointsUpdated.php`、`DeviceCreditOut.php`、`SessionTerminated.php`、`KioskSessionUpdated.php`、`MemberBoundToKiosk.php`、`KioskEscrowPending.php`、`KioskRejected.php`
**嚴重性**：🔴 Critical — 會員隱私全暴露

```php
// MemberPointsUpdated.php
public function broadcastOn(): array {
    return [new Channel('member.' . $this->memberId)]; // Public!
}

// MemberBoundToKiosk.php
public function broadcastOn(): array {
    return [new Channel('kiosk.' . strtolower($this->session->kiosk_id))]; // Public!
}
```

**問題**：所有 WebSocket 事件使用 `Illuminate\Broadcasting\Channel`（Public），而非 `PrivateChannel`。任何人只要知道 `member_id` 或 `kiosk_id`（均為小整數或可推測字串），即可監聽：
- 會員餘額變動（`MemberPointsUpdated`）
- 洗分/開分結果（`DeviceCreditOut`）
- Session 終止（`SessionTerminated`）
- Kiosk 投幣/綁定/裁決（`KioskSessionUpdated`、`MemberBoundToKiosk`、`KioskEscrowPending`）
- 紙鈔退回（`KioskRejected`）

**修復方案**：
1. 所有 Member 相關事件改為 `PrivateChannel`：
   ```php
   return [new PrivateChannel('member.' . $this->memberId)];
   ```
2. Kiosk 平板頻道改為 `PresenceChannel`（需認證）
3. 前端 `echo.js` 加入 Sanctum token 認證
4. `routes/channels.php` 加入頻道授權邏輯

**預估工時**：2-3 小時

---

### P0-4：Engineering 指令端點無任何認證

**檔案**：`routes/api.php` → `EngineeringController::kioskCommand()`
**嚴重性**：🔴 Critical — 可遠端控制硬體設備

```php
Route::post('/engineering/kiosk/cmd', [EngineeringController::class, 'kioskCommand']);
```

**問題**：`kioskCommand()` 方法可發送 OTA / Reboot 等指令給任意 Kiosk 設備，但該路由**沒有任何 auth middleware 或 X-Internal-Key 驗證**。任何人可呼叫此端點遠端重啟或更新場館所有 Kiosk 韌體。

**修復方案**：加入內部金鑰驗證或 Sanctum + admin role 檢查。

**預估工時**：15 分鐘

---

### P0-5：SSL 憑證驗證全面關閉

**檔案**：`app/Http/Controllers/Api/DeviceController.php`、`app/Http/Controllers/Api/KioskController.php`
**嚴重性**：🔴 High — 中間人攻擊風險

```php
$options = ['verify' => false];
```

**問題**：所有對 Infra (`api.tg25.win`) 的 HTTP 呼叫都關閉了 SSL 驗證。在傳輸 `X-Internal-Key`、`X-API-Key`、會員資料、餘額等敏感資料時，允許中間人攻擊攔截。

**修復方案**：
1. 正確配置 CA 憑證路徑
2. 設 `'verify' => true` 或指向系統 CA bundle
3. 若使用自簽憑證，配置 `CURLOPT_CAINFO`

**預估工時**：30 分鐘

---

### P0-6：內部金鑰比對使用 `===` 而非 `hash_equals()`

**檔案**：`DeviceController.php`、`CallbackController.php`、`EngineeringController.php`、`KioskController.php`
**嚴重性**：🟠 Medium-High — 時序攻擊

```php
return $key && $key === config('services.infra.callback_key');
```

**問題**：字串嚴格比較 `===` 可被時序攻擊（timing attack）逐字元破解金鑰。金融級系統必須使用常數時間比較。

**修復方案**：
```php
return $key && hash_equals(config('services.infra.callback_key'), $key);
```

**預估工時**：20 分鐘（約 8 處替換）

---

## 三、🟠 P1 邏輯錯誤與架構問題

### P1-1：幣別常數不一致 — 系統核心矛盾

**影響**：Kiosk 平板綁定後會員餘額顯示永遠為 0

| 位置 | 使用的幣別值 | 是否有對應錢包 |
|:---|:---|:---|
| `MemberWallet::CURRENCY_COIN` | `'COIN'` | ✅ 系統常數 |
| `MemberWallet::CURRENCY_TICKET` | `'TICKET'` | ✅ 系統常數 |
| `AuthController::ensureWalletsExist()` | `'COIN'` + **`'CASH'`** | ❌ 無 CASH 常數 |
| `MemberBoundToKiosk::broadcastWith()` | **`'POINT'`** | ❌ 無 POINT 錢包 |
| `BillAcceptorService` | `['COIN','TOKEN','POINT']` | ❌ TOKEN/POINT 不存在 |

```php
// MemberBoundToKiosk.php — 查詢不存在的 'POINT' 幣別
'balance' => (float)($this->member->wallets()
    ->where('currency_type', 'POINT')->value('balance') ?? 0),
```

**問題**：`MemberBoundToKiosk` 事件查詢 `currency_type = 'POINT'`，但系統常數是 `'COIN'`，導致 Kiosk 平板綁定後顯示餘額永遠為 0。同時 `AuthController` 建立的 `'CASH'` 錢包在整個系統中無人使用。

**修復方案**：
1. 全局搜索 `'POINT'`、`'TOKEN'`、`'CASH'` 字串硬編碼
2. 統一替換為 `MemberWallet::CURRENCY_COIN` / `CURRENCY_TICKET`
3. 移除 `AuthController` 中建立 CASH 錢包的邏輯

**預估工時**：1 小時

---

### P1-2：MemberController 交易查詢無權限驗證

**檔案**：`app/Http/Controllers/Api/MemberController.php`

```php
$memberId = $request->query('member_id');
// 沒有驗證 $request->user()->id === $memberId
$transactions = WalletTransaction::where('member_id', $memberId)...
```

**問題**：任何已登入會員只需修改 URL 參數 `?member_id=1` 即可查看其他會員的交易紀錄。此路由在 `auth:sanctum` middleware 下，但未驗證當前用戶與查詢目標一致。

**修復方案**：`$memberId = $request->user()->id;`（忽略前端傳入）

**預估工時**：10 分鐘

---

### P1-3：CheckOfflineSessions 描述與實作不符

**檔案**：`app/Console/Commands/CheckOfflineSessions.php`

```php
protected $description = 'End active sessions where member heartbeat lost 3 minutes';
// 但實際：
$cutoff = now()->subSeconds(60); // 只等 60 秒，不是 3 分鐘
```

**問題**：描述 3 分鐘但實際 60 秒就終止 Session，可能導致網路不穩時誤踢玩家。

**修復方案**：統一為 180 秒或依需求調整。

**預估工時**：5 分鐘

---

### P1-4：CallbackController::settle() 潛在 NPE（Null Pointer Exception）

**檔案**：`app/Http/Controllers/Api/CallbackController.php`

```php
$wallet = MemberWallet::where('member_id', ...)
    ->where('currency_type', MemberWallet::CURRENCY_COIN)
    ->lockForUpdate()
    ->first();
$wallet->increment('balance', $amountToReturn); // 若 $wallet 為 null 直接炸
```

**問題**：若會員沒有 COIN 錢包（理論上 AuthController 會建立，但若 firstOrCreate 失敗或 race condition），直接呼叫 `->increment()` 會 500 Error，且因在 DB::transaction 中可能導致金額遺失。

**修復方案**：加 null check + firstOrCreate fallback。

**預估工時**：15 分鐘

---

### P1-5：MachineController 與 DeviceController 並存（殭屍代碼）

**問題**：兩套控制器做功能重疊的事：
- `MachineController` 用 `MachineSession` 模型 + 舊版 API（`/api/machine/*`）
- `DeviceController` 用 `DeviceSession` 模型 + 新版 API（`/api/device/*`）

`MachineController` 和 `MachineSession` 為舊版遺留，前端 `play.blade.php` 已全部使用 `/api/device/*`。舊代碼增加攻擊面且造成維護困惑。

**修復方案**：移除 `MachineController`、`MachineSession` 及對應路由，或標記 `@deprecated`。

**預估工時**：30 分鐘

---

### P1-6：KioskController::sessionStatus() 更新心跳導致殭屍 Session

**檔案**：`app/Http/Controllers/Api/KioskController.php`

```php
// 不管 session 有沒有 member，都更新 last_active_at
$session->update(['last_active_at' => now()]);
```

**問題**：平板輪詢 `session-status` 會讓沒有會員綁定的空閒 session 永遠不過期。`CleanupStaleSessions`（10 分鐘無活動清理）永遠無法清理這些殭屍 session。

**修復方案**：僅在 `$session->member_id` 不為 null 時更新 `last_active_at`。

**預估工時**：10 分鐘

---

### P1-7：`database/database.sqlite` 進了 Git

**問題**：SQLite 資料庫本體被版控追蹤，可能造成合併衝突和敏感資料洩漏。

**修復方案**：`git rm --cached database/database.sqlite`，加入 `.gitignore`。

**預估工時**：5 分鐘

---

## 四、🟡 P2 代碼品質與維護性問題

### P2-1：Vue 從 CDN 載入而非 Vite 打包

**檔案**：`resources/views/welcome.blade.php`、`play.blade.php`

```html
import { createApp } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js'
<script src="https://unpkg.com/html5-qrcode"></script>
```

**問題**：
- 已配置 Vite + Tailwind 但完全不用，Vue 直接從 unpkg CDN 載入
- CDN 不穩定時整個前端掛掉
- 無法做 tree-shaking 和版本鎖定
- `resources/js/app.js` 只 import bootstrap，形同虛設

**修復方案**：在 `package.json` 加入 `vue` 和 `html5-qrcode` 依賴，用 Vite 打包。

**預估工時**：2 小時

---

### P2-2：welcome.blade.php 單文件超過 2500 行

**問題**：HTML + CSS + Vue JS 全塞在一個 Blade 模板裡，極難維護。

**修復方案**：拆分為 Vue SFC 組件（`.vue` 檔），用 Vite 編譯。

**預估工時**：4-6 小時（可分批）

---

### P2-3：DeviceController 大量重複代碼

**問題**：
- `checkSession()` 和 `bind()` 有約 100 行幾乎一模一樣的設備查詢 + session 處理 + 錢包初始化 + JSON 回應邏輯
- `creditIn()` 和 `creditOut()` 的設備查詢和 delta 計算也高度重複

**修復方案**：抽取 private helper 方法或獨立 Service 類。

**預估工時**：1-2 小時

---

### P2-4：濫用 `Schema::getColumnListing()` 做動態欄位過濾

```php
$columns = \Schema::getColumnListing('wallet_transactions');
$attributes = array_intersect_key($txData, array_flip($columns));
WalletTransaction::create($attributes);
```

**問題**：
- Eloquent Model 的 `$fillable` 已經做這件事
- 每次呼叫都去查 `information_schema`，效能差
- 出現在 `DeviceController`、`MemberWallet` 等至少 6 處

**修復方案**：移除動態欄位查詢，直接使用 `Model::create($data)`。

**預估工時**：1 小時

---

### P2-5：KioskSession::terminate() 硬編碼 URL

```php
$url = 'https://api.tg25.win/api/internal/mqtt/publish';
```

**修復方案**：使用 `config('services.infra.base_url')`。

**預估工時**：5 分鐘

---

### P2-6：`[PERF]` `[PERF2]` 效能日誌寫死在正式邏輯中

**問題**：`CallbackController` 中大量 `Log::info('[PERF] ...')` 在正式邏輯流程中，會在 production 持續產出大量日誌，影響效能和磁碟空間。

**修復方案**：改用 `Log::debug()` 或加環境判斷 `if (app()->environment('local'))`。

**預估工時**：20 分鐘

---

### P2-7：BillController 無路由（死代碼）

**問題**：`BillController::detected()` 方法存在，但 `routes/api.php` 和 `routes/web.php` 中找不到任何指向它的路由。是死代碼或遺漏路由。

**修復方案**：確認是否需要此功能，若需要則加路由，否則移除。

**預估工時**：10 分鐘

---

### P2-8：`.gitignore` 是 Python 模板

**問題**：包含 `__pycache__/`、`*.pyc`、Django/Flask/Scrapy 等段落，重複條目。不完全適配 Laravel 專案（缺少 `/.env`、`/storage/` 等 Laravel 標準忽略項）。

**修復方案**：替換為 Laravel 標準 `.gitignore`。

**預估工時**：10 分鐘

---

## 五、📋 P3 設定與部署問題

### P3-1：`.env.example` 預設值不利部署

| 項目 | 預設值 | 問題 |
|:---|:---|:---|
| `DB_CONNECTION` | `sqlite` | 遠端部署用 MySQL，範例應標明 |
| `BROADCAST_CONNECTION` | `log` | 遠端用 reverb |
| `CACHE_STORE` | `database` | 遠端用 redis |
| `SESSION_DRIVER` | `database` | 遠端用 redis |
| `QUEUE_CONNECTION` | `database` | 遠端用 redis |

**修復方案**：更新 `.env.example` 為 production 標準配置，加註釋說明 local/dev 差異。

---

### P3-2：`config/services.php` infra 設定冗餘且混亂

```php
'infra' => [
    'url'       => env('INFRA_BASE_URL', 'https://infra.tg25.win'),  // InfraApiService 用
    'base_url'  => env('INFRA_BASE_URL', 'https://api.tg25.win'),   // DeviceController 用
    'key'       => env('INFRA_KEY'),
    'api_key'   => env('INFRA_CREDIT_X_API_KEY'),
    'infra_key' => env('INFRA_KEY'),     // 跟 'key' 完全重複
    'callback_key' => env('INFRA_CALLBACK_INTERNAL_KEY'),
],
```

`url` 和 `base_url` 都讀 `INFRA_BASE_URL` 但預設值不同（`infra.tg25.win` vs `api.tg25.win`），`key` 和 `infra_key` 都讀 `INFRA_KEY` 但名稱不同。

**修復方案**：統一 key 名稱，移除冗餘項，釐清 `infra.tg25.win` 與 `api.tg25.win` 的關係。

---

### P3-3：測試覆蓋率極低

```
tests/Unit/   → 只有 ExampleTest.php (空殼)
tests/Feature/ → DeviceBindTest.php, DeviceCreditTest.php, ExampleTest.php
```

核心的 `KioskController`、`WalletService`、`BillAcceptorService`、`CallbackController` 完全沒有測試。

**修復方案**：優先為 WalletService（金流核心）和 CallbackController（回調驗證）編寫測試。

---

### P3-4：專案根目錄雜物堆積

以下文件/目錄不應出現在 Laravel 專案根目錄：

| 文件/目錄 | 性質 | 處置建議 |
|:---|:---|:---|
| `AGENTS.md.backup_20260816_2` | 備份檔 | 刪除 |
| `SITE_TEST_CHECKLIST.md`、`TASK_*.md` 等 | 任務報告 | 移至 `_agent/archive/` |
| `404.html`、`index.html` | 非 Laravel 標準 | 刪除或移至 `public/` |
| `pyrefly.toml` | Python 工具設定 | 刪除 |
| `hq_agent_tools/` | Python 腳本 | 移至專案外 |
| `_agent/` 大量 Redis JSON 和報告 | 歷史遺留 | 歸檔清理 |
| `public/ota/firmware.bin` | 韌體二進位檔 | 不應在 Member 專案 |
| `public/waw_test.html` | 測試頁面 | 刪除 |
| `test_game_v0_apis.sh` | 測試腳本含硬編碼 key | 清理或移除密鑰 |

---

## 六、修復優先級與建議排程

### 🔴 第一階段：緊急安全修復（建議 1-2 天內完成）

| 順序 | 項目 | 預估工時 | 阻塞性 |
|:---|:---|:---|:---|
| 1 | P0-1: AuthController 後門加環境守衛 | 10min | 阻斷未授權登入 |
| 2 | P0-2: LINE 憑證移至 .env + rotate secret | 30min | 阻斷憑證外洩 |
| 3 | P0-4: Engineering cmd 端點加認證 | 15min | 阻斷遠端設備控制 |
| 4 | P0-6: hash_equals() 替換 === | 20min | 阻斷時序攻擊 |
| 5 | P0-3: WebSocket 改 PrivateChannel | 2-3h | 阻斷資料竊聽 |
| 6 | P0-5: SSL verify 開啟 | 30min | 阻斷 MITM |

### 🟠 第二階段：邏輯修復（建議 1 週內完成）

| 順序 | 項目 | 預估工時 |
|:---|:---|:---|
| 7 | P1-1: 幣別常數統一 | 1h |
| 8 | P1-2: MemberController 加權限檢查 | 10min |
| 9 | P1-4: CallbackController settle NPE 修復 | 15min |
| 10 | P1-6: Kiosk 殭屍 Session 修復 | 10min |
| 11 | P1-3: CheckOfflineSessions 參數修正 | 5min |
| 12 | P1-7: database.sqlite 移出 Git | 5min |
| 13 | P1-5: 移除舊版 MachineController | 30min |

### 🟡 第三階段：代碼品質改善（建議 2 週內分批完成）

| 順序 | 項目 | 預估工時 |
|:---|:---|:---|
| 14 | P2-1: Vue 改用 Vite 打包 | 2h |
| 15 | P2-2: welcome.blade 拆分 | 4-6h |
| 16 | P2-4: 移除 Schema::getColumnListing | 1h |
| 17 | P2-3: DeviceController 去重複 | 1-2h |
| 18 | P2-6: PERF 日誌降級 | 20min |
| 19 | P2-5: KioskSession 硬編碼 URL 修正 | 5min |
| 20 | P2-7: BillController 路由確認 | 10min |
| 21 | P2-8: .gitignore 替換 | 10min |

### 📋 第四階段：設定與部署優化

| 順序 | 項目 | 預估工時 |
|:---|:---|:---|
| 22 | P3-1: .env.example 更新 | 15min |
| 23 | P3-2: config/services.php 統一 | 20min |
| 24 | P3-4: 根目錄清理 | 30min |
| 25 | P3-3: 核心測試編寫 | 4-8h |

---

## 七、總結與建議

Member 專案功能基本完整，Kiosk 儲值 + Device 遊戲機雙系統架構合理。但**安全防護存在系統性缺失**：

1. **憑證管理**：LINE Secret 硬編碼在 Git 中，須立即 rotate
2. **認證守衛**：測試後門在 production 可用，Engineering 指令端點完全無認證
3. **傳輸安全**：SSL 驗證全關，WebSocket 全公開，金鑰比對可時序攻擊
4. **資料隔離**：會員可越權查詢他人交易，幣別常數不一致導致功能異常

**懇請 HQ 裁決**：
1. P0 安全修復是否能以緊急任務派發，不經過常規排程？
2. LINE Secret rotation 是否需要協調 LINE Developers Console 權限（可能需要 Owner 協助）？
3. WebSocket PrivateChannel 改造涉及前端 echo.js 配合，是否需要一併調整 Infra 端的 Broadcasting 設定？
4. 舊版 MachineController 是否確認可安全移除（需確認無其他系統依賴）？

---

**回報人**：Mina (Member)
**回報時間**：2026-09-14 09:30
**等待指示**：HQ 裁決修復排程與跨專案協調
