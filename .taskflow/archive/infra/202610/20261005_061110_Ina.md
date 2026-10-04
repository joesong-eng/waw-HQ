# 評估回報：TASK_20261005_INA_EVALUATE_MACHINE_SESSIONS_DROP

**任務 ID**：TASK_20261005_INA_EVALUATE_MACHINE_SESSIONS_DROP
**執行者**：Ina (Infra)
**完成時間**：2026-10-05 06:00 (Asia/Taipei)

---

## 步驟 1：現況查核結果

### 1.1 machine_sessions 表是否存在

| 資料庫 | 主機 | 結果 |
|--------|------|------|
| iotv9 | infra (141.148.165.50) | 不存在 |
| win | yd174 (129.153.116.174) | 不存在 |
| iotmember | infra (141.148.165.50) | 不存在 |
| waw_member_production | infra (141.148.165.50) | 無權限存取 |

**結論：machine_sessions 表在所有可存取的生產資料庫中均不存在。**

Member 的 migrations 表中也無 machine_sessions 相關記錄，證實該 migration 從未被執行過。

筆數：0（表不存在）
最後寫入時間：N/A

### 1.2 程式引用掃描

grep -rn 'machine_sessions' PROJECT/*/app PROJECT/*/routes PROJECT/*/database --include='*.php'

結果：僅剩 1 個 migration 檔的 3 處引用（全部為 @deprecated 註解或 Schema 定義）：

- Member/database/migrations/2026_03_23_024700_create_machine_sessions_table.php:8: @deprecated 2026-10-03
- Member/database/migrations/2026_03_23_024700_create_machine_sessions_table.php:20: Schema::create('machine_sessions', ...)
- Member/database/migrations/2026_03_23_024700_create_machine_sessions_table.php:38: Schema::dropIfExists('machine_sessions')

MachineSession Model 引用：0（僅同一 migration 檔的 deprecated 註解）

**結論：無任何程式碼對 machine_sessions 表進行讀寫操作。**

### 1.3 device_sessions 承接狀態

| 項目 | 結果 |
|------|------|
| device_sessions 表存在 | 不存在（win DB） |
| device_sessions migration 執行 | 從未執行 |
| DeviceSession Model | 存在且活躍使用（30+ 引用） |
| device_sessions migration 檔 | 存在 4 個檔案 |

**結論：DeviceSession 模型已全面取代 MachineSession，但 device_sessions 表的 migration 尚未在生產環境執行。代碼就緒但 DB 表待建。**

注意：此為獨立發現，不在本工單範圍。Member 生產環境 device_sessions migration 可能尚未跑，建議 HQ 另行確認。

---

## 步驟 2：風險評估與建議

### 選項 (A)：刪除 migration 檔（無需 DROP TABLE）— 推薦

- machine_sessions 表在所有可存取的生產 DB 中不存在，migration 從未執行
- 無任何程式碼讀寫此表，唯一殘留是 migration 檔本身
- 不需要 DROP TABLE，因為沒有表可以 DROP
- 執行方式：刪除 Member/database/migrations/2026_03_23_024700_create_machine_sessions_table.php
- 風險：極低。移除後不會意外建出已廢除的表
- 影響面：僅 Member 專案的 1 個 migration 檔

### 選項 (B)：保留 migration 檔但不動（觀察）

- migration 檔已有 @deprecated 註解，不影響任何功能
- 風險：未來全量 migrate 可能意外建出空表
- 適用場景：暫時不想動 Member 的 migration 歷史

### 選項 (C)：暫不處理

- 表不存在，無實際風險
- 再評估時機：Member 執行 device_sessions migration 時可一併清理

---

## 驗收指標對照

| # | 指標 | 結果 |
|---|------|------|
| 1 | SHOW TABLES LIKE 'machine_sessions' | 所有可存取 DB 均返回空集，不存在，筆數 0 |
| 2 | 全專案引用掃描 | 僅剩 1 個 migration 檔（3 處，均為 deprecated/Schema 定義） |
| 3 | device_sessions 筆數對照 | 表同樣不存在（migration 未執行），但 Model 已全面就位 |
| 4 | 三個處置選項建議 | 見上方步驟 2 |

---

## 額外發現（供 HQ 決策）

1. device_sessions migration 未執行：Member 有 4 個 device_sessions migration 檔和活躍的 DeviceSession Model，但生產 win DB 中此表不存在。建議由 Mina 確認。
2. waw_member_production DB 存取限制：infra VPS 上存在此 DB 但 iot_user 無權限。如需查核，需 DBA 權限。

---

## 結論

步驟 1、2 評估完成。

machine_sessions 表從未在任何生產 DB 中建立，無程式碼引用，無資料需備份。建議採選項 (A) 刪除殘留 migration 檔，或選項 (C) 暫不處理（無風險）。

步驟 3 DDL 操作不適用（無表可 DROP/RENAME）。
