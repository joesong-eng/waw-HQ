# Design Document: Product Management

## Overview

本設計文件描述 Alliance 產品管理模組的完整技術實作方案。

系統核心業務：老邱（Lao_Qiu）銷售通訊卡、兌幣卡、兌幣機等硬體產品。每件含韌體的產品有一筆由開發者設定的固定授權費（`software_license_fee`），計入老邱的成本但不可被老邱修改。套裝產品（Bundle）的硬體成本由 BOM 自動累加，老邱只需設定售價。

**技術棧：** Laravel 11、Blade 模板、MySQL（SSH 隧道 127.0.0.1:3308）

---

## Architecture

### 整體架構

```
┌─────────────────────────────────────────────────────────┐
│                    Blade Views                          │
│  product/index.blade.php  │  product/form.blade.php     │
│  (列表+篩選)               │  (建立/編輯，含 BOM 區塊)    │
└──────────────┬────────────────────────┬─────────────────┘
               │ HTTP Request           │ Alpine.js / JS
               ▼                        ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│   ProductController     │   │  即時成本計算 (前端 JS)   │
│  index / create / store │   │  totalCost, grossProfit  │
│  edit / update / destroy│   │  lossWarning             │
└──────────┬──────────────┘   └─────────────────────────┘
           │
           ▼
┌─────────────────────────┐
│   ProductService        │
│  - 角色權限過濾          │
│  - BOM 成本計算          │
│  - 授權費保護            │
│  - 審計日誌              │
└──────────┬──────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────┐
│                  Eloquent Models                     │
│   Product (ali_products)                             │
│   ProductBundle (ali_product_bundles)                │
│   ProductAuditLog (ali_product_audit_logs)           │
└──────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────┐
│   MySQL (127.0.0.1:3308 via SSH Tunnel)              │
└──────────────────────────────────────────────────────┘
```

### 角色權限矩陣

| 欄位 / 操作 | Developer | Lao_Qiu | Sub_Agent |
|---|---|---|---|
| `software_license_fee` 讀取 | ✅ | ✅（唯讀） | ❌ |
| `software_license_fee` 寫入 | ✅ | ❌ | ❌ |
| Bundle `hardware_base_cost` 讀取 | ✅ | ✅（唯讀） | ❌ |
| Bundle `hardware_base_cost` 寫入 | ✅（自動計算） | ❌ | ❌ |
| `selling_price` 寫入 | ✅ | ✅ | ❌ |
| `has_firmware` 設定 | ✅ | ❌ | ❌ |
| 產品 CRUD | ✅ | ✅ | ❌ |

---

## Components and Interfaces

### 1. Database Migration

**新增 `has_firmware` 欄位：**

```php
// database/migrations/xxxx_add_has_firmware_to_ali_products.php
Schema::table('ali_products', function (Blueprint $table) {
    $table->boolean('has_firmware')->default(false)->after('category');
});
```

**新增審計日誌資料表：**

```php
// database/migrations/xxxx_create_ali_product_audit_logs_table.php
Schema::create('ali_product_audit_logs', function (Blueprint $table) {
    $table->id();
    $table->unsignedBigInteger('product_id');
    $table->string('field_name');
    $table->text('old_value')->nullable();
    $table->text('new_value')->nullable();
    $table->unsignedBigInteger('changed_by');
    $table->timestamps();
    $table->foreign('product_id')->references('id')->on('ali_products');
});
```

### 2. Eloquent Models

**Product Model (`app/Models/Product.php`)：**

