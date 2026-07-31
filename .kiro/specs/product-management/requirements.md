# Requirements Document

## Introduction

本功能完善 Alliance 專案（`ali.tg25.win`，Laravel 11）的產品管理模組。

系統服務三個角色：**開發者**（系統管理員，即韌體/APP 作者）、**老邱**（硬體盟友，主代理商）、**子代理**（如小江，業務通路）。

核心業務邏輯：老邱銷售通訊卡、兌幣卡、兌幣機等硬體產品。每件含韌體或 APP 的產品，都有一筆由開發者設定的**固定隱性授權費**（`software_license_fee`），計入老邱的成本，但不單獨對外銷售。老邱只能修改硬體進貨成本與售價，無法修改授權費。

套裝產品（bundle，如兌幣機）由多個零件（item）組成，其硬體成本應自動累加所有零件的 `hardware_base_cost`，老邱只需設定最終售價。

---

## Glossary

- **System**：Alliance 產品管理系統（Laravel 後端）
- **Developer**：系統管理員，設定 `software_license_fee` 的開發者角色
- **Lao_Qiu**：主代理商（老邱），管理產品、訂單、子代理的一般用戶角色
- **Sub_Agent**：子代理（如小江），業務通路角色，只能查看自己相關的訂單與佣金
- **Product**：`ali_products` 資料表中的一筆產品記錄
- **Bundle**：套裝產品（`category = 'bundle'`），由多個 Item 組成，如兌幣機
- **Item**：單品（`category = 'item'`），可獨立銷售，也可作為 Bundle 的零件
- **Firmware_Item**：軟硬結合的 Item（`has_firmware = true`），含固定 `software_license_fee`，如通訊卡、兌幣卡、平板
- **Hardware_Item**：純硬體 Item（`has_firmware = false`），`software_license_fee = 0`，如機殼、RS232 線
- **BOM**：物料清單（Bill of Materials），Bundle 與其組成 Item 的關聯，存於 `ali_product_bundles`
- **Total_Cost**：總成本 = `hardware_base_cost` + `software_license_fee`
- **Selling_Price**：老邱設定的最終售價（`selling_price`）
- **Gross_Profit**：毛利 = `selling_price` - `Total_Cost`
- **software_license_fee**：開發者設定的固定韌體/APP 授權費，老邱不可修改

---

## Requirements

### Requirement 1：Item 子類型區分（軟硬結合 vs 純硬體）

**User Story：** As a Developer, I want to distinguish firmware items from pure hardware items, so that the system can correctly apply software license fees and support accurate cost accounting.

#### Acceptance Criteria

1. THE System SHALL support a boolean attribute `has_firmware` on each Item Product to indicate whether it contains firmware or an embedded APP.
2. WHEN `has_firmware` is `true`, THE System SHALL treat the Product as a Firmware_Item and apply its `software_license_fee` to cost calculations.
3. WHEN `has_firmware` is `false`, THE System SHALL treat the Product as a Hardware_Item and set its `software_license_fee` to `0`.
4. THE System SHALL display the item subtype (Firmware_Item or Hardware_Item) in the product list and detail views.
5. WHEN creating or editing a Product with `category = 'item'`, THE System SHALL present a toggle or selector for `has_firmware`.

---

### Requirement 2：韌體授權費保護（角色權限控制）

**User Story：** As a Developer, I want to lock the `software_license_fee` field so that Lao_Qiu cannot modify it, so that the developer's licensing revenue is protected.

#### Acceptance Criteria

1. THE System SHALL allow only the Developer role to create or update the `software_license_fee` field on any Product.
2. WHEN a user with the Lao_Qiu role submits a product create or update request, THE System SHALL ignore any submitted value for `software_license_fee` and retain the existing value.
3. WHEN a user with the Lao_Qiu role views the product create or edit form, THE System SHALL render the `software_license_fee` field as read-only (disabled input).
4. IF a Lao_Qiu role user attempts to modify `software_license_fee` via a direct HTTP request, THEN THE System SHALL reject the modification and return an authorization error response.
5. THE System SHALL display the `software_license_fee` value to Lao_Qiu as informational context (visible but not editable).

---

### Requirement 3：Bundle 硬體成本自動累加

**User Story：** As a Developer, I want the bundle's hardware cost to be automatically summed from its component items, so that Lao_Qiu does not need to manually enter it and risk errors.

#### Acceptance Criteria

1. WHEN a Bundle Product's BOM is saved or updated, THE System SHALL automatically calculate the Bundle's `hardware_base_cost` as the sum of `hardware_base_cost` of all associated Item Products in the BOM.
2. THE System SHALL store the calculated `hardware_base_cost` on the Bundle Product record.
3. WHEN a user with the Lao_Qiu role views the Bundle create or edit form, THE System SHALL render the `hardware_base_cost` field as read-only and display the auto-calculated value.
4. IF a Lao_Qiu role user attempts to submit a manual value for a Bundle's `hardware_base_cost`, THEN THE System SHALL ignore the submitted value and use the auto-calculated sum instead.
5. WHEN any component Item's `hardware_base_cost` is updated, THE System SHALL recalculate and update the `hardware_base_cost` of all Bundles that include that Item.

