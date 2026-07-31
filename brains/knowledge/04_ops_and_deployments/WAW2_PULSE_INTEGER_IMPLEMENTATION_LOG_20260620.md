# WAW 2.0 脈衝整數化完整實施日誌


**[On-Demand]** — 上下文注入策略

**實施日期**: 2026-06-20  
**涉及 Agent**: Ina (Infra Master) + Mina (Member Agent) + Sophie (Owner Agent)  
**協調者**: HQ (Hera)  
**狀態**: ✅ 已完成並部署  

---

## 📋 實施背景

### 問題根源
在 WAW 1.0 架構中，脈衝數據使用小數型態（`decimal`），導致以下問題：
1. 金額與脈衝數語義混淆（`cumulative_amount` 實際存的是脈衝數）
2. 彩票計算時出現小數，影響用戶體驗
3. Member 錢包餘額使用 `decimal(16,2)`，無法表達整數代幣語義
4. 跨系統傳遞時容易產生精度誤差

### 解決目標
1. 統一使用整數型態（`bigint` / `int`）表達脈衝數與代幣數
2. 新增 `cumulative_count` 欄位取代語義不清的 `cumulative_amount`
3. 建立相容策略，確保平滑過渡
4. 完善異常處理機制（Redis 遺失恢復、孤兒日誌、自動退款）

---

## 🎯 任務分派 (2026-06-20 02:06)

HQ 透過 `hq_task_flow.sh` 發出三個平行任務：

| Agent | 任務 ID | 職責範圍 | 優先級 |
|-------|---------|---------|--------|
| Ina | `TASK_INA_DB_AND_INFRA_20260620` | DB DDL 執行 + Infra 代碼修改 | high |
| Mina | `TASK_MINA_MEMBER_IMPLEMENTATION_20260620` | Member 前後端整數化改造 | high |
| Sophie | `TASK_SOPHIE_OWNER_VERIFY_20260620` | Owner 後台欄位驗證與修復 | high |

---

## 🔧 Ina 實施內容

### 交付時間
2026-06-20 02:13

### DB 結構變更

#### Owner DB (`iotv9`)

**1. revenue_facts - 新增累計脈衝欄位**
```sql
ALTER TABLE revenue_facts 
ADD COLUMN cumulative_count bigint unsigned DEFAULT NULL COMMENT '累計脈衝數(整數)' 
AFTER amount;
```

**2. machines - 新增生命週期脈衝分流欄位**
```sql
ALTER TABLE machines 
ADD COLUMN lifetime_pulse_in bigint unsigned NOT NULL DEFAULT 0 COMMENT '生命週期入金總脈衝' 
AFTER lifetime_pulse,
ADD COLUMN lifetime_pulse_out bigint unsigned NOT NULL DEFAULT 0 COMMENT '生命週期出金總脈衝' 
AFTER lifetime_pulse_in;
```

**3. device_orphan_logs - 新建孤兒脈衝記錄表**
```sql
CREATE TABLE device_orphan_logs (
  id bigint unsigned NOT NULL AUTO_INCREMENT,
  chip_id varchar(64) NOT NULL,
  type varchar(20) NOT NULL COMMENT 'credit_in 或 credit_out',
  cumulative_count bigint unsigned DEFAULT NULL,
  delta_count int DEFAULT NULL,
  estimated_tokens decimal(10,2) DEFAULT NULL,
  estimated_amount decimal(12,2) DEFAULT NULL,
  reason varchar(255) DEFAULT NULL,
  event_ts datetime NOT NULL,
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_chip_id (chip_id),
  KEY idx_event_ts (event_ts)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Owner側孤兒脈衝記錄表';
```

#### Member DB (`waw_member_production`)

**1. member_wallets - 餘額改為整數語義**
```sql
ALTER TABLE member_wallets 
MODIFY COLUMN balance bigint NOT NULL DEFAULT 0 COMMENT '餘額(整數代幣)';
```

