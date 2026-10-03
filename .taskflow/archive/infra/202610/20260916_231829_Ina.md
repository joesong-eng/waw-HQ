# 任務回報：TASK_20260916_INA_PURGE_MACHINE_TRANSACTIONS_DEPS

**完成時間**：2026-09-16 23:30
**執行者**：Ina (Infra Master)

## 執行結果

### 1. 備份 machine_transactions（1 筆）

存入：backups/machine_transactions_20260916.sql
id=1, machine_id=1, venue_id=1, transaction_type=division, amount=100.00, machine_owner_share=100.00

### 2. kiosk_event_listener.py

無需修改。grep CLEAN：無 profit_sharing_service、無 TransactionWriter、無 machine_transactions 引用。

### 3. api/credit-relay/routers/internal.py

移除 /device/data-event 中：
- TransactionWriter import 與實例化
- write_transaction() 呼叫
- machine_transactions 相關 db_config 建構

重寫 endpoint 直接使用 aiomysql 寫入 revenue_facts。
python3 -m py_compile → OK
零 TransactionWriter 功能引用確認。

### 4. Git commit 與部署

- Commit：9425e3b (refactor: remove machine_transactions/TransactionWriter deps)
- Push main → 成功
- 遠端 fast-forward 至 9425e3b

### 5. 服務驗收

- credit-api：active
- waw-kiosk-listener：active
- curl 127.0.0.1:8084 → FastAPI 正常回應

### 注意事項

- iotv9.machine_transactions / machine_deployments / machines 三表未 DROP，歷史存檔
- 外部 https://api.tg25.win 502 為 nginx 路由問題，非本任務範圍

## 結論

machine_transactions 依賴完全清除，revenue_facts 為唯一固化目標

---
**回報者**：Ina (Infra Master)
**回報時間**：2026-09-16 23:30
