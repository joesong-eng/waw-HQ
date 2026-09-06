# 以脈衝為核心的數據流規範 (Pulse-Based Data Flow Specification)


**[On-Demand]** — 上下文注入策略

> **版本**: 1.0.0  
> **建立日期**: 2026-06-19  
> **狀態**: 🔴 權威定義  
> **維護者**: HQ  
> **核心原則**: 脈衝是物理真理，代幣為整數，金額為換算結果

---

## 📌 核心原則

### 1. 脈衝即真理 (Pulse is Truth)
- ESP32 採集的計數器脈衝是**唯一可信數據源**
- 所有金額、代幣、分數都是「脈衝」的**換算顯示**
- 資料庫必須存儲原始脈衝數，換算比例以「快照 (Snapshot)」形式同時存儲

### 2. 代幣必須為整數 (Tokens are Integers)
- 會員餘額只能是整數代幣（例：50 枚，不可 50.5 枚）
- 所有涉及代幣的欄位使用 `INT` 或 `INTEGER`
- ❌ 禁止：`DECIMAL(16,2)` 用於代幣數量

### 3. 快照存儲 (Snapshot Storage)
- 每筆交易必須記錄「當時的換算比例」
- 即使未來配置變更，歷史交易仍可正確審計

---

## 🔄 完整數據流

```
┌─────────────┐
│   會員手機   │ 點擊「1 代幣」按鈕
└──────┬──────┘
       │ POST /api/device/credit { "tokens": 1 }
       ▼
┌─────────────────────────────────────────┐
│  Member API (Mina)                      │
│  1. 查配置: pulse_to_token = 0.5        │
│  2. 計算脈衝: 1 / 0.5 = 2 次            │
│  3. 預扣代幣: -1 枚 (status=pending)    │
│  4. 請求 Infra 觸發                     │
└──────┬──────────────────────────────────┘
       │ POST /api/device/trigger-pulse { "count": 2 }
       ▼
┌─────────────────────────────────────────┐
│  Infra API (Ina)                        │
│  發布 MQTT: device/{chip_id}/cmd        │
│  { "command": "assign_credit",          │
│    "params": { "count": 2 } }           │
└──────┬──────────────────────────────────┘
       │ MQTT 指令
       ▼
┌─────────────────────────────────────────┐
│  ESP32 韌體 (Coli)                      │
│  1. 觸發 PIN_OUT1 開分按鈕 2 次         │
│  2. 遊戲機計數器跳動 2 下               │
│  3. 採集計數器：累計值 = 1052           │
│  4. 上報 MQTT                           │
└──────┬──────────────────────────────────┘
       │ device/{chip_id}/data
       │ { "type": "credit_in", "count": 1052 }
       ▼
┌─────────────────────────────────────────┐
│  Infra Listener (Ina)                   │
│  1. 計算 delta: 1052 - 1050 = 2         │
│  2. 寫入 revenue_facts (Owner DB)       │
│  3. 轉發 Member Webhook                 │
└──────┬──────────────────────────────────┘
       │ POST /internal/device/credit-in
       │ { "chip_id": "xxx",
       │   "cumulative_count": 1052 }
       ▼
┌─────────────────────────────────────────┐
│  Member Webhook (Mina)                  │
│  1. 查上次累計值: 1050                  │
│  2. 計算 delta: 1052 - 1050 = 2         │
│  3. 換算代幣: 2 * 0.5 = 1 枚            │
│  4. 確認交易: status = confirmed        │
│  5. 記錄快照:                           │
│     - delta_count = 2 (脈衝)            │
│     - tokens = 1 (代幣)                 │
│     - amount = 10 (金額)                │
│     - pulse_to_token = 0.5 (快照)       │
│     - coin_value = 10 (快照)            │
└─────────────────────────────────────────┘
```

---

## 📊 資料庫表結構

### **wallet_transactions 表（Member DB）**

