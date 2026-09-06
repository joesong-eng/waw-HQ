# 遊戲機 3.0 系統架構與業務流程規格書 (Game Machine V3 Core Specification)

> **版本**：v3.0.0 (精煉合併版)  
> **最後更新**：2026-06-05  
> **狀態**：Active / Authoritative  
> **適用角色**：Mina (Member), Ina (Infra), Sophie (Owner), Coli (Firmware)

---

## 導言
本規格書將原有的遊戲機 3.0 (game_v0_v3) 設計決策、API 規格、MQTT 協議與異常矩陣完整合併，作為遊戲機開分與會話管理系統開發之唯一指導法典。

---

## =========================================================================
## 🔴 模組：核心設計決策與架構 (01_design_decisions.md)
## =========================================================================

> **版本**: 3.0.0  
> **日期**: 2026-05-15  
> **維護者**: HQ

---

## 一、設計決策總表（已拍板，不再討論）

| 決策 | 結論 | 理由 |
|------|------|------|
| Session 表位置 | `memberv9.device_sessions` | Session 是「會員與機台的綁定關係」，屬於會員業務邏輯 |
| Session 管理方 | Member（Mina） | 不是 Owner（Sophie） |
| Session 三層保護 | 120秒 + 5分鐘 + 即時 | 互相補充，確保機台不被永久鎖死 |
| 一人一台 | 只查 `device_sessions` | 不影響 `kiosk_sessions` |
| 空窗期撿便宜 | **接受業務風險** | 類比真實街機，不告知店員就離開，別人可能拿走分數 |
| 孤兒分數 | 記錄但不補償 | 寫入 `device_orphan_logs`，累積數據後評估 |
| 洗分方式 | 手機按洗分鍵 | Infra 發 `settle_credit` → 韌體觸發 PIN_OUT2 一次 |
| 累計值傳遞 | Infra 傳原始累計值 | Member 自己算 delta 並存 `cumulative_amount` |
| MQTT topic | `device/{chip_id}/cmd` | 不是 `command` |
| QR Code 格式 | URL 格式 | `https://win.tg25.win/m/play?node_id=device_001` |
| 簡化參數（測試） | 1:1 比例 | 1元=1代幣=1分=1彩票 |
| 測試設備 | i767e3ieju7wncy2 | 模擬器，node_id=device_001 |
| 重複掃碼 | 回傳現有 session | 允許重新打開頁面 |
| ESP32 離線處理 | 提示未連線 | 不強制結束 session，等待恢復或 10 分鐘自動 timeout |
| 合約條款 | 掃碼時顯示 | bind 成功後，遊戲畫面前 |

---

## 二、三層保護機制

### 設計理念
- **不限制遊戲時間**：玩家可以玩任意長時間（只要持續按鍵）
- **快速釋放機台**：玩家離開後 120 秒自動釋放
- **即時偵測斷線**：ESP32 斷線立刻釋放機台
- **兜底保護**：10 分鐘無心跳強制釋放（防止 GPIO 未接線）

### Layer 1: Session 監測（120 秒）

**用途**：判斷「玩家已離開」

**流程**：
```
Member bind 成功
  ↓
發送 MQTT: device/{chip_id}/cmd
  Payload: { "command": "start_session", "params": {"timeout_sec": 120} }
  ↓
ESP32 收到 → 啟動 120 秒計時器
  ↓
GPIO IN4 (SENSE_ACTIVITY) 有活動 → 重置計時器
  ↓
120 秒無活動 → ESP32 發送 MQTT
  Topic: device/{chip_id}/data
  Payload: { "type": "session_timeout" }
  ↓
Infra Listener → POST /internal/device/session-timeout
  ↓
Member 收到 → 解綁 session（status=timeout）
```

**關鍵**：
- ESP32 自己計時（不依賴 Member 排程）
- GPIO IN4 接遊戲機活動按鍵（start鍵、射擊鍵、油門鍵等）
- 不發送 activity MQTT（減少流量）

---

### Layer 2: 診斷心跳（5 分鐘）

**用途**：判斷「ESP32 存活」

**流程**：
```
ESP32 每 5 分鐘發送診斷心跳
  Topic: device/{chip_id}/data/diagnostic
  ↓
Infra Listener 收到：
  1. 更新 iotv9.devices.last_seen_at（Owner DB）
  2. 轉發 Member: POST /internal/device/heartbeat
  ↓
Member 後端：
  1. 查 device_sessions WHERE chip_id=xxx AND status=active
  2. 更新 last_heartbeat_at = now()
  ↓
Member 排程（每分鐘執行）：
  查詢 last_heartbeat_at < NOW() - INTERVAL 10 MINUTE
  → 強制 timeout
```

**關鍵**：
- 已有機制（IOTwawS3 已實作）
- 用於判斷 ESP32 是否存活（不是玩家是否在玩）
- 10 分鐘無心跳 → 強制 timeout（兜底保護）

---

### Layer 3: MQTT LWT（即時）

**用途**：即時偵測「ESP32 斷線」

**流程**：
```
ESP32 斷線（斷電、網路中斷等）
  ↓
MQTT Broker 立刻發布 LWT
  Topic: device/{chip_id}/status
  Payload: offline
  ↓
Infra Listener 收到：
  1. 更新 iotv9.devices.last_seen_at = NULL
  2. 轉發 Member: POST /internal/device/offline
  ↓
Member 後端：
  1. 查 device_sessions WHERE chip_id=xxx AND status=active
  2. 立刻強制 timeout：status=timeout, ended_at=now()
```

**關鍵**：
- 已有機制（IOTwawS3 已實作）
- 即時偵測（不需要等待）
- 立刻釋放機台

---

## 三、業務規則

### 1. 一人一台

**規則**：會員同時只能使用一台遊戲機

**實作**：
```sql
-- bind 時檢查
SELECT * FROM device_sessions 
WHERE member_id = ? AND status = 'active'
```

**注意**：
- 只查 `device_sessions`
- **不查** `kiosk_sessions`（兌幣機的 session）
- 兩者完全分離，互不影響

---

### 2. 空窗期撿便宜（接受業務風險）

**情境**：
1. 小明玩完遊戲，機台上還有 50 分
2. 小明忘記洗分，120 秒後 session timeout
3. 小李掃碼 → 建立新 session
4. 小李可以：
   - 繼續玩這 50 分
   - 洗分拿走 50 張彩票

**系統行為**：
- ✅ 不阻止
- ✅ 不警告
- ✅ 記錄在 wallet_transactions（小李的正常洗分）

**業務決策**：
**接受風險**，類比真實街機：
- 如果玩家不告知店員就離開
- 別人可能拿走剩餘分數
- 這是玩家自己的責任

**合約條款保護**：
> 「120 秒無遊戲活動將自動結束遊戲」  
> 「結束遊戲前請先洗分」