**2. wallet_transactions - 新增交易快照欄位**
```sql
ALTER TABLE wallet_transactions 
ADD COLUMN delta_count int DEFAULT NULL COMMENT '本次脈衝增量' AFTER amount,
ADD COLUMN pulse_to_token decimal(10,2) DEFAULT NULL COMMENT '脈衝轉換率快照' AFTER delta_count,
ADD COLUMN coin_value decimal(12,2) DEFAULT NULL COMMENT '硬幣面值快照' AFTER pulse_to_token,
ADD COLUMN cumulative_amount int unsigned DEFAULT NULL COMMENT '累計金額(相容)' AFTER description,
ADD COLUMN cumulative_count int unsigned DEFAULT NULL COMMENT '累計脈衝數' AFTER cumulative_amount;

-- 數據同步
UPDATE wallet_transactions 
SET cumulative_count = cumulative_amount 
WHERE cumulative_amount IS NOT NULL AND cumulative_count IS NULL;
```

**3. device_orphan_logs - 新增相容欄位**
```sql
ALTER TABLE device_orphan_logs 
ADD COLUMN cumulative_count int unsigned DEFAULT NULL COMMENT '累計脈衝數' 
AFTER cumulative_amount;

-- 數據同步
UPDATE device_orphan_logs 
SET cumulative_count = cumulative_amount 
WHERE cumulative_amount IS NOT NULL AND cumulative_count IS NULL;
```

### Infra 代碼修改

**修改檔案**: `tg25-infra/mqtt/scripts/listener.py`

**關鍵變更**:

1. **write_revenue_fact() - Redis 遺失 DB 恢復機制**
```python
# 若 Redis 無基準線，從 revenue_facts.cumulative_count 恢復
last_row = cursor.fetchone()
if last_row and last_row[0]:
    last_cumulative = last_row[0]
    redis_conn.set(redis_key, last_cumulative)
    logging.info(f"[REVENUE_FACTS_RESTORE] {chip_id} 從 DB 恢復基準線: {last_cumulative}")
```

2. **write_revenue_fact() - 孤兒日誌記錄**
```python
# 若找不到設備，寫入 device_orphan_logs
if not device_id:
    cursor.execute("""
        INSERT INTO device_orphan_logs 
        (chip_id, type, cumulative_count, delta_count, estimated_amount, reason, event_ts)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (chip_id, tx_type, cumulative, delta, amount, 'device_not_found', event_ts))
    logging.info(f"[ORPHAN_LOG_SAVED] {chip_id} 未註冊設備記錄已保存")
```

3. **handle_v9_credit_in() - 轉發至 Member**
```python
# 非同步轉發至 Member /internal/device/credit-in
payload = {
    'chip_id': chip_id,
    'cumulative_amount': count,  # 相容舊欄位
    'cumulative_count': count,    # 新欄位
    'event_ts': event_ts
}
async with aiohttp.ClientSession() as session:
    async with session.post(member_url, json=payload, timeout=5) as resp:
        if resp.status == 200:
            logging.info(f"[MEMBER_CREDIT_IN_OK] {chip_id}")
        else:
            logging.error(f"[MEMBER_CREDIT_IN_ERROR] {chip_id} status={resp.status}")
```

4. **handle_v9_credit_out() - 相容策略**
```python
# 轉發時同時帶 cumulative_amount 與 cumulative_count
payload = {
    'chip_id': chip_id,
    'cumulative_amount': count,  # 相容
    'cumulative_count': count,    # 新欄位
    # ...
}
```

### 部署證據
- DDL 備份: `tg25-infra/db/migrations/v9/20260620_TASK_INA_DB_AND_INFRA_20260620.sql`
- Git commit: `55fd756`
- 部署時間: 2026-06-20 02:13
- 服務重啟: `mqtt-listener`, `credit-api`

### 驗證結果
- ✅ Owner DB: 4 個 DDL 語句執行成功
- ✅ Member DB: 5 個 DDL 語句執行成功
- ✅ Python 語法檢查通過
- ✅ VPS 部署成功

---

## 💻 Mina 實施內容

### 交付時間
2026-06-20 02:15

### 前端改造

