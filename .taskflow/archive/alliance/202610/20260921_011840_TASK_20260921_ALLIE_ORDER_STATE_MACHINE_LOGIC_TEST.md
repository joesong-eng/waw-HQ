# 任務：TASK_20260921_ALLIE_ORDER_STATE_MACHINE_LOGIC_TEST

**派發時間**：2026-09-21
**優先級**：high
**負責人**：Allie (Alliance)
**派發來源**：HQ / Joe
**性質**：遠端邏輯驗收（先測、先報事實）。發現缺陷可修，但禁止順手改 UI、禁止動 burning.blade.php、禁止資料庫 migration DDL。

---

## 背景

Alliance 站點改善的 UI 階段 C/D 已凍結。現在驗 **訂單 7 步狀態機 + 燒錄入庫 + 出貨結算** 是否真的閉環。

HQ 已從程式碼讀到與註解／計畫不一致之處，本工單要你用 **遠端 DB + HTTP/Artisan** 證明現況，不要用「程式看起來對」交差。

本機禁止 `php artisan`、禁止本地 DB。一律：

```bash
../../dev_tools/waw_ops.sh remote alliance "..."
```

必要時才 `deploy alliance`（Ina 已補 migrations 帳本，標準 deploy 應可空跑 migrate）。

---

## 規格（以程式為準，對照預期）

計畫／註解寫的 7 步：

`draft -> confirmed -> burning -> burned -> ready_to_ship -> shipped -> completed`

實際 `OrderController`：

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
| batchDestroy | 僅 draft | 直接 delete（靠 FK cascade） |

`DeviceController::commitRegistration`：寫 `ali_device_bindings` 後，**PHP 仍 `waw_core.devices` updateOrInsert**（commit `548c196`，在 `ba6f6f6` 拔雙寫之後又加回來）。同時 Ina 宣稱 DB Trigger 也會同步。本測必須分清「Trigger 有沒有動」與「PHP 有沒有動」。

---

## 必做驗收（用獨立測試單，勿動老李／正式客戶進行中單）

建一張明顯測試單（客戶名含 `LOGIC-TEST-20260921`，能刪就刪）。產品至少覆蓋兩類：

- A. **含韌體**（has_firmware=true）
- B. **純配件**（has_firmware=false）可另開一張，或同一環境各測一次

每步記錄：變更前 status、HTTP/方法結果、變更後 status、相關列（settlements / royalties / activity_logs / devices）。

### 路徑 A：含韌體正常鏈

1. 開單 draft，無品項 → confirm 必須失敗。
2. 加韌體品項 → confirm → confirmed。
3. revertToDraft → draft → 再 confirm。
4. startBurning → burning。
5. `POST /api/devices/commit-registration` 寫入一筆測試 chip_id（前綴 `TESTLOGIC21`，測完刪）。
6. 查 `alliance_db.ali_device_bindings` 與 `iotv9.devices`：chip_id、owner_id、status=`pending_setup`、public_token。
7. **雙寫稽核**：暫時判斷 Trigger vs PHP。至少附：binding 寫入時間、devices 寫入時間、Laravel log 是否出現 `[Alliance] commitRegistration() 燒錄成功，已同步至 iotv9.devices`。若無法關 Trigger，誠實寫「無法隔離，僅能證明 devices 有列 + PHP log 有/無」。
8. finishBurning：**先故意綁定數 < 訂單數量**，看系統是否仍允許 burned（HQ 預期：目前會允許。確認即可，本波先不要擅自加防呆，除非 Joe 後續下令）。
9. readyToShip → ready_to_ship。
10. 單筆 ship → 訂單變 **completed**（不是 shipped）。必須產出：授權快照、firmware royalties（若 license_fee>0）、AliSettlement、activity_log `ship_order`、notification_inbox（若跨庫通知仍在）。
11. 對已 completed 單呼叫 complete()：必須失敗（因為 complete 只收 shipped）。
12. 對 completed 單確認 show 頁／API 無燒錄入口、不可再 ship／刪除。

### 路徑 B：無韌體捷徑

1. 純配件單 confirmed → startBurning 應 **直接 ready_to_ship**，不進 burning。
2. 此單 ship 是否仍跑 royalties（應跳過無韌體）但仍可能有 settlement。

### 路徑 C：非法跳步（防呆）

對測試單逐一打，預期失敗並維持原 status：

- confirmed 直接 finishBurning
- draft 直接 readyToShip
- completed 再 ship
- burning 直接 complete
- **單筆 ship 從 draft / burning / burned**：HQ 看到程式 **允許**。請實測並標成「規格漏洞」或「有意捷徑」，不要擅自改，除非造成資料損壞。
- batchShip 混打 draft+ready_to_ship：只出貨 ready_to_ship，draft 不動。
- batchDestroy 打非 draft：筆數 0，資料仍在。

### 路徑 D：出貨後核心庫

ship 之後：

- `iotv9.devices` 測試 chip 仍在，不被出貨覆寫成亂 status（pending_setup 可被 SignalHub 後續改 active，本測不要去改 SignalHub）。
- Alliance 本地 binding 仍在。
- 測完 **刪測試單與測試 chip**（devices / bindings / 測試訂單），留下 SQL 證據。

---

## 回報必須附的證據

文字 ✅ 不算完成。每條路徑附：

1. 測試單 `id` / `order_no` / 產品 sku
2. 遠端指令與輸出（migrate:status 一行即可證明環境；重點是訂單 status 查詢）
3. 關鍵 SELECT 結果（orders、bindings、devices、settlements、royalties）
4. 與規格不一致處，用「事實 / 預期 / 建議」三行，**不要直接改狀態機除非資料會壞**

若你判斷必須修程式才能測下去（500、FK 擋刪、Trigger 炸掉），先修最小範圍、獨立 commit，commit message 寫清，再繼續測。

---

## 禁止

- 改 `burning.blade.php`
- 改全站 CSS／階段 C
- 動 production 老李正式單、真實出貨客戶單
- 本機 artisan / 本機 DB
- 未備份就刪非測試資料

## 完成定義

路徑 A/B/C/D 都有遠端證據；測試資料清乾淨；規格漏洞清單交 HQ，不自行擴大重構。