---

### 3. 孤兒分數

**情境**：
- Session 已死（timeout）
- 無人掃碼
- 有人按機台物理洗分鍵

**系統行為**：
```
ESP32 採集 → credit_out
  ↓
Member 收到 → 查無 active session
  ↓
寫入 device_orphan_logs：
  - chip_id
  - cumulative_amount
  - pulse_count
  ↓
彩票不入帳
```

**業務決策**：
- ✅ 記錄但不補償
- ✅ 累積數據後評估是否調整超時時間

---

### 4. 洗分流程

**規則**：不需要再掃碼

**流程**：
1. Session alive + ESP32 alive → 頁面顯示 [繼續開分] [洗分] [結束]
2. Session alive + ESP32 offline → 提示「機台未連線」，無法洗分
3. 如果頁面關閉 → 再掃碼恢復（情境：重複掃碼）

**不需要**：
- ❌ 洗分前再掃一次碼
- ❌ 洗分後再掃碼才能繼續

---

### 5. 重複掃碼

**情境**：小明在存活期再掃自己正在用的機台

**系統行為**：
```
POST /api/device/bind { "node_id": "device_001" }
  ↓
Member 後端：
  1. 查 device_sessions → 有 active session（member_id=2，小明自己）
  2. 查 Infra：ESP32 alive = true ✅
  3. 回傳現有 session
  ↓
前端顯示：[繼續開分] [洗分] [結束]
```

**用途**：
- 允許重新打開頁面
- 手機沒電、關閉頁面後可以重新掃碼

---

### 6. ESP32 離線處理

**情境**：有 session 但 ESP32 離線（alive = false）

**系統行為**：
```
POST /api/device/bind
  ↓
Member 檢查：
  1. 有 active session ✅
  2. ESP32 alive = false ❌
  3. 回傳 503「機台未連線」
  ↓
前端顯示：
  ⚠️ 機台未連線
  請確認機台電源後重新掃描
  [重新掃描] [結束遊戲]
```

**不強制結束 session**：
- 等待 ESP32 恢復 → 小明可以繼續遊戲
- 10 分鐘無心跳 → Member 排程自動 timeout

---

### 7. 合約條款

**顯示時機**：掃碼時（bind 成功後，遊戲畫面前）

**條款內容**：
```
遊戲規則：
1. 請保持手機連線以接收洗分金額
2. 機台斷線時無法洗分，分數將無法找回
3. 120 秒無遊戲活動將自動結束遊戲
4. 結束遊戲前請先洗分

[同意並開始] [取消]
```

**用戶操作**：
- 點擊 [同意並開始] → 顯示遊戲畫面
- 點擊 [取消] → 刪除 session，回到首頁

---

## 四、簡化參數（測試用）

| 參數 | 值 | 說明 |
|------|---|------|
| 兌換比例 | 1元 = 1代幣 | 簡化 |
| 開分比例 | 1代幣 = 1分 | `pulse_to_display=1`, `pulse_to_token=1` |
| 洗分比例 | 1分 = 1彩票 | `out_pulse_to_ticket=1` |
| 開分選項 | [10, 50, 100, 200] | 可選開分金額 |
| 測試設備 chip_id | i767e3ieju7wncy2 | 模擬器 |
| 測試設備 node_id | device_001 | 模擬器 |

---

## 五、與 kiosk_v0 的邊界

| 項目 | game_v0 | kiosk_v0 |
|------|---------|----------|
| 韌體 | IOTwawS3 | IOTkiosk_v0 |
| MQTT 前綴 | `device/{chip_id}/` | `kiosk/{chip_id}/` |
| Session 表 | `memberv9.device_sessions` | `memberv9.kiosk_sessions` |
| Session 管理 | Member（直接操作） | Member（直接操作） |
| 用途 | 遊戲機開分/洗分 | 紙鈔機兌幣 |
| 資產流向 | 代幣 → 開分，洗分 → 彩票 | 現金 → 代幣 |
| QR Code | `?node_id=device_NNN` | `?kiosk_id=kiosk_NNN` |

**⚠️ 嚴禁混淆**：
- 兩個域的 session 表完全分離
- bind 時只查自己的 session 表
- 一個會員可以同時：
  - 使用一台遊戲機（device_sessions）
  - 使用一台兌幣機（kiosk_sessions）

---

*制定者：HQ | 版本：3.0.0 | 日期：2026-05-15*


## =========================================================================
## 🔴 模組：資料庫 Schema 結構設計 (02_db_schema.md)
## =========================================================================

> **版本**: 3.0.0 | **日期**: 2026-05-15 | **維護者**: HQ

---

## device_sessions（memberv9）

**用途**：記錄會員與遊戲機的綁定關係

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| id | bigint unsigned PK | ✅ | 主鍵 |
| member_id | bigint unsigned | ✅ | 會員 ID |
| chip_id | varchar(50) | ✅ | ESP32 chip_id |
| node_id | varchar(20) | ❌ | 機台編號（device_NNN 格式） |
| status | enum | ✅ | active / ended / timeout |
| started_at | timestamp | ✅ | session 開始時間 |
| ended_at | timestamp | ❌ | session 結束時間 |
| last_heartbeat_at | timestamp | ✅ | ESP32 最後診斷心跳時間 |
| created_at / updated_at | timestamp | ✅ | 標準時間戳 |

**索引**：
- `(chip_id, status)` — 查詢機台是否使用中
- `(member_id, status)` — 查詢會員是否已在用其他機台
- `(last_heartbeat_at)` — 排程檢查超時 session

**狀態說明**：

| 狀態 | 觸發條件 |
|------|---------|
| active | bind 成功 |
| ended | 玩家按 [結束] |
| timeout | 120秒無活動 / 10分鐘無心跳 / ESP32 斷線 |

---

## device_orphan_logs（memberv9）

**用途**：記錄無 session 歸屬的洗分事件（孤兒分數）

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | bigint unsigned PK | 主鍵 |
| chip_id | varchar(50) | ESP32 chip_id |
| cumulative_amount | int unsigned | 韌體上報的累計值 |
| pulse_count | int unsigned | 計算出的增量（delta） |
| created_at | timestamp | 記錄時間 |

**索引**：`(chip_id, created_at)`

---

## wallet_transactions（memberv9，新增欄位）

**新增欄位**：

| 欄位 | 類型 | 說明 | 何時填入 |
|------|------|------|---------|
| cumulative_amount | int unsigned nullable | 韌體上報的累計值 | type=machine_settle 時 |

---

## device_credit_logs（memberv9，現有不變）

