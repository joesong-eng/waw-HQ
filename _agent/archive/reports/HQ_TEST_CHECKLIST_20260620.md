# WAW 2.0 脈衝整數化測試清單

**測試目標**: 驗證 DB → Infra → Member → Owner 完整鏈路  
**測試日期**: 2026-06-20  
**測試環境**: VPS 生產環境 (tg25.win)  

---

## 🔴 核心功能測試（必測）

### 1. 玩家開分流程（Member 前端 → Infra）

**測試步驟**:
```
1. 登入 Member 前台 (https://win.tg25.win)
2. 進入遊戲機頁面，點擊「開分」
3. 輸入代幣數量（例如：100）
4. 確認送出
```

**驗證點**:
- [ ] 前端發送的 payload 包含整數 `tokens` 欄位
- [ ] Member 錢包餘額立即扣款（`pending` 狀態）
- [ ] Infra 收到開分請求並記錄 `revenue_facts`
- [ ] Member 收到 Infra 的 `credit_in` 確認
- [ ] `pending` 交易狀態變更為 `success`
- [ ] `wallet_transactions` 記錄包含 `cumulative_count`, `delta_count`, `pulse_to_token`

**檢查命令**:
```bash
# VPS 上檢查 Infra log
ssh tg25 "tail -100 /var/www/mqtt/logs/listener.log | grep -E 'CREDIT_IN|credit_in'"

# 本地檢查 Member DB
ssh tg25
mysql -u root -p
use waw_member_production;
SELECT * FROM wallet_transactions ORDER BY id DESC LIMIT 3;
```

---

### 2. 遊戲機洗分流程（Infra → Member）

**測試步驟**:
```
1. 玩家在已開分的遊戲機上遊玩
2. 贏得彩票（觸發 credit_out）
3. ESP32 上報累計脈衝至 MQTT
```

**驗證點**:
- [ ] Infra 接收到 `credit_out` MQTT 訊息
- [ ] 計算 `delta = cumulative_count - last_cumulative_count`
- [ ] 使用 `floor(delta * out_pulse_to_ticket)` 計算整數彩票
- [ ] Member 收到洗分通知並寫入 `wallet_transactions`
- [ ] 玩家錢包餘額增加（整數彩票）
- [ ] 若無 active session，寫入 `device_orphan_logs`

**檢查命令**:
```bash
# VPS 上檢查 Infra log
ssh tg25 "tail -100 /var/www/mqtt/logs/listener.log | grep -E 'CREDIT_OUT|credit_out'"

# 檢查 Member DB orphan logs
mysql -u root -p waw_member_production
SELECT * FROM device_orphan_logs ORDER BY id DESC LIMIT 5;
```

---

### 3. Infra 轉發至 Member（credit_in 確認）

**測試步驟**:
```
玩家開分後，Infra 需轉發 credit_in 至 Member 確認
```

**驗證點**:
- [ ] Infra `listener.py` 發送 POST 請求至 `https://win.tg25.win/internal/device/credit-in`
- [ ] Payload 同時包含 `cumulative_amount` 與 `cumulative_count`（相容策略）
- [ ] Member 接收成功並回傳 200
- [ ] 若 Member 回傳 404 或 500，Infra log 記錄 `[MEMBER_CREDIT_IN_ERROR]`

**檢查命令**:
```bash
# VPS 上檢查 Infra 轉發 log
ssh tg25 "tail -200 /var/www/mqtt/logs/listener.log | grep -E 'MEMBER_CREDIT_IN|credit_in'"

# 檢查 Member 路由是否存在
ssh tg25 "cd /var/www/Member && php artisan route:list | grep credit-in"
```

---

### 4. 開分失敗自動退款機制

**測試步驟**:
```
1. 模擬 Infra API 調用失敗（例如：暫時停止 mqtt-listener）
2. 玩家嘗試開分
```

**驗證點**:
- [ ] Member 預扣餘額成功（`pending` 狀態）
- [ ] Infra API 調用失敗
- [ ] Member 自動將 `pending` 交易標記為 `failed`
- [ ] Member 自動建立 `manual_adjust` 交易退款
- [ ] 玩家錢包餘額恢復

**檢查命令**:
```bash
# 檢查 Member DB
mysql -u root -p waw_member_production
SELECT * FROM wallet_transactions WHERE status = 'failed' ORDER BY id DESC LIMIT 3;
SELECT * FROM wallet_transactions WHERE type = 'manual_adjust' ORDER BY id DESC LIMIT 3;
```

---

## 🟡 資料一致性測試（建議測）

### 5. Redis 遺失後 DB 恢復機制

