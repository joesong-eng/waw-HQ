# 營收數據流與交易分類規範 (Revenue Data Flow & Transaction Classification)


**[On-Demand]** — 上下文注入策略

> **版本**: 1.0.0  
> **建立日期**: 2026-06-17  
> **狀態**: 🟢 權威定義  
> **維護者**: HQ  
> **關聯設備**: Coli (IOTwawS3 遊戲機通訊卡), Fio (IOTkiosk_v0 紙鈔兌幣卡)

---

## 一、資料流路徑 (Data Flow Path)

```
[韌體] Coli/Fio (累積值) 
   ↓ MQTT
device/{chip_id}/data/credit_in  或  device/{chip_id}/data/credit_out
   ↓ 
[Infra] listener.py (Delta 計算)
   ↓ MySQL
[資料庫] iotv9.revenue_facts (交易固化)
   ↓ 
[前端] RealtimeController.php (期間統計)
```

---

## 二、交易分類標準 (Transaction Type)

所有入金與出金**均記錄於同一張表 `revenue_facts`**，透過 `transaction_type` 欄位區分：

| `transaction_type` 值 | 說明 | 業務場景 |
|-----------------------|------|----------|
| `credit_in` | 玩家入金 | 投幣、掃碼開分、遠端開分 |
| `credit_out` | 玩家出金 | 兌幣、洗分、退款 |

**關鍵原則**：
- ✅ 同一張表，不同 `transaction_type`
- ✅ `delta_value` **永遠是正數**（無論入金或出金）
- ❌ **禁止**用 `delta_value` 正負號區分入出金

---

## 三、Delta 計算邏輯 (Delta Calculation)

### 3.1 基礎概念

韌體發送的是**累積值 (Cumulative Value)**，類似里程表：
- `lifetime_credit_in`: 機台歷史總入金脈衝數（只增不減）
- `lifetime_credit_out`: 機台歷史總出金脈衝數（只增不減）

### 3.2 Delta 計算公式

```python
# listener.py 核心邏輯
last_cumulative = redis.get(f"last_credit_in:{chip_id}")  # 上次的累積值
current_cumulative = mqtt_payload["count"]                 # 當前累積值

delta_value = current_cumulative - last_cumulative         # 增量 (永遠 >= 0)

if delta_value > 0:
    # 寫入 revenue_facts
    INSERT INTO revenue_facts (
        chip_id, transaction_type, delta_value, amount, event_ts
    ) VALUES (
        chip_id, 'credit_in', delta_value, delta_value * pulse_ratio, NOW()
    )
    
    # 更新 Redis 基準線
    redis.set(f"last_credit_in:{chip_id}", current_cumulative)
```

### 3.3 首次啟動處理

當 Redis 中無 `last_cumulative` 時：
- **不寫入 revenue_facts**（避免將歷史累積誤認為當次交易）
- **僅設定 Redis 基準線**：`redis.set(f"last_credit_in:{chip_id}", current_cumulative)`

---

## 四、資料庫結構 (Database Schema)

### 4.1 `revenue_facts` 表

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | BIGINT PK | 主鍵 |
| `chip_id` | VARCHAR(64) | 設備硬體 ID |
| `transaction_type` | VARCHAR(20) | `credit_in` / `credit_out` |
| `device_id` | BIGINT | FK → machines.id (快照) |
| `venue_id` | BIGINT | FK → venues.id (快照) |
| `delta_value` | INT | 增量脈衝數 (永遠 > 0) |
| `amount` | DECIMAL(12,2) | 金額 = delta_value × pulse_ratio |
| `is_valid` | TINYINT(1) | 是否有效 (1=有效, 0=誤投) |
| `event_ts` | DATETIME | 事件發生時間 (UTC) |
| `created_at` | TIMESTAMP | 記錄創建時間 |

**索引**：
```sql
INDEX idx_chip_transaction (chip_id, transaction_type, event_ts)
INDEX idx_device_time (device_id, event_ts)
INDEX idx_venue_time (venue_id, event_ts)
```

