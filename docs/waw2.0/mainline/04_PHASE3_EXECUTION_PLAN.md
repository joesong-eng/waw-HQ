# WAW 2.0 階段三執行計劃
**啟動時間**: 2026-06-15 01:05 (Asia/Taipei)  
**規劃者**: HQ (Hera)  
**狀態**: 🟡 規劃中

---

## 📋 階段三任務清單

### 核心目標
1. **軟性欠費機制** - 欠費不停機，繼續服務但累計欠款
2. **交易分潤固化** - 每筆交易即時查詢協議，寫入 machine_transactions
3. **後台管理限制** - arrears 狀態限制提現、交班
4. **高頻催收** - LINE Notify 每日催收

---

## 🎯 分工規劃

### Ina (Infra) - 3 個任務

#### 任務 1: MQTT Listener 軟性欠費放行
**目標**: 修改 listener.py，欠費機器照常接收 MQTT，標記狀態但不阻斷
```python
# 當收到 MQTT 時：
1. 查詢 devices.subscription_status
2. 若為 'arrears'，寫入 Redis 標記
3. 照常處理消息（不阻斷）
4. 記錄日誌
```

#### 任務 2: 交易分潤固化邏輯
**目標**: 消費事件觸發時，查協議並寫入 machine_transactions
```python
# 當收到消費事件時：
1. 查 profit_sharing_agreements 取得分潤比例
2. 計算分成金額
3. 寫入 machine_transactions 表
4. 固化當下的分潤比例
```

#### 任務 3: 建立 machine_transactions 表
**目標**: 在 iotv9 建立交易流水表
```sql
CREATE TABLE machine_transactions (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  machine_id BIGINT UNSIGNED NOT NULL,
  store_id BIGINT UNSIGNED NOT NULL,
  transaction_type VARCHAR(50) NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  store_owner_share_amount DECIMAL(10,2) NOT NULL,
  machine_owner_share_amount DECIMAL(10,2) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### Sophie (Owner) - 2 個任務

#### 任務 1: 欠費扣款機制
**目標**: 儲值/續費/提現時自動扣除 outstanding_amount
```php
// 在付款流程中：
1. 檢查 users.outstanding_amount
2. 若 > 0，先扣除欠款
3. 剩餘金額才能續費/提現
4. 記錄扣款日誌
```

#### 任務 2: 後台管理限制
**目標**: arrears 狀態限制後台功能
```php
// 在後台 Middleware 中：
1. 檢查用戶設備/場地的 subscription_status
2. 若有任何 'arrears'，限制：
   - 提現功能
   - 交班結算
   - 高級報表
3. 頂部顯示紅色警告
```

---

### Mina (Member) - 1 個任務

#### 任務 1: 玩家端無感驗證
**目標**: 確認欠費時玩家體驗正常
```
測試場景：
1. 設定測試設備為 'arrears' 狀態
2. 玩家掃碼開分
3. 確認流程完全正常
4. 前端無任何欠費提示
```

---

## ⚠️ 執行前確認

### 必須先完成的事
1. **建立 machine_transactions 表** - Ina 先建表
2. **machine_deployments 表** - 需要嗎？（查分潤時需要 store_id）

### 風險評估
1. **高風險**: 修改 MQTT Listener（核心服務）
2. **中風險**: 修改付款流程（金流相關）
3. **低風險**: 後台限制（不影響營業）

---

## 🤔 關鍵問題（需要 Joe 決策）

### 問題 1: machine_deployments 表是否需要？
**背景**: 交易分潤固化需要知道「機器當時在哪個場地」

**選項 A**: 建立 machine_deployments 表
- 優點：符合 WAW 2.0 設計，完整記錄歷史
- 缺點：需要額外開發部署邏輯

**選項 B**: 直接用 devices.venue_id
- 優點：簡單，立即可用
- 缺點：無法追溯歷史搬移記錄

### 問題 2: 階段三是否一次全做？
**選項 A**: 分批執行（推薦）
- 先做 Ina 的表建立 + 分潤固化
- 再做 Sophie 的扣款 + 限制
- 最後測試 Mina 的玩家端

**選項 B**: 全部一起做
- 同時發所有任務
- 風險較高

### 問題 3: Nginx 反向代理是否現在做？
**背景**: 原規劃要拆分 waw-iot (Port 8002) 和 waw-business (Port 8001)

**當前狀況**: 階段二還沒拆分服務，都在 Owner 專案

**建議**: 先完成軟性欠費核心邏輯，服務拆分放到最後

---

## 📅 建議執行順序

### Week 1: 核心邏輯（本週）
1. Ina 建立 machine_transactions 表
2. Ina 實作交易分潤固化
3. Sophie 實作欠費扣款機制
4. 測試驗證

### Week 2: 後台限制（下週）
5. Sophie 實作後台管理限制
6. Sophie 實作 LINE Notify 催收
7. Mina 玩家端驗證

### Week 3: 服務拆分（未來）
8. 拆分 waw-iot 獨立服務
9. Nginx 反向代理設定
10. 完整整合測試

---

## 🎯 今天可以立即做的

### 立即發出的任務（如果你同意）

**Ina 任務 1: 建立 machine_transactions 表**
```bash
./scripts/hq_task_flow.sh task ina TASK_20260615_PHASE3_001 \
"建立 machine_transactions 表到 iotv9 資料庫：
1. 參考 WAW_2.0_ARCHITECTURE_SPEC.md 第 5 節
2. 包含欄位：machine_id, store_id, transaction_type, total_amount, 分成金額
3. 先 SHOW TABLES 確認不重複
4. 執行 CREATE TABLE
5. 驗證表結構並回報" high
```

**Sophie 諮詢: 確認付款流程入口**
```bash
./scripts/hq_task_flow.sh task sophie CONS_20260615_PHASE3_001 \
"確認儲值/續費/提現的代碼入口：
1. 找到處理付款的 Controller/Service
2. 確認哪些流程需要加入欠款扣除邏輯
3. 列出檔案路徑與方法名稱
4. 回報目前是否已有扣款邏輯" normal
```

---

## 等待你的決定

1. **是否先建 machine_deployments 表？**（選項 A / B）
2. **是否分批執行？**（選項 A / B）
3. **是否立即發出上述 2 個任務？**（是 / 否）

