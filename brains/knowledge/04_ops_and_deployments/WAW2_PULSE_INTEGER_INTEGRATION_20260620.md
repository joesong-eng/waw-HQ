# WAW 2.0 脈衝整數化整合任務完成報告


**[On-Demand]** — 上下文注入策略

**任務群組 ID**: TASK_INA_DB_AND_INFRA_20260620 / TASK_MINA_MEMBER_IMPLEMENTATION_20260620 / TASK_SOPHIE_OWNER_VERIFY_20260620
**完成日期**: 2026-06-20
**執行者**: Ina + Mina + Sophie
**狀態**: ✅ 已完成並部署

---

## 整合摘要

三位 Agent 已完成 WAW 2.0 脈衝整數化的完整鏈路改造：

### Ina (Infra + DB)
- ✅ Owner DB (`iotv9`) 與 Member DB (`waw_member_production`) DDL 執行完成
- ✅ `revenue_facts` 新增 `cumulative_count` (bigint)
- ✅ `machines` 新增 `lifetime_pulse_in` / `lifetime_pulse_out` (bigint)
- ✅ `device_orphan_logs` 新建表 (Owner 側與 Member 側)
- ✅ `wallet_transactions` 新增快照欄位：`delta_count`, `pulse_to_token`, `coin_value`, `cumulative_count`
- ✅ `member_wallets.balance` 改為 bigint (整數語義)
- ✅ Infra `listener.py` 修改：Redis 遺失時從 DB 恢復基準線、credit_in 轉發至 Member、孤兒日誌記錄
- ✅ Git commit `55fd756` 已推送並部署至 VPS

### Mina (Member 前後端)
- ✅ 前端 `play.blade.php` 改為發送整數 `tokens`，使用 `Math.floor()` 取整
- ✅ 後端 `DeviceController.php`:
  - `credit()` API 改為接收整數 `tokens`，使用 `pending` 預扣，失敗自動退款
  - `creditIn()` 新增 Webhook `/internal/device/credit-in`，接收 Infra 轉發，確認 `pending` 交易
  - `creditOut()` 修改為支援 `cumulative_count`，計算 `floor(delta * out_pulse_to_ticket)` 彩票
- ✅ `MemberWallet.php` 動態欄位過濾機制（相容 Ina DDL 執行前後）
- ✅ 單元測試 `DeviceCreditTest.php` 全數通過 (4 tests, 16 assertions)

### Sophie (Owner 後台驗證)
- ✅ 確認 `users.outstanding_amount` DDL 正確執行
- ✅ 修復 `Device.php` 的 `getPeriodStats()` 營收統計邏輯（取消註解 `transaction_type` 判斷）
- ✅ 驗證後台 API `DeviceController@show` 正確回傳 `today_revenue`, `today_credit_in`, `today_credit_out`
- ✅ Dashboard 統計邏輯正常，無 500 錯誤

---

## 相容策略

- **`cumulative_amount` ↔ `cumulative_count`**: Infra 同時傳送兩個欄位，Member 優先使用 `cumulative_count`，向下相容 `cumulative_amount`
- **動態欄位過濾**: Member 使用 `\Schema::getColumnListing()` 動態過濾，確保 DDL 執行前後均不報錯
- **韌體影響**: ✅ 無影響（ESP32 使用 `count` 欄位，不依賴 `cumulative_amount`）

---

## 後續整合驗證建議

1. **Member 端 `/internal/device/credit-in` 路由測試**:
   - Infra 已開始轉發，但需實測 Member 接收與確認邏輯
   - 建議監控 `[MEMBER_CREDIT_IN_ERROR]` log

2. **整數彩票計算驗證**:
   - 確認 `floor(delta * out_pulse_to_ticket)` 是否符合業務預期
   - 驗證小數脈衝捨棄對玩家體驗的影響

3. **Owner 側今日營收報表**:
   - 確認後台 Dashboard 與設備詳情頁面的營收數字正確性
   - 監控 `revenue_facts` 查詢效能（建議 Ina 對 `event_ts`, `venue_id`, `transaction_type` 建立複合索引）

4. **孤兒日誌監控**:
   - 監控 `[ORPHAN_LOG_SAVED]` 出現頻率
   - 若頻繁出現，代表有未註冊設備上報，需人工處理

---

## 部署證據

- Ina DDL 備份: `tg25-infra/db/migrations/v9/20260620_TASK_INA_DB_AND_INFRA_20260620.sql`
- Ina Git commit: `55fd756` (已推送至 GitHub 並部署 VPS)
- Mina 單元測試: `vendor/bin/phpunit tests/Feature/DeviceCreditTest.php` (4/4 passed)
- Sophie 驗證: `tinker` 模擬與 API 回傳結果截圖（見報告）

---

**HQ 簽名**: 三個任務已完成並通過驗收，已登記至知識庫。
