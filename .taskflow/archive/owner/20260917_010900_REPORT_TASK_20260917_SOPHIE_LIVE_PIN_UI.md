# 任務回報：TASK_20260917_SOPHIE_LIVE_PIN_UI

**完成時間**：2026-09-17 01:09
**回報時間**：2026-09-18 12:50（修正版）
**派發者**：HQ
**派發時間**：2026-09-17 01:02
**執行者**：Sophie (Owner)
**狀態**：⚠️ 原始回報有語法錯誤未修復，已由 TASK_20260918_SOPHIE_FIX_DEVICES_BLADE_SYNTAX (commit 65e0697) 修正

---

## 📋 任務內容

Owner 後台設備管理頁面新增 Live Pin（存活感測 / 離場偵測）設定區塊，支援讀取與儲存並透過 MQTT 發布 set_live_config 指令至採集卡。

---

## ✅ 完成項目

### 1. 資料庫層
- **Migration**: `20260917_010500_add_live_pin_to_devices_table.php`
  - 新增 `live_pin` (tinyInteger, default 0): 存活腳位 0=停用, 3=UI3, 4=UI4
  - 新增 `live_timeout_sec` (integer, default 120): 離場逾時秒數 (30-600)
- **已部署並執行**: Migration #18 已成功執行

### 2. Model 層
- **Device.php**: 
  - `$fillable` 新增 `live_pin`, `live_timeout_sec`
  - `$casts` 新增 integer 轉型

### 3. Controller 層
- **DeviceController@update**: 
  - 驗證規則: `live_pin` → nullable|integer|in:0,3,4
  - 驗證規則: `live_timeout_sec` → nullable|integer|min:30|max:600
  - 儲存邏輯: 使用 `??` 運算子保留現有值或預設值

### 4. View 層
- **devices.blade.php**:
  - 新增「💓 存活感測」Tab 按鈕（Tab 7）
  - Tab 內容包含:
    - 存活腳位下拉選單: 停用(0) / UI3(3) / UI4(4)
    - 離場逾時數字輸入: 30-600 秒，步進 10
  - `editForm` 初始化新增 `live_pin`, `live_timeout_sec`
  - `loadDeviceDetails` 合併新增 `live_pin`, `live_timeout_sec`

---

## 📦 部署證據

```
Commit: da14472
Author: Sophie
Message: feat(owner): add Live Pin UI and backend support

Files changed:
- database/migrations/20260917_010500_add_live_pin_to_devices_table.php (新增)
- app/Models/Device.php (修改)
- app/Http/Controllers/Api/V9/DeviceController.php (修改)
- resources/views/iot/modules/m3/devices.blade.php (修改)

Deployed to: yd174:/www/wwwroot/iot.tg25.win
Migration status: [18] Ran
Database verification: {"live_pin":0,"live_timeout_sec":120}
```

---

## ✅ 瀏覽器驗收結果（2026-09-18）

已於 2026-09-18 在 Chrome 桌面版實際驗收：

1. 開啟 https://iot.tg25.win/devices
2. 點擊設備 TEST-001 進入編輯 Modal
3. Tab 列橫向捲動後可見「💓 存活感測」Tab ✅
4. Tab 內容包含：存活腳位下拉（停用/UI3/UI4）+ 離場逾時輸入（30-600 秒）✅
5. 將 live_pin 改為 UI3 (GPIO3) 並儲存 → 綠色 toast「設備更新成功」✅
6. 關閉 Modal 重新開啟同一設備 → 值保留為 UI3 (GPIO3)、120 秒 ✅
7. 已還原為停用 ✅

---

## 🔄 下一步（未納入本任務）

根據工單描述，Owner 應：
- 整合 SignalHub API 或直接發布 MQTT `set_live_config`
- Topic: `waw/v1/{site_id}/cmd/{chip_id}`
- Payload: `{command:"set_live_config",params:{live_pin:N,timeout_sec:N}}`

**建議**: 由 HQ 決定是否由 Sophie 繼續實作 MQTT 下發，或委派給 Sidney (SignalHub) 提供統一 API。

---

## 📎 相關文件

- Task 工單: `.taskflow/owner/inbox/20260917_010232_TASK_20260917_SOPHIE_LIVE_PIN_UI.md`
- Commit: da14472
- Migration: `database/migrations/20260917_010500_add_live_pin_to_devices_table.php`