```php
class Product extends Model
{
    protected $table = 'ali_products';

    protected $fillable = [
        'sku_name', 'sku_code', 'description', 'category',
        'has_firmware', 'selling_price', 'hardware_cost',
        'hardware_base_cost', 'software_license_fee',
        'stock_quantity', 'is_essential', 'status',
    ];

    protected $casts = [
        'has_firmware' => 'boolean',
        'is_essential' => 'boolean',
        'selling_price' => 'decimal:2',
        'hardware_base_cost' => 'decimal:2',
        'software_license_fee' => 'decimal:2',
    ];

    // 計算屬性
    public function getTotalCostAttribute(): float
    {
        return (float)$this->hardware_base_cost + (float)$this->software_license_fee;
    }

    public function getGrossProfitAttribute(): float
    {
        return (float)$this->selling_price - $this->total_cost;
    }

    public function isBundle(): bool
    {
        return $this->category === 'bundle';
    }

    public function isFirmwareItem(): bool
    {
        return $this->category === 'item' && $this->has_firmware;
    }

    // BOM 關聯
    public function bundleItems(): BelongsToMany
    {
        return $this->belongsToMany(
            Product::class,
            'ali_product_bundles',
            'bundle_id',
            'item_id'
        )->withPivot('quantity');
    }

    // 此 Item 被哪些 Bundle 包含
    public function parentBundles(): BelongsToMany
    {
        return $this->belongsToMany(
            Product::class,
            'ali_product_bundles',
            'item_id',
            'bundle_id'
        )->withPivot('quantity');
    }
}
```

**ProductBundle Model (`app/Models/ProductBundle.php`)：**

```php
class ProductBundle extends Model
{
    protected $table = 'ali_product_bundles';

    protected $fillable = ['bundle_id', 'item_id', 'quantity'];
}
```

### 3. ProductService

`app/Services/ProductService.php` 封裝所有業務邏輯：

```php
class ProductService
{
    /**
     * 根據角色過濾可寫入欄位
     * Developer 可寫全部；Lao_Qiu 不可寫 software_license_fee
     * Bundle 的 hardware_base_cost 永遠由 BOM 計算，不接受手動輸入
     */
    public function filterWritableFields(array $data, string $role, ?Product $product = null): array;

    /**
     * 建立產品
     * - 過濾欄位
     * - 若 has_firmware=false，強制 software_license_fee=0
     * - 記錄審計日誌
     */
    public function createProduct(array $data, string $role): Product;

    /**
     * 更新產品
     * - 過濾欄位
     * - 若 has_firmware 從 true 改為 false，強制 software_license_fee=0
     * - 若 software_license_fee 有變動，記錄審計日誌
     * - 若為 Item 且屬於某些 Bundle，觸發 Bundle 成本重算
     */
    public function updateProduct(Product $product, array $data, string $role): Product;

    /**
     * 計算並更新 Bundle 的 hardware_base_cost
     * = sum(item.hardware_base_cost * pivot.quantity) for all items in BOM
     */
    public function recalculateBundleCost(Product $bundle): void;

    /**
     * 當某個 Item 的 hardware_base_cost 更新後，
     * 重算所有包含該 Item 的 Bundle
     */
    public function cascadeRecalculateBundles(Product $item): void;

    /**
     * 儲存 BOM（新增/移除零件、調整數量）
     * - 驗證不可加入 Bundle 類型的零件
     * - 驗證 BOM 不可為空
     * - 儲存後觸發 recalculateBundleCost
     */
    public function saveBom(Product $bundle, array $bomItems): void;

    /**
     * 記錄 software_license_fee 變更的審計日誌
     */
    public function logLicenseFeeChange(Product $product, float $oldValue, float $newValue, int $userId): void;
}
```

### 4. ProductController

`app/Http/Controllers/ProductController.php`：

```php
class ProductController extends Controller
{
    // GET /products
    public function index(Request $request): View
    // 支援 search, category, has_firmware, status 篩選參數
    // 分頁顯示

    // GET /products/create
    public function create(): View

    // POST /products
    public function store(ProductStoreRequest $request): RedirectResponse

    // GET /products/{product}
    public function show(Product $product): View

    // GET /products/{product}/edit
    public function edit(Product $product): View

    // PUT /products/{product}
    public function update(ProductUpdateRequest $request, Product $product): RedirectResponse

    // PATCH /products/{product}/status
    public function toggleStatus(Product $product): RedirectResponse
    // 軟停用：只改 status，不刪除記錄
}
```

### 5. Form Requests

**ProductStoreRequest / ProductUpdateRequest：**

```php
public function rules(): array
{
    return [
        'sku_name'           => 'required|string|max:255',
        'sku_code'           => 'required|string|max:100|unique:ali_products,sku_code',
        'description'        => 'nullable|string',
        'category'           => 'required|in:bundle,item',
        'has_firmware'       => 'boolean',
        'hardware_base_cost' => 'required|numeric|min:0',
        'selling_price'      => 'required|numeric|min:0',
        'software_license_fee' => 'nullable|numeric|min:0',
        'is_essential'       => 'boolean',
        'status'             => 'required|in:active,inactive',
        // BOM（僅 bundle）
        'bom'                => 'required_if:category,bundle|array|min:1',
        'bom.*.item_id'      => 'required|exists:ali_products,id',
        'bom.*.quantity'     => 'required|integer|min:1',
    ];
}
```

