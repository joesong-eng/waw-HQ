# Design Document — Kiosk Exchange v2

> **版本**: 1.0.0
> **日期**: 2026-05-08 (UTC+8)
> **狀態**: 設計定稿
> **設計者**: HQ
> **對應 Requirements**: v1.3.0

---

## 1. 系統架構

### 1.1 系統組成

```
Alliance ──配對──▶ iotv9.kiosks (Owner DB)
                        │
                        ▼
iHub (平板) ◀──────▶ Infra (api.tg25.win)
    │                   │
    │ WebSocket          │ MQTT
    ▼                   ▼
Member (win.tg25.win) ◀──webhook──▶ ESP32 韌體 (IOTkiosk_v0)
    │
    ▼
會員手機 (win.tg25.win)
```

### 1.2 職責分工

| 系統 | 職責 | 資料庫 |
|------|------|--------|
| **Alliance** | 硬體配對、燒錄 | `iotv9.kiosks`（Owner DB） |
| **Infra** | MQTT broker、設備認證、webhook 轉發 | PostgreSQL `iotv9` |
| **Member** | Session 管理、金流裁決、代幣入帳 | MySQL `waw_member` |
| **iHub** | 平板 UI、QR Code 顯示、escrow 確認 | 無（stateless） |
| **韌體** | 紙鈔機控制、MQTT 通訊 | NVS（本地持久化） |

### 1.3 設計原則

- **誰擁有資料，誰管 API**：Member 不直接查 Owner DB，透過 Infra API
- **識別碼全小寫**：`kiosk_id`、`esp32_mac`、`chip_id` 一律小寫
- **Fail-Safe 優先**：韌體預設 DISABLED，只有收到 enable 才開放

---

## 2. 資料模型

### 2.1 `kiosk_sessions` 表（Member DB）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | bigint | 主鍵，用於 API 路徑 |
| `kiosk_id` | varchar(32) | 機台 ID，全小寫（如 `kiosk_001`） |
| `kiosk_no` | bigint | 機台編號（從 Infra 取得） |
| `esp32_mac` | varchar(50) | ESP32 MAC，用於 MQTT topic |
| `member_id` | bigint | NULL = 無人使用，有值 = 已綁定 |
| `token` | varchar(64) | QR Code token，唯一索引 |
| `token_expires_at` | timestamp | Token 過期時間（5 分鐘） |
| `status` | enum | `active` / `ended` |
| `total_deposited` | decimal(12,2) | 累計投幣金額（TWD） |
| `started_at` | timestamp | 會員綁定時設定 |
| `last_active_at` | timestamp | 平板心跳更新 |
| `member_last_seen_at` | timestamp | 會員心跳更新 |
| `ended_at` | timestamp | Session 結束時間 |
| `end_reason` | enum | 結束原因（見下） |

**end_reason 值：**
- `manual`：會員手動結束
- `timeout`：會員手機 60 秒無投幣
- `new_session_started`：會員在其他機台掃碼
- `offline`：會員離線（60 秒無 heartbeat）
- `ihub_timeout`：iHub idle timer 到期（5 分鐘）
- `ihub_force_ended`：iHub 強制結束按鈕
- `system_cleanup`：系統排程清理（10 分鐘最後防線）
- `zombie_cleanup`：殭屍 session 清理（member_id=NULL 的異常 session）

### 2.2 `kiosk_transactions` 表（Member DB）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `event_id` | varchar | 唯一索引，用於 idempotency |
| `session_id` | bigint | 關聯 kiosk_sessions |
| `member_id` | bigint | 會員 ID |
| `kiosk_id` | varchar | 機台 ID |
| `amount_twd` | decimal | 投幣金額（TWD） |
| `tokens_credited` | decimal | 入帳代幣數 |
| `transaction_type` | enum | `deposit` |

### 2.3 `kiosks` 表（Owner DB `iotv9`，由 Alliance 管理）

| 欄位 | 說明 |
|------|------|
| `node_id` | 機台 ID，全小寫 |
| `esp32_mac` | ESP32 MAC，全小寫 |
| `screen_mac` | 平板 MAC，保留原始大小寫 |
| `venue_id` | 場館 ID |
| `factory_token` | 32 字元隨機 token |

---

## 3. API 設計

### 3.1 認證規則

