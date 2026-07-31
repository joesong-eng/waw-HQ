# Implementation Plan: Product Management

## Overview

依照 Laravel 11 慣例，按以下順序實作：Migration → Models → ProductService → Form Requests → ProductController → Blade Views → Tests。每個 task 都可獨立執行，並在完成後整合至前一步驟。

設計文件包含 13 個 Correctness Properties，屬性測試使用 **eris/eris** 函式庫。

---

## Tasks

- [x] 1. Database Migrations
  - [x] 1.1 新增 `has_firmware` 欄位至 `ali_products`
    - 建立 migration：`php artisan make:migration add_has_firmware_to_ali_products`
    - 加入 `$table->boolean('has_firmware')->default(false)->after('category');`
    - 確認 rollback `down()` 方法正確移除欄位
    - _Requirements: 1.1, 1.5_

  - [x] 1.2 建立 `ali_product_audit_logs` 資料表
    - 建立 migration：`php artisan make:migration create_ali_product_audit_logs_table`
    - 欄位：`id`, `product_id` (FK→ali_products), `field_name`, `old_value` (nullable text), `new_value` (nullable text), `changed_by` (FK→users), `timestamps`
    - 加入外鍵約束
    - _Requirements: 8.4_

  - [x] 1.3 執行 migrations 並驗證資料表結構
    - 執行 `php artisan migrate`
    - 確認 `ali_products` 含 `has_firmware` 欄位
    - 確認 `ali_product_audit_logs` 資料表存在且結構正確
    - _Requirements: 1.1, 8.4_

- [x] 2. Eloquent Models
  - [x] 2.1 更新 `Product` Model（`app/Models/Product.php`）
    - 在 `$fillable` 加入 `has_firmware`
    - 在 `$casts` 加入 `'has_firmware' => 'boolean'`
    - 實作 `getTotalCostAttribute(): float`（回傳 `hardware_base_cost + software_license_fee`）
    - 實作 `getGrossProfitAttribute(): float`（回傳 `selling_price - total_cost`）
    - 實作 `isBundle(): bool`（`category === 'bundle'`）
    - 實作 `isFirmwareItem(): bool`（`category === 'item' && has_firmware`）
    - 確認 `bundleItems()` 和 `parentBundles()` BelongsToMany 關聯已存在或新增
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.3_

  - [ ]* 2.2 寫 Property Test：總成本計算正確性（Property 2）
    - **Property 2: total cost equals hardware_base_cost + software_license_fee**
    - **Validates: Requirements 1.2, 4.1, 8.2**
    - 使用 eris 生成隨機 `hardware_base_cost`（0~99999.99）和 `software_license_fee`（0~9999.99）
    - 斷言：`$product->total_cost === $hardware_base_cost + $software_license_fee`
    - 最少 100 次迭代

  - [ ]* 2.3 寫 Unit Test：毛利顯示與虧損警告（Property 6）
    - **Property 6: gross_profit equals selling_price - total_cost**
    - **Validates: Requirements 4.3, 4.4**
    - 測試 `gross_profit` 計算正確性
    - 測試 `selling_price < total_cost` 時的虧損判斷邏輯

  - [x] 2.4 建立 `ProductBundle` Model（`app/Models/ProductBundle.php`）
    - 若尚未存在，建立 Model
    - 設定 `$table = 'ali_product_bundles'`
    - 設定 `$fillable = ['bundle_id', 'item_id', 'quantity']`
    - _Requirements: 3.1, 5.1_

  - [x] 2.5 建立 `ProductAuditLog` Model（`app/Models/ProductAuditLog.php`）
    - 建立 Model
    - 設定 `$table = 'ali_product_audit_logs'`
    - 設定 `$fillable = ['product_id', 'field_name', 'old_value', 'new_value', 'changed_by']`
    - _Requirements: 8.4_

- [x] 3. Checkpoint — 確認 Models 與 Migrations 正確
  - 執行 `php artisan test --filter=ProductModelTest`（若已有測試）
  - 確認所有 migrations 無錯誤
  - 確認 `Product::total_cost` 和 `Product::gross_profit` 計算屬性可正常存取
  - 如有問題，請向使用者提問。

