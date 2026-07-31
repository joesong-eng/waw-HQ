# Mina 實作任務：Member 開分/洗分與整數代幣改造


**[On-Demand]** — 上下文注入策略

> 日期：2026-06-20  
> 發起：HQ  
> 任務類型：Member 代碼修改（等待 Ina 完成 DB 變更後落地）  
> 優先級：High

---

## 一、任務前提

DB 結構變更由 Ina 執行。Mina 不寫 migration、不執行 ALTER、不自行改 DB schema。

本任務分兩階段：
1. 先準備代碼變更與影響評估。
2. 等 Ina 回報 DB 變更完成後，再進行整合測試。

---

## 二、核心設計決策

- 會員餘額是代幣數量，不支援半枚代幣。
- 前端顯示永遠是整數代幣。
- 開分 API 改為接收 `tokens`，不再以 `display_amount` 作為主要 payload。
- `display_amount` / 分數只作顯示，不作交易基準。
- 交易記錄必須保存快照：`delta_count`、`pulse_to_token`、`coin_value`。
- 累計值來自 ESP32 NVS 累計脈衝數，欄位標準目標為 `cumulative_count`。

---

## 三、實作需求

### 1. 前端 `play.blade.php`

請調整開分按鈕與 `doCredit`：

- UI 可以繼續顯示分數，例如「1 代幣 / 100 分」。
- 實際 payload 必須送 `tokens` 整數。
- 不要讓會員選「觸發幾個脈衝」。
- `display_amount` 僅可保留為相容欄位或顯示資訊，不應作為後端主要計算依據。

### 2. `DeviceController.php` 開分 API

- 接收 `tokens`，驗證為整數且大於 0。
- 依 `pulse_to_token` 計算 Infra trigger count：`count = tokens / pulse_to_token`。
- 若無法整除，需要明確處理：拒絕或取整，不能默默造成少開分。
- 採 `status=pending` 預扣，Infra 失敗則退款。

### 3. `credit-in` webhook

請確認是否已有 `/internal/device/credit-in`：

- 若已有：調整接收 `cumulative_count`，可短期兼容 `cumulative_amount`。
- 若沒有：新增端點，處理開分確認。
- 應以 DB 上一筆累計值計算 delta，不只依賴 Redis。
- 新交易記錄保存：`cumulative_count`、`delta_count`、`pulse_to_token`、`coin_value`、`tokens`、`amount`。

### 4. `credit-out` webhook

- 調整為接收 `cumulative_count`，短期可兼容現有 `cumulative_amount`。
- 以累計脈衝數計算 delta。
- 換算代幣時使用 `floor()`，因代幣不可有小數。
- 孤兒脈衝仍要記錄，不入會員帳。

### 5. Model / 欄位名稱相容

- 等 Ina 確認 DB 策略後，更新 `WalletTransaction` / `DeviceOrphanLog` fillable。
- 如果 Ina 採「新增 `cumulative_count` 並保留 `cumulative_amount`」的相容方案，Mina 代碼需優先使用 `cumulative_count`，但讀取舊資料時兼容 `cumulative_amount`。

---

## 四、驗證要求

回報必須附證據。

### 必測流程
1. 前端開 1 代幣：payload 是 `tokens: 1`。
2. 後端計算 Infra `count` 正確。
3. Infra 回傳失敗時，pending 交易變 failed 並退款。
4. credit-in webhook 收到累計脈衝後可確認交易。
5. credit-out webhook 收到累計脈衝後可增加 TICKET/洗分結果。
6. 無 active session 時，credit-out 寫入 orphan log。
7. 小數餘額資料若存在，顯示與交易均只能用整數。

### 回報證據
- 修改檔案列表。
- 前端 payload 截圖或 browser/network log。
- API 測試 curl 結果。
- DB 查詢結果（只查，不自行 ALTER）。
- 測試 log。

---

## 五、回報格式

```markdown
# Mina 回報：TASK_MINA_MEMBER_IMPLEMENTATION_20260620

## 影響範圍
- cumulative_amount 使用處：...
- display_amount 使用處：...

## 代碼修改
- 修改檔案：...
- credit API：...
- credit-in webhook：...
- credit-out webhook：...

## 相容策略
- cumulative_count / cumulative_amount：...

## 驗證結果
- 前端 payload：...
- credit 測試：...
- credit-in 測試：...
- credit-out 測試：...

## 阻塞/疑問
- ...
```
