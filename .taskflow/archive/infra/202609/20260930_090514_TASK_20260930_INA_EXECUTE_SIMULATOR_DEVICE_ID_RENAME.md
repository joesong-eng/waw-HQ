# 任務：TASK_20260930_INA_EXECUTE_SIMULATOR_DEVICE_ID_RENAME

**派發時間**：2026-09-30 11:30  
**優先級**：P2（計劃性維護）  
**負責人**：Ina (Infra Master)  
**參考報告**：`.taskflow/infra/outbox/20260930_110500_REPORT_TASK_INA_SIMULATOR_DEVICE_ID_RENAME.md`  
**決策核准**：HQ 核准執行，**Q1 採納「選項 A（同步更新歷史流水與封存表）」**（模擬資料無財務影響，統一 ID 避免報表斷裂）。

---

## 📋 任務目標

將 hardware/simulator 7 台模擬設備 chip_id 由舊隨機字串更新為 12 碼小寫無冒號 MAC 格式，並同步更新程式碼設定、資料庫主表及歷史流水，重啟模擬器服務確保端到端一致。

---

## 🔄 新舊 ID 對照表

舊 chip_id              | 新 chip_id     | 設備名稱
------------------------|----------------|---------------------------
sr9adyxpdyt1tuf7        | a4c3f21b0e91   | 娃娃機 #1
chpw9fz16m6n391l        | b8d72e4a1f05   | 娃娃機 #2
w1ey33c1ta5sxtsr        | c1e84d3b2a67   | 娃娃機 #3
49tmby4z703wxqmp        | d5f96c4e3b18   | 娃娃機 #4
u19iy1yp17sm7o7h        | e2a07b5c4d29   | 博弈機台 #1
hxnz44vshjju0cjz        | f3b18c6d5e30   | 街機遊戲 #1
i767e3ieju7wncy2        | a6c29d7e4f41   | 娃娃機 #5（西門旗艦店，手動模式）

---

## 🛠️ 執行內容與步驟

### 1. 程式碼修改（本機）
- `Infra/hardware/simulator/config/devices.json`：更新 7 台設備 chip_id / device_uuid
- `Infra/mqtt/scripts/generate_mock_snapshots.py`：更新對應 5 個舊 ID
- `Owner/database/seeders/DeviceSeeder.php`：更新對應 5 個舊 ID

### 2. Git 提交與推播
- 完成修改後提交 Git commit 並 push。

### 3. 部署與重啟服務
- 執行 `./dev_tools/waw_ops.sh deploy infra` 部署至遠端 VPS。
- 重啟 hardware-simulator 相關服務。

### 4. 資料庫更新（iotv9 @ infra，採納選項 A）
依對照表執行 UPDATE：
- `devices.chip_id` (5 筆)
- `device_snapshots.chip_id` (~9,380 筆)
- `revenue_facts.chip_id` (~66 萬筆，注意批次或索引，避免鎖表)
- `revenue_facts_archive_20260804.chip_id` (~160 萬筆，批次更新)

### 5. 驗證與回報
- 驗證模擬器重啟後發布之 MQTT payload 為新 MAC 格式。
- 抽查 DB 資料確認更新完成。
- 回報完成報告至 `.taskflow/infra/outbox/`。