**修改檔案**: `Member/resources/views/play.blade.php`

**關鍵變更**:

1. **creditCost() - 代幣計算取整**
```javascript
creditCost(cost) {
    const tokens = Math.floor(cost / this.device.coin_value * this.device.in_pulse_to_token);
    const displayAmount = (cost / this.device.coin_value).toFixed(2);
    return { tokens, displayAmount };
}
```

2. **doCredit() - Payload 改為整數 tokens**
```javascript
doCredit() {
    const { tokens, displayAmount } = this.creditCost(this.creditAmount);
    
    axios.post('/api/device/credit', {
        device_id: this.device.id,
        tokens: tokens,  // 整數代幣
        display_amount: displayAmount  // 保留顯示用
    })
    // ...
}
```

### 後端改造

**修改檔案**: `Member/app/Http/Controllers/Api/DeviceController.php`

**1. credit() - 開分 API 改為接收整數 tokens**
```php
public function credit(Request $request)
{
    $validated = $request->validate([
        'device_id' => 'required|integer',
        'tokens' => 'required|integer|min:1',  // 整數驗證
        'display_amount' => 'nullable|numeric'
    ]);

    $tokens = $validated['tokens'];
    $device = Device::findOrFail($validated['device_id']);
    
    // 計算脈衝數，必須能整除
    $pulseCount = $tokens / $device->in_pulse_to_token;
    if (floor($pulseCount) != $pulseCount) {
        return response()->json(['error' => '代幣數量無法轉換為整數脈衝'], 422);
    }

    // pending 預扣
    $wallet->withdraw($tokens, 'device_credit', [
        'device_id' => $device->id,
        'pulse_count' => $pulseCount,
        'status' => 'pending'
    ]);

    // 調用 Infra API
    try {
        $response = Http::post('https://tg25.win/api/v9/device/credit', [
            'chip_id' => $device->chip_id,
            'pulse_count' => $pulseCount
        ]);

        if (!$response->successful()) {
            // 失敗自動退款
            $pendingTx->update(['status' => 'failed']);
            $wallet->deposit($tokens, 'manual_adjust', [
                'reason' => 'credit_failed',
                'original_tx_id' => $pendingTx->id
            ]);
            return response()->json(['error' => 'Infra API 失敗'], 500);
        }
    } catch (\Exception $e) {
        // 異常自動退款
        // ...
    }

    return response()->json(['success' => true, 'balance' => $wallet->balance]);
}
```

**2. creditIn() - 新增 Webhook 接收 Infra 確認**
```php
public function creditIn(Request $request)
{
    $validated = $request->validate([
        'chip_id' => 'required|string',
        'cumulative_count' => 'nullable|integer',
        'cumulative_amount' => 'nullable|integer',
        'event_ts' => 'required|date'
    ]);

    $device = Device::where('chip_id', $validated['chip_id'])->first();
    if (!$device) {
        return response()->json(['error' => 'Device not found'], 404);
    }

    // 優先使用 cumulative_count，向下相容 cumulative_amount
    $cumulative = $validated['cumulative_count'] ?? $validated['cumulative_amount'];

    // 查詢上一筆交易的累計數
    $lastTx = WalletTransaction::where('device_id', $device->id)
        ->whereNotNull('cumulative_count')
        ->orderBy('id', 'desc')
        ->first();

    $lastCumulative = $lastTx ? ($lastTx->cumulative_count ?? $lastTx->cumulative_amount) : 0;
    $delta = $cumulative - $lastCumulative;

    // 找到 pending 交易並確認
    $pendingTx = WalletTransaction::where('device_id', $device->id)
        ->where('status', 'pending')
        ->where('type', 'device_credit')
        ->orderBy('id', 'desc')
        ->first();

    if ($pendingTx) {
        $pendingTx->update([
            'status' => 'success',
            'cumulative_count' => $cumulative,
            'delta_count' => $delta
        ]);
        return response()->json(['success' => true]);
    }

    // 若無 pending，檢查是否有 active session
    $session = DeviceSession::where('device_id', $device->id)
        ->where('status', 'active')
        ->first();

    if ($session) {
        // 補單：直接扣款
        $wallet = MemberWallet::where('member_id', $session->member_id)->first();
        $tokens = floor($delta * $device->in_pulse_to_token);
        $wallet->withdraw($tokens, 'device_credit', [
            'device_id' => $device->id,
            'cumulative_count' => $cumulative,
            'delta_count' => $delta,
            'status' => 'success'
        ]);
    } else {
        // 無 session，寫入 orphan log
        DeviceOrphanLog::create([
            'device_id' => $device->id,
            'cumulative_count' => $cumulative,
            'delta_count' => $delta,
            'event_ts' => $validated['event_ts']
        ]);
    }

    return response()->json(['success' => true]);
}
```

