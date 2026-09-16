# 任務回報：TASK_20260909_ALLIANCE_UX_REDESIGN_PHASE1

**完成時間**：2026-09-09 18:30  
**執行者**：Allie (Alliance Lead)  
**優先級**：P0 (High)  
**狀態**：✅ 已完成遠端部署並驗證通過  

---

## 一、任務背景與執行目標

落實 Joe 確認之 7 項裁示與 UX 重規劃原則（**「用戶正在做的事情不能被打斷」**），全速完成 Phase 1（P0 最急迫項目）：
1. 訂單開單/編輯頁 4 個 AJAX 彈窗（新增客戶、新增介紹人、快速新增產品、新增夥伴），送出成功後動態更新下拉選單，頁面不刷新、已填寫表單資料不丟失。
2. 建置 `ali_referrals` 簡表（姓名、電話、email、line_id）並與訂單 `referral_id` 串通。
3. 訂單列表加入關鍵字、狀態、日期區間、夥伴、客戶多維搜尋篩選。
4. 側邊欄導航重排，將「燒錄與配對」提升到第 3 位，保留待燒錄紅點 badge。
5. 訂單詳情頁加入「⚡ 前往燒錄」按鈕，帶入 `order_id` 無縫跳轉燒錄工作站自動選中載入。

---

## 二、Git Commit 與異動檔案清單

### Commit 記錄
- `5610046` feat(ux): implement Phase 1 UX redesign with quick modals, referrals table, order filters, and burning shortcuts
- `9de7698` fix(routes): import QuickCreateController in web.php
- `b5f8229` fix(views): safe check for errors bag in create and edit views

### 異動檔案清單（共 18 個檔案）
1. **新建資料表 Migration**：
   - `database/migrations/2026_09_09_180000_create_ali_referrals_table.php`
2. **新建 Model**：
   - `app/Models/AliReferral.php`
3. **新建 Controller**：
   - `app/Http/Controllers/QuickCreateController.php` (包含 4 個 AJAX API)
4. **新建 Blade 元件**：
   - `resources/views/orders/_quick_modals.blade.php` (4 個深色高對比 AJAX 彈窗及動態 JS)
5. **修改 Model**：
   - `app/Models/AliOrder.php` (新增 `referral()` 與 `owner()` 關聯，完善 casts)
   - `app/Models/User.php` (擴展 `phone`, `status`, `line_id` 至 fillable)
   - `app/Models/AliProduct.php` (擴展 `firmware_type` 至 fillable)
6. **修改 Controller 與路由**：
   - `app/Http/Controllers/OrderController.php` (支援多維篩選、介紹人串接、關聯預載)
   - `app/Http/Controllers/DeviceController.php` (支援 `order_id` 參數指定訂單載入)
   - `routes/web.php` (註冊 `POST /api/quick/{customers,referrals,products,partners}`)
7. **修改 Blade 視圖**：
   - `resources/views/layouts/app.blade.php` (側邊欄重排：儀表板 → 訂單管理 → 燒錄與配對 → 產品 → 夥伴 → 結算)
   - `resources/views/orders/index.blade.php` (新增搜尋篩選列、介紹人欄位、快速燒錄按鈕)
   - `resources/views/orders/create.blade.php` (引入 4 個彈窗觸發、介紹人下拉)
   - `resources/views/orders/edit.blade.php` (引入 4 個彈窗觸發、介紹人下拉)
   - `resources/views/orders/show.blade.php` (頂部與操作區新增「⚡ 前往燒錄」按鈕、顯示介紹人資訊)
   - `resources/views/devices/burning.blade.php` (支援 URL `order_id` 自動選定並觸發配對池載入)
8. **版本控制維護**：
   - `.gitignore` (忽略 `.taskbox` symlink)
   - `AGENTS.md`

---

## 三、五大核心項目實作細節

### 1. 訂單開單 4 個 AJAX 快速彈窗（Zero Data Loss）
- **獨立控制器**：建立 `QuickCreateController`，提供專屬的 4 個 API endpoint：
  - `POST /api/quick/customers`：新增 `User (role=owner)`，無信箱自動產生內部專屬 `owner_xxx@ali.local`。
  - `POST /api/quick/referrals`：新增 `AliReferral`。
  - `POST /api/quick/products`：快速建品，支援品名、單價、硬體成本、韌體出貨款、韌體類型。
  - `POST /api/quick/partners`：新增 `AliPartner`。
- **前端動態選入**：
  - 成功回傳後，透過 JS 自動在目標下拉選單中插入 `<option selected>`，並觸發 `change` 事件連動既有欄位（例如客戶自動填入姓名/電話）。
  - 快速建品成功後，自動將產品推入 `allProducts` 陣列並直接呼叫 `selectProduct()` 展開為 BOM 項目，無須重填。
  - 原訂單表單完全不送出、不刷新，所有已填欄位 100% 保持原樣。

