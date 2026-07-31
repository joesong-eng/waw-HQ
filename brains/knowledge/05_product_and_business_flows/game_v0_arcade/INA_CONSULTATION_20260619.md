# Ina 技術架構比對與諮詢報告


**[On-Demand]** — 上下文注入策略

> **日期**: 2026-06-19  
> **發起人**: HQ  
> **目的**: 確認 Infra 系統的 MQTT Listener 和數據轉發實作細節

---

## 📌 背景說明

在與 Joe 討論遊戲機開分/洗分流程時，需要確認 Infra 系統的數據流實作細節，確保與設計文件一致。

**核心原則（已確認）**:
- ✅ **計數器脈衝是唯一真理來源**（硬體跳動，不可偽造）
- ✅ 採集數據分兩路：WebSocket 即時顯示 + 轉發給 Member 記錄
- ✅ 累計值必須完整傳遞，不能在中途算 delta 就丟棄
- ✅ Redis 用於即時監控，資料庫是唯一真理來源

---

## 📊 現有實作確認（Infra 系統）

### **已知的組件**
1. `listener.py` - MQTT 訂閱和處理
2. `mqtt_pulse_handler.py` - 脈衝數據處理（？）
3. Redis - 即時數據快取
4. WebSocket - 即時推送

### **已知的 MQTT 主題**
- `device/{chip_id}/data` - ESP32 上報數據
- `device/{chip_id}/cmd` - 雲端下發指令
- `device/{chip_id}/status` - 設備狀態（LWT）
- `device/{chip_id}/diagnostic` - 診斷心跳

### **已知的 API**
- `POST /api/device/trigger-pulse` - Member 請求觸發脈衝
- `POST /api/device/start-session` - 開始 session
- `POST /api/device/stop-session` - 結束 session

---

## ❓ 需要你確認的問題

### **Q1: ESP32 上報的 MQTT payload 格式是什麼？**

**主題**: `device/{chip_id}/data`

**問題**：
1. ESP32 上報 credit_in 時的 payload 格式是：
```json
// 選項 A
{
  "type": "credit_in",
  "count": 1050,              // 累計脈衝數
  "timestamp": "2026-06-19T08:40:00Z"
}

// 選項 B
{
  "type": "credit_in",
  "amount": 1050,             // 累計值（但不確定單位）
  "ts": 1718784000
}

// 選項 C
{
  "type": "credit_in",
  "value": 10,                // 增量（本次跳動）
  "timestamp": 1718784000
}

// 選項 D：其他格式（請提供實際格式）
```

2. ESP32 上報 credit_out 時的 payload 格式是：
   - 同上，還是不同？請提供實際格式

3. `count` / `amount` / `value` 欄位的單位是：
   - A. 累計脈衝數（里程表）
   - B. 增量脈衝數（本次變化）
   - C. 金額（元）
   - D. 其他（請說明）

---

### **Q2: listener.py 怎麼處理 credit_in / credit_out？**

**問題**：
1. 收到 `device/{chip_id}/data` 後，listener.py 做什麼？
   - A. 直接轉發給 Member（POST /internal/device/pulse-report）
   - B. 計算 delta → 轉發給 Member
   - C. 寫入 Owner DB 的 revenue_facts → 轉發給 Member
   - D. 其他（請說明完整流程）

2. 轉發給 Member 的 API endpoint 是：
   - A. `POST /internal/device/pulse-report`
   - B. `POST /internal/device/credit-in` 和 `/credit-out`
   - C. 其他（請提供實際 endpoint）

3. 轉發的 payload 格式是：
```json
// 請提供實際格式
{
  "chip_id": "aabbcc112233",
  "type": "credit_in",
  "cumulative_count": 1050,    // 累計脈衝數？
  "timestamp": "..."
}
```

4. credit_in 和 credit_out 的處理流程是：
   - A. 完全相同
   - B. 不同（請說明差異）

---

### **Q3: Redis 存的資料格式是什麼？**

**問題**：
1. Redis 存的 key 格式是：
   - A. `last_pulse:{chip_id}:{type}` → 值：累計脈衝數
   - B. `device:status:{chip_id}` → 值：JSON 物件
   - C. 其他（請提供實際格式）

2. Redis 存的是：
   - A. 累計脈衝數（例：1050）
   - B. 完整的 JSON 物件（例：`{"count":1050,"timestamp":"..."}`）
   - C. 其他（請說明）

3. Redis 的值什麼時候更新？
   - A. 每次收到 MQTT 就更新
   - B. 轉發給 Member 成功後才更新
   - C. 其他（請說明）

4. Redis 故障時，如何恢復 last_pulse？
   - A. 從 Member DB 的 wallet_transactions 最後一筆重建
   - B. 從 Owner DB 的 revenue_facts 重建
   - C. 等 ESP32 下次上報時重新設定
   - D. 其他（請說明）

---

### **Q4: WebSocket 推送的格式是什麼？**

**問題**：
1. 收到 ESP32 上報後，有沒有透過 WebSocket 推送？
   - A. 有，推送給前端即時監控頁面
   - B. 沒有，WebSocket 是其他用途
   - C. 其他（請說明）

2. 如果有推送，payload 格式是：
```json
// 請提供實際格式
{
  "chip_id": "aabbcc112233",
  "type": "credit_in",
  "cumulative_count": 1050,      // 累計脈衝數
  "delta_count": 10,             // 增量脈衝數
  "display_tokens": 10,          // 換算代幣數（顯示用）
  "display_score": 1000          // 換算分數（顯示用）
}
```

3. WebSocket 推送時，是否已經做了換算（脈衝 → 代幣 → 分數）？
   - A. 是，已經換算好
   - B. 否，只傳原始脈衝數
   - C. 其他（請說明）