---

## 五、期間統計查詢 (Period Statistics)

### 5.1 正確寫法

```sql
-- 期間入金
SELECT SUM(delta_value) as period_credit_in
FROM revenue_facts
WHERE chip_id = ?
  AND transaction_type = 'credit_in'
  AND event_ts BETWEEN ? AND ?
  AND is_valid = 1;

-- 期間出金
SELECT SUM(delta_value) as period_credit_out
FROM revenue_facts
WHERE chip_id = ?
  AND transaction_type = 'credit_out'
  AND event_ts BETWEEN ? AND ?
  AND is_valid = 1;

-- 期間淨收入
period_net = period_credit_in - period_credit_out
```

### 5.2 ❌ 錯誤寫法 (Ina 犯的錯誤)

```sql
-- ❌ 錯誤：企圖用 delta_value 正負號區分
WHERE delta_value > 0   -- 入金
WHERE delta_value < 0   -- 出金 (永遠撈不到，因為 delta_value 永遠 > 0)
```

---

## 六、WAW 2.0 架構變更

### 6.1 `machines` 表 (新)

WAW 2.0 引入 `machines` 表，取代舊的 `devices` 表用於營運管理：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | BIGINT PK | 主鍵 |
| `machine_owner_id` | BIGINT | FK → users.id (機台所有人) |
| `chip_id` | VARCHAR(50) UNIQUE | 硬體識別碼 |
| `name` | VARCHAR(100) | 機台名稱 |
| `type` | VARCHAR(50) | 機台類型 (claw, arcade, gambling) |
| `subscription_status` | ENUM | `active` / `arrears` / `suspended` |
| `pulse_to_display` | INT | 脈衝轉換率 (顯示用) |
| `pulse_to_token` | DECIMAL(10,2) | 脈衝轉換率 (金流用) |
| `lifetime_credit_in` | BIGINT | 歷史累計入金 |
| `lifetime_credit_out` | BIGINT | 歷史累計出金 |

### 6.2 與 `devices` 表的關係

- `devices`: 硬體資產管理（韌體版本、MQTT 通訊）
- `machines`: 營運管理（分潤、訂閱、財務統計）

---

## 七、命名權威 (Naming Authority)

本文件定義的所有命名，已註冊至 `brains/knowledge/NAMING_AUTHORITY.md`：

| 名稱 | 定義來源 |
|------|---------|
| `transaction_type` | 本文件 |
| `delta_value` | 本文件 |
| `is_valid` | 本文件 |
| `revenue_facts` | 本文件 |
| `machines` | 本文件 |
| `machine_owner_id` | 本文件 |
| `credit_in` | `02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` |
| `credit_out` | `02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` |

---

## 八、檢查清單 (Checklist)

修改涉及營收計算的程式碼時，必須確認：

- [ ] `transaction_type` 用於區分入出金，**不是** `delta_value` 正負號
- [ ] `delta_value` 永遠是正數，代表增量
- [ ] 期間統計使用 `WHERE transaction_type = 'credit_in/credit_out'`
- [ ] 首次啟動時只設 Redis 基準線，不寫 revenue_facts
- [ ] 欄位命名與本文件完全一致

---

## 🔗 文件神經連結

### 強關聯（必讀）
- `../../../NAMING_AUTHORITY.md` - 命名權威總索引
- `../../../02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - MQTT Payload 格式
- `../../../03_system_architecture/WAW_2.0_ARCHITECTURE_SPEC.md` - WAW 2.0 架構規範

### 中關聯（建議讀）
- `/Users/ilawusong/Documents/sysWawIot/tg25-infra/mqtt/scripts/listener.py` - Delta 計算實作
- `/Users/ilawusong/Documents/sysWawIot/waw-core/app/Models/MachineExtensions.php` - 期間統計實作

### 排除混淆
- `delta_value` ≠ 正負號區分入出金（永遠正數）
- `revenue_facts` ≠ 分表（入出金在同一表）

---

*維護者：HQ | 建立：2026-06-17 | 版本：1.0.0*