| 情境 | Header |
|------|--------|
| 後端對後端（Member ↔ Infra） | `X-Internal-Key: v9-internal-key-2026` |
| iHub → Member/Infra | `X-Internal-Key: v9-internal-key-2026` |
| Infra Listener → Member webhook | `X-Internal-Key: v9-internal-key-2026` |
| 會員手機 → Member API | `Authorization: Bearer {sanctum_token}` |
| **例外**：iHub 呼叫 escrow/confirm、reject、heartbeat、complete | `X-Internal-Key`（不用 Bearer） |

### 3.2 Infra API（api.tg25.win）

| 方法 | 路徑 | 呼叫方 | 說明 |
|------|------|--------|------|
| GET | `/api/kiosk/node-id?screen_mac=` | iHub | 查 `node_id` + `esp32_mac` |
| GET | `/api/kiosk/info?node_id=` | Member | 查 `kiosk_no`、`esp32_mac`、`venue_id` |
| POST | `/api/ihub/register` | iHub | 平板造冊 |
| POST | `/api/internal/mqtt/publish` | Member | 代發 MQTT 指令 |
| POST | `/api/internal/cache/reload` | Alliance | 觸發 device cache 重載 |
| POST | `/api/kiosk/hardware-status` | sim-bill | 模擬韌體心跳（測試用） |

### 3.3 Member API（win.tg25.win）

| 方法 | 路徑 | 呼叫方 | 認證 | 說明 |
|------|------|--------|------|------|
| POST | `/api/kiosk/heartbeat` | iHub | X-Internal-Key | 平板心跳 |
| POST | `/api/kiosk/token` | iHub | X-Internal-Key | 取 QR Code token |
| POST | `/api/kiosk/bind` | 會員手機 | Bearer | 掃碼綁定 |
| POST | `/api/kiosk/session/{id}/heartbeat` | 會員手機 | Bearer | 會員心跳 |
| POST | `/api/kiosk/session/{id}/end` | 會員手機 | Bearer | 手動結束 |
| POST | `/api/kiosk/complete` | iHub | X-Internal-Key | iHub 通知結束 |
| POST | `/api/kiosk/escrow/confirm` | iHub | X-Internal-Key | 確認收鈔 |
| POST | `/api/kiosk/escrow/reject` | iHub | X-Internal-Key | 拒絕收鈔 |
| POST | `/internal/kiosk/escrow` | Infra | X-Internal-Key | 轉發 escrow 事件 |
| POST | `/internal/kiosk/stacked` | Infra | X-Internal-Key | 轉發 stacked 事件 |
| POST | `/internal/kiosk/rejected` | Infra | X-Internal-Key | 轉發 rejected 事件 |
| POST | `/internal/kiosk/status` | Infra | X-Internal-Key | 轉發 ba_state 狀態 |

### 3.4 HTTP 狀態碼

| 狀態碼 | 含義 | 使用情境 |
|--------|------|---------|
| 200 | 成功 | 正常回應 |
| 401 | 未授權 | X-Internal-Key 錯誤 或 Bearer token 無效 |
| 404 | 找不到 | Session 不存在 |
| 409 | 衝突 | Kiosk 使用中（busy）或 Session 已結束 |
| 422 | 驗證失敗 | Token 過期 |
| 500 | 伺服器錯誤 | 非預期錯誤 |

---

## 4. MQTT 設計

### 4.1 Topic 規範

| 方向 | Topic | QoS | Retain | 說明 |
|------|-------|-----|--------|------|
| 韌體 → 雲端 | `kiosk/{chip_id}/event` | 2 | ❌ | escrow / stacked / rejected（金流事件，不可遺失） |
| 韌體 → 雲端 | `kiosk/{chip_id}/status` | 1 | ✅ | ba_state 心跳（每 **25 秒**，必須 < Keepalive 30 秒） |
| 雲端 → 韌體 | `kiosk/{chip_id}/cmd` | 2 | ❌ | enable / disable / stack / reject |
| 韌體上下線 | `device/{chip_id}/status` | 1 | ✅ | `"online"` / `"offline"`（LWT） |
| 韌體 → 雲端 | `device/{chip_id}/command/response` | 1 | ❌ | 指令執行結果回報（ok/busy/fail） |
| 韌體 → 雲端 | `device/{chip_id}/info` | 1 | ✅ | 版本資訊、OTA 完工通知（`pending_reboot: true`） |
| 韌體 → 雲端 | `device/{chip_id}/diagnostic` | 1 | ❌ | 系統診斷（每 5 分鐘，RSSI/Heap/Uptime） |
| 韌體 → 雲端 | `kiosk/{chip_id}/debug` | 0 | ❌ | 原始 Debug 字串廣播（開發用） |

