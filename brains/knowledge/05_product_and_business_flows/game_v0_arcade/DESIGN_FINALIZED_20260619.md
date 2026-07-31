# 遊戲機開分/洗分架構設計定稿通知


**[On-Demand]** — 上下文注入策略

> **日期**: 2026-06-19  
> **發起人**: HQ  
> **狀態**: 🔴 設計定稿，準備實作

---

## 📋 背景

經過與 Joe 的討論，以及 Sophie、Mina、Ina 三方的技術諮詢回覆，我們已經完成遊戲機開分/洗分架構的**最終設計拍板**。

---

## ✅ 最終決策總結

### **1. 命名規範**
- ✅ **保持現有命名**：`pulse_to_token`、`pulse_to_display`（不改成 `coin_to_pulse`）
- ✅ **理由**：符合現有技術文件、避免破壞性變更、三方系統已實作

### **2. 累計值單位**
- ✅ **只存脈衝數**：`cumulative_count` 和 `delta_count` 都是脈衝數（不是金額）
- ✅ **金額是換算結果**：統計時直接加總 `amount` 欄位（快照存儲）

### **3. 代幣必須為整數**
- 🔴 **重要變更**：會員餘額 `balance` 必須改為 `INT`（目前是 `DECIMAL(16,2)`）
- ✅ **理由**：代幣是實體單位，不允許小數（例：不可能有 0.5 枚代幣）

### **4. 快照存儲 (Snapshot)**
- ✅ **每筆交易必須記錄配置快照**：
  - `pulse_to_token` (當時的脈衝比例)
  - `coin_value` (當時的代幣幣值)
- ✅ **理由**：即使未來配置變更，歷史交易仍可正確審計

### **5. 前端 Payload 調整**
- 🔴 **需要修改**：前端開分按鈕改送 `tokens`（代幣數），不送 `display_amount`（分數）
- ✅ **理由**：簡化後端計算，避免除法誤差

### **6. 交易狀態鎖定**
- ✅ **採用預扣模式**：`status='pending'` → 確認後改 `confirmed`
- ✅ **不需要 `frozen_balance`**：簡化邏輯

---

## 📚 已更新的規範文件

### **新增文件**
1. ✅ `brains/knowledge/02_protocols_and_standards/PULSE_BASED_DATA_FLOW.md`
   - 完整的數據流規範
   - 包含 SQL 表結構、API Payload、Delta 計算邏輯

### **更新文件**
2. ✅ `brains/knowledge/NAMING_AUTHORITY.md`
   - 新增「脈衝與代幣換算體系」章節
   - 明確標註代幣為整數

---

## 🎯 下一步：實作任務分配

### **Sophie (Owner 系統)**

#### 任務 1：新增脈衝累計欄位
```sql
ALTER TABLE machines 
ADD COLUMN lifetime_pulse_in BIGINT UNSIGNED DEFAULT 0 
COMMENT '累計入金脈衝數' AFTER lifetime_credit_in;

ALTER TABLE machines 
ADD COLUMN lifetime_pulse_out BIGINT UNSIGNED DEFAULT 0 
COMMENT '累計出金脈衝數' AFTER lifetime_credit_out;
```

#### 任務 2：新增孤兒脈衝記錄表
```sql
CREATE TABLE device_orphan_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    chip_id VARCHAR(50) NOT NULL,
    type ENUM('credit_in', 'credit_out') NOT NULL,
    cumulative_count BIGINT UNSIGNED NOT NULL,
    delta_count INT NOT NULL,
    estimated_tokens INT NULL,
    estimated_amount INT NULL,
    reason VARCHAR(255) NULL,
    event_ts TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_chip_time (chip_id, event_ts)
);
```

#### 任務 3：確認 revenue_facts 欄位語義
- 確認 `cumulative_value` 和 `delta_value` 的單位是脈衝數還是金額
- 如果是金額，考慮是否需要新增 `cumulative_pulse` 和 `delta_pulse` 欄位

---

### **Mina (Member 系統)**

#### 任務 1：修改代幣餘額為整數 🔴
```sql
-- 警告：這是破壞性變更，需要數據遷移
ALTER TABLE member_wallets 
MODIFY COLUMN balance INT NOT NULL DEFAULT 0 
COMMENT '代幣餘額（整數，不可小數）';
```

