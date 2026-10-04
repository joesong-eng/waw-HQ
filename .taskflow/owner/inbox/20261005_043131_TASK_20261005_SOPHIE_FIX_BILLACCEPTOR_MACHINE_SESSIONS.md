# 任務：TASK_20261005_SOPHIE_FIX_BILLACCEPTOR_MACHINE_SESSIONS

**派發時間**：2026-10-05 04:30
**優先級**：high
**負責人**：Sophie (Owner)
**來源**：HQ 整體盤點發現

---

## 📋 任務內容

### 問題描述

Owner 專案 app/Services/BillAcceptorService.php 仍在跨庫查詢已廢棄的 machine_sessions 表，未跟隨 ADR-002 裝置會話 SSOT 統一（device_sessions）。

### 受影響位置

| 行號 | 方法 | 問題 |
|------|------|------|
| **L49** | handleEscrow() | 跨庫查 machine_sessions 表，使用 machine_id + status=BUSY |
| **L121** | handleStacked() | 跨庫查 machine_sessions 表，使用 machine_id |

### 對照表（machine_sessions -> device_sessions）

| 舊欄位 | 新欄位 | 說明 |
|--------|--------|------|
| machine_id | chip_id | 識別欄位改名 |
| status = BUSY | status = active | 狀態語意統一 |
| machine_sessions | device_sessions | 表名統一 |

### Member 庫 device_sessions 表結構（參考）

- id (bigint, pk)
- member_id (unsignedBigInteger)
- chip_id (string, 50)
- node_id (string, 20, nullable)
- status (enum: active/ended/timeout, default: active)
- started_at (timestamp)
- ended_at (timestamp, nullable)

### 修改要求

1. **L49 handleEscrow()**：將 machine_sessions 查詢改為 device_sessions，machine_id 改為 chip_id，status=BUSY 改為 status=active
2. **L121 handleStacked()**：同上，machine_sessions -> device_sessions，machine_id -> chip_id
3. **檢查同檔案其他位置**（L132-159 區段）：確認是否也有 machine_sessions 殘留，一併修正
4. **嚴禁只改表名不改欄位**：machine_id 欄位在 device_sessions 表中不存在，必須改為 chip_id

---

## ✅ 驗收指標

1. grep machine_sessions in PROJECT/Owner/app/ = **0 hits**
2. grep machine_id in BillAcceptorService.php = **0 hits**
3. grep device_sessions in BillAcceptorService.php = **>=2 hits**
4. BillAcceptorService 邏輯不變（handleEscrow + handleStacked 流程一致，僅資料來源改表）
5. 附上 controller 載入確認

---

**派發者**：HQ
**派發時間**：2026-10-05 04:30