> ⚠️ `chip_id` = `esp32_mac`，全小寫無冒號

### 4.2 MQTT Payload 格式

**escrow 事件（韌體 → Infra）：**
```json
{
  "event": "escrow",
  "event_id": "uuid-xxxx",
  "amount": 100,
  "timestamp": 1713253800
}
```

**stacked / rejected 事件（韌體 → Infra）：**
```json
{
  "event": "stacked",
  "event_id": "uuid-xxxx",
  "amount": 100,
  "timestamp": 1713253805
}
```

**cmd 指令（Infra → 韌體）：**
```json
{ "action": "enable" }
{ "action": "disable" }
{ "action": "stack" }
{ "action": "reject" }
```

**ba_state 心跳（韌體 → Infra，每 25 秒）：**
```json
{
  "ba_state": "IDLE",
  "ba_error": "NONE",
  "lifetime_total": 12500,
  "lifetime_count": 15,
  "timestamp": 1713253800
}
```

---

## 5. WebSocket 設計

### 5.1 頻道

| 頻道 | 類型 | 用途 |
|------|------|------|
| `kiosk.{kiosk_id}` | Public | 業務事件（iHub、會員手機訂閱） |
| `engineering.{kiosk_id}` | Public | 工程監控（Signal Flow Monitor） |

### 5.2 業務事件（kiosk.{kiosk_id}）

| 事件 | 廣播方 | 說明 |
|------|--------|------|
| `.MemberBoundToKiosk` | Member | 掃碼綁定成功 |
| `.KioskEscrowPending` | Infra | 投幣等待確認 |
| `.KioskSessionUpdated` | Member | 入帳完成 |
| `.KioskSessionEnded` | Member | Session 結束 |

---

## 6. 韌體狀態機

```
開機
  │
  ▼
DISABLED（紅燈）── 預設，拒絕收鈔
  │
  │ 收到 enable 指令
  ▼
IDLE（綠燈）── 可收鈔
  │
  │ 投幣
  ▼
ESCROW（黃燈）── 等待雲端裁決（15 秒 fail-safe）
  │
  ├── 收到 stack → STACKING（藍燈）→ 500ms → STACKED（綠燈）→ 1.5s → IDLE
  ├── 收到 reject → REJECTING（黃燈）→ 500ms → REJECTED（紅燈）→ 1.5s → IDLE
  └── 15 秒超時 → 自動退鈔 → IDLE
```

**MQTT 斷線時：** 立即切換到 DISABLED，保護玩家

---

## 7. Session 生命週期

```
iHub 開機
  │ POST /api/kiosk/token
  ▼
Session 建立（member_id=NULL, status=active）
  │
  │ 會員掃碼 POST /api/kiosk/bind
  ▼
Session 綁定（member_id 填入, started_at 設定）
  │ Member 發 enable → 韌體 IDLE
  │
  │ 投幣 → escrow → 裁決 → stacked
  ▼
Session 更新（total_deposited 累加）
  │
  │ 任一結束條件觸發
  ▼
Session 結束（status=ended, end_reason 記錄）
  │ Member 發 disable → 韌體 DISABLED
```

---

## 8. 金流安全設計

### 8.1 Idempotency
- `kiosk_transactions.event_id` 有唯一索引
- 收到 stacked 時先查 `event_id` 是否存在
- 存在則直接回傳成功，不重複入帳

### 8.2 原子性
- 入帳使用 DB transaction：session 更新 + balance 更新 + transaction 記錄，三者同時成功或同時回滾

### 8.3 Row-level Locking
- 查詢 session 時使用 `lockForUpdate()`，防止並發競爭

### 8.4 Delta 更新
- `total_deposited += amount`（不用絕對值賦值），防止並發覆蓋

---

## 9. 參考文件