### 2. ali_referrals 簡表建置與訂單 referral_id 串通
- 依 Joe 裁示，介紹人純屬紀錄性質、無後台登入權限。
- 建立 `ali_referrals` 資料表（姓名、電話、email、line_id、notes、status），支援索引加速查詢。
- `AliOrder` 與 `AliReferral` 雙向關聯串通，開單及編輯可直接下拉選擇介紹人，訂單詳情與出貨單同步印出介紹人資訊。

### 3. 訂單列表多條件搜尋與篩選工具列
- 在 `orders/index.blade.php` 頂部加入直覺緊湊工具列：
  - 🔍 關鍵字搜尋：涵蓋訂單號、客戶姓名、電話。
  - 狀態篩選：全部、開單中 (draft)、已確認 (confirmed)、處理中 (processing)、出貨單 (completed)。
  - 夥伴篩選：快速篩選所屬合作夥伴。
  - 客戶篩選：快速篩選機台老闆。
  - 日期區間：起始日期與結束日期篩選。
  - 快速清除篩選按鈕。
- 列表表格新增「介紹人」欄位與「⚡ 燒錄」一鍵跳轉捷徑按鈕。

### 4. 側邊欄導航重排（工作頻率導向）
- 依 Joe 裁示，將工作頻率最高的「燒錄與配對」提升到第 3 位：
  `1. 📊 儀表板` → `2. 📋 訂單管理` → `3. ⚡ 燒錄與配對` → `4. 📦 產品管理` → `5. 🤝 合作夥伴` → `6. 💰 結算管理`。
- 完整保留待燒錄紅點 badge（當待燒錄卡片數量大於 0 時顯示紅點與數量徽章）。

### 5. 訂單直跳燒錄工作站
- 在 `orders/show.blade.php` 的頂部操作列與底部狀態控制列均配置醒目金色按鈕「⚡ 前往燒錄」，帶入參數 `?order_id={{ $order->id }}`。
- 在 `DeviceController@index` 中接收 `order_id`，即使該訂單為特定自訂狀態亦確保載入待選集合。
- 燒錄工作站頁面 (`devices/burning.blade.php`) 在初始化時自動鎖定該訂單並觸發配對池更新與燒錄進度載入。

---

## 四、遠端部署與驗收成果

### 1. 遠端部署指令
- 遠端主機：`yd16 / alliance (137.131.50.16)`
- 執行指令：`../../dev_tools/waw_ops.sh deploy alliance`
- Git pull 與遠端 commit 確認：`b5f8229`（與 local main 完全一致）。

### 2. 資料庫 Migration 執行結果
```
   INFO  Running migrations.  

  2026_09_09_180000_create_ali_referrals_table ................. 387.01ms DONE
```

### 3. API 路由與 Controller 驗收
```
  POST  api/quick/customers ................ api.quick.customers › QuickCreateController@storeCustomer
  POST  api/quick/partners ................. api.quick.partners › QuickCreateController@storePartner
  POST  api/quick/products ................. api.quick.products › QuickCreateController@storeProduct
  POST  api/quick/referrals ................ api.quick.referrals › QuickCreateController@storeReferral
```

### 4. 4 個 AJAX Endpoint 遠端 Tinker 實測回傳
- **Customer**：`{"success": true, "message": "客戶新增成功", "data": {"id": 8, "name": "測試新客戶林老闆", "phone": "0977888999", "email": "owner_0977888999@ali.local"}}`
- **Referral**：`{"success": true, "message": "介紹人新增成功", "data": {"id": 2, "name": "測試新介紹人陳先生", "phone": "0966555444", "line_id": "chen_vip"}}`
- **Product**：`{"success": true, "message": "產品新增成功", "data": {"id": 5, "name": "測試快建S3採集卡", "sku": "PROD-FRRJOQ", "price": 2800, "category": "item", "has_firmware": true, "bom": []}}`
- **Partner**：`{"success": true, "message": "合作夥伴新增成功", "data": {"id": 3, "name": "測試新經銷夥伴南區"}}`

### 5. Blade 頁面遠端編譯與渲染檢查（全部通過）
- `orders.index`：渲染 27,464 bytes，無報錯。
- `orders.create`：渲染 60,661 bytes，無報錯。
- `orders.edit`：渲染 59,821 bytes，無報錯。
- `orders.show`：渲染 31,899 bytes，無報錯。
- `devices.burning`：渲染 105,301 bytes，無報錯。

### 6. 公開站點 HTTP 驗證
- 訪問 `https://ali.tg25.win/login`：`HTTP/2 200 OK`，正常提供服務。

---

## 五、後續階段預告 (Phase 2)

Phase 1 驗收通過後，隨時可展開 Phase 2：
1. 訂單狀態機 7 步改造（`draft` → `confirmed` → `burning` → `burned` → `ready_to_ship` → `shipped` → `completed`）。
2. `ali_firmware_royalties` 資料表建置與出貨時自動記帳邏輯（每台綁定設備以產品 `software_license_fee` 記帳給 Joe）。
3. 儀表板待辦工作引導區塊。
4. 個人資料頁暗色系主題統一。

