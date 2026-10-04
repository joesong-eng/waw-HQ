# 任務：TASK_20261005_INA_CREATE_CROSS_DB_TRIGGER

**派發時間**：2026-10-05
**優先級**：high
**負責人**：Ina (Infra / DB)
**性質**：基礎設施執行（先查再做，DDL 需備份）
**架構依據**：`PROPOSAL_20260914_ALLIE_DEVICES_CROSS_DB_ARCHITECTURE_REFACTOR`

---

## 背景與「為什麼要建 Trigger」（Joe 要求說明）

**問題**：Alliance 燒錄站 `commitRegistration()` 目前用 **PHP 應用層雙寫**（同時寫 `alliance_db.ali_device_bindings` 與 `iotv9.devices`）。這有兩個結構性風險：

1. **資料一致性風險**：若 PHP 寫完 binding、寫 devices 前崩潰（或跨庫連線失敗），會產生**孤兒記錄**（binding 有、devices 無），後續 SignalHub/統計全部對不上。
2. **跨庫耦合**：Alliance 的 Web 主機（yd16）需直接持有 `iotv9` 的寫入權限與連線，違反「業務資料庫集中由 Infra 管理」的治理原則。

**架構裁定（2026-09-14）**：改由 **MySQL 跨庫 Trigger** 在 DB 層自動同步——`alliance_db.ali_device_bindings` 一經 INSERT/UPDATE，DB 引擎即在同一交易內同步 `iotv9.devices`。
- **原子性**：與主表寫入同交易，不再有「寫一半」的孤兒。
- **解耦**：應用層拔掉雙寫，Alliance 不需持有 iotv9 寫權限。
- **單一真相**：同步邏輯集中在 DB，不再散落 PHP 各處。

**這正是 Allie 於 `TASK_20261005_ALLIE_ORDER_STATE_MACHINE_LOGIC_TEST` 發現的 G5**：程式碼註解聲稱 Trigger 已接管，但 `SHOW TRIGGERS` 為空 → **同步實際仍靠 PHP 雙寫，註解與實作不符**。

---

## 你 09-14 的回報 vs 現況（矛盾需釐清）

你於 `TASK_20260914_INA_CROSS_DB_TRIGGER_AND_DEVICE_STATUS_API`（2026-09-14 13:45）回報：
> 「觸發器 `trg_ali_device_bindings_sync_to_iotv9`（AFTER INSERT）與 `..._upd`（AFTER UPDATE）已建立，並以 INSERT/ROLLBACK 測試通過。」

但 Allie 於 2026-10-05 實測 `SHOW TRIGGERS FROM alliance_db` → **空陣列**。

**可能原因**（請查清）：
1. Trigger 從未真正在生產執行（僅在測試環境跑過）
2. 生產環境重建 / 還原 / 主從切換導致 Trigger 遺失
3. Allie 查的是錯的 DB / 主機
4. 其他

---

## 任務步驟

### 步驟 1：現況查核（唯讀，先做）
1. 到正確的 DB 主機，查 `alliance_db` 的 Trigger：
   ```sql
   SELECT TRIGGER_SCHEMA, TRIGGER_NAME, EVENT_OBJECT_TABLE, ACTION_TIMING, EVENT_MANIPULATION
   FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA='alliance_db';
   ```
2. 查 `iotv9.devices` 現有筆數，並抽樣確認其來源（是否有 Trigger 痕跡 / 全由 PHP 寫入）。
3. 釐清 09-14 回報與現況的矛盾原因（明確結論）。

### 步驟 2：建立 Trigger（若確認不存在）
- 使用既有檔案：`PROJECT/Infra/db/migrations/20260914_cross_db_trigger_ali_device_to_iotv9.sql`
  （內含 `trg_ali_device_bindings_sync_to_iotv9` AFTER INSERT + `..._upd` AFTER UPDATE）
- 執行前**先備份**現有 Trigger 定義與 `information_schema.TRIGGERS` 快照。
- 採 idempotent（檔案內已含 `DROP TRIGGER IF EXISTS`）。

### 步驟 3：驗證
- 以 **ROLLBACK 交易**做 INSERT 測試（沿用你 09-14 的方法）：
  - 插入測試 binding（chip_id 前綴 `TRGTEST`）→ 查 `iotv9.devices` 是否自動出現 → **ROLLBACK**，確認 0 污染。
- 驗證 UPDATE 事件（改 public_token/status）亦同步。

---

## 驗收指標（附實際指令與輸出）

1. `information_schema.TRIGGERS` 查詢結果（步驟 1 現況 + 步驟 3 建立後）
2. 09-14 矛盾原因的明確結論
3. ROLLBACK 測試的 devices 自動寫入證據 + 污染筆數 0
4. `iotv9.devices` 抽樣來源說明

---

## 後續影響（HQ 會另行處理，你不用做）
- 確認 Trigger 生效後，HQ 會派 Allie **拔除 PHP 雙寫**，並修正 G5 的錯誤註解。

## 禁止

- 未備份不得執行 DDL
- 不刪除既有資料
- 不動 Alliance / Member 專案程式碼

## 完成定義

Trigger 建立並以 ROLLBACK 測試驗證通過，4 項驗收有實際輸出，回報寫入 `.taskflow/infra/outbox/`。
若確認 Trigger 其實存在（Allie 查錯），亦請照實回報並提供證據。