```sql
CREATE TABLE wallet_transactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    member_id BIGINT NOT NULL COMMENT '會員 ID',
    chip_id VARCHAR(64) NULL COMMENT '機台晶片 ID',
    
    -- ===== 原始脈衝數據（物理真理）=====
    cumulative_count BIGINT NULL COMMENT '累計脈衝數（里程表）',
    delta_count INT NULL COMMENT '增量脈衝數（本次跳動）',
    
    -- ===== 換算數據（業務單位）=====
    tokens INT NOT NULL COMMENT '代幣數量（整數，不可小數）',
    amount INT NOT NULL COMMENT '金額（元）= tokens * coin_value',
    
    -- ===== 配置快照（審計用）=====
    pulse_to_token DECIMAL(10,4) NULL COMMENT '當時的脈衝比例（快照）',
    coin_value INT NULL COMMENT '當時的代幣幣值（快照）',
    
    -- ===== 交易狀態 =====
    status ENUM('pending','confirmed','failed') DEFAULT 'confirmed' 
        COMMENT '交易狀態（支援預扣確認機制）',
    
    type VARCHAR(50) NOT NULL COMMENT '交易類型',
    currency_type VARCHAR(20) NOT NULL COMMENT 'COIN / TICKET',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_member (member_id, created_at),
    INDEX idx_chip_cumulative (chip_id, cumulative_count),
    INDEX idx_status (status)
) COMMENT '交易流水表（以脈衝為核心）';
```

### **member_wallets 表（Member DB）**

```sql
CREATE TABLE member_wallets (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    member_id BIGINT NOT NULL,
    currency_type VARCHAR(20) NOT NULL COMMENT 'COIN / TICKET',
    
    -- ✅ 必須為整數
    balance INT NOT NULL DEFAULT 0 COMMENT '代幣餘額（整數，不可小數）',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_member_currency (member_id, currency_type)
) COMMENT '會員錢包表（代幣為整數）';
```

### **device_orphan_logs 表（Member DB）**

```sql
CREATE TABLE device_orphan_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    chip_id VARCHAR(64) NOT NULL,
    type ENUM('credit_in', 'credit_out') NOT NULL,
    
    -- ===== 原始脈衝數據 =====
    cumulative_count BIGINT NOT NULL COMMENT '累計脈衝數',
    delta_count INT NOT NULL COMMENT '增量脈衝數',
    
    -- ===== 估算數據（統計用）=====
    estimated_tokens INT NULL COMMENT '估算代幣數',
    estimated_amount INT NULL COMMENT '估算金額',
    
    reason VARCHAR(255) NULL COMMENT '孤兒原因（例：no_session）',
    event_ts TIMESTAMP NOT NULL COMMENT '事件發生時間',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_chip_time (chip_id, event_ts),
    INDEX idx_type (type)
) COMMENT '孤兒脈衝記錄表';
```

---

## 📡 API Payload 標準

### **前端 → Member: 開分請求**

```json
POST /api/device/credit
{
  "chip_id": "aabbcc112233",
  "tokens": 1  // ✅ 直接傳代幣數（整數），不傳分數
}
```

### **Member → Infra: 觸發脈衝**

```json
POST /api/device/trigger-pulse
{
  "chip_id": "aabbcc112233",
  "count": 2  // 計算後的脈衝次數 = tokens / pulse_to_token
}
```

### **ESP32 → Infra: 上報脈衝**

```json
device/{chip_id}/data
{
  "type": "credit_in",
  "count": 1052,  // 累計脈衝數（里程表）
  "timestamp": "2026-06-19T10:45:00Z"
}
```

### **Infra → Member: 轉發脈衝**

```json
POST /internal/device/credit-in
{
  "chip_id": "aabbcc112233",
  "cumulative_count": 1052,  // ✅ 完整傳遞累計值
  "timestamp": "2026-06-19T10:45:00Z"
}
```

---

## 🎯 關鍵邏輯：Delta 計算與快照存儲

### **Delta 計算（Member 端）**