| 文件 | 路徑 | 備註 |
|------|------|------|
| ~~完整 API 規格~~ | ~~`pubdocs/04_features/kiosk_exchange_v2/api_spec.md`~~ | ⚠️ 已過時，以本文件第 10 章為準 |
| ~~資料庫設計~~ | ~~`pubdocs/04_features/kiosk_exchange_v2/database_schema.md`~~ | ⚠️ 已過時，以本文件第 2 章為準 |
| ~~流程總覽~~ | ~~`pubdocs/04_features/kiosk_exchange_v2/flow_overview.md`~~ | ⚠️ 已過時，以本文件第 7 章為準 |
| MQTT 主題規範 | `brains/knowledge/MQTT_TOPIC_STANDARD.md` | 仍有效，MQTT 唯一真理 |
| 韌體整合規格 | `docs/IHUB_INTEGRATION.md` | 仍有效，韌體層細節 |
| 韌體互動流程 | `brains/knowledge/kiosk_bill_acceptor_interaction_flow.md` | 仍有效，RS232 時序細節 |

---

*設計者：HQ | 日期：2026-05-08 (UTC+8) | 版本：1.0.0*

---

## 10. 接口完整對照表

> **⚠️ 本章節為唯一真理。**  
> 韌體已測試通過，以下所有接口格式不得自行修改。外部系統（sim-bill、iHub、Infra Listener）必須對齊本表，不得自行發明欄位名稱或格式。  
> 所有內容均來自實際代碼查證，無猜測。

---

### 10.1 識別碼規則

| 識別碼 | 格式範例 | 用於 | 不可用於 |
|--------|---------|------|---------|
| `chip_id` / `esp32_mac` | `e072a1f73a78`（全小寫無冒號） | MQTT topic、API `chip_id` 欄位 | WebSocket 頻道 |
| `node_id` / `kiosk_id` | `kiosk_001`（全小寫） | WebSocket 頻道、API `kiosk_id` 欄位 | MQTT topic |
| `screen_mac` | `STB-T1BQTYBDUEGX`（保留原始大小寫） | iHub 開機查詢 | 其他用途 |

---

### 10.2 MQTT 接口（韌體 ↔ 雲端）

> 韌體已實作並測試通過，以下格式為標準，不得更改。

#### 上行（韌體 → Infra Listener）

| Topic | QoS | Retain | 觸發時機 |
|-------|-----|--------|---------|
| `kiosk/{chip_id}/event` | 2 | ❌ | escrow / stacked / rejected |
| `kiosk/{chip_id}/status` | 1 | ✅ | 開機後立即 + 每 25 秒心跳 |
| `device/{chip_id}/status` | 1 | ✅ | 上線 `"online"` / 下線 LWT `"offline"` |

**`kiosk/{chip_id}/event` Payload（escrow）**：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `event` | string | `"escrow"` |
| `event_id` | string | 唯一識別碼（韌體生成） |
| `amount` | number | 面額（TWD 整數） |
| `timestamp` | number | Unix timestamp（秒） |

**`kiosk/{chip_id}/event` Payload（stacked / rejected）**：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `event` | string | `"stacked"` 或 `"rejected"` |
| `event_id` | string | 同 escrow 的 event_id |
| `amount` | number | 面額 |
| `timestamp` | number | Unix timestamp（秒） |

> Infra Listener 解析：`event_type = payload.get('event_type') or payload.get('event')`，兩個欄位名稱都接受。

**`kiosk/{chip_id}/status` Payload**：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `ba_state` | string | 狀態值（全大寫），見狀態表 |
| `ba_error` | string | `"NONE"` 或錯誤碼 |
| `lifetime_total` | number | 累計收鈔金額（TWD） |
| `lifetime_count` | number | 累計收鈔張數 |
| `timestamp` | number | Unix timestamp（秒） |

#### 下行（Infra → 韌體）

| Topic | QoS | Payload | 說明 |
|-------|-----|---------|------|
| `kiosk/{chip_id}/cmd` | 2 | `{"action": "enable"}` | 啟用收鈔 |
| `kiosk/{chip_id}/cmd` | 2 | `{"action": "disable"}` | 禁用收鈔 |
| `kiosk/{chip_id}/cmd` | 2 | `{"action": "stack"}` | 確認收鈔 |
| `kiosk/{chip_id}/cmd` | 2 | `{"action": "reject"}` | 拒絕收鈔 |
| `kiosk/{chip_id}/cmd` | 2 | `{"action": "reboot"}` | 遠端重啟 |
| `kiosk/{chip_id}/cmd` | 2 | `{"action": "ota_update", "url": "..."}` | OTA 更新 |