### 6. Blade Views

**產品列表 (`resources/views/products/index.blade.php`)：**
- 搜尋欄（sku_name / sku_code）
- 篩選器：category、has_firmware、status
- 分頁表格：SKU code、名稱、類型、子類型、售價、總成本、狀態、操作

**產品表單 (`resources/views/products/form.blade.php`)：**
- 基本欄位區塊
- `has_firmware` toggle（僅 category=item 時顯示）
- `software_license_fee`：Developer 可編輯，Lao_Qiu 唯讀
- `hardware_base_cost`：Item 可編輯，Bundle 唯讀（顯示自動計算值）
- 即時成本計算區塊（JavaScript）
- BOM 管理區塊（僅 category=bundle 時顯示）

---

## Data Models

### ali_products（更新後）

| 欄位 | 類型 | 說明 |
|---|---|---|
| id | bigint PK | |
| sku_name | varchar(255) | 產品名稱 |
| sku_code | varchar(100) UNIQUE | SKU 編號 |
| description | text nullable | 描述 |
| category | enum('bundle','item') | 產品類型 |
| **has_firmware** | boolean default false | **新增：是否含韌體/APP** |
| selling_price | decimal(10,2) | 售價（老邱設定） |
| hardware_cost | decimal(10,2) | 硬體進貨成本（老邱設定） |
| hardware_base_cost | decimal(10,2) | 硬體基礎成本（Bundle 自動累加） |
| software_license_fee | decimal(10,2) default 0 | 授權費（Developer 設定） |
| stock_quantity | int default 0 | 庫存 |
| is_essential | boolean default false | 是否為必要品 |
| status | enum('active','inactive') | 狀態 |
| created_at | timestamp | |
| updated_at | timestamp | |

### ali_product_bundles（現有）

| 欄位 | 類型 | 說明 |
|---|---|---|
| id | bigint PK | |
| bundle_id | bigint FK → ali_products.id | Bundle 產品 |
| item_id | bigint FK → ali_products.id | 零件產品（只能是 item） |
| quantity | int default 1 | 數量 |
| created_at | timestamp | |
| updated_at | timestamp | |

**約束：** `item_id` 對應的產品 `category` 必須為 `'item'`（不允許 Bundle 嵌套）

### ali_product_audit_logs（新增）

| 欄位 | 類型 | 說明 |
|---|---|---|
| id | bigint PK | |
| product_id | bigint FK → ali_products.id | 被修改的產品 |
| field_name | varchar(100) | 被修改的欄位名稱 |
| old_value | text nullable | 修改前的值 |
| new_value | text nullable | 修改後的值 |
| changed_by | bigint FK → users.id | 操作者 |
| created_at | timestamp | |
| updated_at | timestamp | |

### 資料流：BOM 成本計算

