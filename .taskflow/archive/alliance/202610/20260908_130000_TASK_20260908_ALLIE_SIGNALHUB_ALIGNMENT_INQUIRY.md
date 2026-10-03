# 任務：TASK_20260908_ALLIE_SIGNALHUB_ALIGNMENT_INQUIRY

**派發時間**：2026-09-08 13:00  
**優先級**：high  
**負責人**：Allie (Alliance Lead)  
**發起人**：HQ (協調中心)  
**關聯規範文檔**：`brains/knowledge/04_deployment_operations/SIGNALHUB_FULL_FEATURE_E2E_TEST_PLAN.md`

---

## 📋 任務背景與詢問目的

Sidney (SignalHub) 目前已全數完成 `signal.tg25.win` 的介面收斂與後端優化（最新里程碑 Commit `4e6a5fc`）。
HQ 與 Joe（Boss）目前正在規劃 **SignalHub 全功能端到端閉環測試**。

本次測試的**起點業務場景**設定為：
> **「清空歷史舊數據後，由老邱（Alliance）建立全新出貨單，出貨 3 台 ESP32-S3 遊戲採集卡至業主老李（owner_id: 11）名下，接續進行老李登入後的批量設置、腳位通道定義與開洗分驗證。」**

為了確保 Alliance（老邱）與 SignalHub（老李/合作端）在此階段的業務流程、數據結構與狀態流轉完全同步且無縫對接，HQ 特此向 Allie 提出對齊與協同度確認。

---

## 🔍 對齊詢問重點（請 Allie 逐項評估回覆）

### 1. 出貨單與設備註冊鏈條 (`AliOrder` → `devices`)
- **現行流程確認**：當老邱在 Alliance 後台完成出貨操作（`AliOrder::ship` / `commitRegistration`）時，Alliance 寫入 `waw_core.devices`（或 `iotv9.devices`）的資料格式為何？
- **欄位一致性**：SignalHub 的待設置機制依賴以下欄位：
  - `chip_id`: ESP32 硬體識別碼（例如：`C8F09E030001`）
  - `owner_id` (或 `collector_owner_id`): 綁定購買者（老李 `user_id = 11`）
  - `name`: 出貨品名（例如：`老邱出貨-S3採集卡#01`）
  - `status`: 初始狀態必須為 `'pending_setup'`（或 null）
- **問**：Alliance 目前的出貨邏輯是否已能完整寫入上述欄位？是否有需要微調之處？

---

### 2. 設備狀態流轉同步 (`pending_setup` → `active`)
- **業務閉環**：
  1. 老邱出貨時，設備狀態為 `pending_setup`。
  2. 老李登入 `signal.tg25.win`，前端偵測到 `pendingSetup()` 設備並於頂部跳出橘色「⚠️ 待設置的採集卡」。
  3. 老李/工程師透過批量設置精靈完成機台命名與腳位映射後，SignalHub 會自動將 `devices.status` 更新為 `'active'`。
- **問**：Alliance 系統後續是否會依據 `devices.status = 'active'` 來追蹤客戶是否已完成現場開卡？此狀態流轉是否完全符合 Alliance 的預期與管理邏輯？

---

### 3. 出廠燒錄與韌體版本關聯 (`IOTwawS3`)
- **燒錄站機制**：在 Alliance 燒錄站 (`/devices/burning`)，老邱對採集卡進行燒錄與出廠檢驗。
- **問**：目前 Alliance 針對 S3 採集卡燒錄的韌體版本源（`https://hware.tg25.win/api/version.json`）是否與 Coli 的最新標準一致？出廠時的硬體檢測與本次測試流程是否相容？

---

### 4. 本次測試配合方式評估
- **問**：針對本次全功能測試的 3 台新採集卡：
  - **選項 A**：由老邱/Allie 直接在 Alliance 後台開立正式測試出貨單（產生 `ali_orders`, `ali_device_bindings` 並自動同步至 `devices`）。
  - **選項 B**：由 HQ 先行以資料庫標準種子腳本在 `devices` 產生符合 Alliance 出貨規格的 3 筆 `pending_setup` 記錄進行測試，後續再與 Alliance 進行跨系統真實 API 對接。
  - 請 Allie 提供目前最順暢、對專案干擾最小的建議做法。

---

## 📝 回報格式

請 Allie 於 `.taskflow/alliance/outbox/` 提交回報：

```markdown
# 任務回報：TASK_20260908_ALLIE_SIGNALHUB_ALIGNMENT_INQUIRY

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：Allie

## 一、 數據鏈條與欄位配合度確認
（回覆問題 1）

## 二、 狀態機同步與業務邏輯確認
（回覆問題 2）

## 三、 燒錄與韌體對接確認
（回覆問題 3）

## 四、 本次測試出貨配合建議（選項 A 或 B）
（回覆問題 4）

## 結論
✅ 配合度完全同步 / ⚠️ 需要先調整以下項目

---
**回報者**：Allie  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-09-08 13:00
