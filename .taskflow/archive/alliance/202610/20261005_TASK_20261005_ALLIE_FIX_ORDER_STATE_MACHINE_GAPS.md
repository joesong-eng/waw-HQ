# 任務：TASK_20261005_ALLIE_FIX_ORDER_STATE_MACHINE_GAPS

**派發時間**：2026-10-05
**優先級**：high
**負責人**：Allie (Alliance)
**性質**：修復訂單狀態機規格漏洞
**來源**：`TASK_20261005_ALLIE_ORDER_STATE_MACHINE_LOGIC_TEST` 回報之 7 項漏洞（Joe 裁定：開單修）
**架構依據**：訂單 7 步狀態機 `draft → confirmed → burning → burned → ready_to_ship → shipped → completed`

---

## 背景

Allie 遠端邏輯驗收（2026-10-05）證實 `OrderController` 狀態機有 7 項缺陷。Joe 已裁定**開單修復**。
以下逐項為**事實（Allie 實測 + HQ 本機複核）→ 預期 → 修法**。

> ⚠️ 動 `ship()` 等高風險路徑前，先寫測試或於遠端用測試單驗證，嚴禁直接改動後不驗。
> ⚠️ 全程不得動 `burning.blade.php`、不得動全站 CSS。

---

## 修復清單

### G1｜`ship()` 允許 `draft`/`burning` 直接出貨（高風險）
- **事實**：`OrderController.php:447` allowed = `['ready_to_ship', 'burned', 'burning', 'draft']`。draft 可直接跳到 completed。
- **預期**：出貨僅允許 `ready_to_ship`（或至少 `burned`/`ready_to_ship`，**不含 draft/burning**）。
- **修法**：收斂 allowed 列表，移除 `'draft'`、`'burning'`；錯誤訊息同步更正。
- **驗收**：對 draft 單呼叫 ship → 被拒（維持 draft）；對 burning 單 → 被拒。

### G2｜`ship()` 跳過 `shipped` 狀態，7 步實際只有 5~6 步
- **事實**：`ship()` 直接設 `completed`，`shipped` 永不出現；`complete()` 因此不可達（G3）。
- **預期**：需先與 Joe/HQ 確認目標語意（見下方「待決策」），**預設修法**：
  - `ship()` → 設為 `shipped`（寫 `shipped_date`）；
  - `complete()` → 由 `shipped` → `completed`（寫 `delivered_date`）。
- **驗收**：完整鏈 `ready_to_ship → shipped → completed` 可走通；`shipped` 狀態確實出現。

### G3｜`complete()` 不可達（dead code）
- 由 G2 修復後即恢復可達；若 G2 採其他方案，需明確處理 `complete()`（保留或移除）。

### G4｜`finishBurning` 不檢查綁定數量
- **事實**：綁定數 < 訂單數量仍可轉 `burned`。
- **預期**：韌體品項需綁定數 >= 訂單數量方可 `burned`（或至少警告）。
- **修法**：於 `finishBurning` 加入數量檢查（**先確認是否有合理例外**，如有請回報再改）。

### G5｜Trigger 不存在，但程式註解聲稱有
- **事實**：`OrderController.php:471`、`:603` 註解寫「跨庫同步已改由 MySQL 觸發器 `trg_ali_device_bindings_sync_to_iotv9` 自動接管」，但 `SHOW TRIGGERS` 為空；同步實際全靠 PHP `commitRegistration()` 的 `updateOrInsert`。
- **預期**：註解與實作一致。
- **修法**：**先與 Ina 確認**是否計畫建 Trigger。
  - 若無 → 移除/更正這兩處錯誤註解（改回「由 PHP 雙寫同步」）。
  - 若有 → 由 Ina 建 Trigger，Allie 不動。

### G6｜所有產品 `license_fee=0` → royalties 不建帳
- **事實**：`recordFirmwareRoyalties()` 中 `$licenseFee <= 0` 時 `continue`，4 個產品全為 0。
- **預期**：需確認是**資料設定問題**還是**邏輯問題**。
- **修法**：**先回報** 4 個產品的 `software_license_fee` 現值與應設值；若邏輯無誤（fee=0 不建帳為合理），僅需確認資料，**不要改邏輯**。

### G7｜`destroy` 允許 `burning`/`burned` 刪單
- **事實**：destroy 允許非 shipped/completed/ready_to_ship，含 burning/burned，恐殘留 `iotv9.devices` 孤兒。
- **預期**：已燒錄/燒錄中訂單不應可刪（或刪除時需同步清 `iotv9.devices`）。
- **修法**：收斂 destroy 允許範圍，或補上 devices 清理。

---

## 待決策（動工前先回報 HQ）

1. **G2 語意**：7 步狀態機是否要保留 `shipped` 這一關？（影響 G2/G3 修法）
2. **G4 例外**：是否有「綁定數 < 數量仍可出貨」的合理業務情境？
3. **G5**：Ina 是否要建 Trigger？（Allie 不自行決定）
4. **G6**：`software_license_fee` 應設非零嗎？

> 上述 4 點若能在工單外快速釐清，直接修；否則**先回報 HQ 等待裁定**再動工，不得自行擴大重構。

---

## 驗收指標（附實際指令與輸出）

1. 每項修復前後 diff（`git diff`）
2. 遠端以**測試單**重跑路徑 A/B/C/D，附 status 查詢輸出
3. 測試資料清乾淨（orders / bindings / devices / settlements / royalties）
4. 站點存活：`curl -sI https://ali.tg25.win/` → 200/302
5. commit + push（附 hash）

---

## 禁止

- 改 `burning.blade.php`、全站 CSS、階段 C
- 動 production 老李正式單、真實客戶單
- 本機 artisan / 本機 DB
- 未確認 G2 語意前，不得擅自改變訂單狀態機的業務語意

## 完成定義

7 項逐一處理（修復或回報決策），驗收有實際佐證，回報寫入 `.taskflow/alliance/outbox/`。
