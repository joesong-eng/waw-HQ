# 任務：TASK_20261005_ALLIE_REMOVE_PHP_DUAL_WRITE

**派發時間**：2026-10-05
**優先級**：high
**負責人**：Allie (Alliance)
**性質**：架構收尾（⚠️ 先評估再動工）
**前置**：`TASK_20261005_INA_CREATE_CROSS_DB_TRIGGER`（Trigger 已建立）
**架構依據**：`PROPOSAL_20260914_ALLIE_DEVICES_CROSS_DB_ARCHITECTURE_REFACTOR`

---

## 背景

跨庫 Trigger 已由 Ina 建立並驗證（`trg_ali_device_bindings_sync_to_iotv9` INSERT + `..._upd` UPDATE）。
依原架構設計，下一步是**拔除 Alliance 應用層的 PHP 雙寫**，改由 Trigger 單一負責同步。

**現行雙寫位置**：
- `DeviceController.php:214` `DB::connection('waw_core')->table('devices')->updateOrInsert(...)`
- （`OrderController::syncDevicesToCore()` 已不存在，確認一下即可）

---

## ⚠️ 動工前必先評估的關鍵風險（HQ 已發現）

**Trigger 的守衛條件與 PHP 行為不一致**：

| 機制 | 同步條件 |
|------|----------|
| **PHP（現行）** | `chip_id` 有值即同步（**不等 node_id**）|
| **Trigger（新）** | `chip_id` 非空 **且 `node_id` 非空** 才同步（`20260914_cross_db_trigger...sql:36-37`）|

而**燒錄時序**是：
1. `commitRegistration()` 建 binding，**此時 `node_id = null`**（`DeviceController.php:194`）
2. 之後 `pair()` 階段才設 `node_id`（`DeviceController.php:372`）

**→ 若直接拔除 PHP 雙寫，燒錄當下 Trigger 因 node_id 為 null 不會同步，`iotv9.devices` 將延後到配對階段才出現。**

這是否可接受，**取決於業務預期**。

---

## 任務

### 步驟 1：評估並回報（先做，勿直接改）
回報以下判斷：
1. 現行業務上，**燒錄後到配對前**，`iotv9.devices` 是否需要有記錄？
   - 若有需求（例如掃碼/裝機前就要認得裝置）→ Trigger 守衛需放寬（改為 chip_id 有值即同步），**此改動須由 Ina 調整 Trigger，不在你範圍**。
   - 若可接受延後 → 直接進行步驟 2。
2. 確認 `OrderController` 是否仍有 `syncDevicesToCore()` 或其他雙寫殘留。

### 步驟 2：拔除 PHP 雙寫（經 HQ/Ina 確認後）
- 移除 `DeviceController.php` 的 `waw_core.devices` `updateOrInsert` 區塊（含其 Log）。
- **保留** try/catch 與錯誤處理骨架（改為驗證 Trigger 是否已寫入，或移除）。
- 修正 G5 相關錯誤註解（若先前已修則確認）。

### 步驟 3：驗證
- 燒錄 + 配對完整流程測試（測試單），確認 `iotv9.devices` 有正確記錄。
- 對照：移除前後 `iotv9.devices` 的寫入時機差異。

---

## 驗收指標（附實際佐證）

1. 步驟 1 的評估回報（含「燒錄→配對」時序對業務影響的判斷）
2. 移除的 diff
3. 測試單流程：binding 建立後 `iotv9.devices` 的狀態（觸發時機）
4. 測試資料清乾淨
5. commit + push（附 hash）
6. 站點存活：`curl -sI https://ali.tg25.win/` → 200/302

---

## 禁止

- 未經 HQ 確認，不得自行放寬 Trigger 守衛（那是 Ina 範圍）
- 改 `burning.blade.php`、全站 CSS
- 動 production 正式客戶單

## 完成定義

步驟 1 評估回報為**必須**；步驟 2 需等 HQ/Ina 就守衛條件裁定後執行。
回報寫入 `.taskflow/alliance/outbox/`。