**用途**：記錄每次開分操作

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | bigint unsigned PK | 主鍵 |
| session_id | bigint unsigned | device_sessions.id |
| member_id | bigint unsigned | 會員 ID |
| chip_id | varchar(50) | ESP32 chip_id |
| display_amount | int unsigned | 開了多少分 |
| pulse_count | int unsigned | 發了幾個脈衝 |
| token_cost | decimal(10,2) | 扣了多少代幣 |
| created_at | timestamp | 記錄時間 |

---

## 累計值（里程表）設計

ESP32 上報的 `amount` 是**自開機以來的總累計值**，不是本次增量。

**範例**：
- 第一次洗分 10 脈衝 → amount = 10
- 第二次洗分 8 脈衝 → amount = 18
- 第三次洗分 12 脈衝 → amount = 30

**為什麼用累計值**：萬一漏一筆 MQTT，下一筆仍可正確計算 delta（自動補回）。

**delta 計算方式**：查 wallet_transactions 最新一筆的 cumulative_amount，用當前值減去它。

**注意**：Infra 必須傳原始累計值給 Member，不能在中途算 delta 就丟掉。

---

*制定者：HQ | 版本：3.0.0 | 日期：2026-05-15*


## =========================================================================
## 🔴 模組：API 規格標準規範 (03_api_spec.md)
## =========================================================================

> **版本**: 3.0.0 | **日期**: 2026-05-15 | **維護者**: HQ

---

## 公開 API（Bearer token）

### POST /api/device/bind — 掃碼綁定

**Request**：`{ "node_id": "device_001" }`（向下相容：可傳 chip_id）

**後端邏輯**：
1. 若傳 node_id → 呼叫 Infra 取得 chip_id
2. 呼叫 Infra 確認機台 status=active 且 is_alive=true
3. 查 device_sessions：會員是否已在用其他機台 → 有則 409
4. 查 device_sessions：此機台是否被他人使用 → 有則 409
5. 查 device_sessions：此機台是否被自己使用 → 有則直接回傳現有 session
6. 建立新 session，last_heartbeat_at=now()
7. 呼叫 Infra start-session（發 start_session 給 ESP32）
8. 回傳機台資訊 + 玩家餘額

**Response 200**：session_id、device 資訊（chip_id, node_id, name, pulse_to_display, pulse_to_token, out_pulse_to_ticket, credit_options）、player 餘額（token_balance, ticket_balance）

**錯誤回應**：

| HTTP | 情境 |
|------|------|
| 401 | 未登入 |
| 403 | 帳號凍結 |
| 404 | node_id 不存在 |
| 400 | 機台設定不完整 / 機台暫停服務 |
| 503 | ESP32 離線（is_alive=false） |
| 409 | 機台被他人使用 / 會員已在用其他機台 |

---

### POST /api/device/credit — 開分

**Request**：`{ "chip_id": "...", "display_amount": 100 }`

**後端邏輯**：
1. 查 device_sessions 確認 active session 屬於自己 → 找不到回 403
2. 呼叫 Infra 取得機台參數
3. 驗證 display_amount 是 pulse_to_display 的整數倍
4. 計算 pulse_count 和 token_cost
5. 確認代幣餘額足夠
6. DB transaction：扣代幣、寫 wallet_transactions(machine_load)、寫 device_credit_logs
7. 呼叫 Infra trigger-pulse
8. 若 Infra 失敗 → 回滾 transaction，退還代幣

**Response 200**：display_amount, pulse_count, token_cost, token_balance

**錯誤回應**：403 無 session / 400 金額無效或代幣不足 / 500 開分失敗已退款

---

### POST /api/device/settle — 洗分

**Request**：`{ "chip_id": "..." }`

**後端邏輯**：
1. 查 device_sessions 確認 active session 屬於自己 → 找不到回 403
2. 確認 ESP32 is_alive → 否則回 503
3. 呼叫 Infra trigger-settle
4. 回傳 queued（彩票等 MQTT 上報後才入帳）

**Response 200**：`{ "status": "queued", "message": "洗分指令已發送，彩票將於洗分完成後入帳" }`

**錯誤回應**：403 無 session / 503 機台未連線

---

### POST /api/device/unbind — 結束 session

**Request**：`{ "chip_id": "..." }`

**後端邏輯**：
1. 查 device_sessions 確認 active session 屬於自己 → 找不到回 403
2. 更新 status=ended, ended_at=now()
3. 呼叫 Infra stop-session

**Response 200**：`{ "message": "session ended" }`

---

## 內部 API（X-Internal-Key，Infra 呼叫）

### POST /internal/device/heartbeat — 診斷心跳

**Request**：`{ "chip_id": "..." }`

**後端邏輯**：查 active session → 更新 last_heartbeat_at=now()（找不到則靜默回 200）

---

### POST /internal/device/offline — ESP32 斷線

**Request**：`{ "chip_id": "..." }`

**後端邏輯**：查 active session → 更新 status=timeout, ended_at=now()（找不到則靜默回 200）

---

### POST /internal/device/session-timeout — 玩家活動超時

**Request**：`{ "chip_id": "..." }`

**後端邏輯**：查 active session → 更新 status=timeout, ended_at=now()（找不到則靜默回 200）

---

### POST /internal/device/credit-out — 洗分入帳

**Request**：`{ "chip_id": "...", "cumulative_amount": 80 }`

**後端邏輯（有 active session）**：
1. 查 wallet_transactions 最新一筆 cumulative_amount（例：0）
2. delta = 80 - 0 = 80
3. ticket_count = delta × out_pulse_to_ticket
4. 增加 TICKET 餘額，寫 wallet_transactions(machine_settle, cumulative_amount=80, pulse_count=80)
5. WebSocket 推送 DeviceCreditOut

**後端邏輯（無 active session，孤兒分數）**：
1. 計算 delta（同上）
2. 寫入 device_orphan_logs
3. 彩票不入帳，回傳 `{ "status": "orphan" }`

---

## 排程任務

**每分鐘執行**：查 device_sessions WHERE status=active AND last_heartbeat_at < 10分鐘前 → 更新 status=timeout，呼叫 Infra stop-session

---

## WebSocket 事件

**Channel**：`member.{member_id}`  
**Event**：`DeviceCreditOut`  
**Payload**：chip_id, ticket_count, ticket_balance, token_balance

---

## 前端流程說明

**掃碼後**：顯示合約條款 → 用戶同意 → 顯示遊戲畫面（[開分選項] [洗分] [結束]）

**洗分後**：顯示「洗分處理中...」→ 等 WebSocket DeviceCreditOut → 更新彩票餘額

**結束後**：顯示本次統計（開分代幣數、洗分彩票數）

---

*制定者：HQ | 版本：3.0.0 | 日期：2026-05-15*


## =========================================================================
## 🔴 模組：MQTT 通訊 Payload 與主題規格 (04_mqtt_spec.md)
## =========================================================================

> **版本**: 3.0.0 | **日期**: 2026-05-15 | **維護者**: HQ

---

## 主題命名

