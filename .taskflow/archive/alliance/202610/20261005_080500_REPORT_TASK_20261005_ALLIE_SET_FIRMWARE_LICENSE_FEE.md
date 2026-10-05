# 回報：TASK_20261005_ALLIE_SET_FIRMWARE_LICENSE_FEE

**執行者**：Allie
**完成時間**：2026-10-05 08:05 (Asia/Taipei)
**任務 ID**：TASK_20261005_ALLIE_SET_FIRMWARE_LICENSE_FEE
**Commit**：`af09fca`

---

## 1. 更新前後 SELECT

### 更新前
| id | sku_name | sku_code | software_license_fee |
|----|----------|----------|---------------------|
| 2 | 橋接卡（兌幣機） | BRIDGE-COIN | **0.00** |
| 4 | 通訊卡（遊戲機採集） | COMM-S3 | **0.00** |

> 注：DB 中 sku_code 為 `BRIDGE-COIN` / `COMM-S3`（非工單寫的 `BRIDGE-CARD-001` / `COMM-CARD-001`，Seeder 中為後者）

### 更新後
| id | sku_name | sku_code | software_license_fee |
|----|----------|----------|---------------------|
| 2 | 橋接卡（兌幣機） | BRIDGE-COIN | **4500.00** |
| 4 | 通訊卡（遊戲機採集） | COMM-S3 | **4000.00** |

## 2. 前端顯示

- `form.blade.php:181`: `(int) round()` → 顯示 4500 / 4000（整數，無小數點） ✅
- `show.blade.php:492,499`: `number_format(..., 0)` → 顯示整數 ✅

## 3. 出貨 Royalties 驗證

測試單 `FEE-TEST-20261005` (id=19)，含橋接卡x1 + 通訊卡x1：

```
ROYALTIES count=2
  chip=FEETEST01 product=橋接卡（兌幣機） fee=4500.00 month=2026-10
  chip=FEETEST02 product=通訊卡（遊戲機採集） fee=4000.00 month=2026-10
```

✅ royalties 正確建帳，金額非 0。

## 4. 測試資料清理

```
CLEANUP: remain=0
```

## 5. Seeder 同步

`database/seeders/DefaultProductSeeder.php` 已更新：
- COMM-CARD-001: `software_license_fee => 4000`
- BRIDGE-CARD-001: `software_license_fee => 4500`

## 結論

✅ 完成。兩產品 license_fee 設定、前端整數顯示、出貨 royalties 正確建帳、Seeder 同步。