```
BOM 儲存/更新
    │
    ▼
ProductService::saveBom()
    │
    ├── 驗證：item 不可為 bundle 類型
    ├── 驗證：BOM 不可為空
    ├── 寫入 ali_product_bundles
    │
    ▼
ProductService::recalculateBundleCost()
    │
    ├── SELECT SUM(p.hardware_base_cost * pb.quantity)
    │   FROM ali_product_bundles pb
    │   JOIN ali_products p ON p.id = pb.item_id
    │   WHERE pb.bundle_id = ?
    │
    └── UPDATE ali_products SET hardware_base_cost = ? WHERE id = ?
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: has_firmware=false 強制授權費為零

*For any* product where `has_firmware` is set to `false`, the system SHALL ensure `software_license_fee` equals `0`, regardless of any previously stored value or submitted input.

**Validates: Requirements 1.3, 8.5**

---

### Property 2: 總成本計算正確性

*For any* product with any `hardware_base_cost` value and any `software_license_fee` value, the computed `total_cost` SHALL equal `hardware_base_cost + software_license_fee`.

**Validates: Requirements 1.2, 4.1, 8.2**

---

### Property 3: Lao_Qiu 無法修改授權費

*For any* product and any HTTP request submitted by a user with the Lao_Qiu role, the `software_license_fee` stored in the database SHALL remain unchanged after the request, regardless of what value was submitted in the request body.

**Validates: Requirements 2.1, 2.2, 2.4**

---

### Property 4: BOM 硬體成本加總不變式

*For any* bundle product with any set of component items and quantities, the bundle's `hardware_base_cost` SHALL always equal the sum of (`item.hardware_base_cost × quantity`) for all items in the BOM, after any BOM save, item update, or item removal operation.

**Validates: Requirements 3.1, 3.2, 3.4, 5.3**

---

### Property 5: BOM 成本級聯更新

*For any* item product that is a component in one or more bundles, after updating that item's `hardware_base_cost`, every bundle containing that item SHALL have its `hardware_base_cost` recalculated to reflect the new item cost.

**Validates: Requirements 3.5, 8.3**

---

### Property 6: 毛利顯示與虧損警告

*For any* product with any `selling_price` and `total_cost`, the displayed `gross_profit` SHALL equal `selling_price - total_cost`, and a loss warning SHALL be visible if and only if `selling_price < total_cost`.

**Validates: Requirements 4.3, 4.4**

---

### Property 7: 禁止 Bundle 嵌套

*For any* bundle product, attempting to add another bundle (a product with `category = 'bundle'`) as a BOM component SHALL always be rejected with a validation error.

**Validates: Requirements 5.4**

---

### Property 8: 篩選結果符合條件

*For any* combination of filter criteria (search term, category, has_firmware, status) applied to any product dataset, every product in the returned result set SHALL satisfy all applied filter conditions, and no product that satisfies all conditions SHALL be excluded from the results.

**Validates: Requirements 6.2, 6.3, 6.4, 6.5**

---

### Property 9: 產品建立資料持久化

*For any* valid product data submitted through the creation form, after a successful save, querying the database by the returned product ID SHALL return a record with field values matching the submitted data (subject to role-based field filtering).

**Validates: Requirements 7.3**

---

### Property 10: 軟停用保留記錄

*For any* product, after setting its `status` to `inactive`, the product record SHALL still be retrievable from the database with all its original data intact.

**Validates: Requirements 7.5**

---

### Property 11: SKU 編號唯一性

*For any* existing `sku_code` in the system, attempting to create a new product with the same `sku_code` SHALL always be rejected with a validation error, regardless of other field values.

**Validates: Requirements 7.6**

---

### Property 12: 必填欄位驗證完整性

*For any* subset of required fields that are missing or empty in a product creation/update request, the system SHALL return validation errors specifically identifying each missing required field, and SHALL NOT persist any partial data.

**Validates: Requirements 7.2**

---

### Property 13: 授權費變更審計日誌

*For any* change to a product's `software_license_fee` by a Developer, the system SHALL create an audit log entry containing the product ID, the previous value, the new value, the Developer's user ID, and a timestamp.

**Validates: Requirements 8.4**

---

## Error Handling

### 角色權限錯誤

- **情境：** Lao_Qiu 嘗試透過直接 HTTP 請求修改 `software_license_fee`
- **處理：** `ProductService::filterWritableFields()` 在服務層靜默移除該欄位；不拋出例外，但欄位值不變
- **回應：** 正常儲存成功，但 `software_license_fee` 維持原值

### 表單驗證錯誤

- **情境：** 必填欄位缺失、`sku_code` 重複、Bundle BOM 為空
- **處理：** Laravel Form Request 驗證，失敗時自動重導回表單
- **回應：** 顯示欄位層級錯誤訊息，保留已輸入的其他資料（`old()` helper）

### BOM 嵌套錯誤

- **情境：** 嘗試將 Bundle 加入另一個 Bundle 的 BOM
- **處理：** `ProductService::saveBom()` 驗證每個 `item_id` 的 `category` 必須為 `'item'`
- **回應：** 拋出 `ValidationException`，前端顯示錯誤訊息

### 資料庫連線錯誤

- **情境：** SSH 隧道斷線（127.0.0.1:3308 不可用）
- **處理：** Laravel 預設的 `QueryException` 處理
- **回應：** 顯示通用錯誤頁面，記錄至 Laravel log

### BOM 成本計算失敗

- **情境：** BOM 中的 Item 被刪除或狀態異常
- **處理：** `recalculateBundleCost()` 使用 `COALESCE` 處理 NULL，確保計算不中斷
- **回應：** 計算結果為現有有效 Item 的加總

---

## Testing Strategy

### 單元測試（PHPUnit）

針對 `ProductService` 的純邏輯：

```php
// tests/Unit/ProductServiceTest.php