**遷移策略**：
```php
// 遷移前檢查是否有小數餘額
$hasDecimals = DB::table('member_wallets')
    ->whereRaw('balance != FLOOR(balance)')
    ->exists();

if ($hasDecimals) {
    // 選項 A：無條件捨去
    DB::table('member_wallets')
        ->update(['balance' => DB::raw('FLOOR(balance)')]);
    
    // 選項 B：四捨五入
    DB::table('member_wallets')
        ->update(['balance' => DB::raw('ROUND(balance)')]);
}
```

#### 任務 2：新增交易快照欄位
```sql
ALTER TABLE wallet_transactions 
ADD COLUMN delta_count INT NULL 
COMMENT '增量脈衝數（本次跳動）';

ALTER TABLE wallet_transactions 
ADD COLUMN pulse_to_token DECIMAL(10,4) NULL 
COMMENT '當時的脈衝比例（配置快照）';

ALTER TABLE wallet_transactions 
ADD COLUMN coin_value INT NULL 
COMMENT '當時的代幣幣值（配置快照）';

-- 修改 tokens 為整數
ALTER TABLE wallet_transactions 
MODIFY COLUMN tokens INT NOT NULL 
COMMENT '代幣數量（整數）';

-- 修改 amount 為整數
ALTER TABLE wallet_transactions 
MODIFY COLUMN amount INT NOT NULL 
COMMENT '金額（元）';
```

#### 任務 3：修改前端 Payload
**檔案**: `resources/views/play.blade.php`

**修改前**：
```javascript
// 傳送分數
POST /api/device/credit {
  chip_id: "xxx",
  display_amount: 1000  // 分數
}
```

**修改後**：
```javascript
// 傳送代幣數
POST /api/device/credit {
  chip_id: "xxx",
  tokens: 10  // 代幣數量（整數）
}
```

#### 任務 4：確認孤兒脈衝表
- 已有 `device_orphan_logs` 表（根據你的回報）
- 確認欄位是否符合新規範（`delta_count`、`estimated_tokens` 為整數）

---

### **Ina (Infra 系統)**

#### 任務 1：確認 MQTT Payload 格式
根據你的回報，ESP32 上報格式是：
```json
{
  "type": "credit_in",
  "count": 1052,  // 累計脈衝數
  "timestamp": "..."
}
```

✅ 這個格式**符合規範**，不需要修改。

#### 任務 2：確認轉發給 Member 的 Payload
請確認目前轉發的格式是否為：
```json
POST /internal/device/credit-in
{
  "chip_id": "aabbcc112233",
  "cumulative_count": 1052,  // 累計脈衝數
  "timestamp": "..."
}
```

如果欄位名是 `cumulative_amount`，請改為 `cumulative_count`（統一命名）。

#### 任務 3：WebSocket 推送（選做）
目前 WebSocket 是禁用狀態。如果未來要啟用，推送格式應為：
```json
{
  "chip_id": "aabbcc112233",
  "type": "credit_in",
  "cumulative_count": 1052,
  "delta_count": 2,
  "display_tokens": 1,      // 換算代幣（顯示用）
  "display_score": 100      // 換算分數（顯示用）
}
```

---

## ⚠️ 重點注意事項

### **1. 代幣小數處理**
在計算代幣時，必須使用 `floor()` 取整：
```php
$tokens = (int) floor($deltaCount * $pulseToToken);
```

### **2. 數據遷移**
- `member_wallets.balance`：從 DECIMAL 改 INT，需要遷移現有數據
- `wallet_transactions.tokens`：從 DECIMAL 改 INT，需要遷移現有數據

### **3. 配置快照**
從現在開始，所有新建的交易記錄都必須包含：
- `delta_count`（增量脈衝數）
- `pulse_to_token`（配置快照）
- `coin_value`（配置快照）

---

## 📅 時程安排

1. **今天 (2026-06-19)**：收到本通知，閱讀新規範
2. **明天 (2026-06-20)**：回報「是否有技術問題或疑問」
3. **後天 (2026-06-21)**：HQ 生成完整的 Migration 腳本
4. **下週開始**：依序執行實作與測試

---

## 🔗 規範文件連結

- 📘 `brains/knowledge/02_protocols_and_standards/PULSE_BASED_DATA_FLOW.md`
- 📘 `brains/knowledge/NAMING_AUTHORITY.md`
- 📘 `brains/knowledge/02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md`

---

**請在 24 小時內回報「已閱讀並理解」或「有技術疑問」。** 🎯

*發送者: HQ | 日期: 2026-06-19*
