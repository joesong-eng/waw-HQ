# 任務：TASK_20260908_INA_DEVICES_SYNC_SCHEMA_AUDIT

**派發時間**：2026-09-08 16:30  
**優先級**：HIGH  
**負責人**：Ina (Infra Database Lead)  
**協同對象**：Allie (Alliance Lead), Sidney (SignalHub Lead), Sophie (Owner Lead)

---

## 📋 任務背景與核心目標

針對 Alliance 老邱出貨（S3採集卡）至 SignalHub 老李設備開卡之自動化閉環，需要由 Alliance OrderController::ship 跨庫寫入核心庫 iotv9.devices（連線名稱：waw_core）。

為杜絕歷史 Commit 672892c 因欄位不一致導致 SQL 報錯之問題，並嚴格遵循 DB 治理規範，請 Ina 審定並出具官方的 **devices 入庫欄位白名單與寫入規範**。

---

## 🔍 任務執行要點

1. **審核現有 iotv9.devices Schema**：
   - 檢查所有 NOT NULL 且無 DEFAULT 的欄位，確認新增一筆設備入庫時必填欄位清單。
   - 確認 WAW 2.0 雙產權欄位（collector_owner_id, machine_owner_id）在出貨時的填寫原則（原則上皆填入該訂單業主 owner_id）。
   - 確認 status 欄位列舉值（ENUM 或 VARCHAR）是否支援 'pending_setup'，此狀態為 SignalHub 觸發設置精靈之關鍵狀態。
   - 確認 chip_id 的 UNIQUE 約束與資料型態。
2. **出具官方寫入白名單規範文件**：
   - 明確列出 Alliance 跨庫 updateOrInsert 應寫入的欄位清單（如 chip_id, owner_id, collector_owner_id, machine_owner_id, name, type, status, created_at, updated_at 等）。
   - 標明哪些欄位嚴禁寫入（如舊歷史誤寫的 mac_address, node_id 等）。
3. **回報至 Outbox**：
   - 形成正式規範回報於 .taskflow/infra/outbox/，供 Allie 依約實作跨庫寫入邏輯。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260908_INA_DEVICES_SYNC_SCHEMA_AUDIT

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：Ina (Infra Database Lead)

## 審核結論與 devices 入庫白名單標準
（詳細列出欄位、型態、預設值、必填項與寫入範例）

## 結論
✅ 審核完成，已發布規範供 Allie 實作 / ❌ 需進一步遷移調整
```

---
**派發者**：HQ  
**派發時間**：2026-09-08 16:30
