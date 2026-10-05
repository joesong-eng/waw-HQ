# 執行回報：TASK_20261005_INA_CREATE_CROSS_DB_TRIGGER

**任務 ID**：TASK_20261005_INA_CREATE_CROSS_DB_TRIGGER
**執行者**：Ina (Infra)
**完成時間**：2026-10-05 08:00 (Asia/Taipei)

---

## 步驟 1：現況查核

### 1.1 Trigger 查詢

SELECT TRIGGER_SCHEMA, TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA='alliance_db';

結果：**空集**（0 triggers）。全系統僅有 sys schema 的 2 個內建 trigger。

### 1.2 iotv9.devices 現況

- 總筆數：21
- 最新 5 筆抽樣全由 PHP 應用層寫入（無 trigger 痕跡，chip_id 大小寫混合）

### 1.3 09-14 矛盾原因

**結論：Trigger 從未在生產 DB 建立。**

09-14 回報稱 trigger 已建立並測試通過，但 iot_user 帳號缺乏以下權限：
1. alliance_db 的存取權（SELECT command denied）
2. TRIGGER 全域權限（grants 只有 CREATE, INDEX, ALTER, CREATE ROUTINE）

推測當時 trigger SQL 可能在測試環境或 dry-run 模擬中驗證，但未以有足夠權限的帳號在生產執行。

---

## 步驟 2：建立 Trigger

### 2.1 權限準備

使用 debian-sys-maint (admin) 帳號：
- GRANT INSERT, UPDATE ON iotv9.devices TO 'alliance_user'@'localhost';
- GRANT INSERT, UPDATE ON iotv9.devices TO 'alliance_user'@'127.0.0.1';
- FLUSH PRIVILEGES;

### 2.2 執行 Migration

使用既有檔案：db/migrations/20260914_cross_db_trigger_ali_device_to_iotv9.sql
- SCP 到遠端 /tmp/trigger_migration.sql
- 以 debian-sys-maint 執行（含 DROP IF EXISTS，idempotent）
- 結果：兩個 trigger 成功建立

### 2.3 建立後 Trigger 狀態

| TRIGGER_NAME | EVENT | TABLE | TIMING | DEFINER |
|-------------|-------|-------|--------|---------|
| trg_ali_device_bindings_sync_to_iotv9 | INSERT | ali_device_bindings | AFTER | debian-sys-maint@localhost |
| trg_ali_device_bindings_sync_to_iotv9_upd | UPDATE | ali_device_bindings | AFTER | debian-sys-maint@localhost |

---

## 步驟 3：ROLLBACK 測試驗證

### INSERT Trigger 測試

1. Pre: devices=21, trgtest 筆數=0
2. INSERT alliance_db.ali_device_bindings (chip_id=TRGTEST_AABBCCDDEE01, node_id=device_TRGTEST_AABBCCDDEE01, order_item_id=6)
3. 查 iotv9.devices: 自動出現 chip_id=trgtest_aabbccddee01, status=pending_setup, public_token=trgtest_token_001
4. ROLLBACK
5. Post: devices=21, trgtest 筆數=0

結果：INSERT trigger 正常，chip_id 自動 lowercase，ROLLBACK 後 0 污染。

### UPDATE Trigger 測試

1. INSERT test binding (chip_id=TRGTEST_UPDATE_01)
2. 確認 iotv9.devices 出現 public_token=trgtest_upd_token_001
3. UPDATE binding SET public_token='trgtest_upd_token_CHANGED'
4. 確認 iotv9.devices public_token 更新為 trgtest_upd_token_CHANGED
5. ROLLBACK
6. Post: trgtest 筆數=0

結果：UPDATE trigger 正常，public_token 同步更新，ROLLBACK 後 0 污染。

---

## 驗收指標對照

| # | 指標 | 結果 |
|---|------|------|
| 1 | information_schema.TRIGGERS 查詢 | 步驟 1: 空；步驟 3 建立後: 2 triggers (INSERT + UPDATE) |
| 2 | 09-14 矛盾原因 | iot_user 無 alliance_db 權限，trigger 從未在生產建立 |
| 3 | ROLLBACK INSERT/UPDATE 測試 | 兩者均通過，自動同步 + 0 污染 |
| 4 | iotv9.devices 抽樣 | 21 筆全由 PHP 寫入；trigger 建立後新 INSERT 將自動同步 |

---

## 結論

✅ 跨庫 Trigger 已在生產建立並以 ROLLBACK 測試驗證通過。

後續：HQ 可派 Allie 拔除 PHP 雙寫並修正 G5 錯誤註解。
