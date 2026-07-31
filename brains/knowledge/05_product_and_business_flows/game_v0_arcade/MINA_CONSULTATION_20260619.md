# Mina 技術架構比對與諮詢報告


**[On-Demand]** — 上下文注入策略

> **日期**: 2026-06-19  
> **發起人**: HQ  
> **目的**: 確認 Member 系統的遊戲機開分/洗分實作細節

---

## 📌 背景說明

在與 Joe 討論遊戲機開分/洗分流程時，需要確認 Member 系統的實作細節，確保與設計文件一致。

**核心原則（已確認）**:
- ✅ **計數器脈衝是唯一真理來源**（硬體跳動，不可偽造）
- ✅ 會員餘額是「代幣數量」（整數）
- ✅ 代幣和分數都是「換算後的顯示單位」
- ✅ 採集數據分兩路：WebSocket 即時顯示 + 資料庫記錄

---

## 📊 現有實作確認（Member 系統）

### **已知的資料表**
1. `member_wallets` - 會員錢包
2. `wallet_transactions` - 交易流水
3. `device_sessions` - 遊戲機會話
4. `device_credit_logs` - 開分日誌（？）

### **已知的欄位（wallet_transactions）**
```php
'member_id',
'currency_type',           // COIN / TICKET
'amount',                  // DECIMAL(16,2)
'cumulative_amount',       // ✅ 已有（2026-05-13 新增）
'chip_id',                 // ✅ 已有（2026-05-13 新增）
'type',                    // ENUM
'reference_type',
'reference_id',
'description'
```

### **已知的 API**
- `POST /api/device/bind` - 掃碼綁定
- `POST /api/device/credit` - 會員開分
- `POST /api/device/unbind` - 結束遊戲
- `POST /internal/device/credit-in` - Infra 轉發入金（？）
- `POST /internal/device/credit-out` - Infra 轉發出金（？）

---

## ❓ 需要你確認的問題

### **Q1: 會員餘額的單位是什麼？**

**member_wallets 表**：
```php
'currency_type' => 'COIN',
'balance' => DECIMAL(16,2)
```

**問題**：
1. `currency_type = 'COIN'` 的 `balance` 單位是？
   - A. 代幣數量（例：50 = 50 枚代幣）
   - B. 金額（例：50 = 50 元）
   - C. 其他（請說明）

2. 為什麼用 `DECIMAL(16,2)` 而不是 `INT`？
   - 是否允許小數代幣（例：0.5 枚）？

3. 前端顯示給會員看的是：
   - A. 只顯示代幣數（例：「您的餘額：50 枚代幣」）
   - B. 顯示代幣 + 金額（例：「50 枚代幣 (500 元)」）
   - C. 只顯示金額（例：「您的餘額：500 元」）

---

### **Q2: wallet_transactions.cumulative_amount 存的是什麼？**

**已知**：
- 2026-05-13 新增了 `cumulative_amount` 欄位
- 設計文件說應該存「累計脈衝數」（里程表）

**問題**：
1. 目前 `cumulative_amount` 存的是：
   - A. 累計脈衝數（例：1050 = 計數器跳了 1050 次）
   - B. 累計金額（例：1050 = 累計 1050 元）
   - C. 累計代幣數（例：1050 = 累計 1050 枚代幣）
   - D. 其他（請說明）

2. 這個欄位是從哪裡來的？
   - A. Infra 透過 webhook 傳過來的
   - B. Member 自己計算的
   - C. ESP32 直接傳的

3. 有沒有同時記錄「增量」（delta）？
   - 例如：上一筆 1040，這一筆 1050，增量 = 10

---

### **Q3: 會員開分的流程是怎樣的？**

**場景**：會員點擊「開 10 代幣」

**問題**：
1. 目前的實作流程是：
   - A. 立即扣 10 代幣 → 發 MQTT → 等待確認
   - B. 先凍結 10 代幣 → 發 MQTT → 確認後才扣除
   - C. 先記錄待確認交易 → 發 MQTT → 確認後才扣代幣
   - D. 其他（請說明）

2. 有沒有 `status` 欄位來標記交易狀態？
   - 例如：`pending` / `confirmed` / `failed`

3. 如果 ESP32 回報的脈衝數不符合預期，怎麼處理？
   - 例如：預期 10 次，但只跳了 8 次

4. 如果 ESP32 超時未回報（例：30 秒），怎麼處理？

---

### **Q4: 洗分（credit-out）的流程是怎樣的？**

**場景**：會員點擊「洗分」按鈕

**問題**：
1. `/internal/device/credit-out` API 實作了嗎？
   - A. 已實作，正常運行
   - B. 已實作，但有 TODO 或註釋說未完成
   - C. 完全沒實作
   - D. 其他（請說明）

2. 如果已實作，收到 credit-out 後做什麼？
   - A. 計算增量 → TICKET 入帳 → 記錄交易
   - B. 直接用 Infra 傳來的金額入帳
   - C. 其他（請說明）

