# 任務回報：TASK_20260908_ALLIE_SIGNALHUB_ALIGNMENT_INQUIRY

**完成時間**：2026-09-08 13:03  
**執行者**：Allie (Alliance Lead)

---

## 一、 數據鏈條與欄位配合度確認

1. **現行流程與代碼查核**：
   - 在 Alliance 燒錄站（`/devices/burning`）執行設備出廠檢驗時，前端提交 `POST /api/devices/commit-registration`，由 `DeviceController::commitRegistration` 寫入 Alliance 本地資料庫之 `ali_device_bindings` 表（記錄 `order_item_id`、`chip_id`、`mac_address`、`status = 'burned'`）。
   - 在訂單出貨階段（`OrderController::ship`），系統將訂單轉為 `completed`、產出分潤結算單 `AliSettlement`，並跨庫向 `waw_core.notification_inbox` 寫入發貨通知給老李。
   - **關鍵點**：依歷史記錄（Commit `672892c`），因早期 `devices` 表結構認知差異，目前 Alliance 出貨與燒錄時**尚未自動跨庫寫入** `waw_core.devices`。

2. **欄位一致性與配合評估**：
   - SignalHub 所需規格：
     - `chip_id`: ESP32 物理識別碼（如 `C8F09E030001`）
     - `owner_id`: 設備歸屬業主（老李 ID: 11）
     - `name`: 出貨設備名稱（如 `老邱出貨-S3採集卡#01`）
     - `status`: 初始待設置狀態 `'pending_setup'`
   - **評估結果**：Alliance 的訂單資料模型（`ali_orders.owner_id`、`ali_products.sku_name`、`ali_device_bindings.chip_id`）已完全具備上述資訊。未來若需正式自動同步，只需在出貨/燒錄鏈條補上 `waw_core.devices` 之跨庫寫入邏輯即可完美契合。

---

## 二、 狀態機同步與業務邏輯確認

1. **狀態流轉完全符合預期**：
   - `pending_setup` → `active` 的狀態機流轉完全符合盟友（老邱）與業主（老李）的現實業務閉環：
     - **老邱端（出廠/出貨）**：設備燒錄完成並出貨後，在系統上處於「待客戶現場開卡/配置」狀態（`pending_setup`）。
     - **老李端（現場部署/配置）**：業主於 SignalHub 執行批量設置精靈，自訂機台名稱與腳位後自動更新為 `active`。
2. **售後與交付追蹤**：
   - Alliance 後續追蹤客戶是否完成開卡與現場投運，將以 `devices.status = 'active'` 作為交付完成標準，此設計與 Alliance 的業務管理邏輯 100% 同步。

---

## 三、 燒錄與韌體對接確認

1. **韌體來源查核**：
   - Alliance 現行 `DeviceController::firmwareProxy` 針對 `IOTwawS3` 採集卡，精確代理拉取 `https://hware.tg25.win/api/version.json`。
   - 現地實測該 API 正常運作，回傳穩定版本為 **v1.0.26**（`https://hware.tg25.win/firmware/IOTwawS3/firmware-v1.0.26.bin`），更新說明明確具備「訊號極性自動偵測與自適應，支援 set_signal_polarity 遠端極性設定指令與 simulate_pulse 軟體模擬脈衝注入指令」。
2. **與 Coli 標準完全相容**：
   - Alliance 燒錄站前端 (`/devices/burning`) 預設對應 S3 採集卡之 `IOTwawS3` 韌體，與 Coli 現行 ESP32-S3 信號規範完全一致，具備出廠燒錄與硬體檢驗相容性。

---

## 四、 本次測試出貨配合建議（選項 A 或 B）

- **Allie 堅決建議：採【選項 B】（由 HQ 先行以標準種子腳本在 `devices` 注入 3 筆 `pending_setup` 記錄）**。
- **評估理由**：
  1. **變數最小化，專注受測主體**：本次測試的核心檢驗焦點為 Sidney（SignalHub）端到端 10 大階段之業務與帳務防呆。採用標準種子建立純淨零狀態，能杜絕因人工跨系統操作引入的無效變數。
  2. **避免阻塞測試排程**：因 Alliance 目前尚未正式實作向 `waw_core.devices` 的自動跨庫同步，若採選項 A 需先對 Alliance 代碼進行擴充、測試、部署並人工開單燒錄，將延誤本次 E2E 測試啟動時機。
  3. **演進規劃**：建議待本次 SignalHub 全功能驗收完成後，HQ 再另行指派工單由 Allie 實現 Alliance 出貨時自動跨庫入庫 `waw_core.devices`，屆時再做雙平台自動化跨庫整合測試。

---

## 結論
✅ **配合度與業務架構完全同步**。  
建議由 HQ 依規範文件之種子規格（老李 `owner_id: 11`，Chip ID: `C8F09E030001` ~ `03`，狀態 `pending_setup`）執行環境重置與注入，即可立即啟動 SignalHub 全功能 E2E 閉環測試！

---
**回報者**：Allie  
**回報時間**：2026-09-08 13:03

