# Sophie 技術架構比對與諮詢報告


**[On-Demand]** — 上下文注入策略

> **日期**: 2026-06-19  
> **發起人**: HQ  
> **目的**: 比對現有實作與設計文件，確認遊戲機開分/洗分架構的統一規範

---

## 📊 現狀總覽

### **Owner 系統 (waw-core) - 你負責的部分**

#### 已實作的資料表
1. **`devices` 表**（舊版，尚未完全棄用）
2. **`machines` 表**（WAW 2.0，已建立）
3. **`revenue_facts` 表**（營收流水，已建立）

#### 已實作的欄位（machines 表）
```php
// /waw-core/database/migrations/2026_06_11_000001_create_machines_table.php
'pulse_to_display' => 100,        // ✅ 已有
'pulse_to_token' => 0.00,         // ✅ 已有
'out_pulse_to_ticket' => null,    // ✅ 已有
'lifetime_credit_in' => 0,        // ✅ 已有
'lifetime_credit_out' => 0,       // ✅ 已有
'lifetime_pulse' => 0,            // ✅ 已有
```

#### 已實作的欄位（revenue_facts 表）
```php
// /waw-core/app/Models/RevenueFact.php
'chip_id',
'transaction_type',        // ✅ 已有（credit_in / credit_out）
'device_id',
'venue_id',
'pulse_count',             // ✅ 已有
'pulse_ratio',             // ✅ 已有
'amount',                  // ✅ 已有
'cumulative_value',        // ✅ 已有
'delta_value',             // ✅ 已有
'is_valid',                // ✅ 已有
'event_ts',                // ✅ 已有
```

---

### **Member 系統 (Member) - Mina 負責的部分**

#### 已實作的資料表
1. **`member_wallets` 表**（會員錢包）
2. **`wallet_transactions` 表**（交易流水）
3. **`device_sessions` 表**（遊戲機會話）

#### 已實作的欄位（wallet_transactions 表）
```php
// /Member/database/migrations/
'member_id',
'currency_type',           // COIN / TICKET
'amount',                  // ✅ 已有
'cumulative_amount',       // ✅ 已有（2026-05-13 新增）
'chip_id',                 // ✅ 已有（2026-05-13 新增）
'type',                    // ENUM
'reference_type',
'reference_id',
'description'
```

#### 已實作的欄位（device_sessions 表）
```php
'member_id',
'chip_id',
'status',                  // active / ended / timeout
'started_at',
'ended_at',
'node_id',                 // ✅ 已有（2026-05-13 新增）
'last_activity_at'         // ✅ 已有（2026-05-13 新增）
```

---

## 🔴 發現的問題：命名不一致

### **問題 1：脈衝換算參數的命名方向不同**

| 位置 | 現有命名 | Joe 提出的命名 | 邏輯方向 |
|------|---------|---------------|---------|
| **machines 表** | `pulse_to_display` | `coin_to_score` | 反向 vs 正向 |
| **machines 表** | `pulse_to_token` | `coin_to_pulse` | 反向 vs 正向 |
| **文件** | `pulse_to_token` | `coin_to_pulse` | 反向 vs 正向 |

**範例對比**：
```
現有邏輯（反向）:
  pulse_to_display = 100 → 跳 1 下脈衝 = 顯示 100 分
  pulse_to_token = 1.00 → 跳 1 下脈衝 = 1 代幣

Joe 的邏輯（正向）:
  coin_to_pulse = 2 → 投 1 代幣 = 觸發 2 次脈衝
  coin_to_score = 100 → 投 1 代幣 = 顯示 100 分
```

**為什麼 Joe 的邏輯更合理**：
1. Owner 設定時更直觀：「這台機器投一枚幣會跳幾下？」
2. 計算代幣數時：`actual_coins = pulses / coin_to_pulse`（除法）
3. 現有邏輯：`actual_coins = pulses * pulse_to_token`（乘法，但 pulse_to_token 的語義是「每個脈衝等於多少代幣」，容易混淆）