前綴：`device/{chip_id}/`（game_v0 專用，不可與 kiosk 混用）

| 方向 | 主題 | 用途 |
|------|------|------|
| 雲端 → ESP32 | `device/{chip_id}/cmd` | 指令下發 |
| ESP32 → 雲端 | `device/{chip_id}/cmd/response` | 指令回應 |
| ESP32 → 雲端 | `device/{chip_id}/data` | 數據上報 |
| ESP32 → 雲端 | `device/{chip_id}/data/diagnostic` | 診斷心跳（每 5 分鐘） |
| ESP32 → 雲端 | `device/{chip_id}/status` | 在線狀態（LWT） |

---

## 雲端 → ESP32（指令）

所有指令 QoS=1，Retain=false，發到 `device/{chip_id}/cmd`。

### 開分指令

| 欄位 | 值 |
|------|---|
| command | `assign_credit` |
| params.count | 脈衝數（整數） |
| transaction_id | UUID |

ESP32 行為：觸發 PIN_OUT1 count 次 → 機台上分

---

### 洗分指令

| 欄位 | 值 |
|------|---|
| command | `settle_credit` |
| transaction_id | UUID |

ESP32 行為：觸發 PIN_OUT2 **1 次**（固定，不接受 count）→ 機台洗分 → 採集退分脈衝 → 上報 credit_out

---

### 啟動 Session 監測（v3 新增）

| 欄位 | 值 |
|------|---|
| command | `start_session` |
| params.timeout_sec | 120 |
| transaction_id | UUID |

ESP32 行為：啟動 120 秒計時器，GPIO IN4 活動重置計時器，120 秒無活動發送 session_timeout

---

### 停止 Session 監測（v3 新增）

| 欄位 | 值 |
|------|---|
| command | `stop_session` |
| transaction_id | UUID |

ESP32 行為：停止計時器

---

## ESP32 → 雲端（回應）

主題：`device/{chip_id}/cmd/response`，QoS=1

| 欄位 | 說明 |
|------|------|
| transaction_id | 對應請求的 UUID |
| command_type | 指令類型 |
| status | success / error |
| timestamp | Unix timestamp |

---

## ESP32 → 雲端（數據上報）

主題：`device/{chip_id}/data`，QoS=1

### 開分採集（credit_in）

| 欄位 | 說明 |
|------|------|
| type | `credit_in` |
| amount | 累計值（自開機以來總脈衝數） |
| timestamp | Unix timestamp |

Infra Listener 收到後**忽略**（Member 已在開分時扣代幣）

---

### 洗分採集（credit_out）

| 欄位 | 說明 |
|------|------|
| type | `credit_out` |
| amount | 累計值（自開機以來總退分脈衝數） |
| timestamp | Unix timestamp |

Infra Listener 收到後轉發 Member（傳原始累計值，不算 delta）

---

### Session 超時（session_timeout，v3 新增）

| 欄位 | 說明 |
|------|------|
| type | `session_timeout` |
| timestamp | Unix timestamp |

觸發條件：ESP32 收到 start_session 後，120 秒無 GPIO IN4 活動  
Infra Listener 收到後轉發 Member

---

## ESP32 → 雲端（診斷心跳）

主題：`device/{chip_id}/data/diagnostic`，QoS=1，每 5 分鐘發送

Payload 包含：uptime、free_heap、wifi_rssi、timestamp（具體欄位由 Coli 定義）

Infra Listener 收到後：
1. 更新 iotv9.devices.last_seen_at
2. 轉發 Member POST /internal/device/heartbeat

---

## ESP32 → 雲端（在線狀態）

主題：`device/{chip_id}/status`，QoS=1，Retain=true

| 值 | 時機 |
|----|------|
| `online` | ESP32 連線時主動發布 |
| `offline` | ESP32 斷線時由 MQTT Broker 自動發布（LWT） |

Infra Listener 收到 offline 後：
1. 更新 iotv9.devices.last_seen_at = NULL
2. 轉發 Member POST /internal/device/offline

---

## 累計值說明

ESP32 上報的 amount 是**自開機以來的總累計值**，不是本次增量。

優點：萬一漏一筆 MQTT，下一筆仍可正確計算 delta（自動補回）。

Infra 必須傳原始累計值給 Member，由 Member 計算 delta。

---

## QoS 選擇

所有主題均使用 QoS=1（確保送達，不使用 QoS=2 避免開銷過大）

---

*制定者：HQ | 版本：3.0.0 | 日期：2026-05-15*


## =========================================================================
## 🔴 模組：基礎設施 Listener 邏輯規格 (05_infra_spec.md)
## =========================================================================

> **版本**: 3.0.0 | **日期**: 2026-05-15 | **維護者**: HQ

---

## Infra API（X-Internal-Key）

### GET /api/device/{chip_id} — 查詢設備（現有）

回傳：chip_id, node_id, name, status, is_alive, last_seen_at, pulse_to_display, pulse_to_token, out_pulse_to_ticket, config_json（credit_options, credit_default）

`is_alive` 判斷：last_seen_at 在 5 分鐘內則為 true

---

### GET /api/device/by-node/{node_id} — 依 node_id 查詢（現有）

回傳：同上。找不到回 404。

---

### POST /api/device/trigger-pulse — 開分脈衝（現有，需修正）

**Request**：chip_id, count

**行為**：發 MQTT `device/{chip_id}/cmd`，command=assign_credit，params.count=count

⚠️ **需修正**：現在發到 `device/{chip_id}/command`（錯誤），必須改為 `device/{chip_id}/cmd`

---

### POST /api/device/trigger-settle — 洗分（現有）

**Request**：chip_id

**行為**：發 MQTT `device/{chip_id}/cmd`，command=settle_credit

---

### POST /api/device/start-session — 啟動 Session 監測（v3 新增）

**Request**：chip_id, timeout_sec（預設 120）

**行為**：發 MQTT `device/{chip_id}/cmd`，command=start_session，params.timeout_sec=120

---

### POST /api/device/stop-session — 停止 Session 監測（v3 新增）

**Request**：chip_id

**行為**：發 MQTT `device/{chip_id}/cmd`，command=stop_session

---

## Infra Listener 訂閱

### 訂閱清單

| 主題 | 現有/新增 | 處理邏輯 |
|------|---------|---------|
| `device/+/data` | 現有（需新增 session_timeout 處理） | credit_out → 轉發 Member；session_timeout → 轉發 Member |
| `device/+/data/diagnostic` | 現有（需新增轉發 Member） | 更新 Owner DB last_seen_at + 轉發 Member heartbeat |
| `device/+/status` | 現有（需新增轉發 Member） | offline → 更新 Owner DB + 轉發 Member offline |

---

### device/+/data 處理邏輯

收到後根據 type 路由：

