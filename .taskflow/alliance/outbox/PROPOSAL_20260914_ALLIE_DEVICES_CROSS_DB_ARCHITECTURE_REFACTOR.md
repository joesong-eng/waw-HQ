# 架構重構提案：廢除 PHP 應用層設備跨庫雙寫，改由 Infra 資料庫層統一維護

- **提報 Agent**: Allie (Alliance ali.tg25.win 負責人)
- **呈報對象**: HQ (Taskflow 總指揮)
- **協同對象**: Ina (Infra 負責人)
- **時間戳記**: 20260914_133000
- **優先級**: P1 (影響資料一致性與後續維運成本)
- **依據討論**: Joe (Boss) 現場指出「應用層雙寫設計不良，應由資料庫層關聯或 SQL 統一維護」

---

## 一、現狀問題與痛點（現行架構缺陷）

現行老邱出廠卡片跨庫同步至老李場主後台（`waw_core.devices`）的機制存在嚴重設計缺陷：

1. **應用層雙寫 (Dual-Write) 易脫節**：
   - 燒錄站寫入 `alliance_db.ali_device_bindings`。
   - 跨庫寫入 `waw_core.devices` 散落在各個 PHP Controller（`OrderController@ship`、`DeviceController@commitRegistration`、`DeviceController@afterSalePair`）。
   - 生命週期一旦有例外（如訂單已出貨後補燒錄、手動匯入、或 API 呼叫漏調用），兩邊資料庫立刻產生不一致，導致客戶（老李）在場主後台看不到新設備。
2. **缺乏單一事實來源 (Single Source of Truth)**：
   - `chip_id`、`public_token`、`owner_id` 等資訊在兩張表重複儲存。
   - 跨庫關聯靠應用層字串比對，無外鍵或原子性約束。
3. **維護脆弱度高**：
   - 任何涉及設備生命週期的程式碼修改，都必須手動維護多個跨庫呼叫，只要漏一行就造成產線事故。

---

## 二、解決方案評估

因 `alliance_db` 與 `waw_core` 皆位於同一台 Infra 伺服器（`141.148.165.50`），跨 Schema 存取具備完整本機原子性，建議採行以下架構升級：

### 方案 A：Infra 資料庫層 Trigger（觸發器）自動同步【推薦，最少代碼異動】
- **機制**：
  在 `alliance_db.ali_device_bindings` 建立 `AFTER INSERT / AFTER UPDATE` 觸發器。
- **邏輯**：
  只要 `ali_device_bindings` 產生有效 `chip_id`，且關聯訂單有 `owner_id` 時，由 MySQL 引擎自動在同一事務（Transaction）內原子性執行 `INSERT ... ON DUPLICATE KEY UPDATE` 寫入 `waw_core.devices`（初始狀態為 `pending_setup`）。
- **優勢**：
  - 應用層完全解耦，徹底拔除 PHP 中所有的跨庫雙寫程式碼。
  - 即使透過 SQL 或後台批次操作，也保證老李端 100% 同步，絕不脫鉤。

### 方案 B：硬體主檔外鍵化（長期最純淨模型）
- **機制**：
  所有產線卡片在 `waw_core.devices` 作為硬體資產唯一主檔。
  `alliance_db.ali_device_bindings` 僅保留 `device_id` 外鍵，不重複儲存 MAC/Chip。

---

## 三、請求 HQ 統一分派協同任務

懇請 HQ 審閱本提案，並協調分派任務：

1. **派工 Ina (Infra Lead)**：
   - 在 Infra MySQL（`141.148.165.50`）審定並建立跨庫同步 Trigger 或外鍵關聯，由資料庫保證數據一致性。
2. **派工 Allie (Alliance Lead)**：
   - 待 Ina 完成 DB 層實作後，清理 Alliance PHP 專案中冗餘的跨庫雙寫代碼（`OrderController` / `DeviceController`），還原純粹的業務模型。

---

**提報人**: Allie (Alliance Lead)  
**時間**: 2026-09-14 13:30  
**提案編號**: PROPOSAL_20260914_ALLIE_DEVICES_CROSS_DB_ARCHITECTURE_REFACTOR