> `action` 值全小寫。韌體收到指令後會在 `device/{chip_id}/command/response` 回報執行結果。

#### 韌體狀態值（ba_state）

| 值 | 燈號 | 說明 |
|----|------|------|
| `DISABLED` | 🔴 紅 | 開機預設，拒絕收鈔 |
| `IDLE` | 🟢 綠 | 可收鈔 |
| `ESCROW` | 🟡 黃 | 鈔票暫存，等待雲端裁決 |
| `STACKING` | 🔵 藍 | 吞鈔中 |
| `STACKED` | 🟢 綠 | 收鈔成功（1.5 秒後自動回 IDLE） |
| `REJECTING` | 🟡 黃 | 退鈔中 |
| `REJECTED` | 🔴 紅 | 退鈔完成（1.5 秒後自動回 IDLE） |
| `FAULT` | 🔴 紅 | 故障 |

---

### 10.3 Infra API（api.tg25.win）

#### GET /api/kiosk/node-id

| 項目 | 值 |
|------|---|
| 呼叫方 | iHub（開機初始化） |
| Auth | `X-Internal-Key: v9-internal-key-2026` |
| Query | `screen_mac={screen_mac}` |

回應：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `node_id` | string | `kiosk_001`（全小寫） |
| `esp32_mac` | string | `e072a1f73a78`（全小寫） |

錯誤：`404 {"error": "not_paired", "message": "..."}`

---

#### GET /api/kiosk/info

| 項目 | 值 |
|------|---|
| 呼叫方 | Member（bind 時查詢） |
| Auth | `X-Internal-Key: v9-internal-key-2026` |
| Query | `node_id={node_id}` |

回應：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `kiosk_no` | number | 機台流水號（DB id） |
| `node_id` | string | 全小寫 |
| `esp32_mac` | string | 全小寫 |
| `venue_id` | number | 場館 ID |
| `status` | string | `active` / `inactive` |

---

#### POST /api/kiosk/token（Bridge）

| 項目 | 值 |
|------|---|
| 呼叫方 | iHub |
| Auth | `X-Internal-Key: v9-internal-key-2026` |
| Body | `{"kiosk_id": "kiosk_001"}` |

> Infra 橋接轉發到 `win.tg25.win/api/kiosk/token`，回應格式同 Member token 端點。

---

#### POST /api/kiosk/heartbeat

| 項目 | 值 |
|------|---|
| 呼叫方 | iHub（每 60 秒） |
| Auth | `X-Internal-Key: v9-internal-key-2026` |
| Body | `{"node_id": "kiosk_001"}` |

回應：`{"success": true, "message": "heartbeat_ok"}`

---

#### POST /api/kiosk/escrow/confirm

| 項目 | 值 |
|------|---|
| 呼叫方 | iHub（人工確認收鈔） |
| Auth | `X-Internal-Key: v9-internal-key-2026` |
| Body | `{"kiosk_id": "kiosk_001"}` |

> Infra 橋接轉發到 `win.tg25.win/api/kiosk/escrow/confirm`

回應：`{"action": "stack", "success": true}`

---

#### POST /api/kiosk/escrow/reject

| 項目 | 值 |
|------|---|
| 呼叫方 | iHub（人工拒絕收鈔） |
| Auth | `X-Internal-Key: v9-internal-key-2026` |
| Body | `{"kiosk_id": "kiosk_001"}` |

回應：`{"action": "reject", "reason": "user_cancelled", "success": true}`

---

#### POST /api/internal/mqtt/publish

| 項目 | 值 |
|------|---|
| 呼叫方 | Member（代發 MQTT 指令） |
| Auth | `X-Internal-Key: v9-internal-key-2026` |

Body：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `topic` | string | 例如 `kiosk/e072a1f73a78/cmd` |
| `payload` | object | 例如 `{"action": "enable"}` |
| `qos` | number | 預設 `1`，cmd 用 `2` |

回應：`{"status": "published"}`

---

#### POST /api/kiosk/hardware-status（sim-bill 專用）

| 項目 | 值 |
|------|---|
| 呼叫方 | sim-bill 模擬器 |
| Auth | `X-Internal-Key: v9-internal-key-2026` |
| Body | `{"chip_id": "test-esp32", "ba_state": "IDLE"}` |