**測試步驟**:
```
1. 清空 Redis 中的設備累計脈衝數
2. 設備上報新的脈衝數據
```

**驗證點**:
- [ ] Infra 發現 Redis 無基準線
- [ ] 從 `revenue_facts.cumulative_count` 恢復最後一筆記錄
- [ ] Infra log 記錄 `[REVENUE_FACTS_RESTORE]`
- [ ] 若 DB 也無記錄，從 `device_orphan_logs` 恢復
- [ ] 恢復後繼續正常計算 delta

**檢查命令**:
```bash
# 清空 Redis
redis-cli DEL "device:sr9adyxpdyt1tuf7:cumulative_in"

# 檢查 Infra log
ssh tg25 "tail -100 /var/www/mqtt/logs/listener.log | grep RESTORE"
```

---

### 6. 孤兒脈衝記錄機制

**測試步驟**:
```
使用未註冊的 chip_id 上報 MQTT 訊息
```

**驗證點**:
- [ ] Infra 無法在 `machines` 表中找到設備
- [ ] 寫入 `device_orphan_logs` (Owner 側)
- [ ] Infra log 記錄 `[ORPHAN_LOG_SAVED]`
- [ ] 記錄包含 `chip_id`, `cumulative_count`, `delta_count`, `event_ts`

**檢查命令**:
```bash
# 檢查 Owner DB orphan logs
ssh tg25
mysql -u root -p iotv9
SELECT * FROM device_orphan_logs ORDER BY id DESC LIMIT 5;

# 檢查 Infra log
ssh tg25 "tail -100 /var/www/mqtt/logs/listener.log | grep ORPHAN"
```

---

### 7. Owner 後台營收統計

**測試步驟**:
```
1. 登入 Owner 後台 (https://admin.tg25.win)
2. 查看 Dashboard 今日營收
3. 查看設備詳情頁面的統計數據
```

**驗證點**:
- [ ] Dashboard 顯示正確的今日淨營收 (credit_in - credit_out)
- [ ] 設備詳情頁面顯示 `today_revenue`, `today_credit_in`, `today_credit_out`
- [ ] `lifetime_pulse_in` 與 `lifetime_pulse_out` 分別累計
- [ ] 無 500 錯誤

**檢查命令**:
```bash
# 檢查 Owner DB
ssh tg25
mysql -u root -p iotv9
SELECT id, chip_id, lifetime_pulse, lifetime_pulse_in, lifetime_pulse_out FROM machines WHERE id = 1;
SELECT transaction_type, COUNT(*), SUM(amount) FROM revenue_facts WHERE DATE(event_ts) = CURDATE() GROUP BY transaction_type;
```

---

## 🟢 相容性測試（選測）

### 8. 動態欄位過濾機制

**測試步驟**:
```
1. 暫時移除 Member DB 的 `cumulative_count` 欄位（模擬 DDL 未執行）
2. 玩家開分/洗分
```

**驗證點**:
- [ ] Member 使用 `\Schema::getColumnListing()` 動態過濾
- [ ] 寫入 `wallet_transactions` 時只寫入存在的欄位
- [ ] 不會出現 "Unknown column 'cumulative_count'" 錯誤
- [ ] 使用 `cumulative_amount` 向下相容

**檢查命令**:
```bash
# 暫時移除欄位（謹慎操作）
mysql -u root -p waw_member_production
ALTER TABLE wallet_transactions DROP COLUMN cumulative_count;

# 測試後恢復
ALTER TABLE wallet_transactions ADD COLUMN cumulative_count int unsigned DEFAULT NULL AFTER cumulative_amount;
```

---

## 📊 測試報告格式

測試完成後，請記錄以下資訊：

```
測試項目: [項目名稱]
測試結果: ✅ 通過 / ❌ 失敗
測試時間: [時間]
測試環境: [VPS / 本地]
問題描述: [若失敗，描述錯誤訊息]
截圖/Log: [附上相關截圖或 log]
```

---

## 🚨 若發現問題

使用 HQ Task Flow 召集對應 Agent 修復：

```bash
# Infra 問題 → Ina
./scripts/hq_task_flow.sh task ina TASK_FIX_INFRA_ISSUE_001 "描述問題" high

# Member 問題 → Mina
./scripts/hq_task_flow.sh task mina TASK_FIX_MEMBER_ISSUE_001 "描述問題" high

# Owner 問題 → Sophie
./scripts/hq_task_flow.sh task sophie TASK_FIX_OWNER_ISSUE_001 "描述問題" high
```

---

**HQ 簽名**: 我是 HQ，測試清單已準備完成。祝測試順利！