---

### **問題 2：缺少 `coin_value` 欄位**

**Joe 說的核心事實**：
- 會員餘額是「代幣數量」（整數）
- 同一場地的所有機台使用統一代幣幣值（例：1 代幣 = 10 元）
- 幣值存在 `venues.token_value_twd`

**現有問題**：
- `machines` 表沒有 `coin_value` 欄位
- 每次計算金額時需要 JOIN `venues` 表
- 跨資料庫查詢（Member API 需要讀取 Owner DB）

**需要確認**：
- Q1: `coin_value` 是從 `venues.token_value_twd` 繼承（只讀），還是可以在機台層級覆寫？
- Q2: 是否需要在 `machines` 表快取 `coin_value`？

---

### **問題 3：累計值的命名不統一**

| 表 | 欄位名 | 語義 |
|----|--------|------|
| **machines** | `lifetime_credit_in` | 累計入金**金額**（元） |
| **machines** | `lifetime_pulse` | 累計脈衝數 |
| **revenue_facts** | `cumulative_value` | 累計值（但不清楚單位） |
| **revenue_facts** | `delta_value` | 增量值 |
| **wallet_transactions** | `cumulative_amount` | 累計金額（但 Joe 說應該是累計**脈衝數**） |

**Joe 的要求**：
```
累計值應該是「脈衝數」，不是「金額」：
  - ESP32 上報: count = 1050（累計脈衝數）
  - Infra 轉發: cumulative_count = 1050（累計脈衝數）
  - Member 存儲: cumulative_count = 1050（累計脈衝數）
  - 換算金額: amount = cumulative_count / coin_to_pulse * coin_value
```

**現有矛盾**：
- `lifetime_credit_in` 是金額（元），不是脈衝數
- `cumulative_value` 和 `delta_value` 的單位不明確

---

### **問題 4：缺少脈衝數欄位**

**revenue_facts 表有但不完整**：
```php
'pulse_count',             // ✅ 已有（但語義不明確）
'cumulative_value',        // ✅ 已有（但單位不明確）
'delta_value',             // ✅ 已有（但單位不明確）
```

**wallet_transactions 表缺少**：
```php
'cumulative_amount',       // ✅ 已有（但 Joe 說應該是 cumulative_count）
// ❌ 缺少: delta_count（增量脈衝數）
// ❌ 缺少: coin_to_pulse（配置快照）
// ❌ 缺少: coin_value（配置快照）
```

---

### **問題 5：會員餘額的單位不清楚**

**member_wallets 表**：
```php
'currency_type' => 'COIN',   // COIN 的語義是？
'balance' => DECIMAL(16,2)   // 是代幣數量？還是金額？
```

**Joe 的明確要求**：
- 會員餘額是「代幣數量」（整數，例：50 枚代幣）
- 前端顯示：「您的餘額：50 枚代幣」（不顯示金額）

**需要確認**：
- Q3: `member_wallets.balance` 的單位是代幣數量嗎？
- Q4: 為什麼用 `DECIMAL(16,2)` 而不是 `INT`？

---

## 🔴 發現的問題：邏輯矛盾

### **矛盾 1：累計值到底是什麼單位？**

**HARDWARE_PULSE_MAPPING.md 說**：
```
lifetime_credit_in: 歷史累計入金脈衝數
```

**machines 表註釋說**：
```sql
'lifetime_credit_in' => 0 COMMENT '累計開分金額（元）'
```

**矛盾**：一個說是脈衝數，一個說是金額（元）。

---

### **矛盾 2：`pulse_to_token` 的語義模糊**

**HARDWARE_PULSE_MAPPING.md 說**：
```
pulse_to_token = 1 → 1 脈衝 = 1 代幣
```

**但實際計算時**：
```
如果 pulse_to_token = 0.5
→ 1 脈衝 = 0.5 代幣？
→ 還是 2 脈衝 = 1 代幣？
```

