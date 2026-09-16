# 任務回報：TASK_20260909_ALLIANCE_UX_REDESIGN_PHASE2

**完成時間**：2026-09-09 19:30  
**執行者**：Allie (Alliance Lead)  
**優先級**：P0 (High)  
**狀態**：✅ 已完成遠端部署並驗證通過（100% Passed）  

---

## 一、任務背景與執行目標

依據 HQ 與 Joe 最新指示，落實「連續自動審核與推進模式」，全速展開並完成 Phase 2 施工：
1. **訂單狀態機 7 步全鏈路改造**：
   - 完整狀態流轉：`draft`（開單中） → `confirmed`（已確認） → `burning`（燒錄中） → `burned`（已燒錄） → `ready_to_ship`（待出貨） → `shipped`（已出貨） → `completed`（已完成）。
   - Controller 動作切換、前置條件校驗與安全防禦。
   - `orders/show` 與 `orders/index` 加入 7 步視覺化進度條（Step Indicator）與狀態切換動作按鈕。
2. **`ali_firmware_royalties` 表與出貨自動記帳**：
   - 建立資料表 migration 與 `AliFirmwareRoyalty` Model。
   - 在 `OrderController::ship()`（出貨時）遍歷該訂單所有已綁定設備，對包含 `has_firmware` 之產品，自動寫入韌體出貨款（預設供應商 `'Joe'`，軟體授權費金額對齊產品設定）。
3. **儀表板今日待辦引導區塊 (dashboard/index.blade.php)**：
   - 頂部醒目「今日待辦 / 快捷指引」卡片（待確認訂單數、待燒錄設備數、待出貨訂單數、待結算筆數）。
   - 點擊卡片直接帶入條件跳轉至篩選後的目標頁面。
4. **個人資料頁暗色系主題統一 (profile/index.blade.php)**：
   - 徹底消除白底 Tailwind，統一改為全站一致的深色玻璃質感（Dark Glassmorphism，`slate-900 / amber-500`）風格。

---

## 二、Git Commit 與異動檔案清單

### Commit 記錄
- `b1e4595` feat(ux): implement Phase 2 with 7-step order state machine, firmware royalties auto-accounting, dashboard todos, and dark profile
- `a5fd07f` fix(profile): use safe check for validation errors in profile view
- `a5e8cc6` fix(order): handle optional partner settlement and notification on shipping

### 異動檔案清單（共 10 個檔案）
1. **新建資料表 Migration**：
   - `database/migrations/2026_09_09_190000_create_ali_firmware_royalties_table.php`
2. **新建 Model**：
   - `app/Models/AliFirmwareRoyalty.php`
3. **修改 Model**：
   - `app/Models/AliOrder.php` (新增 `firmwareRoyalties()` 關聯)
4. **修改 Controller 與路由**：
   - `app/Http/Controllers/OrderController.php` (實作 7 步流轉切換：`confirm`, `startBurning`, `finishBurning`, `readyToShip`, `ship`, `complete`, `revertToDraft`，出貨自動記帳 `recordFirmwareRoyalties()`，防禦無合作夥伴出貨結算)
   - `app/Http/Controllers/DashboardController.php` (統計今日待辦數據 `$todayTodos`：draft, burning, ready_to_ship, unsettled)
   - `routes/web.php` (新增 7 步狀態動作路由 `POST /orders/{order}/...`)
5. **修改 Blade 視圖**：
   - `resources/views/orders/show.blade.php` (新增 7 步橫向進度指示器、各步驟對應之動作切換按鈕、狀態色標)
   - `resources/views/orders/index.blade.php` (7 步狀態篩選下拉選單與色標標籤)
   - `resources/views/dashboard/index.blade.php` (頂部加入 4 格今日待辦快捷卡片)
   - `resources/views/profile/index.blade.php` (全面改寫為深色高對比 Glassmorphism 風格)

---

## 三、核心實作詳細說明

### 1. 訂單狀態機 7 步全鏈路流轉
- **流轉邏輯與規則**：
  1. `draft` → `confirmed`：業務確認訂單，鎖定產品快照。
  2. `confirmed` → `burning`：若含韌體設備，點擊進入燒錄狀態（若全為非韌體產品可直跳 `ready_to_ship`）。
  3. `burning` → `burned`：確認全部或已指派之硬體燒錄完成。
  4. `burned` → `ready_to_ship`：倉儲揀貨、包裝完成，等待物流取件。
  5. `ready_to_ship` → `shipped`：確認出貨，同時自動觸發：
     - ① 快照授權費 (`createSnapshot`)
     - ② 韌體出貨款自動記帳 (`recordFirmwareRoyalties`)
     - ③ 生成合作夥伴分潤結算單（若有指定夥伴）
     - ④ 跨庫發送出貨通知至 `waw_core.notification_inbox`
     - ⑤ 跨庫同步已綁定設備至 `waw_core.devices` (`syncDevicesToCore`)
  6. `shipped` → `completed`：買家簽收確認送達，訂單結案。
