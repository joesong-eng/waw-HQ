# 任務回報：revenue_facts 需要建立複合索引

## 回報時間
2026-08-17

## 事由
Owner 在 realtime 頁面效能診斷過程中，發現 revenue_facts 表查詢速度過慢，需要 Ina 協助建立複合索引。

## 問題詳情

### 資料庫：iotv9（生產環境）
- 伺服器：yd174 / 141.148.165.50
- 表：revenue_facts
- 資料量：654,448 筆 / 60.6 MB

### 現有索引（各自獨立，無法組合）
```
device_id         ← 獨立索引
event_ts          ← 獨立索引
transaction_type  ← 獨立索引
is_valid          ← 無索引
```

### 查詢條件（realtime 頁面每次載入都執行）
```sql
WHERE device_id = ?
  AND event_ts >= '今天 00:00 UTC'
  AND is_valid = 1
  AND transaction_type = 'credit_in'
```

MySQL 只能選其中一個索引，剩下的全部逐行掃描整個 device 的記錄 → 慢。

## 請 Ina 執行

在生產資料庫 iotv9 的 revenue_facts 表建立以下複合索引：

```sql
CREATE INDEX idx_device_ts_type
ON revenue_facts (device_id, event_ts, transaction_type, is_valid);
```

### 注意
- InnoDB Online DDL，不鎖讀取，但建索引期間 DB 負載會升高
- 65 萬筆預計需要 1~3 分鐘
- 建議低流量時段執行

## 預期效果
查詢從掃整個 device_id 所有記錄 → 只掃今天該台設備的幾十筆。

## 回報人
Sophie（Owner Agent）

