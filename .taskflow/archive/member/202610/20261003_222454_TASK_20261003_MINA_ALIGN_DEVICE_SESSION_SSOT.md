# 任務工單：Member 裝置會話 SSOT 對齊（廢除 MachineSession）

- **工單編號**：TASK_20261003_MINA_ALIGN_DEVICE_SESSION_SSOT
- **派發時間**：2026-10-03
- **負責人**：Mina (Member)
- **優先級**：P2
- **架構依據**：`brains/knowledge/03_system_architecture/ADR-002_MEMBER_DEVICE_SESSION_SSOT.md`

---

## 一、HQ 架構裁定摘要（已定案）

Member 專案同時存在兩套裝置會話模型：

| 模型 | 表 | 狀態 |
|:---|:---|:---|
| `DeviceSession` | `device_sessions` | **現行 SSOT**（DeviceController 20+ 處、channels、timeout 指令使用）|
| `MachineSession` | `machine_sessions` | **殘留**（僅 CallbackController 2 處）|

**裁定：廢除 `MachineSession`，統一為 `DeviceSession`。**

依據：`NAMING_AUTHORITY.md`（識別為 chip_id + node_id）、
`DECISION_REMOVE_MACHINE_NUMBER_2026-09-04`（移除 machine_* 命名）、
Owner/Infra 已全面改 Device 語意。

---

## 二、工作項目

### 項目 1：改寫 `CallbackController` 兩處

**檔案**：`app/Http/Controllers/Api/CallbackController.php`

| 行 | 現況 | 改為 |
|:--|:---|:---|
| 59 | `MachineSession::where('machine_id', $tx->reference_id)->update(['status' => 'ERROR'])` | `DeviceSession::where('chip_id', $tx->reference_id)->update(['status' => 'ended', 'ended_at' => now()])` |
| 138 | `MachineSession::where('machine_id', $deviceId)->delete()` | `DeviceSession::where('chip_id', $deviceId)->where('status', 'active')->update(['status' => 'ended', 'ended_at' => now()])` |

**注意**：
- `DeviceSession` status enum 為 `active|ended|timeout`（非 `IDLE|BUSY|ERROR`）。
- 用**結束會話**語意（`ended`）而非刪除，保留歷史軌跡（符合 `TimeoutDeviceSessions` 既有模式）。
- 記得 `use App\Models\DeviceSession;`（移除 `MachineSession` 引用）。

### 項目 2：刪除 `MachineSession` Model

- 刪除 `app/Models/MachineSession.php`。

### 項目 3：`machine_sessions` migration 標記 deprecated

- 於 `database/migrations/2026_03_23_024700_create_machine_sessions_table.php` 加註解說明已廢棄。
- **勿 drop 表**（歷史資料待 Ina 評估）。

---

## 三、驗收指標（必須附實際輸出）

| # | 驗收項 | 方式 | 期望 |
|:--|:---|:---|:---|
| 1 | MachineSession 引用歸零 | `grep -rn 'MachineSession' app/ routes/` | 0 hits |
| 2 | 退款路徑正常 | `POST /api/callback/settle` | 200，對應 DeviceSession 轉 `ended` |
| 3 | 無回歸 | DeviceController / channels / timeout 功能 | 正常 |
| 4 | 站點存活 | `curl -sI https://win.tg25.win/` | 2xx |

---

## 四、回報要求

寫入 `.taskflow/member/outbox/`，附：Commit SHA、grep 驗收輸出、API 測試結果、curl 狀態碼。

---

## 五、注意

- **只改 CallbackController 兩處 + 刪 Model**，勿動其他 DeviceSession 邏輯。
- 若不確定某處語意，先回報 HQ，勿臆測。
