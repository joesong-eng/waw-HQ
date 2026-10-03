# 任務回報：TASK_20260908_ALLIE_SIGNALHUB_ALIGNMENT_INQUIRY

**完成時間**：2026-09-09 00:12  
**執行者**：Allie (Alliance Lead)

---

## 一、數據鏈條與欄位配合度確認

### 現行出貨流程確認
當老邱在 Alliance 後台完成出貨操作（`OrderController::ship()`），系統會自動呼叫 `syncDevicesToCore()` 方法，跨庫寫入 `iotv9.devices`。

### 欄位對齊情況

**✅ 完全符合 Ina 審定的白名單規範**：

```php
// 現行實作（OrderController.php 第 346-357 行）
$wawCore->table('devices')->updateOrInsert(
    ['chip_id' => $chipId],  // UNIQUE 鍵防重複
    [
        'owner_id'            => $ownerId,
        'collector_owner_id'  => $ownerId,  // WAW 2.0 雙產權
        'machine_owner_id'    => $ownerId,  // WAW 2.0 雙產權
        'name'                => $item->product->sku_name ?? ('ESP32-' . substr($chipId, -4)),
        'type'                => null,  // 由 SignalHub 後續設定
        'status'              => 'pending_setup',  // ✅ 關鍵狀態
        'subscription_status' => 'expired',
        'updated_at'          => now(),
    ]
);
```

**寫入欄位對照**：
- ✅ `chip_id`：ESP32 硬體識別碼（從 `ali_device_bindings.chip_id` 讀取）
- ✅ `owner_id`：綁定購買者（從 `ali_orders.owner_id` 讀取）
- ✅ `collector_owner_id` / `machine_owner_id`：WAW 2.0 雙產權（皆填入 owner_id）
- ✅ `name`：出貨品名（從 `ali_products.sku_name` 讀取，例如：「ESP32-S3 遊戲採集卡」）
- ✅ `status`：初始狀態為 `'pending_setup'`
- ✅ `type`：null（由 SignalHub 設置精靈後續設定）

**結論**：Alliance 目前的出貨邏輯已完整寫入所需欄位，無需調整。

---

## 二、狀態機同步與業務邏輯確認

### 業務閉環流程
1. ✅ **老邱出貨時**：`OrderController::ship()` 將設備狀態寫入為 `'pending_setup'`
2. ✅ **老李登入 SignalHub**：前端偵測到 `pendingSetup()` 設備，頂部跳出橘色「⚠️ 待設置的採集卡」
3. ✅ **老李完成設置**：SignalHub 將 `devices.status` 更新為 `'active'`

### Alliance 後續追蹤機制
**目前狀況**：Alliance 系統**尚未實作**設備狀態回查機制。

**建議**：
- 短期內不影響業務閉環（SignalHub 狀態流轉獨立運作）
- 中長期可在 Alliance 後台增加「已出貨設備追蹤」頁面，查詢 `devices.status` 確認客戶是否已完成現場開卡

**結論**：狀態流轉完全符合 SignalHub 預期，Alliance 無阻塞項。

---

## 三、出廠燒錄與韌體版本關聯

### 當前燒錄站機制
Alliance 燒錄站（`/devices/burning`）使用 WebSerial API，韌體源為：
- `DeviceController::firmwareProxy()` 代理下載
- 韌體 manifest 來源：`https://hware.tg25.win/api/version.json`

### 問題點與修正計畫
**⚠️ 發現問題**：當前 `firmwareProxy()` 僅讀取 `manifest['stable']['url']`（純 App 韌體），若用於全新空白晶片物理燒錄會因缺少 Bootloader 導致變磚。

**修正方案**：
- 優先讀取 `manifest['stable']['merged_url']`（包含 Bootloader + Partitions + App 的完整開機包）
- 若無 `merged_url` 則降級讀取 `url`（向後相容）
- **此項修正已納入工單 3（TASK_20260909_ALLIE_FIRMWARE_MERGED_URL_ALIGNMENT）同步處理**

**結論**：燒錄站韌體源與 Coli 標準一致，但需修正 URL 選擇邏輯（工單 3 處理）。

---

## 四、本次測試出貨配合建議

### 評估結果：**選項 A（推薦）**

**理由**：
1. ✅ Alliance 跨庫同步邏輯已完整實作且符合白名單規範
2. ✅ 真實出貨流程可完整驗證數據鏈條（訂單 → 燒錄 → 出貨 → devices 同步）
3. ✅ 可同步測試出貨通知機制（`notification_inbox`）
4. ✅ 對專案干擾最小（無需額外種子腳本或手動資料庫操作）

### 建議操作流程
1. **老邱/Allie** 在 Alliance 後台建立測試訂單（客戶：老李 `owner_id=11`）
2. 訂單內容：3 台 ESP32-S3 遊戲採集卡
3. 透過燒錄站完成燒錄（產生 `chip_id` 並寫入 `ali_device_bindings`）
4. 點擊「轉為出貨單」觸發 `ship()`，自動同步至 `devices` 表
5. 老李登入 SignalHub 驗證「待設置的採集卡」提示是否出現

---

## 結論

✅ **配合度完全同步，無阻塞項**

### 關鍵確認
1. ✅ 數據鏈條與欄位對齊：完全符合 Ina 白名單規範
2. ✅ 狀態機同步：`pending_setup` → `active` 流程清晰
3. ⚠️ 韌體 URL 需修正：已納入工單 3 處理
4. ✅ 測試配合建議：選項 A（真實出貨流程）

### 待辦事項
- [ ] 工單 3：修正 `firmwareProxy()` 優先讀取 `merged_url`

---

**回報者**：Allie (Alliance Lead)  
**回報時間**：2026-09-09 00:12