- [x] 4. ProductService
  - [x] 4.1 建立 `ProductService`（`app/Services/ProductService.php`）
    - 建立 Service class，注入依賴（若需要）
    - _Requirements: 2.1, 2.2, 3.1_

  - [x] 4.2 實作 `filterWritableFields(array $data, string $role, ?Product $product): array`
    - Developer 可寫全部欄位
    - Lao_Qiu 不可寫 `software_license_fee`（靜默移除，不拋例外）
    - Bundle 的 `hardware_base_cost` 永遠由 BOM 計算，移除手動輸入值
    - _Requirements: 2.1, 2.2, 2.4, 3.4_

  - [ ]* 4.3 寫 Unit Test：Lao_Qiu 無法修改授權費（Property 3）
    - **Property 3: Lao_Qiu role cannot modify software_license_fee**
    - **Validates: Requirements 2.1, 2.2, 2.4**
    - 使用 eris 生成隨機 `software_license_fee` 值
    - 斷言：Lao_Qiu 角色呼叫 `filterWritableFields` 後，`software_license_fee` 不在回傳陣列中
    - 最少 100 次迭代

  - [x] 4.4 實作 `createProduct(array $data, string $role): Product`
    - 呼叫 `filterWritableFields`
    - 若 `has_firmware === false`，強制 `software_license_fee = 0`
    - 建立並儲存 Product
    - 若 `software_license_fee > 0`，呼叫 `logLicenseFeeChange`
    - _Requirements: 1.3, 7.3, 8.1, 8.4_

  - [ ]* 4.5 寫 Unit Test：has_firmware=false 強制授權費為零（Property 1）
    - **Property 1: has_firmware=false forces software_license_fee=0**
    - **Validates: Requirements 1.3, 8.5**
    - 使用 eris 生成隨機 `software_license_fee` 值（0~9999.99）
    - 操作：建立產品，設定 `has_firmware=false`
    - 斷言：`$product->software_license_fee === 0.00`
    - 最少 100 次迭代

  - [x] 4.6 實作 `updateProduct(Product $product, array $data, string $role): Product`
    - 呼叫 `filterWritableFields`
    - 若 `has_firmware` 從 `true` 改為 `false`，強制 `software_license_fee = 0`
    - 若 `software_license_fee` 有變動，呼叫 `logLicenseFeeChange`
    - 若為 Item 且 `hardware_base_cost` 有變動，呼叫 `cascadeRecalculateBundles`
    - 儲存並回傳更新後的 Product
    - _Requirements: 1.3, 2.2, 3.5, 8.2, 8.3, 8.4, 8.5_

  - [x] 4.7 實作 `recalculateBundleCost(Product $bundle): void`
    - 查詢 `ali_product_bundles` JOIN `ali_products`
    - 計算 `SUM(p.hardware_base_cost * pb.quantity)`
    - 使用 `COALESCE` 處理 NULL（BOM 為空時結果為 0）
    - 更新 Bundle 的 `hardware_base_cost`
    - _Requirements: 3.1, 3.2_

  - [ ]* 4.8 寫 Property Test：BOM 硬體成本加總不變式（Property 4）
    - **Property 4: bundle hardware_base_cost equals sum of item costs times quantities**
    - **Validates: Requirements 3.1, 3.2, 3.4, 5.3**
    - 使用 eris 生成隨機 1~10 個 Item，每個有隨機 `hardware_base_cost` 和 `quantity`
    - 操作：建立 Bundle，設定 BOM，呼叫 `recalculateBundleCost`
    - 斷言：`$bundle->hardware_base_cost === sum(item.hardware_base_cost * quantity)`
    - 最少 100 次迭代

  - [x] 4.9 實作 `cascadeRecalculateBundles(Product $item): void`
    - 查詢所有包含該 Item 的 Bundle（透過 `parentBundles` 關聯）
    - 對每個 Bundle 呼叫 `recalculateBundleCost`
    - _Requirements: 3.5, 8.3_

  - [ ]* 4.10 寫 Unit Test：BOM 成本級聯更新（Property 5）
    - **Property 5: updating item cost recalculates all parent bundles**
    - **Validates: Requirements 3.5, 8.3**
    - 建立 Item，加入多個 Bundle
    - 更新 Item 的 `hardware_base_cost`，呼叫 `cascadeRecalculateBundles`
    - 斷言：所有包含該 Item 的 Bundle 都已重算

  - [x] 4.11 實作 `saveBom(Product $bundle, array $bomItems): void`
    - 驗證每個 `item_id` 對應的產品 `category` 必須為 `'item'`（不允許 Bundle 嵌套）
    - 驗證 `$bomItems` 不可為空陣列
    - 同步 `ali_product_bundles`（新增/移除/更新數量）
    - 儲存後呼叫 `recalculateBundleCost`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 4.12 寫 Unit Test：禁止 Bundle 嵌套（Property 7）
    - **Property 7: adding bundle as BOM component throws validation exception**
    - **Validates: Requirements 5.4**
    - 建立兩個 Bundle，嘗試將一個加入另一個的 BOM
    - 斷言：拋出 `ValidationException`

  - [x] 4.13 實作 `logLicenseFeeChange(Product $product, float $oldValue, float $newValue, int $userId): void`
    - 建立 `ProductAuditLog` 記錄
    - 欄位：`product_id`, `field_name='software_license_fee'`, `old_value`, `new_value`, `changed_by`
    - _Requirements: 8.4_

  - [ ]* 4.14 寫 Unit Test：授權費變更審計日誌（Property 13）
    - **Property 13: changing software_license_fee creates audit log entry**
    - **Validates: Requirements 8.4**
    - Developer 更新 `software_license_fee`
    - 斷言：`ali_product_audit_logs` 中有對應記錄，含正確的 `product_id`, `old_value`, `new_value`, `changed_by`

