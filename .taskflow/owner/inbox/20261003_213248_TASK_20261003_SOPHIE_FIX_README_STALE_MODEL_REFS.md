# 任務工單：修正 Owner README 過時 Model 引用（Machine / MachineExtensions）

- **工單編號**：TASK_20261003_SOPHIE_FIX_README_STALE_MODEL_REFS
- **派發時間**：2026-10-03
- **負責人**：Sophie (Owner)
- **優先級**：P3 (Low)
- **關聯模組**：Owner (iot.tg25.win / yd174)
- **來源**：HQ 全域盤點（Sophie 第三輪稽核遺留項）

---

## 一、背景

`PROJECT/Owner/README.md` 仍描述已於 Device SSOT 重構中刪除的 `Machine.php` 與 `MachineExtensions.php`，屬文件誤導。實際 `app/Models/` 已無此二檔。

---

## 二、問題位置（已確認）

| 行號 | 現況 | 問題 |
|:--|:---|:---|
| 188-192 | `### Machine.php` 設備的業務邏輯擴展（machine_code / 營運狀態 / 交易統計） | Model 已刪除 |
| 200-203 | `### MachineExtensions.php` 設備擴展功能（客製化參數 / 特殊功能開關） | Model 已刪除 |
| 238-240 | 待補測試清單 `[ ] Machine.php 模型測試` | Model 已刪除 |

**現況事實**：
- `app/Models/` 實際存在：`Device.php`、`OwnerSubscription.php`、`DeviceSnapshot.php` 等 31 個 Model，**無 Machine.php / MachineExtensions.php**。
- `Device.php` 已是設備 SSOT，已涵蓋 chip_id / device_type / status / venue_id / parameters。

---

## 三、修正要求

1. 移除或改寫第 188-192、200-203 兩段過時 Model 描述。
   - 若「機台編號、營運狀態、交易統計」等業務概念仍存在，請改掛到 `Device.php` 或正確的現行 Model 下。
   - 若已完全廢除，直接刪除該段。
2. 修正第 238-240 待補測試清單，移除 `Machine.php` 項；若 `Device.php` 測試尚缺，改列 `Device.php`。
3. 順帶檢查 README 全文是否還有其他 `Machine`（單數舊模型）殘留，一併修正。

---

## 四、驗收指標

| # | 驗收項 | 方式 | 期望 |
|:--|:---|:---|:---|
| 1 | 舊 Model 引用歸零 | `grep -n 'MachineExtensions\|Machine\.php' README.md` | 0 hits |
| 2 | 文件與現行 Model 一致 | 逐項核對所述 Model 皆存在於 `app/Models/` | 通過 |
| 3 | 提交 | Commit SHA + Push origin/main | 完成 |

---

## 五、回報要求

完工後寫入 `.taskflow/owner/outbox/`，附 Commit SHA 與 `grep` 驗收輸出。

---

## 六、注意

- **僅修改 README.md 文件，不得改動任何程式碼。**
- 不確定某業務概念對應哪個現行 Model 時，先回報 HQ 確認，勿臆測。