```php
// 查詢上次累計值
$lastTx = WalletTransaction::where('chip_id', $chipId)
    ->whereNotNull('cumulative_count')
    ->orderBy('created_at', 'desc')
    ->first();

$lastCumulative = $lastTx ? $lastTx->cumulative_count : 0;
$currentCumulative = $request->input('cumulative_count');
$deltaCount = $currentCumulative - $lastCumulative;

if ($deltaCount <= 0) {
    // 重複上報或異常，忽略
    return response()->json(['status' => 'no_change']);
}

// 查詢當前機台配置
$device = $this->fetchDeviceInfo($chipId);
$pulseToToken = $device['pulse_to_token'];
$coinValue = $device['coin_value'];

// 換算代幣與金額
$tokens = (int) floor($deltaCount * $pulseToToken);  // ✅ 取整數
$amount = $tokens * $coinValue;

// 記錄交易（含快照）
WalletTransaction::create([
    'member_id' => $session->member_id,
    'chip_id' => $chipId,
    'cumulative_count' => $currentCumulative,  // 累計脈衝
    'delta_count' => $deltaCount,              // 增量脈衝
    'tokens' => $tokens,                       // 代幣數（整數）
    'amount' => $amount,                       // 金額
    'pulse_to_token' => $pulseToToken,         // 快照
    'coin_value' => $coinValue,                // 快照
    'type' => 'machine_settle',
    'currency_type' => 'TICKET',
    'status' => 'confirmed'
]);
```

---

## 📈 營收統計查詢

### **按機台統計期間營收**

```sql
-- ✅ 直接加總 amount（快速）
SELECT 
    chip_id,
    SUM(amount) as total_revenue
FROM wallet_transactions
WHERE type = 'machine_settle'
  AND created_at BETWEEN '2026-06-01' AND '2026-06-30'
  AND status = 'confirmed'
GROUP BY chip_id;
```

### **驗證脈衝數與金額的一致性**

```sql
-- 用於審計：重新計算金額
SELECT 
    chip_id,
    SUM(delta_count) as total_pulses,
    SUM(amount) as recorded_amount,
    SUM(delta_count * pulse_to_token * coin_value) as calculated_amount
FROM wallet_transactions
WHERE type = 'machine_settle'
  AND created_at BETWEEN '2026-06-01' AND '2026-06-30'
GROUP BY chip_id
HAVING recorded_amount != calculated_amount;  -- 找出不一致的記錄
```

---

## ⚠️ 重要注意事項

### 1. 代幣小數處理
**問題**：如果 `deltaCount * pulseToToken` 產生小數怎麼辦？

**解決**：
```php
$tokens = (int) floor($deltaCount * $pulseToToken);  // 無條件捨去
```

**原因**：代幣必須為整數，零頭忽略不計（符合實體代幣邏輯）。

### 2. 首次啟動處理
**場景**：Redis 無 `last_pulse`，且資料庫無該機台記錄。

**處理**：
```php
if ($lastCumulative == 0 && $currentCumulative > 0) {
    // 首次啟動，只設定基準線，不入帳
    WalletTransaction::create([
        'cumulative_count' => $currentCumulative,
        'delta_count' => 0,
        'tokens' => 0,
        'type' => 'baseline'
    ]);
    return response()->json(['status' => 'baseline_set']);
}
```

### 3. 累計值回退檢測
**場景**：ESP32 重啟後累計值歸零。

**處理**：
```php
if ($currentCumulative < $lastCumulative) {
    Log::warning('Cumulative value reset detected', [
        'chip_id' => $chipId,
        'last' => $lastCumulative,
        'current' => $currentCumulative
    ]);
    // 選項 A：視為新基準線
    // 選項 B：拒絕處理，等人工確認
}
```

---

## 🔗 文件神經連結

### 強關聯（必讀）
- `../NAMING_AUTHORITY.md` - 變數命名權威定義
- `TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - API Payload 格式
- `../../05_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md` - 業務流程

### 中關聯（建議讀）
- `HARDWARE_PULSE_MAPPING.md` - 硬體脈衝映射
- `../../05_business_flows/waw2_migration/REVENUE_DATA_FLOW_SPEC.md` - 營收數據流

---

*制定者：HQ | 版本：1.0.0 | 日期：2026-06-19*