- [x] 5. Checkpoint — 確認 ProductService 邏輯正確
  - 執行 `php artisan test --filter=ProductService`
  - 確認所有 Unit Tests 通過
  - 如有問題，請向使用者提問。

- [x] 6. Form Requests
  - [x] 6.1 建立 `ProductStoreRequest`（`app/Http/Requests/ProductStoreRequest.php`）
    - 實作 `authorize()`：允許 Developer 和 Lao_Qiu 角色
    - 實作 `rules()`：
      - `sku_name`: required|string|max:255
      - `sku_code`: required|string|max:100|unique:ali_products,sku_code
      - `description`: nullable|string
      - `category`: required|in:bundle,item
      - `has_firmware`: boolean
      - `hardware_base_cost`: required|numeric|min:0
      - `selling_price`: required|numeric|min:0
      - `software_license_fee`: nullable|numeric|min:0
      - `is_essential`: boolean
      - `status`: required|in:active,inactive
      - `bom`: required_if:category,bundle|array|min:1
      - `bom.*.item_id`: required|exists:ali_products,id
      - `bom.*.quantity`: required|integer|min:1
    - _Requirements: 7.1, 7.2, 7.6, 5.5_

  - [x] 6.2 建立 `ProductUpdateRequest`（`app/Http/Requests/ProductUpdateRequest.php`）
    - 與 `ProductStoreRequest` 相同規則，但 `sku_code` unique 規則排除當前產品 ID
    - `sku_code`: `unique:ali_products,sku_code,{$this->product->id}`
    - _Requirements: 7.4, 7.6_

  - [ ]* 6.3 寫 Unit Test：必填欄位驗證完整性（Property 12）
    - **Property 12: missing required fields returns field-level validation errors**
    - **Validates: Requirements 7.2**
    - 測試各必填欄位缺失時的驗證錯誤訊息
    - 斷言：每個缺失欄位都有對應的錯誤訊息

  - [ ]* 6.4 寫 Unit Test：SKU 編號唯一性（Property 11）
    - **Property 11: duplicate sku_code is always rejected**
    - **Validates: Requirements 7.6**
    - 使用 eris 生成隨機 `sku_code` 字串
    - 建立第一個產品，再嘗試建立相同 `sku_code` 的第二個產品
    - 斷言：第二次建立拋出驗證錯誤
    - 最少 100 次迭代

