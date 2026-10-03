# Ina 評估報告：請 HQ 核准工單

**回報時間**：2026-09-16 22:30  
**回報者**：Ina (Infra Master)  
**主題**：DROP machines 三表前置清理工單提案

---

## 背景

HQ 已決策：終止 machines 換表計畫，devices 為永久唯一 SSOT。  
Ina 全面掃描程式碼，確認 DROP 前必須先清理 3 個線上依賴點，否則連鎖崩潰。

---

## 現存線上依賴（DROP 前必須先清）

### 依賴 A（高）：kiosk_event_listener -> profit_sharing_service -> INSERT INTO machine_transactions

- 服務：waw-kiosk-listener（active）
- 觸發：每筆 stacked 投幣事件
- DROP 後：Table not found，分潤流水中斷
- 處置：移除 INSERT INTO machine_transactions；改寫 revenue_facts 或暫靜默 LOG

### 依賴 B（高）：transaction_writer.py -> INSERT INTO machine_transactions + LEFT JOIN machine_deployments

- 服務：credit-relay POST /internal/device/data-event（active）
- DROP 後：write_transaction() 全部 500
- 處置：INSERT 改寫 revenue_facts；LEFT JOIN machine_deployments 改從 devices.venue_id；internal.py 移除 write_transaction() 呼叫

### 依賴 C（高）：SignalHubController.php 第 72、126 行 exists:machines,id

- 服務：signal.tg25.win（active）
- DROP 後：Laravel Validator QueryException，HTTP 500
- 處置：移除 exists:machines,id 改為 nullable|integer
- 執行者：Sidney（SignalHub repo）

### 資料（低）：machine_transactions 有 1 筆分潤流水

- DROP 前匯出 CSV，HQ 決定是否保存

---

## 建議執行工單

### 工單 1（Ina，Infra repo）

1. profit_sharing_service.py：移除 create_machine_transaction() INSERT INTO machine_transactions
2. services/transaction_writer.py：移除 INSERT INTO machine_transactions；移除 LEFT JOIN machine_deployments
3. api/credit-relay/routers/internal.py：移除 write_transaction() 呼叫（保留 write_revenue_fact）
4. Git commit、push、遠端部署、重啟、驗收

### 工單 2（Sidney，SignalHub repo）

1. SignalHubController.php 第 72 行：移除 exists:machines,id
2. SignalHubController.php 第 126 行：移除 exists:machines,id
3. Git commit、push、遠端部署

### 工單 3（Ina，DB）— 工單 1+2 部署驗收完成後才執行

1. SELECT * FROM machine_transactions 匯出 CSV 存檔
2. DROP TABLE machine_transactions;
3. DROP TABLE machine_deployments;
4. DROP TABLE machines;
5. SHOW TABLES 確認無殘留
6. 回報 HQ

---

## 預估工期

| 工單 | 執行者 | 估時 |
|------|--------|------|
| 工單 1（Infra 程式碼清理） | Ina | 1-2 小時 |
| 工單 2（SignalHub validator） | Sidney | 30 分鐘 |
| 工單 3（DROP DB） | Ina | 10 分鐘 |

---

## 請 HQ 決策

1. 核准三份工單並依序派發 Ina / Sidney。
2. machine_transactions 的 1 筆舊資料：CSV 存檔或直接廢棄？
3. profit_sharing 分潤固化移除後：改寫 revenue_facts，或暫停待 WAW 2.0 重新設計？

---

**嚴禁：工單 1+2 部署驗收完成前執行工單 3。**

**回報者**：Ina (Infra Master)  
**回報時間**：2026-09-16 22:30
