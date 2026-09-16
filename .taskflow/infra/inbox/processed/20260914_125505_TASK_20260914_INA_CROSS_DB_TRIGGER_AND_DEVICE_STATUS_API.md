# 任務：TASK_20260914_INA_CROSS_DB_TRIGGER_AND_DEVICE_STATUS_API
**派發時間**：2026-09-14 14:05
**優先級**：🔴 HIGH (架構重構與跨專案解耦)
**負責人**：Ina (Infra Master)
**來源**：
1. Allie 提案 PROPOSAL_20260914_ALLIE_DEVICES_CROSS_DB_ARCHITECTURE_REFACTOR.md (Joe 指示：廢除應用層雙寫)
2. Mina UX-P1-4 機台活動防誤踢需求 (Ina 回報建議方案 A)

---

## 一、任務背景與目的

1. **老邱出廠卡片同步老李後台**：
   目前 Alliance 產線燒錄站透過 PHP 應用層多個 Controller 手動跨庫雙寫至 `iotv9.devices`，極易因例外狀況或漏寫導致老李後台看不到設備。
   因 `alliance_db` 與 `iotv9`（或核心庫）皆在同一台 MySQL 實例（`141.148.165.50`），依 Joe 指示，改由資料庫層 Trigger 自動維護資料一致性。
2. **Member 機台活躍度判斷**：
   Mina 需要知道玩家正在玩的機台是否仍然活躍，以防 120 秒無手機操作被誤踢。請依你的回報建議，提供讀取 Redis 快取的 API。

---

## 二、具體執行項目

### 項目 1：建立 MySQL 跨庫同步觸發器 (Trigger)
- **位置**：MySQL `141.148.165.50`
- **觸發對象**：`alliance_db.ali_device_bindings`
- **事件**：`AFTER INSERT` 與 `AFTER UPDATE`
- **業務規則**：
  1. 當 `NEW.chip_id` 不為空，且對應訂單有 `owner_id` 時：
  2. 自動在同一 Transaction 內同步至 `iotv9.devices`：
     ```sql
     INSERT INTO iotv9.devices (
         chip_id, 
         node_id, 
         public_token, 
         owner_id, 
         status, 
         created_at, 
         updated_at
     ) VALUES (
         NEW.chip_id, 
         NEW.node_id, 
         NEW.public_token, 
         (SELECT owner_id FROM alliance_db.ali_orders WHERE id = NEW.order_id), 
         'pending_setup', 
         NOW(), 
         NOW()
     ) ON DUPLICATE KEY UPDATE 
         node_id = VALUES(node_id),
         public_token = COALESCE(VALUES(public_token), iotv9.devices.public_token),
         owner_id = COALESCE(VALUES(owner_id), iotv9.devices.owner_id),
         updated_at = NOW();
     ```
  *(請根據 iotv9.devices 實際 schema 欄位校準並編寫 Migration 腳本留存)*。
- **回測驗收**：
  - 測試在 `ali_device_bindings` 插入/更新一筆假資料，確認 `iotv9.devices` 自動同步。
  - 完成後通報 HQ，HQ 將通知 Allie 拔除 PHP 應用層的跨庫雙寫。

---

### 項目 2：提供設備狀態查詢 API (讀取 Redis)
- **服務**：`api/credit-relay` (或現有 Infra API 專案)
- **端點**：`GET /api/device/{chip_id}/status`
- **認證**：相容現有 `X-Internal-Key` / `X-API-Key`
- **邏輯**：
  - 從 Redis 讀取 `v9:machine:{chip_id}:status`。
  - 回傳 JSON：
    ```json
    {
      "chip_id": "{chip_id}",
      "status": "online|offline|unknown",
      "last_seen_at": "2026-09-14T05:00:00Z",
      "is_active": true
    }
    ```
  - 若 Redis 查無資料，可回退查 `iotv9.machines` / `iotv9.devices` 的 `last_seen_at` 或 `updated_at`。

---

## 三、回報要求
完成後請將報告寫入 `.taskflow/infra/outbox/`：
1. Trigger SQL 遷移檔路徑與在生產庫部署驗證結果。
2. API 端點測試（curl 範例與 JSON 回傳結果）。
3. 提示 Allie 與 Mina 可以開始接軌。

---
**派發者**：HQ  
**派發時間**：2026-09-14 14:05