**Joe 的邏輯**：
```
coin_to_pulse = 2 → 1 代幣 = 2 脈衝（清楚明確）
```

---

### **矛盾 3：InternalPulseController 沒有處理 credit-out**

**InternalPulseController.php**：
```php
public function creditOut(Request $request)
{
    // TODO: 實作 credit-out 脈衝處理邏輯
    // 目前 credit-out 由 Infra 直接寫入 revenue_facts
    return response()->json(['status' => 'not_implemented'], 501);
}
```

**GAME_V0_FLOW_AND_SESSION.md 說**：
```
洗分流程：
  ESP32 → Infra → Member API (/internal/device/credit-out)
  → Member 計算 delta → 彩票入帳
```

**矛盾**：文件說 Member 要處理，但代碼說 Infra 直接寫。

---

## ✅ Joe 提出的新需求總結

### **1. 統一命名：改用正向邏輯**

| 舊命名 | 新命名 | 說明 |
|--------|--------|------|
| `pulse_to_display` | `coin_to_score` | 1 代幣顯示多少分 |
| `pulse_to_token` | `coin_to_pulse` | 1 代幣觸發幾次脈衝 |
| - | `coin_value` | 1 代幣等值多少元（從 venues 繼承） |

### **2. 累計值統一為脈衝數**

| 表 | 新欄位 | 說明 |
|----|--------|------|
| `machines` | `lifetime_credit_in` → 改註釋為「累計入金脈衝數」 | 不是金額 |
| `machines` | `lifetime_credit_out` → 改註釋為「累計出金脈衝數」 | 不是金額 |
| `wallet_transactions` | `cumulative_count` | 累計脈衝數（里程表） |
| `wallet_transactions` | `delta_count` | 增量脈衝數（本次跳動） |

### **3. 新增配置快照欄位**

**wallet_transactions 表需要新增**：
```sql
ALTER TABLE wallet_transactions 
ADD COLUMN delta_count INT COMMENT '增量脈衝數';

ALTER TABLE wallet_transactions 
ADD COLUMN coin_to_pulse INT COMMENT '當時的換算比例（配置快照）';

ALTER TABLE wallet_transactions 
ADD COLUMN coin_value DECIMAL(10,2) COMMENT '當時的代幣幣值（配置快照）';
```

**為什麼需要配置快照**：
- 如果 Owner 修改了 `coin_to_pulse` 或 `coin_value`
- 歷史交易記錄需要知道「當時」的換算比例
- 才能正確審計和重新計算歷史營收

### **4. 新增交易狀態欄位（支援鎖定機制）**

**wallet_transactions 表需要新增**：
```sql
ALTER TABLE wallet_transactions 
ADD COLUMN status ENUM('pending','confirmed','failed') DEFAULT 'confirmed';
```

**流程**：
```
會員點擊「開 10 代幣」
  → 建立 status='pending' 交易
  → 扣除 10 代幣（或凍結）
  → 發 MQTT 給 ESP32
  → 等待 ESP32 回報脈衝數
  → 如果脈衝數正確：status='confirmed'
  → 如果脈衝數不符或超時：status='failed'，退款
```

### **5. 新增孤兒脈衝記錄表**

**需要新建表**：
```sql
CREATE TABLE device_orphan_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    chip_id VARCHAR(64) NOT NULL,
    type ENUM('credit_in', 'credit_out') NOT NULL,
    cumulative_count BIGINT NOT NULL COMMENT '累計脈衝數',
    delta_count INT NOT NULL COMMENT '增量脈衝數',
    estimated_tokens DECIMAL(10,2) COMMENT '估算代幣數',
    estimated_amount DECIMAL(10,2) COMMENT '估算金額',
    reason VARCHAR(255) COMMENT '孤兒原因',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_chip_time (chip_id, created_at)
);
```