**type=credit_out**：
- 取出 chip_id 和 amount（累計值）
- 轉發 Member：POST /internal/device/credit-out，帶 chip_id 和 cumulative_amount
- 記錄 log

**type=session_timeout**（v3 新增）：
- 取出 chip_id
- 轉發 Member：POST /internal/device/session-timeout，帶 chip_id
- 記錄 log

**type=credit_in**：
- 忽略（Member 已在開分時扣代幣）

---

### device/+/data/diagnostic 處理邏輯

1. 更新 iotv9.devices.last_seen_at = 當前時間（直接 SQL）
2. 轉發 Member：POST /internal/device/heartbeat，帶 chip_id

---

### device/+/status 處理邏輯

收到 `offline` 時：
1. 更新 iotv9.devices.last_seen_at = NULL（直接 SQL）
2. 轉發 Member：POST /internal/device/offline，帶 chip_id

收到 `online` 時：
1. 更新 iotv9.devices.last_seen_at = 當前時間

---

## 需要修正的現有問題

| 問題 | 現狀 | 修正 |
|------|------|------|
| trigger-pulse topic 錯誤 | 發到 `device/{chip_id}/command` | 改為 `device/{chip_id}/cmd` |
| diagnostic 未轉發 Member | 只更新 Owner DB | 新增轉發 Member heartbeat |
| status offline 未轉發 Member | 只更新 Owner DB | 新增轉發 Member offline |

---

*制定者：HQ | 版本：3.0.0 | 日期：2026-05-15*


## =========================================================================
## 🔴 模組：會話生命週期狀態機 (06_session_lifecycle.md)
## =========================================================================

> **版本**: 3.0.0 | **日期**: 2026-05-15 | **維護者**: HQ

---

## 狀態機

```
無 session（空閒）
    │
    │ 玩家掃碼 + ESP32 alive
    ▼
  active ◄─── 玩家再掃碼（回傳現有 session）
    │
    ├─ 玩家按 [結束] ──────────────► ended
    │
    ├─ 120秒無 GPIO 活動（session_timeout）─► timeout
    │
    ├─ ESP32 斷線（LWT offline）──────────► timeout
    │
    └─ 10分鐘無心跳（排程兜底）──────────► timeout
```

---

## Session 建立

**觸發**：玩家掃碼 POST /api/device/bind

**前置檢查**（依序）：
1. 會員是否已在用其他機台 → 有則 409
2. 此機台是否被他人使用 → 有則 409
3. 此機台是否被自己使用 → 有則直接回傳現有 session
4. ESP32 is_alive → false 則 503

**建立後**：
- 寫入 device_sessions（status=active, last_heartbeat_at=now()）
- 呼叫 Infra start-session → ESP32 啟動 120 秒計時器

---

## 三層保護機制

### Layer 1：玩家活動監測（120 秒）

- bind 成功 → Infra 發 start_session 給 ESP32
- ESP32 啟動 120 秒計時器
- GPIO IN4 有活動 → 重置計時器（不發 MQTT，ESP32 內部計時）
- 120 秒無活動 → ESP32 發 session_timeout → Infra 轉發 Member → session timeout

**用途**：判斷「玩家已離開」

---

### Layer 2：診斷心跳（5 分鐘）

- ESP32 每 5 分鐘發送診斷心跳
- Infra 轉發 Member → 更新 last_heartbeat_at
- Member 排程每分鐘檢查：last_heartbeat_at 超過 10 分鐘 → 強制 timeout

**用途**：判斷「ESP32 存活」，兜底保護

---

### Layer 3：MQTT LWT（即時）

- ESP32 斷線 → MQTT Broker 立刻發布 LWT（offline）
- Infra 轉發 Member → 立刻強制 timeout

**用途**：即時偵測「ESP32 斷線」

---

## Session 結束方式

| 方式 | 觸發 | DB 狀態 | 是否發 stop_session |
|------|------|---------|-------------------|
| 玩家主動結束 | POST /api/device/unbind | ended | ✅ 是 |
| 玩家活動超時 | ESP32 session_timeout | timeout | ❌ 否（ESP32 自己停止） |
| ESP32 斷線 | MQTT LWT offline | timeout | ❌ 否（ESP32 已斷線） |
| 心跳超時（兜底） | Member 排程 | timeout | ✅ 是（盡力而為） |

---

## 空窗期

Session 結束後，機台上可能有殘留分數，但無人綁定。

| 操作 | 結果 |
|------|------|
| 任何人掃碼 | 建立新 session（可繼續玩殘留分數） |
| 按機台物理洗分鍵 | 孤兒分數（記錄但不入帳） |

**業務決策**：接受空窗期撿便宜的風險（類比真實街機）

---

## 時序圖（正常流程）

```
玩家     Member      Infra       ESP32
  │         │            │           │
  │ bind    │            │           │
  │────────►│            │           │
  │         │ start-sess │           │
  │         │───────────►│           │
  │         │            │start_sess │
  │         │            │──────────►│
  │◄────────│            │           │ 計時器啟動
  │ 合約條款│            │           │
  │ 同意    │            │           │
  │         │            │           │
  │ credit  │            │           │
  │────────►│            │           │
  │         │ trig-pulse │           │
  │         │───────────►│           │
  │         │            │assign_crd │
  │         │            │──────────►│ 計時器重置（GPIO）
  │◄────────│            │           │
  │         │            │           │
  │ settle  │            │           │
  │────────►│            │           │
  │         │ trig-settl │           │
  │         │───────────►│           │
  │         │            │settle_crd │
  │         │            │──────────►│
  │         │            │ credit_out│
  │         │            │◄──────────│
  │         │ credit-out │           │
  │         │◄───────────│           │
  │ WS push │            │           │
  │◄────────│            │           │
  │         │            │           │
  │ unbind  │            │           │
  │────────►│            │           │
  │         │ stop-sess  │           │
  │         │───────────►│           │
  │         │            │stop_sess  │
  │         │            │──────────►│ 計時器停止
  │◄────────│            │           │
```

---

*制定者：HQ | 版本：3.0.0 | 日期：2026-05-15*


## =========================================================================
## 🔴 模組：邊界與異常情境處理矩陣 (07_scenarios_matrix.md)
## =========================================================================

> **版本**: 3.0.0 | **日期**: 2026-05-15 | **維護者**: HQ

---

## 維度定義

| 維度 | 選項 |
|------|------|
| **Session** | A = 有 active session（自己）/ B = 無 active session |
| **ESP32** | 1 = alive（5分鐘內有心跳）/ 2 = offline |
| **操作** | α = 掃碼 / β = 手機洗分 / γ = 機台物理洗分 |

---

## 完整情境矩陣

