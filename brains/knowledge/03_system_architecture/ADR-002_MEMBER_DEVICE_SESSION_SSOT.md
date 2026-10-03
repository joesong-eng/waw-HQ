# ADR-002：Member 裝置會話 SSOT 對齊（廢除 MachineSession）

> **文件類型**：Architecture Decision Record
> **決策者**：HQ
> **建立日期**：2026-10-03
> **狀態**：Accepted（待實作）
> **關聯 SPEC**：`WAW_CLEANUP_AND_TASKS_SPEC_20261003.md` P2-1
> **關聯權威**：`NAMING_AUTHORITY.md`、`DECISION_REMOVE_MACHINE_NUMBER_2026-09-04.md`、
> `05_business_flows/game_v0_arcade/DEVICE_IDENTIFICATION_SYSTEM.md`

---

## 1. 背景

HQ 盤點發現 Member 專案**同時存在兩套裝置會話模型**：

| 模型 | 表 | 使用情況 |
|:---|:---|:---|
| `DeviceSession` | `device_sessions` | **現行 SSOT**：`DeviceController`(20+ 處)、`channels.php`、`TimeoutDeviceSessions`、`CheckOfflineSessions`、`DeviceCreditLog` 關聯 |
| `MachineSession` | `machine_sessions` | **殘留**：僅 `CallbackController.php:59/138` 兩處使用 |

### 欄位對照

```
device_sessions (現行)          machine_sessions (殘留)
─────────────────────────      ─────────────────────────
id                              id
member_id (FK)                  member_id (nullable FK)
chip_id  (12位hex)              machine_id  (ESP32 id)
node_id  (device_NNN)           —
status (active|ended|timeout)   status (IDLE|BUSY|ERROR)
started_at / ended_at           session_start_at / last_active_at
last_activity_at                —
is_agreed                       —
                                mac_address, hardware_state
```

### 架構事實

1. `machine_sessions` 表**除 migration 定義外，無任何有效讀寫路徑**（全域搜尋確認）。
2. `MachineSession` 的兩處使用（`CallbackController`）語意上即「依裝置識別碼更新/刪除會話」，
   與 `DeviceSession` 完全重疊。
3. 命名權威（`NAMING_AUTHORITY.md`）明確：遊戲機識別為 **`chip_id`（硬體層）+ `node_id`（產品層）**，
   會話應為 `device_sessions.node_id`。
4. `DECISION_REMOVE_MACHINE_NUMBER_2026-09-04` 已裁定移除 `machine_*` 命名概念。
5. Owner / Infra 已全面改用 Device 語意（Sophie 於 2026-10-03 完成 `machines` 表清除）。

---

## 2. 核心決策

### 決策一：廢除 `MachineSession`，統一為 `DeviceSession`

**理由**：`MachineSession` 是 `machines` 舊概念的殘留，與 `DeviceSession` 功能重疊，
且違反 `DECISION_REMOVE_MACHINE_NUMBER` 與 `NAMING_AUTHORITY`。保留會造成雙寫/語意混淆。

### 決策二：`CallbackController` 改用 `DeviceSession`

`CallbackController` 的兩處 `MachineSession` 呼叫需改寫：

| 行 | 現況 | 改為 |
|:--|:---|:---|
| 59 | `MachineSession::where('machine_id', $tx->reference_id)->update(['status' => 'ERROR'])` | `DeviceSession::where('chip_id', $tx->reference_id)->update(['status' => 'ended'])` |
| 138 | `MachineSession::where('machine_id', $deviceId)->delete()` | `DeviceSession::where('chip_id', $deviceId)->where('status', 'active')->update(['status' => 'ended', 'ended_at' => now()])` |

> **注意**：`DeviceSession` 的 status enum 為 `active|ended|timeout`，
> 與 `MachineSession` 的 `IDLE|BUSY|ERROR` 不同。改用**結束會話**語意（`ended`），
> 而非刪除記錄（保留歷史軌跡，符合 `TimeoutDeviceSessions` 既有模式）。

### 決策三：`machine_sessions` 表處置

- **不立即 drop**（避免影響未知的歷史資料）。
- 先將 migration 標記為 deprecated（加註解），列為後續清理項。
- 確認無資料依賴後，再由 Ina 評估 drop。

---

## 3. 影響範圍

| 檔案 | 變更 |
|:---|:---|
| `app/Models/MachineSession.php` | 刪除 |
| `app/Http/Controllers/Api/CallbackController.php` | 2 處改用 `DeviceSession` |
| `database/migrations/2026_03_23_024700_create_machine_sessions_table.php` | 加 deprecated 註解 |

---

## 4. 實作派工

| 任務 | 負責 | 內容 |
|:---|:---|:---|
| MB-1 | **Mina** | 依決策二改寫 `CallbackController` 兩處 + 刪 `MachineSession` Model |
| MB-2 | **Ina** | 評估 `machine_sessions` 表是否有歷史資料，決定 drop 時機（P3，後續）|

---

## 5. 驗收

| # | 驗收項 | 期望 |
|:--|:---|:---|
| 1 | `MachineSession` 引用歸零 | `grep -rn 'MachineSession' app/ routes/` = 0 hits |
| 2 | Callback 退款路徑正常 | `POST /api/callback/settle` 回 200，對應 DeviceSession 狀態轉 `ended` |
| 3 | 無回歸 | 既有 `DeviceSession` 功能（DeviceController / channels / timeout）不受影響 |
| 4 | 站點存活 | `curl -sI https://win.tg25.win/` = 2xx |

---

**維護者**：HQ
**最後更新**：2026-10-03
