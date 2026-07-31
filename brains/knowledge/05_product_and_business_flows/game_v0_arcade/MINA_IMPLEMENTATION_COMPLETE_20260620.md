# Mina 完成遊戲機開分/洗分整數化實作


**[On-Demand]** — 上下文注入策略

> **完成時間**：2026-06-20 02:15 UTC (10:15 UTC+8)  
> **執行者**：Mina (Member Agent)  
> **任務 ID**：TASK_MINA_MEMBER_IMPLEMENTATION_20260620  
> **狀態**：✅ Completed

---

## 📋 實作摘要

Mina 已完成 Member 系統中遊戲機開分/洗分流程的整數化改造，核心變更包括：

### 1. 前端變更
- **檔案**：`resources/views/play.blade.php`
- **變更**：開分請求改為傳送 `tokens` (整數代幣)，保留 `display_amount` 作為顯示相容
- **計算**：使用 `Math.floor()` 確保代幣為整數

### 2. 後端 API 變更
- **檔案**：`app/Http/Controllers/Api/DeviceController.php`
- **credit API**：接收並驗證 `tokens` 整數，無法整除時回傳 422 拒絕開分
- **creditIn Webhook**：新增端點 `/internal/device/credit-in`，處理開分確認
- **creditOut Webhook**：支援 `cumulative_count` 優先，相容舊的 `cumulative_amount`

### 3. 資料庫相容策略
- **動態欄位過濾**：使用 `\Schema::getColumnListing` 動態篩選可寫入欄位
- **雙欄位支援**：同時支援 `cumulative_count` 與 `cumulative_amount`
- **優雅降級**：Ina 執行 migration 前後均不會出錯

---

## ✅ 測試驗證

### 測試結果
```bash
PHPUnit 11.5.55 by Sebastian Bergmann and contributors.
....                                                                4 / 4 (100%)
Time: 00:00.286, Memory: 46.50 MB
OK (4 tests, 16 assertions)
```

### 測試覆蓋
1. **開分成功**：`tokens` 整數驗證、預扣款、pending 交易生成
2. **開分失敗退款**：Infra API 失敗時自動退款
3. **creditIn 確認**：計算 delta、更新 pending 為 success
4. **creditOut 洗分**：floor 換算彩票、記錄快照

---

## 🔄 與 Ina 的協調點

### Ina 需執行的 DDL
```sql
-- wallet_transactions 表
ALTER TABLE wallet_transactions 
  ADD COLUMN cumulative_count INT UNSIGNED NULL AFTER cumulative_amount,
  ADD COLUMN delta_count INT NULL AFTER cumulative_count,
  ADD COLUMN pulse_to_token DECIMAL(10,4) NULL,
  ADD COLUMN coin_value INT NULL,
  ADD COLUMN tokens INT NULL;

-- device_orphan_logs 表
ALTER TABLE device_orphan_logs 
  ADD COLUMN cumulative_count INT UNSIGNED NULL,
  ADD COLUMN delta_count INT NULL,
  ADD COLUMN estimated_tokens INT NULL;
```

### 相容保證
- Mina 的代碼在 Ina 執行 migration **前後**都能正常運作
- 寫入時動態檢測欄位存在性
- 讀取時優先查詢新欄位，無值時回退到舊欄位

---

## 📊 技術亮點

### 1. 冪等性保證
- 使用 `cumulative_count` 作為里程表
- Delta 計算確保重複上報不會重複入帳

### 2. 預扣款機制
- 開分時先建立 `pending` 交易
- Infra 失敗時自動標記 `failed` 並退款
- creditIn 確認時更新為 `success`

### 3. 孤兒分數處理
- 無 active session 時寫入 `device_orphan_logs`
- 保留資料供後續管理員處理

### 4. Floor 換算策略
- 使用 `floor()` 無條件捨去零頭
- 零頭脈衝保留在機台累計值中

---

## 🎯 後續行動項

### HQ 層級
- [x] 收集 Mina 回報
- [ ] 確認 Ina 已收到 DDL 需求
- [ ] 協調 Sophie/Mina/Ina 進行整合測試

### Ina 層級
- [ ] 執行資料庫 DDL migration
- [ ] 確認 Infra API 支援 `cumulative_count` 欄位
- [ ] 更新 MQTT Payload 包含新欄位

### Sophie 層級
- [ ] 確認 Owner 後台是否需要顯示 `cumulative_count`
- [ ] 孤兒分數管理介面需求評估

---

## 📁 相關文件

- **設計定稿**：`brains/knowledge/05_product_and_business_flows/game_v0_arcade/DESIGN_FINALIZED_20260619.md`
- **技術標準**：`brains/knowledge/02_protocols_and_standards/PULSE_BASED_DATA_FLOW.md`
- **完整回報**：`/Users/ilawusong/Documents/sysWawIot/Member/_agent/REPORT_20260620_020628_TASK_MINA_MEMBER_IMPLEMENTATION_20260620.md`

---

## 🔗 文件神經連結

- 上級文件：`05_product_and_business_flows/game_v0_arcade/README.md`
- 關聯任務：`TASK_MINA_MEMBER_IMPLEMENTATION_20260620`
- 下游依賴：等待 Ina 執行 DDL (TASK_INA_DB_AND_INFRA_20260620)