| 情境 | Session | ESP32 | 操作 | HTTP | 後端動作 | 前端顯示 |
|------|---------|-------|------|------|---------|---------|
| **A1α** | 有（自己） | alive | 再掃碼 | 200 | 回傳現有 session | [繼續開分] [洗分] [結束] |
| **A1β** | 有（自己） | alive | 手機洗分 | 200 | 發 settle_credit 指令 | 洗分處理中...（等 WebSocket） |
| **A1γ** | 有（自己） | alive | 機台物理洗分 | — | credit_out → 彩票入帳 | WebSocket 推送彩票入帳 |
| **A2α** | 有（自己） | offline | 再掃碼 | 503 | 不動 session | ⚠️ 機台未連線，請確認電源後重新掃描 |
| **A2β** | 有（自己） | offline | 手機洗分 | 503 | 不動 session | ❌ 機台未連線，無法洗分 |
| **A2γ** | 有（自己） | offline | 機台物理洗分 | — | ESP32 離線，無法採集 | 無反應（分數消失） |
| **B1α** | 無 | alive | 掃碼 | 200 | 建立新 session，發 start_session | 顯示合約條款 → 遊戲畫面 |
| **B1β** | 無 | alive | 手機洗分 | 403 | 無動作 | ❌ 無 active session |
| **B1γ** | 無 | alive | 機台物理洗分 | — | credit_out → 寫 orphan_logs | 無反應（孤兒分數，不入帳） |
| **B2α** | 無 | offline | 掃碼 | 503 | 無動作 | ❌ 機台未連線，請確認電源後重新掃描 |
| **B2β** | 無 | offline | 手機洗分 | 403 | 無動作 | ❌ 無 active session |
| **B2γ** | 無 | offline | 機台物理洗分 | — | ESP32 離線，無法採集 | 無反應（分數消失） |

---

## 特殊情境

### 機台被他人使用（C1α）

| 維度 | 值 |
|------|---|
| Session | 有（他人） |
| ESP32 | alive |
| 操作 | 掃碼 |
| HTTP | 409 |
| 後端動作 | 無動作 |
| 前端顯示 | ❌ 此機台使用中，請移步其他機台 |

---

### 會員已在用其他機台（D1α）

| 維度 | 值 |
|------|---|
| Session | 自己有 active session（其他機台） |
| ESP32 | alive |
| 操作 | 掃碼新機台 |
| HTTP | 409 |
| 後端動作 | 無動作 |
| 前端顯示 | ❌ 您已在使用街機B，請先結束後再掃碼 |

---

### 空窗期撿便宜（B1α 的特殊案例）

| 步驟 | 說明 |
|------|------|
| 1 | 小明 session timeout，機台上有 50 分殘留 |
| 2 | 小李掃碼 → B1α → 建立新 session |
| 3 | 小李洗分 → A1β → 彩票入小李帳戶 50 張 |
| 業務決策 | ✅ 接受（類比真實街機，不告知店員就離開，別人可能拿走分數） |

---

### 多人競爭（同時掃碼）

| 步驟 | 說明 |
|------|------|
| 1 | 小明和小李幾乎同時掃碼同一台機台 |
| 2 | DB transaction 鎖，先到先得 |
| 3 | 先到的建立 session（200），後到的收到 409 |

---

## Session 結束方式對照

| 結束方式 | 觸發 | DB status | 是否發 stop_session |
|---------|------|-----------|-------------------|
| 玩家主動結束 | POST /api/device/unbind | ended | ✅ 是 |
| 玩家活動超時 | ESP32 session_timeout | timeout | ❌（ESP32 自己停止） |
| ESP32 斷線 | MQTT LWT offline | timeout | ❌（ESP32 已斷線） |
| 心跳超時兜底 | Member 排程 | timeout | ✅ 是（盡力而為） |

---

*制定者：HQ | 版本：3.0.0 | 日期：2026-05-15*


## =========================================================================
## 🔴 模組：使用者與營運端交互情境 (08_user_scenarios.md)
## =========================================================================

> **版本**: 3.0.0 | **日期**: 2026-05-15 | **維護者**: HQ

---

## 前置條件

| 項目 | 值 |
|------|---|
| 小明 member_id | 2，代幣 100，彩票 0 |
| 小李 member_id | 3 |
| chip_id | i767e3ieju7wncy2（模擬器） |
| node_id | device_001 |
| 參數 | 1代幣=1分=1彩票（全部 1:1） |
| 開分選項 | [10, 50, 100, 200] |
| QR Code | `https://win.tg25.win/m/play?node_id=device_001` |

---

## 情境 1：正常遊戲流程

**步驟 1：掃碼**

小明掃描 QR Code → POST /api/device/bind { node_id: "device_001" }

Member 確認：無 active session、ESP32 alive → 建立 session → 呼叫 Infra start-session → ESP32 啟動 120 秒計時器

手機顯示合約條款，小明點擊 [同意並開始]，進入遊戲畫面：
```
街機A | device_001
代幣：100  彩票：0
[10分] [50分] [100分] [200分]
[洗分] [結束]
```

---

**步驟 2：開分 100 分**

小明點擊 [100分] → POST /api/device/credit { display_amount: 100 }

Member 扣代幣 100 → 呼叫 Infra trigger-pulse { count: 100 } → ESP32 觸發 PIN_OUT1 100 次 → 機台上分 100 分

手機顯示：代幣 100 → 0，「開分成功！機台已上分 100 分」

---

**步驟 3：遊戲中**

小明持續按遊戲按鍵 → GPIO IN4 觸發 → ESP32 重置 120 秒計時器（不發 MQTT）

效果：可以玩任意長時間，只要持續按鍵

---

**步驟 4：洗分（剩 80 分）**

小明點擊 [洗分] → POST /api/device/settle → Infra 發 settle_credit → ESP32 觸發 PIN_OUT2 → 機台退分 80 脈衝 → ESP32 上報 credit_out { amount: 80 }

Infra 轉發 Member → delta = 80 - 0 = 80 → 彩票入帳 80 → WebSocket 推送

手機顯示：彩票 0 → 80，「洗分成功！本次獲得 80 張彩票」

---

**步驟 5：結束**

小明點擊 [結束] → POST /api/device/unbind → session status=ended → Infra 發 stop_session → ESP32 停止計時器

手機顯示：「遊戲結束，開分 100 代幣，洗分 80 彩票」

---

## 情境 2：Session 超時（120 秒無活動）

小明開分 100 分，玩到剩 50 分，忘記洗分離開

120 秒無 GPIO 活動 → ESP32 發 session_timeout → Infra 轉發 Member → session status=timeout

手機顯示（如果還開著）：「Session 已超時，系統已自動結束遊戲」

機台上的 50 分進入空窗期

---

## 情境 3：空窗期撿便宜（小李掃碼）

小明 timeout 後，機台上還有 50 分

小李掃碼 → 無 active session → 建立新 session（member_id=3）