**場景**：ESP32 上報了計數器跳動，但當時沒有 active session（會員已離開）。

---

## ❓ 需要你回答的問題

### **Q1: 命名要不要統一改成正向邏輯？**

**選項 A**：保持現有命名（`pulse_to_token`, `pulse_to_display`）
- 優點：不需要改代碼
- 缺點：Owner 設定時不直觀

**選項 B**：改用正向命名（`coin_to_pulse`, `coin_to_score`）
- 優點：更直觀，避免混淆
- 缺點：需要修改代碼、遷移資料

**你的選擇**：A / B / 其他建議？

---

### **Q2: `lifetime_credit_in` 到底是脈衝數還是金額？**

**現狀**：
- 註釋說「金額（元）」
- 文件說「脈衝數」

**選項 A**：改成脈衝數
```sql
ALTER TABLE machines MODIFY COLUMN 
lifetime_credit_in BIGINT COMMENT '累計入金脈衝數';
```

**選項 B**：保持金額，但新增 `lifetime_pulse_in`
```sql
ALTER TABLE machines ADD COLUMN 
lifetime_pulse_in BIGINT DEFAULT 0 COMMENT '累計入金脈衝數';
```

**你的選擇**：A / B？

---

### **Q3: `coin_value` 要不要存在 machines 表？**

**選項 A**：不存，每次從 `venues.token_value_twd` JOIN 取得
- 優點：單一數據來源
- 缺點：跨庫查詢（Member API 需要讀 Owner DB）

**選項 B**：快取在 `machines` 表，從 `venues` 繼承
- 優點：查詢效率高
- 缺點：需要同步機制

**選項 C**：允許單台機器覆寫
- 優點：彈性最高
- 缺點：違反「同一場地統一幣值」的原則

**你的選擇**：A / B / C？

---

### **Q4: 營收統計用哪種方式？**

**選項 A**：用脈衝數重新計算（Joe 推薦）
```sql
SELECT SUM(delta_count) / d.coin_to_pulse * d.coin_value as revenue
FROM wallet_transactions t
JOIN machines d ON t.chip_id = d.chip_id
WHERE ...
```

**選項 B**：直接加總 `amount` 欄位
```sql
SELECT SUM(amount) as revenue FROM wallet_transactions WHERE ...
```

**你的選擇**：A / B？

---

### **Q5: 交易鎖定機制要不要加 `frozen_balance`？**

**選項 A**：只用 `status='pending'`
- 扣款後記錄 pending
- 失敗時退款

**選項 B**：新增 `frozen_balance` 欄位
- 先凍結代幣
- 確認後才扣除

**你的選擇**：A / B？

---

### **Q6: 孤兒脈衝需要記錄嗎？**

**需要** / **不需要**？

如果需要，是否計入營收統計？

---

## 📋 建議的修改方案（待你確認）

### **方案 A：最小修改**
1. 只修改註釋，不改欄位名稱
2. 補充缺失的欄位（`delta_count`, `status`, 配置快照）
3. 新增 `device_orphan_logs` 表

### **方案 B：完整重構**
1. 改用正向命名（`coin_to_pulse`, `coin_to_score`）
2. 統一累計值為脈衝數
3. 補充所有缺失欄位
4. 更新所有相關代碼

**你傾向哪個方案？**

---

## 🎯 下一步行動（等你回覆後）

1. **你回答 Q1-Q6**
2. **HQ 更新所有規範文件**（NAMING_AUTHORITY, TECHNICAL_NAMING, HARDWARE_PULSE_MAPPING 等）
3. **HQ 生成 Migration 腳本**（給你和 Mina）
4. **HQ 派發任務**：
   - Sophie: 修改 Owner 後台的機台設定介面
   - Mina: 修改 Member API 的開分/洗分邏輯
   - Ina: 修改 Infra Listener 的數據轉發邏輯

---

*準備者: HQ | 日期: 2026-06-19 | 待回覆: Sophie*