- [x] 7. ProductController
  - [x] 7.1 建立或更新 `ProductController`（`app/Http/Controllers/ProductController.php`）
    - 注入 `ProductService`
    - _Requirements: 7.1, 7.3_

  - [x] 7.2 實作 `index(Request $request): View`
    - 支援篩選參數：`search`（sku_name/sku_code LIKE）、`category`、`has_firmware`、`status`
    - 分頁顯示（`paginate(20)`）
    - 傳遞篩選參數至 View 以保留篩選狀態
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [ ]* 7.3 寫 Feature Test：篩選結果符合條件（Property 8）
    - **Property 8: all returned products satisfy all applied filter conditions**
    - **Validates: Requirements 6.2, 6.3, 6.4, 6.5**
    - 使用 eris 生成隨機產品資料集（混合 category、has_firmware、status）
    - 套用隨機篩選條件，呼叫 `GET /products`
    - 斷言：所有結果都符合篩選條件，且所有符合條件的產品都在結果中
    - 最少 100 次迭代

  - [x] 7.4 實作 `create(): View`
    - 傳遞可用的 Item 產品清單（供 BOM 選擇）
    - 傳遞當前使用者角色至 View
    - _Requirements: 7.1_

  - [x] 7.5 實作 `store(ProductStoreRequest $request): RedirectResponse`
    - 取得當前使用者角色
    - 呼叫 `ProductService::createProduct($request->validated(), $role)`
    - 若 category=bundle，呼叫 `ProductService::saveBom($product, $request->bom)`
    - 成功後重導至產品列表，附帶 success flash message
    - _Requirements: 7.3, 5.1_

  - [ ]* 7.6 寫 Feature Test：產品建立資料持久化（Property 9）
    - **Property 9: valid product creation persists all fields correctly**
    - **Validates: Requirements 7.3**
    - 提交有效的產品建立表單
    - 斷言：資料庫中有對應記錄，欄位值與提交資料一致（考慮角色過濾）

  - [x] 7.7 實作 `edit(Product $product): View`
    - 傳遞產品資料、可用 Item 清單、當前 BOM
    - 傳遞當前使用者角色至 View
    - _Requirements: 7.4_

  - [x] 7.8 實作 `update(ProductUpdateRequest $request, Product $product): RedirectResponse`
    - 取得當前使用者角色
    - 呼叫 `ProductService::updateProduct($product, $request->validated(), $role)`
    - 若 category=bundle，呼叫 `ProductService::saveBom($product, $request->bom)`
    - 成功後重導，附帶 success flash message
    - _Requirements: 7.4, 3.5, 8.2_

  - [ ]* 7.9 寫 Feature Test：HTTP 層角色保護（Property 3 HTTP 層）
    - **Property 3: Lao_Qiu HTTP request cannot change software_license_fee**
    - **Validates: Requirements 2.1, 2.2, 2.4**
    - 以 Lao_Qiu 角色提交含 `software_license_fee` 的 PUT 請求
    - 斷言：資料庫中 `software_license_fee` 維持原值

  - [x] 7.10 實作 `toggleStatus(Product $product): RedirectResponse`
    - 切換 `status` 在 `active` / `inactive` 之間
    - 不刪除記錄（軟停用）
    - 成功後重導，附帶 flash message
    - _Requirements: 7.5_

  - [ ]* 7.11 寫 Feature Test：軟停用保留記錄（Property 10）
    - **Property 10: setting status inactive retains product record**
    - **Validates: Requirements 7.5**
    - 呼叫 `PATCH /products/{id}/status` 設為 inactive
    - 斷言：資料庫中仍可查到該產品，且所有欄位資料完整

  - [x] 7.12 在 `routes/web.php` 註冊路由
    - `Route::resource('products', ProductController::class)->except(['destroy'])`
    - `Route::patch('products/{product}/status', [ProductController::class, 'toggleStatus'])->name('products.toggleStatus')`
    - _Requirements: 7.1, 7.5_

- [x] 8. Checkpoint — 確認 Controller 與路由正確
  - 執行 `php artisan test --filter=ProductController`
  - 確認所有 Feature Tests 通過
  - 如有問題，請向使用者提問。

- [x] 9. Blade Views
  - [x] 9.1 建立產品列表頁（`resources/views/products/index.blade.php`）
    - 搜尋欄（sku_name / sku_code）
    - 篩選器：category（bundle/item）、has_firmware（含韌體/純硬體）、status（active/inactive）
    - 分頁表格欄位：SKU code、名稱、類型（bundle/item）、子類型（firmware/hardware）、售價、總成本、狀態、操作（編輯/停用）
    - 無結果時顯示 empty state 訊息
    - 保留篩選狀態（`request()->query()`）
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [x] 9.2 建立產品表單（`resources/views/products/form.blade.php`）
    - 基本欄位區塊：`sku_name`, `sku_code`, `description`, `category`, `is_essential`, `status`
    - `has_firmware` toggle：僅 `category=item` 時顯示（Alpine.js 或 JS 控制）
    - `software_license_fee`：Developer 可編輯，Lao_Qiu 顯示為 disabled input
    - `hardware_base_cost`：Item 可編輯，Bundle 顯示為 readonly（顯示自動計算值）
    - `selling_price` 欄位
    - 使用 `old()` helper 保留已輸入資料
    - 顯示欄位層級驗證錯誤訊息
    - _Requirements: 7.1, 7.2, 1.5, 2.3, 2.5, 3.3_

  - [x] 9.3 加入即時成本計算區塊（JavaScript）
    - 顯示成本明細：Hardware Cost + License Fee = Total Cost
    - 當 `hardware_base_cost` 或 `software_license_fee` 變動時，即時更新 Total Cost
    - 當 `selling_price` 變動時，即時更新 Gross Profit
    - 當 `selling_price < total_cost` 時，顯示虧損警告（紅色提示）
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 9.4 加入 BOM 管理區塊（僅 `category=bundle` 時顯示）
    - 搜尋並新增 Item 產品（排除 Bundle 類型）
    - 顯示每個 BOM 零件：名稱、`hardware_base_cost`、`software_license_fee`、數量輸入框、移除按鈕
    - 移除零件時即時更新 Bundle 的 `hardware_base_cost` 顯示
    - 以 hidden input 陣列傳遞 BOM 資料（`bom[0][item_id]`, `bom[0][quantity]`）
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 9.5 建立 create 和 edit 頁面（`create.blade.php`, `edit.blade.php`）
    - 兩者都 `@include` 或 `@extends` form.blade.php
    - create 頁面：空白表單，POST 至 `products.store`
    - edit 頁面：預填現有資料，PUT 至 `products.update`
    - _Requirements: 7.1, 7.4_