> 發布 MQTT `kiosk/{chip_id}/status`，模擬韌體心跳。

回應：`{"success": true, "message": "Status IDLE published to kiosk/test-esp32/status"}`

---

#### POST /api/internal/cache/reload

| 項目 | 值 |
|------|---|
| 呼叫方 | Alliance（新機台配對後觸發） |
| Auth | `X-Internal-Key: v9-internal-key-2026` |
| Body | 無 |

---

### 10.4 Member API（win.tg25.win）

#### POST /api/kiosk/token

| 項目 | 值 |
|------|---|
| 呼叫方 | iHub（透過 Infra bridge） |
| Auth | `X-Internal-Key: v9-internal-key-2026` |
| Body | `{"kiosk_id": "kiosk_001"}` |

回應：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `status` | string | `"success"` |
| `kiosk_id` | string | 全小寫 |
| `token` | string | 32 字元隨機 token |
| `expires_at` | number | Unix timestamp（秒） |

> QR Code 內容格式：`KIOSK:{kiosk_id}:TOKEN:{token}`（全小寫）

---

#### POST /api/kiosk/bind

| 項目 | 值 |
|------|---|
| 呼叫方 | 會員手機 |
| Auth | `Authorization: Bearer {sanctum_token}` |
| Body | `{"kiosk_id": "kiosk_001", "token": "abc..."}` |

回應（成功）：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `status` | string | `"success"` |
| `session_id` | number | Session ID |
| `kiosk_id` | string | 全小寫 |
| `esp32_mac` | string | 全小寫 |
| `member` | object | `{id, name}` |

錯誤：`409 kiosk busy`、`422 token expired`、`401 unauthorized`

---

#### POST /api/kiosk/heartbeat

| 項目 | 值 |
|------|---|
| 呼叫方 | iHub（每 60 秒） |
| Auth | `X-Internal-Key: v9-internal-key-2026` |
| Body | `{"kiosk_id": "kiosk_001"}` |

回應：`{"status": "ok"}`

---

#### POST /api/kiosk/session/{id}/heartbeat

| 項目 | 值 |
|------|---|
| 呼叫方 | 會員手機（每 30 秒） |
| Auth | `Authorization: Bearer {sanctum_token}` |
| Body | 無 |

回應：`{"status": "ok", "last_seen_at": 1713253800}`

---

#### POST /api/kiosk/session/{id}/end

| 項目 | 值 |
|------|---|
| 呼叫方 | 會員手機 |
| Auth | `Authorization: Bearer {sanctum_token}` |
| Body | `{"reason": "manual"}` |

回應：`{"status": "ok", "total_deposited": 300}`

錯誤：`409 session already ended`（含 `ended_at`）

---

#### POST /api/kiosk/complete

| 項目 | 值 |
|------|---|
| 呼叫方 | iHub |
| Auth | `X-Internal-Key: v9-internal-key-2026` |
| Body | `{"session_id": 123, "reason": "ihub_timeout"}` |

`reason` 可選值：`ihub_timeout`（預設）、`ihub_force_ended`

回應：`{"status": "success", "message": "儲值完成！", "total_deposited": 300}`

---

#### POST /api/kiosk/escrow/confirm

| 項目 | 值 |
|------|---|
| 呼叫方 | iHub（透過 Infra bridge） |
| Auth | `X-Internal-Key: v9-internal-key-2026` |
| Body | `{"kiosk_id": "kiosk_001"}` |

回應：`{"action": "stack", "success": true}`

---

#### POST /api/kiosk/escrow/reject

| 項目 | 值 |
|------|---|
| 呼叫方 | iHub（透過 Infra bridge） |
| Auth | `X-Internal-Key: v9-internal-key-2026` |
| Body | `{"kiosk_id": "kiosk_001"}` |

回應：`{"action": "reject", "reason": "user_cancelled", "success": true}`

---

### 10.5 Member Internal Webhook（Infra Listener → Member）

#### POST /internal/kiosk/escrow

| 項目 | 值 |
|------|---|
| 呼叫方 | Infra Listener |
| Auth | `X-Internal-Key: v9-internal-key-2026` |

Body：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `kiosk_id` | string | node_id（Listener 從 device cache 查出） |
| `esp32_mac` | string | chip_id |
| `amount` | number | 面額 |
| `event_id` | string | 韌體生成的唯一 ID |
| `firmware_timestamp` | number | 韌體 timestamp |

