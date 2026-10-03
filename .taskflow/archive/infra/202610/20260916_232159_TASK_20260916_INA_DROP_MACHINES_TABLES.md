# 工單：TASK_20260916_INA_DROP_MACHINES_TABLES

**派發時間**：2026-09-16 23:35
**優先級**：HIGH
**負責人**：Ina (Infra Master)
**決策背景**：工單 1（Ina 代碼依賴清理）與工單 2（Sidney 表單驗證清理）皆已驗收完成，HQ 正式核准執行 DROP。

---

## 任務內容

於生產環境資料庫 iotv9 執行實體刪除已廢棄之 machines 三張表：

### 1. 執行順序（依外鍵相依性）
```sql
DROP TABLE IF EXISTS machine_transactions;
DROP TABLE IF EXISTS machine_deployments;
DROP TABLE IF EXISTS machines;
```

### 2. 驗證
- 執行 SHOW TABLES LIKE 'machine%'，確認三張表已完全移除。
- 檢查關聯服務日誌（waw-mqtt-listener、waw-kiosk-listener、credit-relay），確認運行平穩無 SQL 報錯。

---

## 回報格式
完成後使用 agent_report_to_hq_v2.sh 提交報告至 HQ outbox。