小李點擊 [洗分] → ESP32 採集 credit_out { amount: 50 } → Member 找到 active session（小李）→ 彩票入小李帳戶 50 張

**業務決策**：接受（類比真實街機）

---

## 情境 4：ESP32 離線，小明再掃碼

小明有 active session，ESP32 斷線

小明再掃碼 → Member 查到有 active session（自己）→ 查 Infra：alive=false → 回傳 503

手機顯示：「機台未連線，請確認機台電源後重新掃描」[重新掃描] [結束遊戲]

後續：ESP32 恢復 → 重新掃碼 → 回傳現有 session；10 分鐘無心跳 → 自動 timeout

---

## 情境 5：ESP32 斷線（LWT 即時通知）

ESP32 斷電 → MQTT Broker 發布 LWT offline → Infra 轉發 Member → 立刻強制 timeout

效果：機台立刻釋放，不需要等 10 分鐘

---

## 情境 6：診斷心跳（背景運作）

ESP32 每 5 分鐘發送診斷心跳 → Infra 更新 Owner DB last_seen_at + 轉發 Member → Member 更新 last_heartbeat_at

效果：Member 排程知道 ESP32 還活著，不會誤判超時

---

## 情境 7：孤兒分數

小明 timeout，無人掃碼，有人按機台物理洗分鍵

ESP32 採集 credit_out → Member 查無 active session → 寫入 device_orphan_logs → 彩票不入帳

**業務決策**：記錄但不補償

---

## 情境 8：重複掃碼（存活期）

小明有 active session，手機沒電充電後再掃碼

Member 查到有 active session（自己）→ ESP32 alive → 回傳現有 session

手機顯示：[繼續開分] [洗分] [結束]（允許重新打開頁面）

---

## 情境 9：會員已在用其他機台

小明正在用 device_002，去掃 device_001

Member 查到小明有 active session（device_002）→ 回傳 409

手機顯示：「您已在使用街機B，請先結束後再掃碼」[前往當前機台] [強制結束]

---

## 情境 10：機台使用中（其他玩家）

小李正在用 device_001，小明去掃

Member 查到 device_001 有 active session（小李）→ 回傳 409

手機顯示：「此機台使用中，請移步其他機台」

---

*制定者：HQ | 版本：3.0.0 | 日期：2026-05-15*


## =========================================================================
## 🔴 模組：Agent 任務分配分配 (09_task_allocation.md)
## =========================================================================

> **版本**: 3.0.0 | **日期**: 2026-05-15 | **維護者**: HQ

---

## 任務總覽

| Agent | 任務數 | 優先順序 |
|-------|--------|---------|
| Coli（韌體） | 3 | 🔴 P1 |
| Ina（Infra） | 6 | 🔴 P1 |
| Mina（Member） | 12 | 🔴 P1 |
| Allie（Alliance） | 1 | 🟡 P2 |

---

## Coli（IOTwawS3 韌體）

### C1：新增 start_session 指令處理

訂閱 `device/{chip_id}/cmd`，處理 command=start_session。

收到後：啟動內部計時器（timeout_sec=120），監聽 GPIO IN4 活動，活動時重置計時器，回應 cmd/response。

---

### C2：新增 session_timeout 事件發送

計時器倒數結束（120 秒無 GPIO IN4 活動）時，發送 MQTT：
- Topic：`device/{chip_id}/data`
- Payload：type=session_timeout，timestamp

---

### C3：新增 stop_session 指令處理

收到 command=stop_session 時，停止計時器，回應 cmd/response。

---

## Ina（Infra 後端）

### I1：修正 trigger-pulse topic

現在發到 `device/{chip_id}/command`（錯誤），改為 `device/{chip_id}/cmd`。

---

### I2：新增 start-session API

`POST /api/device/start-session`，接收 chip_id 和 timeout_sec，發 MQTT command=start_session。

---

### I3：新增 stop-session API

`POST /api/device/stop-session`，接收 chip_id，發 MQTT command=stop_session。

---

### I4：Listener 新增診斷心跳轉發

訂閱 `device/+/data/diagnostic`（已有），在更新 Owner DB last_seen_at 之後，新增轉發 Member：POST /internal/device/heartbeat { chip_id }。

---

### I5：Listener 新增 LWT 轉發

訂閱 `device/+/status`（已有），收到 offline 時，在更新 Owner DB 之後，新增轉發 Member：POST /internal/device/offline { chip_id }。

---

### I6：Listener 新增 session_timeout 處理

訂閱 `device/+/data`（已有），新增處理 type=session_timeout，轉發 Member：POST /internal/device/session-timeout { chip_id }。

---

## Mina（Member 後端）

### M1：建立 device_sessions 表

Migration：建立 device_sessions 表，欄位與索引見 `02_db_schema.md`。

---

### M2：建立 device_orphan_logs 表

Migration：建立 device_orphan_logs 表，欄位見 `02_db_schema.md`。

---

### M3：wallet_transactions 新增 cumulative_amount 欄位

Migration：新增 cumulative_amount INT UNSIGNED NULL 欄位。

---

### M4：bind 前顯示合約條款

POST /api/device/bind 成功後，前端顯示合約條款（見 `01_design_decisions.md` 第七節），用戶同意後才顯示遊戲畫面，取消則刪除 session。

---

### M5：bind 成功後呼叫 Infra start-session

建立 session 後，呼叫 Infra POST /api/device/start-session { chip_id, timeout_sec: 120 }。

---

### M6：新增 POST /internal/device/heartbeat

收到後查 active session，更新 last_heartbeat_at=now()，找不到則靜默回 200。

---

### M7：新增 POST /internal/device/offline

收到後查 active session，更新 status=timeout, ended_at=now()，找不到則靜默回 200。

---

### M8：新增 POST /internal/device/session-timeout

收到後查 active session，更新 status=timeout, ended_at=now()，找不到則靜默回 200。

---

### M9：修改 POST /internal/device/credit-out（孤兒 log）

現有邏輯：查 session → 發放彩票。

新增邏輯：查無 active session 時，計算 delta，寫入 device_orphan_logs，回傳 { status: "orphan" }，彩票不入帳。

---

### M10：unbind 時呼叫 Infra stop-session

POST /api/device/unbind 更新 session 後，呼叫 Infra POST /api/device/stop-session { chip_id }。

---

### M11：排程檢查（10 分鐘無心跳）

Laravel Scheduler 每分鐘執行：查 device_sessions WHERE status=active AND last_heartbeat_at < 10 分鐘前，更新 status=timeout，呼叫 Infra stop-session（盡力而為）。

---

### M12：bind 時檢查 ESP32 alive 狀態

POST /api/device/bind 時，呼叫 Infra GET /api/device/{chip_id}，若 is_alive=false 回傳 503「機台未連線」。

---

## Allie（Alliance 燒錄站）