- **視圖呈現**：
  - `orders/show.blade.php` 頂部放置橫向 Step Indicator，已完成步驟為琥珀金底綠勾，當前步驟高亮呼吸燈提示，未完成步驟淡化。
  - 右上方依當前狀態動態呈現可執行的操作按鈕（例如：`確認訂單`、`進入燒錄`、`前往燒錄工作站`、`完成燒錄`、`備貨完成待發`、`確認出貨`、`確認送達結案`、`退回草稿修改`）。

### 2. 韌體出貨款自動記帳機制
- **資料表結構 (`ali_firmware_royalties`)**：
  - 欄位：`id`, `order_id`, `order_item_id`, `chip_id`, `product_id`, `product_name`, `license_fee`, `supplier_name` (預設 `'Joe'`), `shipped_at`, `billing_month` (如 `'2026-09'`), `status` (`unsettled` / `settled`), `settled_at`, `notes`, `timestamps`。
- **記帳觸發時機**：
  - 於 `OrderController::ship()` 執行出貨時，系統自動檢查訂單中包含 `has_firmware = true` 的產品，依照已綁定的設備 `chip_id`（或無個別 chip_id 時依數量）寫入 `ali_firmware_royalties`。
  - 透過 `firstOrCreate` 依 `(order_id, chip_id)` 去重，防止重複點擊造成重複記帳。

### 3. 儀表板今日待辦引導區塊
- 於 `dashboard/index.blade.php` 頂部加入四色玻璃質感卡片：
  - 🟡 **待確認訂單**：`draft` 狀態筆數，點擊直達 `/orders?status=draft`。
  - 🟠 **待燒錄設備**：`burning` 狀態筆數，點擊直達 `/devices/burning`。
  - 🔵 **待出貨訂單**：`ready_to_ship` 狀態筆數，點擊直達 `/orders?status=ready_to_ship`。
  - 🟢 **待結算款項**：未結算筆數，點擊直達 `/settlements?status=pending`。

### 4. 個人資料頁深色主題統一
- 消除原有的白色 Tailwind 背景與邊框，採用與全站一致的 `bg-slate-900/60 backdrop-blur-xl border border-slate-700/50` 風格。
- 輸入框全面改為 `bg-slate-950/80 border-slate-700/60 text-slate-100 focus:border-amber-500`，字體清晰高對比，按鈕採用琥珀金漸層。

---

## 四、遠端部署與實測驗證

### 1. 遠端部署與權限確認
- 目標主機：`yd16` (`137.131.50.16`)，路徑 `/www/wwwroot/ali.tg25.win`。
- Git 同步：遠端已 Fast-forward 同步至 `a5e8cc6`（分支與 `origin/main` 完全一致）。
- 權限修正：確保 `storage` 與 `bootstrap/cache` 權限歸屬 `www:www` (775)，解決 php-fpm 運行身份相容性。
- 快取更新：完成 `view:clear`、`config:cache`、`cache:clear`。

### 2. 資料庫 Migration 狀態
- Migration `2026_09_09_190000_create_ali_firmware_royalties_table` 已在 remote 成功執行（Batch 3 Ran）。

### 3. 狀態機 7 步全鏈路 E2E 測試輸出
遠端執行完整流程測試腳本，結果如下：
```text
FLOW: ["draft","confirmed","burning","burned","ready_to_ship","shipped","completed"]
ROYALTY: {
    "id": 3,
    "order_id": 7,
    "order_item_id": 6,
    "chip_id": "E2E_CHIP_9999",
    "product_id": 6,
    "product_name": "E2E測試採集卡",
    "license_fee": "500.00",
    "supplier_name": "Joe",
    "shipped_at": "2026-09-09T10:10:06.000000Z",
    "billing_month": "2026-09",
    "status": "unsettled",
    "settled_at": null,
    "notes": "訂單 ALI-E2E-1788948605 出貨自動記帳",
    "created_at": "2026-09-09T10:10:06.000000Z",
    "updated_at": "2026-09-09T10:10:06.000000Z"
}
```
- 狀態 7 步切換無阻礙流轉成功。
- 韌體出貨款自動計算、金額 `500.00`、供應商 `Joe`、記帳月份 `2026-09` 完全正確。

### 4. Authenticated 視圖渲染實測（真實登入環境）
```text
1. Dashboard render: OK, length 37341
2. Orders Index render: OK, length 36599
3. Orders Show render: OK, length 39107
4. Profile render: OK, length 23111
```
四大主要介面均無任何 Blade 語法或運行期錯誤，全數正常渲染。

### 5. 外網站點連線檢驗
```text
curl -sI https://ali.tg25.win/login
HTTP/2 200 
server: cloudflare
```
線上站點服務完全正常。

---

## 五、結論與後續排程

Phase 2 全部 4 大目標已 100% 達成、部署上線並經嚴格 E2E 與視圖渲染測試通過。  
隨時待命聽候 HQ 與 Joe 的後續 Phase 3 指示！