3. 如果收到 credit-out 但沒有 active session（孤兒分數），怎麼處理？
   - A. 回 422 錯誤
   - B. 回 200 但記錄孤兒 log
   - C. 忽略不處理
   - D. 其他（請說明）

---

### **Q5: 機台配置參數從哪裡取得？**

**開分時需要的參數**：
- `coin_to_pulse`：1 代幣觸發幾次脈衝（例：水果台 = 2）
- `coin_to_score`：1 代幣顯示多少分（例：彈珠台 = 100）
- `coin_value`：1 代幣等值多少元（例：10 元）

**問題**：
1. 這些參數目前存在哪裡？
   - A. Member DB 有自己的 `device_configs` 表
   - B. 跨庫查詢 Owner DB 的 `machines` 表
   - C. 從 Redis 快取讀取
   - D. 從 Infra API 取得
   - E. 其他（請說明）

2. 如果需要跨庫查詢，是否有性能問題？

3. 會員掃碼時，機台配置是：
   - A. 每次都重新查詢
   - B. 存在 session 中，綁定時查一次
   - C. 存在 Redis/LocalStorage，定期同步
   - D. 其他（請說明）

---

### **Q6: device_sessions 表的用途是什麼？**

**已知欄位**：
```php
'member_id',
'chip_id',
'node_id',
'status',                  // active / ended / timeout
'started_at',
'ended_at',
'last_activity_at'
```

**問題**：
1. `device_sessions` 有沒有存「累計脈衝數」？
   - 例如：`last_cumulative_in`、`last_cumulative_out`

2. 如果有，這個值是用來：
   - A. 計算 delta（本次增量）
   - B. 顯示給會員看（當前累計）
   - C. 其他（請說明）

3. 如果沒有，計算 delta 時是從哪裡取「上一次的累計值」？
   - A. 從 `wallet_transactions` 的最後一筆記錄
   - B. 從 Redis
   - C. 其他（請說明）

---

### **Q7: 前端開分按鈕的邏輯是什麼？**

**場景**：會員掃碼後看到機台頁面

**問題**：
1. 前端按鈕顯示的是：
   - A. 「1 代幣」、「5 代幣」、「10 代幣」
   - B. 「100 分」、「500 分」、「1000 分」
   - C. 「10 元」、「50 元」、「100 元」
   - D. 其他（請說明）

2. 點擊按鈕時，發送給後端的 payload 是：
   - A. `{ "tokens": 10 }`（代幣數量）
   - B. `{ "score": 1000 }`（分數）
   - C. `{ "amount": 100 }`（金額）
   - D. 其他（請說明）

3. 機台配置（`coin_to_pulse`、`coin_to_score`）存在：
   - A. LocalStorage（掃碼時取得）
   - B. 每次都向後端請求
   - C. 其他（請說明）

---

### **Q8: 有沒有「孤兒脈衝記錄表」？**

**場景**：ESP32 上報脈衝，但當時沒有 active session

**問題**：
1. 目前有沒有記錄孤兒脈衝的表或日誌？
   - A. 有專門的表（請提供表名和結構）
   - B. 記錄在一般日誌（log 檔案）
   - C. 完全不記錄
   - D. 其他（請說明）

2. 如果有記錄，是否計入營收統計？

---

## 📋 請提供的資訊

### **1. 完整的 API 路由列表**
```bash
# 請執行並提供結果
cd /path/to/Member
php artisan route:list | grep device
```

### **2. 資料庫表結構**
```bash
# 請提供這些表的完整結構（或 migration 檔案路徑）
- member_wallets
- wallet_transactions
- device_sessions
- device_credit_logs（如果存在）
- device_orphan_logs（如果存在）
```

### **3. 關鍵 Controller 代碼路徑**
```
請提供以下檔案的路徑（如果存在）：
- DeviceController.php（處理 bind/credit/unbind）
- InternalDeviceController.php（處理 Infra webhook）
- DeviceSessionController.php（管理 session）
```

### **4. Model 檔案路徑**
```
- MemberWallet.php
- WalletTransaction.php
- DeviceSession.php
```

---

## 🎯 回覆清單（請逐項回答）

- [ ] Q1: 會員餘額的單位？前端顯示方式？
- [ ] Q2: cumulative_amount 存的是什麼？如何計算？
- [ ] Q3: 會員開分的流程？有鎖定機制嗎？
- [ ] Q4: credit-out API 實作了嗎？孤兒分數怎麼處理？
- [ ] Q5: 機台配置參數從哪裡取得？
- [ ] Q6: device_sessions 存累計值嗎？
- [ ] Q7: 前端按鈕顯示什麼？payload 格式？
- [ ] Q8: 有孤兒脈衝記錄表嗎？

**補充說明**（如果有其他重要細節）:
```
（請在這裡填寫）
```

---

*準備者: HQ | 日期: 2026-06-19 | 待回覆: Mina*
