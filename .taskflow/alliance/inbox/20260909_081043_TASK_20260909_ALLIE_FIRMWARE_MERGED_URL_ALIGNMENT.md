# 任務：TASK_20260909_ALLIE_FIRMWARE_MERGED_URL_ALIGNMENT

**派發時間**：2026-09-09 08:15  
**優先級**：HIGH  
**負責人**：Allie (Alliance Lead)  
**協同對象**：Coli (IOTwawS3 Lead), Ina (Infra Lead)

---

## 📋 任務背景與核心目標

經硬體與韌體架構審計，Alliance 網頁燒錄站（`resources/views/devices/burning.blade.php:852`）採用 WebSerial API，固定將韌體寫入晶片 Flash 起始位址 `address: 0x0`。

ESP32-S3 晶片記憶體架構：
- `0x0`：Bootloader (開機引導程式)
- `0x8000`：Partition Table (分區表)
- `0x10000`：App 韌體

目前 `Alliance/app/Http/Controllers/DeviceController.php` 的 `firmwareProxy` 僅讀取 `$manifest['stable']['url']`（此為純 App 韌體，供已上線設備 OTA 升級使用）。若將純 App 韌體直接寫入全新空白晶片的 `0x0`，會因為缺少 Bootloader 與分區表導致**新卡直接變磚無法開機**。

Coli 已於 `api/version.json` 提供雙軌分流標準：
- `url`：純 App 韌體（OTA 專用）
- `merged_url`：包含 Bootloader@0x0 + Partitions@0x8000 + App@0x10000 之完整開機二進位包（出廠物理燒錄專用）

---

## 🔍 任務執行要點

### 1. 修改 DeviceController::firmwareProxy 讀取邏輯
修改 `PROJECT/Alliance/app/Http/Controllers/DeviceController.php`：
優先讀取 `merged_url`，若無則降級讀取 `url`：
```php
$firmwareUrl = $manifest['stable']['merged_url'] ?? $manifest['stable']['url'] ?? null;
```
確保 Alliance 燒錄站代理下載時，永遠取得可直接於 `0x0` 燒錄開機之完整 Merged 包。

### 2. 部署至 Alliance 正式機
- 本地測試通過後，透過標準流程部署至 Alliance 伺服器（`ali.tg25.win`）。
- 驗證 `/api/firmware-proxy?project=IOTwawS3` 下載之韌體大小為 Merged 包大小（約 1MB+，非純 App 的小容量）。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260909_ALLIE_FIRMWARE_MERGED_URL_ALIGNMENT

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：Allie (Alliance Lead)

## 1. 程式碼修改與 Commit
- 修改檔案與邏輯說明
- Git Commit ID

## 2. 測試與部署驗證
- firmware-proxy API 測試結果（下載檔名、大小與 HTTP 狀態碼）
- ali.tg25.win 線上驗證

## 結論
✅ 燒錄代理已對齊 merged_url 並完成驗證 / ❌ 遇到問題
```

---
**派發者**：HQ  
**派發時間**：2026-09-09 08:15