// Property 1: has_firmware=false 強制授權費為零
test('setting has_firmware to false forces software_license_fee to zero')

// Property 2: 總成本計算
test('total cost equals hardware_base_cost plus software_license_fee')

// Property 3: Lao_Qiu 無法修改授權費
test('lao_qiu role cannot modify software_license_fee')

// Property 4: BOM 加總不變式
test('bundle hardware_base_cost equals sum of item costs times quantities')

// Property 5: 級聯更新
test('updating item cost recalculates all parent bundles')

// Property 7: 禁止 Bundle 嵌套
test('adding bundle as bom component throws validation exception')

// Property 11: SKU 唯一性
test('duplicate sku_code is rejected')

// Property 13: 審計日誌
test('changing software_license_fee creates audit log entry')
```

### 功能測試（PHPUnit Feature Tests）

針對 HTTP 層的完整流程：

```php
// tests/Feature/ProductControllerTest.php

// Property 3: HTTP 層角色保護
test('lao_qiu http request cannot change software_license_fee')

// Property 8: 篩選功能
test('product list filter by category returns only matching products')
test('product list filter by has_firmware returns only matching products')
test('product list search by sku_name returns only matching products')

// Property 9: 建立持久化
test('valid product creation persists all fields correctly')

// Property 10: 軟停用
test('setting status inactive retains product record')

// Property 12: 驗證完整性
test('missing required fields returns field level validation errors')
```

### 屬性測試（Property-Based Testing）

使用 **[eris/eris](https://github.com/giorgiosironi/eris)**（PHP 的 QuickCheck 風格 PBT 函式庫）。

每個屬性測試最少執行 **100 次迭代**。

```php
// tests/Property/ProductPropertyTest.php

/**
 * Feature: product-management, Property 1: has_firmware=false forces software_license_fee=0
 */
test('for any product, has_firmware=false always results in software_license_fee=0')
// 生成器：隨機 software_license_fee 值（0 到 9999.99）
// 操作：建立/更新產品，設定 has_firmware=false
// 斷言：software_license_fee === 0.00

/**
 * Feature: product-management, Property 2: total cost calculation correctness
 */
test('for any hardware_base_cost and software_license_fee, total_cost equals their sum')
// 生成器：隨機 hardware_base_cost（0 到 99999.99），隨機 software_license_fee（0 到 9999.99）
// 斷言：product->total_cost === hardware_base_cost + software_license_fee

/**
 * Feature: product-management, Property 4: BOM sum invariant
 */
test('for any bundle with any items and quantities, bundle hardware_base_cost equals BOM sum')
// 生成器：隨機 1-10 個 Item，每個有隨機 hardware_base_cost 和 quantity
// 操作：建立 Bundle，設定 BOM
// 斷言：bundle->hardware_base_cost === sum(item.hardware_base_cost * quantity)

/**
 * Feature: product-management, Property 8: filter results match criteria
 */
test('for any filter criteria, all returned products satisfy all applied filters')
// 生成器：隨機產品資料集（混合 category、has_firmware、status）
// 操作：套用隨機篩選條件
// 斷言：所有結果都符合篩選條件，且所有符合條件的產品都在結果中

/**
 * Feature: product-management, Property 11: SKU code uniqueness
 */
test('for any existing sku_code, creating another product with same sku_code is always rejected')
// 生成器：隨機 sku_code 字串
// 操作：建立第一個產品，再嘗試建立相同 sku_code 的第二個產品
// 斷言：第二次建立拋出 ValidationException
```

### 測試執行

```bash
# 執行所有測試
php artisan test

# 只執行屬性測試
php artisan test --filter=PropertyTest

# 只執行功能測試
php artisan test --filter=ProductControllerTest
```
