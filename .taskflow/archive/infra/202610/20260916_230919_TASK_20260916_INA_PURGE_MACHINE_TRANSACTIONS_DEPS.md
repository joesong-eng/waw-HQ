# 工單：TASK_20260916_INA_PURGE_MACHINE_TRANSACTIONS_DEPS

**派發時間**：2026-09-16 22:45  
**優先級**：HIGH  
**負責人**：Ina (Infra Master)  
**前置決策**：HQ 已核准（profit_sharing 寫入拔除，不改寫 revenue_facts；歷史 1 筆 machine_transactions 資料備份後廢棄）

---

## 任務內容

配合終止 machines 體系計畫，清理 Infra 服務層對 machine_transactions 與 machine_deployments 的程式碼依賴：

### 1. 備份 machine_transactions 資料（1 筆）
- 執行 mysqldump 或查詢匯出成 CSV/SQL，存放於 Infra 專案備份目錄留底。

### 2. 清理 kiosk_event_listener.py
- 移除 profit_sharing_service 呼叫邏輯（stacked 事件處理中的 profit_service.process_consumption_event）。
- 移除頂部 from profit_sharing_service import ProfitSharingService 與實例化代碼。
- 註：主營收由既有 write_revenue_fact 負責，不需將分潤改寫至 revenue_facts。

### 3. 清理 api/credit-relay/services/transaction_writer.py
- 移除對 machine_transactions 的 INSERT 邏輯。
- 移除關聯 machine_deployments 的 LEFT JOIN 查詢。

### 4. 清理 api/credit-relay/routers/internal.py
- 移除 write_transaction 呼叫，僅保留 write_revenue_fact 營收寫入。

### 5. 驗證與部署
- 本地語法與測試確認。
- 部署至 VPS infra (141.148.165.50)。
- 重啟 waw-kiosk-listener 與 credit-relay 服務。
- 監聽 log 確認接收事件正常、無報錯。

---

## 回報格式
完成後使用 agent_report_to_hq_v2.sh 提交報告至 HQ outbox。