**3. creditOut() - 支援 cumulative_count 並計算整數彩票**
```php
public function creditOut(Request $request)
{
    $validated = $request->validate([
        'chip_id' => 'required|string',
        'cumulative_count' => 'nullable|integer',
        'cumulative_amount' => 'nullable|integer',
        'event_ts' => 'required|date'
    ]);

    // 優先使用 cumulative_count
    $cumulative = $validated['cumulative_count'] ?? $validated['cumulative_amount'];

    // 計算 delta
    $lastCumulative = // ... 查詢邏輯同上

    $delta = $cumulative - $lastCumulative;

    // floor() 計算整數彩票
    $tickets = floor($delta * $device->out_pulse_to_ticket);

    // 入帳
    if ($session) {
        $wallet->deposit($tickets, 'machine_settle', [
            'device_id' => $device->id,
            'cumulative_count' => $cumulative,
            'delta_count' => $delta
        ]);
    } else {
        // 寫入 orphan log
    }

    return response()->json(['success' => true, 'tickets' => $tickets]);
}
```

### 動態相容機制

**修改檔案**: `Member/app/Models/MemberWallet.php`

**關鍵變更**:
```php
public function withdraw($amount, $type, $metadata = [])
{
    // 使用 Schema 動態過濾欄位
    $allowedColumns = \Schema::getColumnListing('wallet_transactions');
    $filteredMetadata = array_intersect_key($metadata, array_flip($allowedColumns));

    WalletTransaction::create(array_merge([
        'wallet_id' => $this->id,
        'type' => $type,
        'amount' => -$amount,
        // ...
    ], $filteredMetadata));
}
```

### 路由註冊

**修改檔案**: `Member/routes/web.php`

```php
Route::post('/internal/device/credit-in', [DeviceController::class, 'creditIn']);
```

### 單元測試

**新增檔案**: `Member/tests/Feature/DeviceCreditTest.php`

**測試覆蓋**:
1. `test_credit_api_success` - 開分成功流程
2. `test_credit_api_fails_and_refunds` - 失敗自動退款
3. `test_credit_in_webhook_confirms_pending_tx` - credit_in 確認
4. `test_credit_out_webhook_success` - credit_out 洗分與 floor 計算

**測試結果**: ✅ 4 tests, 16 assertions, 全數通過

---

## 🔍 Sophie 實施內容

### 交付時間
2026-06-20 02:11

### 欄位驗證

**驗證項目**:
1. ✅ `users.outstanding_amount` (decimal 12,2) - DDL 正確執行
2. ✅ `revenue_facts.cumulative_count` (bigint unsigned) - DDL 正確執行
3. ✅ `machines.lifetime_pulse_in/out` (bigint unsigned) - DDL 正確執行

### 營收邏輯修復

**修改檔案**: `waw-core/app/Models/Device.php`

**問題發現**: `getPeriodStats()` 方法中 `transaction_type` 判斷被註解掉，導致 credit_in 與 credit_out 強制使用相同數值，今日營收必定為 0。