4. 如果已換算，機台配置（`coin_to_pulse`、`coin_to_score`）從哪裡取得？
   - A. 從 Redis 快取
   - B. 從 Owner DB 查詢
   - C. 從 Member API 取得
   - D. 其他（請說明）

---

### **Q5: 計算 delta 的邏輯是什麼？**

**問題**：
1. listener.py 有沒有計算 delta（增量）？
   - A. 有，收到累計值後，用 Redis 的 last_pulse 計算 delta
   - B. 沒有，直接轉發累計值給 Member，由 Member 計算
   - C. 其他（請說明）

2. 如果有計算 delta，邏輯是：
```python
# 請提供實際代碼片段或邏輯描述
current_count = mqtt_payload['count']
last_count = redis.get(f"last_pulse:{chip_id}:credit_in")
delta = current_count - last_count

if delta > 0:
    # 做什麼？
```

3. 如果 delta <= 0，怎麼處理？
   - A. 忽略，不轉發
   - B. 記錄異常 log
   - C. 轉發但標記為異常
   - D. 其他（請說明）

4. 首次啟動（Redis 無 last_pulse）時，怎麼處理？
   - A. 只設定 Redis 基準線，不轉發
   - B. 直接轉發當前累計值
   - C. 其他（請說明）

---

### **Q6: credit-out 的處理邏輯是什麼？**

**Owner 系統的 InternalPulseController.php 說**：
```php
public function creditOut(Request $request)
{
    // TODO: 實作 credit-out 脈衝處理邏輯
    // 目前 credit-out 由 Infra 直接寫入 revenue_facts
    return response()->json(['status' => 'not_implemented'], 501);
}
```

**問題**：
1. 收到 credit_out 時，listener.py 真的有「直接寫入 revenue_facts」嗎？
   - A. 是，直接寫入 Owner DB
   - B. 否，轉發給 Member 處理
   - C. 兩者都做（寫 revenue_facts + 轉發 Member）
   - D. 其他（請說明）

2. 如果直接寫入 revenue_facts，為什麼不轉發給 Member？
   - 因為 Member 的 API 沒實作？還是其他原因？

3. 如果轉發給 Member，Member 沒有 active session 時，怎麼處理？
   - A. 不管，讓 Member 自己處理（回 200 或 422）
   - B. 記錄孤兒 log
   - C. 其他（請說明）

---

### **Q7: MQTT 指令下發的格式是什麼？**

**Member 請求開分時，Infra 需要發 MQTT 指令給 ESP32**

**問題**：
1. `POST /api/device/trigger-pulse` 收到的 payload 格式是：
```json
// 請提供實際格式
{
  "chip_id": "aabbcc112233",
  "count": 10              // 觸發 10 次脈衝
}
```

2. 轉換成 MQTT 指令後，發布到 `device/{chip_id}/cmd`，payload 是：
```json
// 請提供實際格式
{
  "command": "assign_credit",
  "params": {
    "count": 10
  }
}
```

3. 洗分指令（settle_credit）的 payload 是：
```json
// 請提供實際格式
{
  "command": "settle_credit",
  "params": {}           // 不需要 count？
}
```

4. 有沒有 `transaction_id` 或其他追蹤欄位？

---

### **Q8: 錯誤處理和重試機制是什麼？**

**問題**：
1. 如果轉發給 Member 失敗（例：Member API 503），怎麼處理？
   - A. 記錄 log，丟棄
   - B. 重試 N 次
   - C. 寫入失敗佇列（例：Redis queue）
   - D. 其他（請說明）

2. 如果 MQTT 連線斷開，listener.py 怎麼恢復？
   - A. 自動重連
   - B. Systemd/Supervisor 重啟
   - C. 其他（請說明）

3. 如果 Redis 連線失敗，是否還能運作？
   - A. 可以，但無法計算 delta（直接轉發累計值）
   - B. 不行，listener.py 會 crash
   - C. 其他（請說明）

---

## 📋 請提供的資訊

### **1. listener.py 的完整路徑和核心代碼**
```bash
# 請提供檔案路徑
/path/to/tg25-infra/mqtt/listener.py

# 請提供核心邏輯代碼片段（處理 credit_in / credit_out 的部分）
```

### **2. MQTT Payload 實際範例**
```json
// 請提供實際抓取的 MQTT 消息範例
// Topic: device/{chip_id}/data
{
  // 實際格式
}
```

### **3. Infra API 路由列表**
```bash
# 如果是 FastAPI，請提供路由定義
# 或者提供 API 文件連結
```

### **4. Redis 實際存儲範例**
```bash
# 請執行並提供結果
redis-cli
> KEYS *pulse*
> KEYS device:*
> GET last_pulse:aabbcc112233:credit_in
```

### **5. WebSocket 推送範例**
```json
// 如果有 WebSocket 推送，請提供實際範例
```

---

## 🎯 回覆清單（請逐項回答）

- [ ] Q1: ESP32 上報的 MQTT payload 格式？（請提供實際範例）
- [ ] Q2: listener.py 的處理流程？轉發給 Member 的 API 和 payload？
- [ ] Q3: Redis 的 key/value 格式？更新時機？故障恢復？
- [ ] Q4: WebSocket 推送格式？是否已換算？
- [ ] Q5: 有沒有計算 delta？邏輯是什麼？
- [ ] Q6: credit-out 是直接寫 DB 還是轉發 Member？
- [ ] Q7: MQTT 指令下發的格式？（assign_credit / settle_credit）
- [ ] Q8: 錯誤處理和重試機制？

**補充說明**（如果有其他重要細節）:
```
（請在這裡填寫）
```

---

*準備者: HQ | 日期: 2026-06-19 | 待回覆: Ina*
