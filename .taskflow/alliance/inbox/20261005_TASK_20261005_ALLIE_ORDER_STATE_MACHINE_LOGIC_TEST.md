# 任務：TASK_20261005_ALLIE_ORDER_STATE_MACHINE_LOGIC_TEST（重新派發）

**派發時間**：2026-10-05
**優先級**：high
**負責人**：Allie (Alliance)
**性質**：遠端邏輯驗收（先測、先報事實）
**原單**：TASK_20260921_ALLIE_ORDER_STATE_MACHINE_LOGIC_TEST（2026-09-21 派發，**查無回報，判定掉單**）

> ⚠️ HQ 全系統盤點發現：原單從未回報（`.taskflow` 與 `archive/` 均無對應 REPORT）。本單為重新派發，內容與原單一致，請務必完成並回報。

---

## 背景

Alliance 站點改善的 UI 階段 C/D 已凍結。現在要驗 **訂單 7 步狀態機 + 燒錄入庫 + 出貨結算** 是否真的閉環。

HQ 已從程式碼讀到與註解／計畫不一致之處，本工單要你用 **遠端 DB + HTTP/Artisan** 證明現況，不要用「程式看起來對」交差。

**本機禁止** `php artisan`、禁止本地 DB。一律使用：
```bash
../../dev_tools/waw_ops.sh remote alliance "..."
```
必要時才 `deploy alliance`（Ina 已補 migrations 帳本，標準 deploy 應可空跑 migrate）。

---

## 規格（以程式為準，對照預期）

計畫／註解寫的 7 步：
`draft -> confirmed -> burning -> burned -> ready_to_ship -> shipped -> completed`

實際 `OrderController` 行為（HQ 靜態判讀，需你實測驗證）：

| 動作 | 允許來源 | 結果 |
|---|---|---|
| confirm | draft（且有 orderItems） | confirmed |
| revertToDraft | confirmed | draft |
| startBurning | confirmed | 有韌體 → burning；無韌體 → **直接 ready_to_ship** |
| finishBurning | burning | burned（**不檢查綁定數量是否滿額**） |
| readyToShip | burned 或 confirmed | ready_to_ship |
| ship | ready_to_ship **或 burned / burning / draft** | **直接 completed**（shipped_date + delivered_date 同寫） |
| complete | **僅 shipped** | completed |
| batchShip | **僅 ready_to_ship** | 同上 completed |
| destroy | 非 shipped/completed/ready_to_ship | 先刪 orderItems 再刪單 |
| batchDestroy | 僅 draft 直接 delete（靠 FK cascade） | — |

`DeviceController::commitRegistration`：寫 `ali_device_bindings` 後，**PHP 仍對 `waw_core.devices` updateOrInsert**（commit `548c196`，在 `ba6f6f6` 拔雙寫之後又加回來）。同時 Ina 宣稱 DB Trigger 也會同步。本測必須分清「Trigger 有沒有動」與「PHP 有沒有動」。

---

## 必做驗收（用獨立測試單，勿動老李／正式客戶進行中單）

建立測試單 `LOGIC-TEST-20261005`（能刪就刪）。產品至少覆蓋兩類。

### 路徑 A：狀態機逐步驗證
依序 `confirm → startBurning → finishBurning → readyToShip → ship`，每步記錄：
- 訂單 status、HTTP/方法結果
- 變更後 `POST /api/devices/commit-registration` 之回應

### 路徑 B：燒錄入庫（chip 綁定）
測試 chip `TESTLOGIC21`，測完刪。
- `alliance_db.ali_device_bindings` 與 `iotv9.devices` 是否同步
- chip_id、owner_id、status=`pending_setup`、public_token
- 分清 Trigger 與 PHP 各自做了什麼

### 路徑 C：出貨結算
至少附：binding、`iotv9.devices` 之結果。若無法開單，記錄阻塞點。

### 路徑 D：邊界（不合規轉換）
驗證 HQ 判讀的「漏洞」（如 ship 允許 draft 直接 completed、finishBurning 不檢查數量、burned 可被 readyToShip 覆蓋等），用「事實 / 預期 / 建議」三行回報，**不要直接改狀態機除非資料會壞**。

**測完刪測試單與測試 chip**（devices / bindings / 測試訂單），留下 SQL 證據。

---

## 回報必須附的證據（文字 ✅ 不算完成）

每條路徑附：
1. 測試單 `id` / `order_no` / 產品 sku
2. 遠端指令與輸出（migrate:status 一行即可證明環境；重點是訂單 status 查詢）
3. 關鍵 SELECT 結果（orders、bindings、devices、settlements、royalties）
4. 與規格不一致處，用「事實 / 預期 / 建議」三行

若判斷必須修程式才能測下去（500、FK 擋刪、Trigger 炸掉），先修最小範圍、獨立 commit，commit message 寫清，再繼續測。

---

## 禁止

- 改 `burning.blade.php`
- 改全站 CSS／階段 C
- 動 production 老李正式單、真實出貨客戶單
- 本機 artisan / 本機 DB
- 未備份就刪非測試資料

## 完成定義

路徑 A/B/C/D 都有遠端證據；測試資料清乾淨；規格漏洞清單交 HQ，不自行擴大重構。
回報寫入 `.taskflow/alliance/outbox/`。