---

### Requirement 4：UI 總成本即時提示

**User Story：** As Lao_Qiu, I want to see the total cost displayed next to the selling price field in real time, so that I can set a price that covers all costs and avoids selling at a loss.

#### Acceptance Criteria

1. WHEN Lao_Qiu views the product create or edit form for any Product, THE System SHALL display a read-only `Total_Cost` indicator showing `hardware_base_cost + software_license_fee`.
2. WHEN the `hardware_base_cost` field value changes on a non-Bundle product form, THE System SHALL update the displayed `Total_Cost` without requiring a page reload.
3. WHEN Lao_Qiu enters a `selling_price` value, THE System SHALL display a real-time `Gross_Profit` indicator showing `selling_price - Total_Cost`.
4. WHEN `selling_price` is less than `Total_Cost`, THE System SHALL display a visual warning to indicate the product would be sold at a loss.
5. THE System SHALL display the cost breakdown as: Hardware Cost + License Fee = Total Cost, so that Lao_Qiu understands the composition of costs.

---

### Requirement 5：Bundle BOM 管理（零件關聯 CRUD）

**User Story：** As Lao_Qiu, I want to add, remove, and adjust quantities of component items in a bundle's BOM, so that I can accurately define what a bundle product contains.

#### Acceptance Criteria

1. WHEN creating or editing a Bundle Product, THE System SHALL present a BOM section where Lao_Qiu can search and add Item Products as components.
2. THE System SHALL allow Lao_Qiu to set a quantity for each component Item in the BOM.
3. WHEN Lao_Qiu removes a component Item from the BOM, THE System SHALL recalculate the Bundle's `hardware_base_cost` immediately.
4. THE System SHALL prevent adding a Bundle as a component of another Bundle (no nested bundles).
5. WHEN saving a Bundle with an empty BOM, THE System SHALL display a validation error requiring at least one component Item.
6. THE System SHALL display each BOM component with its name, `hardware_base_cost`, `software_license_fee`, and quantity.

---

### Requirement 6：產品列表與篩選

**User Story：** As Lao_Qiu, I want to browse, search, and filter the product list, so that I can quickly find and manage specific products.

#### Acceptance Criteria

1. THE System SHALL display all Products in a paginated list showing: SKU code, name, category (bundle/item), item subtype (firmware/hardware), selling price, total cost, and status.
2. WHEN Lao_Qiu enters a search term, THE System SHALL filter the product list to show only Products whose `sku_name` or `sku_code` contains the search term.
3. THE System SHALL allow filtering the product list by `category` (bundle or item).
4. THE System SHALL allow filtering the product list by `has_firmware` (firmware item or hardware item).
5. THE System SHALL allow filtering the product list by `status` (active or inactive).
6. WHEN no products match the filter criteria, THE System SHALL display an empty state message.

---

### Requirement 7：產品 CRUD 基本操作

**User Story：** As Lao_Qiu, I want to create, view, edit, and deactivate products, so that I can maintain an accurate product catalog.

#### Acceptance Criteria

1. THE System SHALL provide a product creation form with fields: `sku_name`, `sku_code`, `description`, `category`, `has_firmware` (for items), `hardware_base_cost`, `selling_price`, `is_essential`, and `status`.
2. WHEN Lao_Qiu submits a product creation form with missing required fields, THE System SHALL display field-level validation error messages without losing other entered data.
3. WHEN Lao_Qiu saves a valid product, THE System SHALL persist the record and redirect to the product detail or list page with a success message.
4. THE System SHALL allow Lao_Qiu to edit any product field that is not restricted by role permissions.
5. WHEN Lao_Qiu sets a product's `status` to inactive, THE System SHALL retain the product record and all historical associations rather than deleting it.
6. IF a `sku_code` already exists in the system, THEN THE System SHALL reject the duplicate and display a validation error.

---

### Requirement 8：開發者設定韌體費（管理員操作）

**User Story：** As a Developer, I want to set and update the `software_license_fee` for firmware items, so that the licensing cost is accurately reflected in all cost calculations.

#### Acceptance Criteria

1. WHEN a Developer creates a Firmware_Item, THE System SHALL allow the Developer to enter a `software_license_fee` value greater than or equal to zero.
2. WHEN a Developer updates the `software_license_fee` of a Firmware_Item, THE System SHALL immediately reflect the new value in all `Total_Cost` calculations for that Product.
3. WHEN a Developer updates the `software_license_fee` of a Firmware_Item that is a component in one or more Bundles, THE System SHALL recalculate the `software_license_fee` contribution for those Bundles.
4. THE System SHALL log the previous and new `software_license_fee` value whenever a Developer changes it, for audit purposes.
5. WHEN a Developer sets `has_firmware` to `false` on an existing Firmware_Item, THE System SHALL automatically set `software_license_fee` to `0`.

