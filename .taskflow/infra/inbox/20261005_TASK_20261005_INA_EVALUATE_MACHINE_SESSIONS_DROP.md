# 任務：TASK_20261005_INA_EVALUATE_MACHINE_SESSIONS_DROP

**派發時間**：2026-10-05
**優先級**：medium
**負責人**：Ina (Infra / DB)
**性質**：結案評估（先查再做，禁止未備份 DDL）
**架構依據**：`ADR-002_MEMBER_DEVICE_SESSION_SSOT.md`

---

## 背景

ADR-002 已廢除 `MachineSession` 模型與 `machine_sessions` 表，裝置會話 SSOT 統一為 `device_sessions` / `App\Models\DeviceSession`。

現況（HQ 盤點 2026-10-05）：
- Member 程式碼：`MachineSession` 引用 **0**（僅剩 migration 檔的 `@deprecated` 註解）
- Member `database/migrations/2026_03_23_024700_create_machine_sessions_table.php` 仍存在（保留 `@deprecated` 註解）
- 生產 DB（Member 對應庫）之 `machine_sessions` 表**尚未 drop**

Mina 於 TASK_20261003_MINA_ALIGN_DEVICE_SESSION_SSOT 回報中明確註記：
> 「本表暫不 drop，歷史資料待 Ina 評估後另行處理。」

本單即為該評估。

---

## 任務

### 步驟 1：現況查核（唯讀）
1. 確認生產 DB 中 `machine_sessions` 表是否存在、筆數、最後寫入時間。
2. 確認是否仍有**任何**程式（Member 及其他專案）對該表讀寫（含 raw SQL、DB facade）。
3. 確認 `device_sessions` 是否已承接全部會話資料（筆數對照）。

### 步驟 2：風險評估
回報三種處置的建議與理由：
- (A) 直接 `DROP TABLE`（附影響面分析）
- (B) 先 `RENAME` 為 `_deprecated_machine_sessions` 觀察一段時間再 drop
- (C) 暫不 drop，僅保留現狀（需說明何時可再評估）

### 步驟 3：執行（僅在選 A/B 且 HQ 核准後）
- **DROP 前必須先備份**（mysqldump 單表），備份檔命名含日期，並於回報中提供備份路徑。
- 採線上無鎖 DDL（若適用）。

> ⚠️ **本單預設只做步驟 1、2（評估與回報）**。步驟 3 的實際 DDL **須待 HQ 依你的評估核准後另行派工**，不得自行執行。

---

## 驗收指標（附實際指令與輸出）

1. `SHOW TABLES LIKE 'machine_sessions'` → 存在/不存在 + 筆數
2. 全專案引用掃描：
   `grep -rn 'machine_sessions' PROJECT/*/app PROJECT/*/routes PROJECT/*/database --include='*.php'` → 結果
3. `device_sessions` 筆數對照
4. 三個處置選項的建議與理由（含風險）

---

## 禁止

- 未經 HQ 核准，**不得執行任何 DDL**（DROP/RENAME）
- 未備份不得刪除任何資料
- 不動 Member 以外的專案

## 完成定義

步驟 1、2 完成，4 項驗收有實際輸出，回報寫入 `.taskflow/infra/outbox/`。