### A1：燒錄頁面 QR Code 改 URL 格式

檔案：`resources/views/devices/burning.blade.php`，函數 showQrPreview。

type=collector 時，QR Code 內容改為 URL 格式：`https://win.tg25.win/m/play?node_id={nodeId}`。

若 nodeId 為空，顯示提示：「請先至 Owner 後台設定機台編號（node_id），再列印 QR Code」。

---

## 任務依賴關係

```
C1-C3（韌體）
    ↓
I2-I3（Infra API）
    ↓
M1-M3（DB migrations）
    ↓
M4-M12（Member API）
    ↓
A1（QR Code）
```

I1（修正 topic）、I4-I6（Listener）可與其他任務並行。

---

## 驗收標準

| Agent | 驗收方式 |
|-------|---------|
| Coli | 發 start_session → ESP32 回應 success；10 秒無活動 → 收到 session_timeout |
| Ina | 呼叫 start-session API → MQTT 發送成功；診斷心跳 → Member 收到 heartbeat |
| Mina | 完整流程：掃碼→開分→洗分→結束，DB 狀態正確，WebSocket 推送正確 |
| Allie | 燒錄頁面生成 URL 格式 QR Code，掃描後可正確跳轉 |

---

*制定者：HQ | 版本：3.0.0 | 日期：2026-05-15*


## =========================================================================
## 🔴 模組：整合聯調測試指南 (10_testing_guide.md)
## =========================================================================

> **版本**: 3.0.0 | **日期**: 2026-05-15 | **維護者**: HQ

---

## 測試環境

| 項目 | 值 |
|------|---|
| chip_id | i767e3ieju7wncy2（模擬器） |
| node_id | device_001 |
| Member | `https://win.tg25.win` |
| Infra | `https://api.tg25.win` |
| MQTT Broker | `mqtt.tg25.win` |
| SSH Member | `ssh yd47`，路徑 `/www/wwwroot/win.tg25.win` |
| SSH Infra | `ssh infra` |

---

## 一、DB 驗收

SSH 到 yd47，進入 Member 專案，用 `php artisan tinker` 執行：

- 確認 device_sessions 表存在，欄位包含：id, member_id, chip_id, node_id, status, started_at, ended_at, last_heartbeat_at
- 確認 device_orphan_logs 表存在，欄位包含：id, chip_id, cumulative_amount, pulse_count
- 確認 wallet_transactions 有 cumulative_amount 欄位
- 確認目前無 active session

---

## 二、正常流程驗收

### 步驟 1：掃碼綁定

用 Bearer token 呼叫 `POST /api/device/bind { "node_id": "device_001" }`

預期：
- Response 200，包含 session_id、device 資訊、player 餘額
- DB：device_sessions 有一筆 status=active 的記錄
- MQTT：收到 `device/i767e3ieju7wncy2/cmd`，command=start_session

---

### 步驟 2：開分

呼叫 `POST /api/device/credit { "chip_id": "i767e3ieju7wncy2", "display_amount": 100 }`

預期：
- Response 200，token_balance 減少 100
- DB：wallet_transactions 有一筆 type=machine_load
- DB：device_credit_logs 有一筆 pulse_count=100
- MQTT：收到 command=assign_credit，params.count=100

---

### 步驟 3：模擬洗分

用 MQTT 工具發布：Topic=`device/i767e3ieju7wncy2/data`，Payload=`{"type":"credit_out","amount":80,"timestamp":...}`

等待 2-3 秒後驗證：
- DB：wallet_transactions 有一筆 type=machine_settle，cumulative_amount=80，pulse_count=80
- DB：TICKET 餘額增加 80
- WebSocket：收到 DeviceCreditOut 事件

---

### 步驟 4：結束遊戲

呼叫 `POST /api/device/unbind { "chip_id": "i767e3ieju7wncy2" }`

預期：
- Response 200
- DB：device_sessions status=ended
- MQTT：收到 command=stop_session

---

## 三、三層保護機制驗收

### Layer 1：session_timeout

1. 掃碼綁定
2. 用 MQTT 工具發布：Topic=`device/i767e3ieju7wncy2/data`，Payload=`{"type":"session_timeout","timestamp":...}`
3. 驗證：device_sessions status=timeout

---

### Layer 2：心跳超時（排程兜底）

1. 掃碼綁定
2. 用 tinker 手動將 last_heartbeat_at 設為 11 分鐘前
3. 等待排程執行（最多 1 分鐘）
4. 驗證：device_sessions status=timeout

---

### Layer 3：LWT offline

1. 掃碼綁定
2. 用 MQTT 工具發布：Topic=`device/i767e3ieju7wncy2/status`，Payload=`offline`，Retain=true
3. 等待 2-3 秒
4. 驗證：device_sessions status=timeout

---

## 四、孤兒分數驗收

1. 確認無 active session
2. 用 MQTT 工具發布：Topic=`device/i767e3ieju7wncy2/data`，Payload=`{"type":"credit_out","amount":50,"timestamp":...}`
3. 驗證：device_orphan_logs 有一筆記錄，TICKET 餘額不變

---

## 五、診斷心跳驗收

1. 掃碼綁定
2. 用 MQTT 工具發布：Topic=`device/i767e3ieju7wncy2/data/diagnostic`，Payload 任意 JSON
3. 驗證：device_sessions last_heartbeat_at 更新
4. 驗證：SSH infra，查 iotv9.devices.last_seen_at 更新

---

## 六、錯誤情境驗收

| 情境 | 操作 | 預期 HTTP |
|------|------|----------|
| 機台使用中 | 用另一個帳號掃碼同一台 | 409 |
| 機台未連線 | 發 offline LWT 後掃碼 | 503 |
| 代幣不足 | 代幣為 0 時開分 | 400 |
| 無 session 洗分 | 無 active session 時呼叫 settle | 403 |

---

## 七、Infra API 驗收

SSH 到 infra，用 curl 呼叫（帶 X-Internal-Key）：

- `POST /api/device/start-session { chip_id, timeout_sec: 120 }` → 預期 MQTT 發送成功
- `POST /api/device/stop-session { chip_id }` → 預期 MQTT 發送成功
- `POST /api/device/trigger-pulse { chip_id, count: 100 }` → 確認 topic 是 `device/{chip_id}/cmd`（不是 command）

---

*制定者：HQ | 版本：3.0.0 | 日期：2026-05-15*


---

## 🔗 文件神經連結

### 強關聯（必讀）
- `brains/knowledge/02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - 技術命名與 Payload 數據負載標準規範。
- `brains/knowledge/05_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md` - 遊戲機開分與會話生命週期流程。

### 中關聯（建議讀）
- `brains/knowledge/03_system_architecture/V9_SYSTEM_SPLITTING_DESIGN.md` - V9 系統拆分遷移設計書。