回應：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `status` | string | `"pending"` |
| `member_name` | string | 會員名稱 |
| `member_phone` | string | 完整手機號 |
| `tokens_credited` | number | 預計入帳代幣數 |

> Member 同時廣播 `KioskEscrowPending` 到 `kiosk.{kiosk_id}`

---

#### POST /internal/kiosk/stacked

| 項目 | 值 |
|------|---|
| 呼叫方 | Infra Listener |
| Auth | `X-Internal-Key: v9-internal-key-2026` |

Body 同 escrow（`kiosk_id`, `esp32_mac`, `amount`, `event_id`, `firmware_timestamp`）

回應：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `status` | string | `"credited"` |
| `tokens_credited` | number | 實際入帳代幣數 |
| `idempotent` | boolean | 是否為重複請求 |

---

#### POST /internal/kiosk/rejected

| 項目 | 值 |
|------|---|
| 呼叫方 | Infra Listener |
| Auth | `X-Internal-Key: v9-internal-key-2026` |

Body 同 escrow，額外有 `reason` 欄位（`"timeout"` / `"rejected_by_server"` / `"hardware"`）

回應：`{"status": "logged"}`

---

#### POST /internal/kiosk/status

| 項目 | 值 |
|------|---|
| 呼叫方 | Infra Listener |
| Auth | `X-Internal-Key: v9-internal-key-2026` |

Body：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `kiosk_id` | string | node_id |
| `chip_id` | string | chip_id |
| `ba_state` | string | 狀態值（全大寫） |

回應：`{"status": "ok"}`

---

### 10.6 WebSocket 事件（Member Reverb → 訂閱方）

| 項目 | 值 |
|------|---|
| WebSocket Server | `win.tg25.win`（Member Reverb） |
| Port | `443`（WSS） |
| Channel Type | Public Channel |
| 業務頻道 | `kiosk.{node_id}`（全小寫） |
| 工程頻道 | `engineering.{node_id}`（全小寫） |

**事件對照表**：

| 前端監聽名稱 | `broadcastAs()` | Event Class | 廣播頻道 | 廣播方 |
|------------|----------------|-------------|---------|--------|
| `.MemberBoundToKiosk` | `MemberBoundToKiosk` | `MemberBoundToKiosk` | `kiosk.{kiosk_id}` | Member |
| `.KioskEscrowPending` | `KioskEscrowPending` | `KioskEscrowPending` | `kiosk.{kiosk_id}` | Member |
| `.KioskSessionUpdated` | `KioskSessionUpdated` | `KioskSessionUpdated` | `kiosk.{kiosk_id}` | Member |
| `.KioskSessionEnded` | `KioskSessionEnded` | `KioskSessionEnded` | `kiosk.{kiosk_id}` | Member |
| `infra.cmd` | `infra.cmd` | `KioskInfraCmd` | `kiosk.{kiosk_id}` | Member |

**`.MemberBoundToKiosk` Payload**：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `status` | string | `"bound"` ← 檢查這個，不是 `result` |
| `session_id` | number | Session ID |
| `kiosk_id` | string | node_id |
| `member` | object | `{id, name, phone, balance}` |
| `message` | string | 歡迎訊息 |

**`.KioskEscrowPending` Payload**：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `event_id` | string | 韌體 event_id |
| `amount` | number | 面額 |
| `tokens` | number | 預計入帳代幣數 |
| `member` | object | `{name, phone}` |

**`.KioskSessionUpdated` Payload**：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `status` | string | session 狀態 |
| `session_id` | number | Session ID |
| `member` | object | `{id, name, balance, currency}` |
| `total_deposited` | number | 累計投幣金額 |
| `tokens_credited` | number | 本次入帳代幣數 |
| `member_balance` | number | 入帳後餘額 |
| `currency` | string | 幣種 |

**`.KioskSessionEnded` Payload**：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `status` | string | `"ended"` |
| `session_id` | number | Session ID |
| `kiosk_id` | string | node_id |
| `message` | string | `"交易已結束，謝謝光臨"` |
| `ended_at` | string | 結束時間（datetime string） |

**`infra.cmd` Payload**：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `action` | string | `"stack"` 或 `"reject"` |
| `chip_id` | string | chip_id |
| `kiosk_id` | string | node_id |
