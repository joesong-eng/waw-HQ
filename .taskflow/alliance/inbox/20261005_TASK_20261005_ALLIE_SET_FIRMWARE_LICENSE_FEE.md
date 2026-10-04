# 任務：TASK_20261005_ALLIE_SET_FIRMWARE_LICENSE_FEE

**派發時間**：2026-10-05
**優先級**：high
**負責人**：Allie (Alliance)
**性質**：資料設定（Joe 裁定）
**關聯**：`TASK_20261005_ALLIE_FIX_ORDER_STATE_MACHINE_GAPS` 之 G6

---

## 背景

G6 回報確認：正式韌體產品 `software_license_fee = 0.00`，導致出貨時 royalties 不建帳。
Joe 已裁定設定值。

## Joe 裁定值

| 產品 | sku_code | 新 `software_license_fee` |
|------|----------|--------------------------|
| 橋接卡（兌幣機） | `BRIDGE-CARD-001` | **4500** |
| 通訊卡（遊戲機採集） | `COMM-CARD-001` | **4000** |

- **整數，不要小數點**（Joe 明確要求）。
- 其餘產品維持原值。

---

## 重要：欄位型別與顯示

- DB 欄位為 `decimal(10,2)`（`2026_06_17_174850_create_ali_base_tables.php:35`），
  存入 `4500` 會以 `4500.00` 形式儲存，**這是 decimal 型別的正常行為**。
- 表單已用 `(int) round(...)` 處理（`products/form.blade.php:181`），顯示為整數。
- 因此請**確認前端顯示為整數（4500 / 4000）**；若前端出現 `.00`，請修正顯示層（`form.blade.php` 或列表頁）而非改 DB 型別。

---

## 任務步驟

1. **先確認** `BRIDGE-CARD-001` / `COMM-CARD-001` 目前值與 id（供對照）。
2. **更新** 兩筆產品的 `software_license_fee`（正式環境 DB）。
3. **驗證** 前端產品頁 / 列表顯示為整數無小數點。
4. **驗證** 出貨流程：以測試單出貨含此兩產品的訂單，確認 `ali_firmware_royalties` 正確建帳（非 0）。
5. 若 seeder（`DefaultProductSeeder.php`）亦需同步（供未來重建），一併更新並 commit。

---

## 驗收指標（附實際佐證）

1. 更新前後 SELECT 結果（`sku_code, software_license_fee`）
2. 前端顯示截圖或 HTML（顯示 `4500` / `4000`，無小數點）
3. 測試出貨後 `ali_firmware_royalties` 的 SELECT 結果（金額正確、非 0）
4. 測試資料清乾淨
5. commit + push（若動到 seeder/顯示層，附 hash）

---

## 禁止

- 改 DB 欄位型別（decimal 是對的）
- 動 production 正式客戶單
- 本機 DB 操作（走 `waw_ops.sh remote alliance` 或標準 deploy）

## 完成定義

兩產品 license_fee 設定完成、前端顯示整數、出貨 royalties 正確建帳，5 項驗收有輸出，回報寫入 `.taskflow/alliance/outbox/`。