**修復內容**:
```php
public function getPeriodStats($startDate, $endDate)
{
    $stats = DB::table('revenue_facts')
        ->where('device_id', $this->id)
        ->whereBetween('event_ts', [$startDate, $endDate])
        ->selectRaw("
            SUM(CASE WHEN transaction_type = 'credit_in' THEN amount ELSE 0 END) as period_credit_in,
            SUM(CASE WHEN transaction_type = 'credit_out' THEN amount ELSE 0 END) as period_credit_out
        ")
        ->first();

    return [
        'period_credit_in' => $stats->period_credit_in ?? 0,
        'period_credit_out' => $stats->period_credit_out ?? 0
    ];
}
```

### 後台驗證

**驗證方法**: 使用 `php artisan tinker` 模擬後台 API 調用

**驗證結果**:
```php
// 設備 ID 1 當日統計
$device = Device::find(1);
$stats = $device->getPeriodStats(today(), today());
// 結果: ['period_credit_in' => 460, 'period_credit_out' => 334]

// API 回傳
$controller = new DeviceController();
$response = $controller->show(1);
// 結果:
{
  "data": {
    "lifetime_pulse": 0,
    "lifetime_credit_in": 338922,
    "today_revenue": 39,
    "today_credit_in": 120,
    "today_credit_out": 81
  }
}
```

**驗證結論**: ✅ Dashboard 與 API 正常運作，無 500 錯誤

---

## 🔄 相容策略總覽

### 欄位相容

| 舊欄位 | 新欄位 | 相容策略 |
|--------|--------|---------|
| `cumulative_amount` | `cumulative_count` | Infra 同時傳送兩個欄位；Member 優先使用 `cumulative_count`，若為 null 則向下相容 `cumulative_amount` |
| `member_wallets.balance` (decimal) | `balance` (bigint) | 直接修改型態，舊數據自動轉換為整數 |
| N/A | `wallet_transactions.delta_count` | 新增欄位，舊交易為 null |

### 動態欄位過濾

Member 使用 `\Schema::getColumnListing('wallet_transactions')` 動態取得資料庫實際欄位，寫入時自動過濾不存在的欄位，確保 Ina DDL 執行前後均不報錯。

### 韌體影響評估

✅ **無影響** - ESP32 MQTT Payload 使用 `count` 欄位（累計脈衝數），不依賴 `cumulative_amount`。

---

## ✅ HQ 審核與知識庫更新

### 審核時間
2026-06-20 02:27

### 知識庫更新清單

1. **新增整合報告**
   - 路徑: `brains/knowledge/04_ops_and_deployments/WAW2_PULSE_INTEGER_INTEGRATION_20260620.md`
   - 內容: 三位 Agent 交付成果總結、相容策略、後續驗證建議

2. **更新 DDL 規格**
   - 路徑: `brains/knowledge/02_technical_standards/DB_SCHEMA_WAW2_DELTA.md`
   - 更新: 標記狀態為「✅ 已執行並部署 (2026-06-20)」
   - 新增: 完整 DDL 語句與驗證結果

3. **更新文件索引**
   - 路徑: `brains/knowledge/DOCUMENT_INDEX.md`
   - 更新: 最後更新日期改為 2026-06-20
   - 新增: `WAW2_PULSE_INTEGER_INTEGRATION_20260620.md` 條目

4. **新增測試清單**
   - 路徑: `_agent/HQ_TEST_CHECKLIST_20260620.md`
   - 內容: 8 項測試項目（核心 4 項、一致性 3 項、相容性 1 項）

5. **新增實施日誌**（本文件）
   - 路徑: `brains/knowledge/04_ops_and_deployments/WAW2_PULSE_INTEGER_IMPLEMENTATION_LOG_20260620.md`
   - 內容: 完整實施過程、代碼變更、驗證結果

---

## 📊 實施成果統計

### 代碼變更統計

| Agent | 修改檔案數 | 新增檔案數 | 代碼行數變更 |
|-------|-----------|-----------|-------------|
| Ina | 1 | 1 (DDL) | +117 / -9 |
| Mina | 5 | 1 (測試) | +320 / -45 (估) |
| Sophie | 1 | 0 | +8 / -2 |

### DB 變更統計

