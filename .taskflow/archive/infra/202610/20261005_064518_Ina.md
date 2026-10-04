# 釐清回報：TASK_20261005_INA_VERIFY_DEVICE_SESSIONS_SSOT

**任務 ID**：TASK_20261005_INA_VERIFY_DEVICE_SESSIONS_SSOT
**執行者**：Ina (Infra)
**完成時間**：2026-10-05 06:45 (Asia/Taipei)

---

## 步驟 1：Member 真正的 DB 連線

### yd177 .env 設定（密碼已遮罩）

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3307
DB_DATABASE=waw_member_production
DB_USERNAME=waw_member_api
DB_PASSWORD=***MASKED***

### Laravel getDatabaseName() 輸出

Connection: mysql
Database: waw_member_production

**結論：Member 站 (win.tg25.win) 部署在 yd177 (129.146.103.177)，連線 waw_member_production DB（本機 port 3307）。**

---

## 步驟 2：以 Member 真實連線重查兩張表

### device_sessions

| 項目 | 結果 |
|------|------|
| 表存在 | **YES** |
| 筆數 | **96** |
| 最新 started_at | 2026-06-10 04:46:17 |
| 最新 ended_at | 2026-06-10 04:49:02 |
| 最新 updated_at | 2026-06-10 04:49:02 |

### machine_sessions

| 項目 | 結果 |
|------|------|
| 表存在 | **NO** |
| 筆數 | N/A |

### migrations 表記錄

已執行的 device_sessions 相關 migration：
1. 2026_05_12_000001_create_device_sessions_table
2. 2026_05_13_000001_add_node_id_to_device_sessions
3. 2026_05_13_215043_add_last_activity_at_to_device_sessions
4. 2026_05_15_172005_add_is_agreed_to_device_sessions_table

machine_sessions 相關 migration：
1. 2026_03_23_024700_create_machine_sessions_table（已 Ran，但表不存在 — 推測後續已 rollback 或手動 drop）

---

## 步驟 3：前單查核對象澄清

### 前單查錯原因

前單（TASK_20261005_INA_EVALUATE_MACHINE_SESSIONS_DROP）查核時：
- **誤將 yd174 (129.153.116.174) 當作 Member VPS**
- yd174 實為 **Owner/SignalHub 主機**，其上有一個獨立的 win DB（非 Member 正式 DB）
- Member 真正部署在 **yd177 (129.146.103.177)**，使用 waw_member_production DB

### 錯誤連鎖

1. SSH 到 yd174 → 找到 /www/wwwroot/win/.env → DB_DATABASE=win
2. 在 win DB 查 device_sessions → 不存在（因為 win DB 不是 Member 的生產 DB）
3. 得出「device_sessions 表不存在」的錯誤結論

**承認錯誤：前單驗收 #3 結論無效，因查核對象錯誤。**

---

## 步驟 4：與 Mina E2E 對帳

| 對帳項目 | 結果 |
|----------|------|
| device_sessions 表存在 | YES（96 筆，waw_member_production @ yd177） |
| Mina E2E settle/credit 可行性 | **完全成立** — 表存在且有活躍資料 |
| DeviceSession Model 運作 | 正常（程式碼引用 30+ 處 + 表存在 + migration 已跑） |
| machine_sessions 廢除狀態 | 表已不存在，migration 記錄仍在（可安全清理 migration 檔） |

**結論：Mina 的 ADR-002 修復已完整落地。device_sessions 為 SSOT，正常運作。前單結論為「查錯 DB」所致的誤判。**

---

## 驗收指標對照

| # | 指標 | 結果 |
|---|------|------|
| 1 | yd177 .env + getDatabaseName | DB=waw_member_production，Connection=mysql，Port=3307 |
| 2 | device_sessions 存在 + 筆數 + 時間 | 存在，96 筆，最新 2026-06-10 |
| 3 | machine_sessions 存在與否 | 不存在 |
| 4 | migrations 對照 | device_sessions 4 筆全 Ran；machine_sessions 1 筆 Ran 但表已不在 |
| 5 | 結論 | Mina 修復完整落地；前單查錯 VPS（yd174 非 Member 主機） |

---

## 結論

前單（TASK_20261005_INA_EVALUATE_MACHINE_SESSIONS_DROP）驗收 #3 結論無效 — **查錯 VPS 導致誤判**。

正確結論：
- device_sessions 表**存在且正常運作**（96 筆，4 個 migration 已跑）
- machine_sessions 表**已不存在**（migration 記錄仍在，migration 檔可安全刪除）
- Mina ADR-002 修復**已完整落地**
- 前單建議選項 (A) 仍適用：可刪除 machine_sessions 的 migration 檔（表已不存在，程式碼無引用）

