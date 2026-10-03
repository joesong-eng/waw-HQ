# 任務回報：TASK_20260916_INA_DROP_MACHINES_TABLES

**完成時間**：2026-09-16 23:45
**執行者**：Ina (Infra Master)

## 執行結果

### 1. DROP 執行

DROP TABLE IF EXISTS machine_transactions; -- OK
DROP TABLE IF EXISTS machine_deployments;  -- OK
DROP TABLE IF EXISTS machines;             -- OK

依外鍵相依性順序執行，無錯誤。

### 2. 驗證：SHOW TABLES LIKE 'machine%'

結果：空（0 筆），三張表完全移除。

### 3. 服務狀態

- credit-api：active
- waw-kiosk-listener：active
- waw-mqtt-listener：inactive（V8 legacy，非本任務範圍）

### 4. 前置確認

- internal.py 僅含廢棄說明注釋，無功能性 SQL 引用
- archive/ 目錄為歷史存檔，無服務載入

## 結論

iotv9.machine_transactions / machine_deployments / machines 三張表已完全從生產 DB 移除。
machines 體系終止，devices 為唯一 SSOT。

---
**回報者**：Ina (Infra Master)
**回報時間**：2026-09-16 23:45