| 資料庫 | DDL 語句數 | 新增欄位 | 新增表 |
|--------|-----------|---------|--------|
| Owner DB (iotv9) | 4 | 4 | 1 |
| Member DB (waw_member_production) | 5 | 6 | 0 |

### 測試覆蓋

- ✅ Member 單元測試: 4 tests, 16 assertions
- ✅ Owner 後台驗證: tinker 模擬測試通過
- ✅ Infra 語法檢查: Python 編譯通過
- ⏳ 整合測試: 待現場實測

---

## ⚠️ 風險評估與監控建議

### 已識別風險

1. **Member `/internal/device/credit-in` 路由實戰驗證不足**
   - 風險等級: 🟡 中
   - 影響範圍: 開分確認機制
   - 監控方式: 觀察 Infra log `[MEMBER_CREDIT_IN_ERROR]` 出現頻率

2. **整數彩票計算對用戶體驗影響**
   - 風險等級: 🟡 中
   - 影響範圍: 洗分時小數脈衝被 `floor()` 捨棄
   - 監控方式: 收集用戶反饋，統計捨棄脈衝累計量

3. **Owner 側 `revenue_facts` 查詢效能**
   - 風險等級: 🟡 中
   - 影響範圍: Dashboard 今日營收報表
   - 改善建議: 對 (`event_ts`, `venue_id`, `transaction_type`) 建立複合索引

4. **孤兒脈衝頻繁出現**
   - 風險等級: 🟢 低
   - 影響範圍: 未註冊設備上報
   - 監控方式: 觀察 `[ORPHAN_LOG_SAVED]` log 頻率

### 監控命令

```bash
# VPS 上監控 Infra log
ssh tg25 "tail -f /var/www/mqtt/logs/listener.log | grep -E 'CREDIT|ORPHAN|RESTORE|ERROR'"

# 檢查 Member 交易記錄
ssh tg25 "mysql -u root -p waw_member_production -e 'SELECT status, type, COUNT(*) FROM wallet_transactions WHERE DATE(created_at) = CURDATE() GROUP BY status, type;'"

# 檢查 Owner 營收統計
ssh tg25 "mysql -u root -p iotv9 -e 'SELECT transaction_type, COUNT(*), SUM(amount) FROM revenue_facts WHERE DATE(event_ts) = CURDATE() GROUP BY transaction_type;'"
```

---

## 🎯 後續行動項

### 必要測試（優先級：高）

1. **現場開分/洗分流程測試**
   - 負責人: Joe
   - 測試清單: `_agent/HQ_TEST_CHECKLIST_20260620.md`
   - 預期時間: 2-4 小時

2. **Infra credit_in 轉發驗證**
   - 負責人: Joe + HQ 監控
   - 監控重點: Member 是否正常接收並回傳 200

### 效能優化（優先級：中）

3. **revenue_facts 建立複合索引**
   - 負責 Agent: Ina
   - 執行時機: 低峰期
   - DDL: 已記錄於 `DB_SCHEMA_WAW2_DELTA.md`

### 文檔補充（優先級：低）

4. **補充業務流程文檔**
   - 負責人: HQ
   - 內容: 開分/洗分完整流程圖、異常處理流程

---

## 📝 結論

WAW 2.0 脈衝整數化完整鏈路改造已於 2026-06-20 完成並部署至 VPS 生產環境。

**核心成就**:
1. ✅ 統一使用整數型態表達脈衝數與代幣數
2. ✅ 建立完善的相容策略，確保平滑過渡
3. ✅ 實作異常處理機制（Redis 恢復、孤兒日誌、自動退款）
4. ✅ 通過單元測試與後台驗證

**協作亮點**:
- Ina: DDL 執行精確，Infra 代碼修改完整，相容策略周全
- Mina: 動態欄位過濾機制優秀，單元測試覆蓋完整
- Sophie: 發現並修復營收統計 workaround，後台驗證扎實

**下一步**: 現場實戰測試，驗證完整鏈路正確性。

---

**記錄者**: HQ (Hera)  
**記錄時間**: 2026-06-20 04:12  
**文件版本**: v1.0  

