# WAW 2.0 進度追蹤 - 2026-06-17


**[On-Demand]** — 上下文注入策略

> **建立日期**: 2026-06-17  
> **維護者**: HQ  
> **狀態**: 🔴 發現 Schema 不匹配，阻塞 realtime 頁面

---

## 🔴 阻塞問題：revenue_facts Schema 不匹配

### 症狀
- `https://iot.tg25.win/realtime` 頁面 API `/api/v9/realtime/devices` 回傳 500
- Laravel log 錯誤：`SQLSTATE[42S22]: Column not found: 1054 Unknown column 'transaction_type' in 'field list'`

### 根本原因
`waw-core` 的 `MachineExtensions.php` (`getPeriodStatistics`) 查詢 `revenue_facts` 時，
假設存在 `transaction_type` 和 `is_valid` 欄位，但 `infra (iotv9)` 上的實際 Schema 不包含這兩個欄位。

**waw-core 程式碼期待的欄位（在 MachineExtensions.php getPeriodStatistics）：**
```sql
SELECT transaction_type, SUM(amount) as period_amount
FROM revenue_facts
WHERE chip_id = ? AND event_ts >= ? AND is_valid = 1
GROUP BY transaction_type
```

**infra `iotv9.revenue_facts` 實際欄位：**
| 欄位 | 存在 |
|------|------|
| id | ✅ |
| chip_id | ✅ |
| device_id | ✅ |
| venue_id | ✅ |
| delta_value | ✅ |
| amount | ✅ |
| event_ts | ✅ |
| created_at | ✅ |
| transaction_type | ❌ 不存在 |
| is_valid | ❌ 不存在 |
| pulse_count | ❌ 不存在 |
| pulse_ratio | ❌ 不存在 |
| local_date | ❌ 不存在 |

### 解決方案（二擇一）

**方案 A（推薦）：Ina 在 infra 補齊欄位**
在 `iotv9.revenue_facts` 新增 `transaction_type` 和 `is_valid` 欄位，
並 backfill `transaction_type = 'credit_in'`（所有現有資料預設為 credit_in）

```sql
ALTER TABLE revenue_facts
  ADD COLUMN transaction_type VARCHAR(20) NOT NULL DEFAULT 'credit_in' COMMENT '交易類型: credit_in / credit_out' AFTER chip_id,
  ADD COLUMN is_valid TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否有效' AFTER amount,
  ADD INDEX idx_transaction_type (transaction_type);
```

**方案 B：Sophie 修改 waw-core 程式碼**
修改 `app/Models/MachineExtensions.php` 的 `getPeriodStatistics()`，
改用 `delta_value` 替代分組，不依賴 `transaction_type` 和 `is_valid`。

### HQ 裁定
採用**方案 A**。Schema 補齊是 Ina 職責，waw-core 程式碼的設計假設是正確的（WAW 2.0 規格 `revenue_facts` 應有這兩個欄位）。
不應為了遷移不完整而改動 waw-core 業務邏輯。

---

## 任務紀錄

| 任務 ID | 指派對象 | 狀態 | 說明 |
|---------|---------|------|------|
| TASK_20260617_SCHEMA_FIX_001 | Ina | 🟡 已發送 | 補齊 revenue_facts 欄位 |