- [ ] 10. 安裝 eris/eris 並設定屬性測試環境
  - 在 Alliance 專案目錄執行：`composer require --dev giorgiosironi/eris`
  - 建立 `tests/Property/` 目錄
  - 建立 `tests/Property/ProductPropertyTest.php` 基礎結構
  - 確認 PHPUnit 可正確載入 Property 測試
  - _Requirements: 全部 Properties_

- [ ] 11. 屬性測試（Property-Based Tests）
  - [ ]* 11.1 寫 Property Test：has_firmware=false 強制授權費為零（Property 1）
    - **Property 1: for any product, has_firmware=false always results in software_license_fee=0**
    - **Validates: Requirements 1.3, 8.5**
    - 生成器：隨機 `software_license_fee`（0~9999.99）
    - 操作：建立/更新產品，設定 `has_firmware=false`
    - 斷言：`$product->software_license_fee === 0.00`
    - 最少 100 次迭代

  - [ ]* 11.2 寫 Property Test：總成本計算正確性（Property 2）
    - **Property 2: for any hardware_base_cost and software_license_fee, total_cost equals their sum**
    - **Validates: Requirements 1.2, 4.1, 8.2**
    - 生成器：隨機 `hardware_base_cost`（0~99999.99）、隨機 `software_license_fee`（0~9999.99）
    - 斷言：`$product->total_cost === $hardware_base_cost + $software_license_fee`
    - 最少 100 次迭代

  - [ ]* 11.3 寫 Property Test：BOM 硬體成本加總不變式（Property 4）
    - **Property 4: for any bundle with any items and quantities, bundle hardware_base_cost equals BOM sum**
    - **Validates: Requirements 3.1, 3.2, 3.4, 5.3**
    - 生成器：隨機 1~10 個 Item，每個有隨機 `hardware_base_cost` 和 `quantity`
    - 操作：建立 Bundle，設定 BOM，呼叫 `recalculateBundleCost`
    - 斷言：`$bundle->hardware_base_cost === sum(item.hardware_base_cost * quantity)`
    - 最少 100 次迭代

  - [ ]* 11.4 寫 Property Test：篩選結果符合條件（Property 8）
    - **Property 8: for any filter criteria, all returned products satisfy all applied filters**
    - **Validates: Requirements 6.2, 6.3, 6.4, 6.5**
    - 生成器：隨機產品資料集（混合 category、has_firmware、status）
    - 操作：套用隨機篩選條件，查詢產品列表
    - 斷言：所有結果都符合篩選條件，且所有符合條件的產品都在結果中
    - 最少 100 次迭代

  - [ ]* 11.5 寫 Property Test：SKU 編號唯一性（Property 11）
    - **Property 11: for any existing sku_code, creating another product with same sku_code is always rejected**
    - **Validates: Requirements 7.6**
    - 生成器：隨機 `sku_code` 字串
    - 操作：建立第一個產品，再嘗試建立相同 `sku_code` 的第二個產品
    - 斷言：第二次建立拋出 `ValidationException`
    - 最少 100 次迭代

- [ ] 12. Final Checkpoint — 確認所有測試通過
  - 執行 `php artisan test`
  - 確認所有 Unit Tests、Feature Tests、Property Tests 通過
  - 執行 `php artisan optimize:clear` 清除快取
  - 如有問題，請向使用者提問。

---

## Notes

- Tasks 標記 `*` 為選填，可跳過以加速 MVP 開發
- 每個 task 都引用對應的 Requirements 以確保可追溯性
- Checkpoint tasks 確保每個階段的增量驗證
- Property Tests 使用 **eris/eris** 函式庫，每個屬性最少 100 次迭代
- Unit Tests 驗證具體範例與邊界條件
- Feature Tests 驗證完整 HTTP 流程
- 部署前執行 `php artisan optimize:clear`
- 資料庫連線透過 SSH 隧道（127.0.0.1:3308）
