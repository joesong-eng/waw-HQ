# 遊戲機開分與會話生命週期流程規格書 (Game Machine Flow & Session Lifecycle Specification)

> **版本**：v2.0.0 (合併版)  
> **最後更新**：2026-06-05  
> **狀態**：Active / Authoritative  
> **適用角色**：Mina (Member), Ina (Infra), Sophie (Owner), Coli (Firmware)

---

## 區塊一：通用遊戲機開分基礎業務流程

# 遊戲機開分/洗分 — 完整流程

> **版本**: 3.0.0
> **日期**: 2026-05-15
> **維護者**: HQ（唯一寫入權）
> **狀態**: ✅ 設計定稿，待派任務實作
> **公開路徑**: `pubdocs/02_projects/hq/01_業務場景故事/05_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md`

---

## ⚠️ Agent 執行守則（必讀，違反視為重大失職）

1. **本文件是唯一設計依據**。實作前必須完整閱讀，不得憑記憶或猜測動手。
2. **禁止自作主張修改設計**。任何覺得「這樣更好」的想法，一律透過 HQ Message Hub 回報 HQ，等待裁決後才能執行。
3. **禁止另外尋求解決方案**。遇到技術困難、規格不清、或發現衝突，停下來回報 HQ，不得自行繞路或發明替代方案。
4. **有問題一律回報 HQ 裁決**。不確定的事情問比做錯了再修更省時間。
5. **回報必須附驗證結果**。不接受口頭回報「已完成」，必須附上 curl 結果、log 截圖或時間戳證明。

---

## 一、設計決策（已拍板，不再討論）

| 決策 | 結論 |
|------|------|
| Session 表位置 | `memberv9.device_sessions`（Member DB，不是 iotv9） |
| Session 三層保護 | Layer 1: ESP32 Session 監測（120秒，GPIO 活動重置，發 session_timeout）<br>Layer 2: 診斷心跳（5分鐘，已有，更新 last_heartbeat_at）<br>Layer 3: MQTT LWT（即時，已有，立刻強制 timeout） |
| 一人一台 | bind 時只查 `device_sessions`，不影響 `kiosk_sessions` |
| 空窗期撿便宜 | **接受業務風險**（類比真實街機，不告知店員就離開，別人可能拿走分數） |
| 孤兒分數 | 記錄 `device_orphan_logs`，不補償 |
| 洗分方式 | 手機按洗分鍵 → Infra 發 `settle_credit` → 韌體觸發 PIN_OUT2 一次 |
| 洗分流程 | **不需要再掃碼**，頁面直接顯示 [繼續開分] [洗分] [結束] |
| 重複掃碼 | 存活期再掃同一台 → 回傳現有 session（允許重新打開頁面） |
| ESP32 離線處理 | 提示「機台未連線」，不強制結束 session（等待恢復或 10 分鐘自動 timeout） |
| 累計值傳遞 | Infra 傳原始累計值給 Member，Member 自己算 delta 並存 `cumulative_amount` |
| MQTT topic | 韌體訂閱 `device/{chip_id}/cmd`（不是 `command`） |
| QR Code 格式 | URL 格式：`https://win.tg25.win/m/play?node_id=device_001` |
| 簡化參數（測試） | 1元=1代幣=1分=1彩票（全部 1:1 比例） |
| 測試設備 | chip_id=i767e3ieju7wncy2, node_id=device_001（模擬器） |
| 合約條款 | 掃碼時顯示遊戲規則，用戶同意後才能 bind |
| 訊號極性自適應 | **開機自動偵測**（5次取樣防呆）+ **MQTT 遠端覆寫**（支援 active_high/low） |

---

## 二、硬體物理機制（必讀）

### 開分的物理過程

```
玩家手機按開分
  → Member 扣代幣
  → Infra 發 MQTT assign_credit（脈衝數 N）到 device/{chip_id}/cmd
  → ESP32 觸發 PIN_OUT1（開分腳）N 次
  → 遊戲機收到脈衝，上分
  → 遊戲機開分計數器跳動 N 下
  → ESP32 PCNT 採集開分計數器脈衝，累計 credit_in += N
  → MQTT 上報 device/{chip_id}/data { type: "credit_in", amount: 累計值 }
```

### 洗分的物理過程

```
玩家手機按洗分
  → Member 確認 active session
  → Infra 發 MQTT settle_credit 到 device/{chip_id}/cmd
  → ESP32 觸發 PIN_OUT2（洗分腳）1 次（固定，不接受 count）
  → 遊戲機收到脈衝，自行將所有分數歸零
  → 遊戲機退分計數器根據剩餘分數跳動 N 下（例：100分÷10跳/次 = 10下）
  → ESP32 PCNT 採集退分計數器脈衝，累計 credit_out += N
  → MQTT 上報 device/{chip_id}/data { type: "credit_out", amount: 累計值 }
  → Infra Listener 收到 → 轉發給 Member（傳原始累計值）
  → Member 計算 delta → 彩票入帳
```

### 累計值（里程表）設計

ESP32 上報的 `amount` 是**自開機以來的總累計值**，不是本次增量。

```
開機後第一次洗分 10 脈衝 → amount = 10
第二次洗分 8 脈衝 → amount = 18（不是 8）
第三次洗分 12 脈衝 → amount = 30（不是 12）
```

**為什麼用累計值**：萬一中間漏一筆 MQTT，下一筆收到時仍可正確計算 delta：
```
正常：10 → 18 → 30，delta = 10, 8, 12 ✅
漏一筆：10 → (漏18) → 30，delta = 10, 20 ✅（自動補回）
```

**累計值必須完整傳到 Member DB，不能在中途算 delta 就丟掉。**

---

## 三、核心狀態機

```
無 session
    │ 玩家掃碼 POST /api/device/bind
    ▼
session: active
    │
    ├─ 玩家選分確認 POST /api/device/credit（可重複）
    │    → 扣代幣 → Infra 發 MQTT assign_credit → 機台上分
    │
    ├─ 玩家按手機洗分鍵 POST /api/device/settle
    │    → Infra 發 MQTT settle_credit → 機台洗分
    │    → ESP32 採集退分脈衝 → MQTT credit_out
    │    → Infra Listener → POST /internal/device/credit-out → 彩票入帳
    │
    ├─ 遊戲中按鍵觸發 MQTT device/{chip_id}/activity
    │    → Infra → POST /internal/device/activity
    │    → Member 更新 last_activity_at（保活）
    │
    ├─ 120 秒無 activity → 排程自動 timeout
    │
    └─ 玩家按 [結束] POST /api/device/unbind
    ▼
session: ended / timeout
```

---

## 四、資料表設計

### `device_sessions`（Member DB，yd47）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | bigint unsigned PK | |
| `member_id` | bigint unsigned | 玩家 ID |
| `chip_id` | varchar(50) | 遊戲機識別碼 |
| `node_id` | varchar(20) nullable | device_NNN 格式 |
| `status` | enum('active','ended','timeout') | |
| `started_at` | timestamp | |
| `ended_at` | timestamp nullable | |
| `last_activity_at` | timestamp nullable | GPIO 活動保活用 ⚠️ 需新增 migration |
| `created_at` / `updated_at` | timestamp | |

### `wallet_transactions`（新增欄位）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `cumulative_amount` | int unsigned nullable | 韌體原始累計值（洗分時填入）⚠️ 需新增 migration |

### `device_orphan_logs`（新建表）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | bigint unsigned PK | |
| `chip_id` | varchar(50) | |
| `cumulative_amount` | int unsigned | 韌體上報的原始累計值 |
| `pulse_count` | int unsigned | 計算出的 delta |
| `created_at` | timestamp | |

### `device_credit_logs`（現有，不變）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | bigint unsigned PK | |
| `session_id` | bigint unsigned | |
| `member_id` | bigint unsigned | |
| `chip_id` | varchar(50) | |
| `display_amount` | int unsigned | 開了多少分 |
| `pulse_count` | int unsigned | 發了幾個脈衝 |
| `token_cost` | decimal(10,2) | 扣了多少代幣 |
| `created_at` | timestamp | |

---

## 五、API 規格

### 5.1 掃碼綁定 `POST /api/device/bind`（Bearer token）
**負責**：Mina

```json
Request: { "node_id": "device_001" }
// 向下相容：{ "chip_id": "iot002" }
```

後端邏輯：
1. 若傳 node_id → 呼叫 Infra `GET /api/device/by-node/{node_id}` 取得 chip_id
2. 呼叫 Infra `GET /api/device/{chip_id}` → 確認 status=active
3. **一人一台檢查**：查 `device_sessions` WHERE member_id=我 AND status=active
   - 有（任何一台）→ 409「您已在使用另一台機台，請先結束後再掃碼」
   - ⚠️ 只查 `device_sessions`，**絕對不碰 `kiosk_sessions`**
4. 查 `device_sessions` WHERE chip_id + status=active
   - 有，member_id ≠ 我 → 409「此機台使用中，請移步其他機台」
   - 有，member_id = 我 → 直接回傳現有 session
   - 無 → 建立新 session，`last_activity_at = now()`
5. 回傳機台資訊 + 玩家代幣/彩票餘額

```json
Response 200:
{
  "session_id": 42,
  "device": {
    "chip_id": "iot002",
    "node_id": "device_001",
    "name": "街機A",
    "pulse_to_display": 100,
    "pulse_to_token": 1.0,
    "out_pulse_to_ticket": 1.0,
    "credit_options": [100, 200, 500],
    "credit_default": 100
  },
  "player": { "token_balance": 350.0, "ticket_balance": 1060.0 }
}
```

| 情境 | HTTP | 訊息 |
|------|------|------|
| 機台不存在 | 404 | 找不到此機台 |
| 機台維修中 | 400 | 此機台暫停服務 |
| 機台使用中（他人） | 409 | 此機台使用中，請移步其他機台 |
| 會員已綁其他機台 | 409 | 您已在使用另一台機台，請先結束後再掃碼 |

---

### 5.2 開分 `POST /api/device/credit`（Bearer token）
**負責**：Mina

```json
Request: { "chip_id": "iot002", "display_amount": 100 }
```

後端邏輯：
1. 查 `device_sessions` WHERE chip_id + status=active + member_id=我 → 找不到回 403
2. 呼叫 Infra `GET /api/device/{chip_id}` 取得 `pulse_to_display`、`pulse_to_token`
3. 驗證 `display_amount` 是 `pulse_to_display` 的整數倍
4. 計算：`pulse_count = display_amount / pulse_to_display`，`token_cost = pulse_count × pulse_to_token`
5. 確認 COIN 餘額 ≥ token_cost
6. DB transaction：扣 COIN + 寫 `wallet_transactions(type=machine_load)` + 寫 `device_credit_logs`
7. 呼叫 Infra `POST /api/device/trigger-pulse { chip_id, count: pulse_count }`（非同步；失敗需退款）

```json
Response 200: { "display_amount": 100, "pulse_count": 1, "token_cost": 1.0, "token_balance": 349.0 }
```

---

### 5.3 手機洗分 `POST /api/device/settle`（Bearer token）
**負責**：Mina（新增）

```json
Request: { "chip_id": "iot002" }
```

後端邏輯：
1. 查 `device_sessions` WHERE chip_id + status=active + member_id=我 → 找不到回 403
2. 呼叫 Infra `POST /api/device/trigger-settle { chip_id }`
3. 回傳 queued

```json
Response 200: { "status": "queued", "message": "洗分指令已發送，彩票將於洗分完成後入帳" }
```

> ⚠️ 彩票**不在此 API 入帳**。等 ESP32 採集到退分脈衝上報後，走 credit-out 鏈路入帳。

---

### 5.4 洗分入帳 `POST /internal/device/credit-out`（X-Internal-Key，Infra 呼叫）
**負責**：Mina（修改現有）

```json
Request: { "chip_id": "iot002", "cumulative_amount": 1080 }
```

後端邏輯：
1. 驗證 X-Internal-Key
2. 查 `device_sessions` WHERE chip_id + status=active
   - **找到** → 正常入帳
   - **找不到** → 孤兒洗分，寫入 `device_orphan_logs`，回 200 `{status:"orphan"}`，不報錯
3. 查 `wallet_transactions` 最新一筆的 `cumulative_amount`（例：1050）
4. `delta = 1080 - 1050 = 30`
5. `ticket_count = delta × out_pulse_to_ticket`
6. DB transaction：增加 TICKET 餘額 + 寫 `wallet_transactions(type=machine_settle, cumulative_amount=1080, pulse_count=30)`
7. WebSocket 推送 `DeviceCreditOut`

```json
Response 200: { "member_id": 456, "ticket_count": 30, "ticket_balance": 1120 }
Response 200: { "status": "orphan", "message": "no active session, logged" }
```

---

### 5.5 GPIO 活動保活 `POST /internal/device/activity`（X-Internal-Key，Infra 呼叫）
**負責**：Mina（新增）

```json
Request: { "chip_id": "iot002" }
```

後端邏輯：
1. 驗證 X-Internal-Key
2. 查 `device_sessions` WHERE chip_id + status=active
   - 找到 → 更新 `last_activity_at = now()`
   - 找不到 → 靜默回 200

```json
Response 200: { "status": "ok" }
```

---

### 5.6 結束 session `POST /api/device/unbind`（Bearer token）
**負責**：Mina

```json
Request: { "chip_id": "iot002" }
```

後端邏輯：
1. 查 `device_sessions` WHERE chip_id + status=active + member_id=我 → 找不到回 403
2. 更新 status=ended、ended_at=now()

```json
Response 200: { "message": "session ended" }
```

---

## 六、MQTT 規範（從 IOTwawS3 原始碼查證）

### 6.1 開分指令（雲端 → ESP32）
**負責修正 topic**：Ina

**Topic**：`device/{chip_id}/cmd`（⚠️ 是 `cmd`，不是 `command`，Infra 現在發錯了）
**QoS**：1
**Payload**：
```json
{ "command": "assign_credit", "params": { "count": 1 }, "transaction_id": "uuid" }
```

**ESP32 回應**：
```
Topic: device/{chip_id}/cmd/response
Payload: { "transaction_id": "uuid", "command_type": "assign_credit", "status": "success" }
```

---

### 6.2 洗分指令（雲端 → ESP32）
**負責新增 API**：Ina

**Topic**：`device/{chip_id}/cmd`
**QoS**：1
**Payload**：
```json
{ "command": "settle_credit", "transaction_id": "uuid" }
```

> 韌體固定觸發 PIN_OUT2（洗分腳）1 次，不接受 count 參數（防作弊）。

---

### 6.3 洗分採集（ESP32 → 雲端）

**Topic**：`device/{chip_id}/data`
**QoS**：1
**Payload**：
```json
{ "type": "credit_out", "amount": 1080, "timestamp": 1715456887 }
```

`amount` 是累計值，見第二節說明。

---

### 6.4 開分採集（ESP32 → 雲端，目前忽略）

**Topic**：`device/{chip_id}/data`
**Payload**：`{ "type": "credit_in", "amount": 累計值, "timestamp": ... }`

Infra Listener 收到後目前忽略（Member 已在開分時扣代幣）。

---

### 6.5 GPIO 活動保活（ESP32 → 雲端）
**負責新增**：Coli（韌體）、Ina（Listener）

**Topic**：`device/{chip_id}/activity`
**QoS**：0
**Payload**：`{ "timestamp": 1715456887 }`

**觸發條件**：IN4（PIN_IN4=GPIO 2，預留腳位）偵測到信號變化
**接線**：接遊戲機活動鍵（start鍵、射擊鍵、油門鍵等遊戲中持續觸發的按鍵）
**防抖**：韌體 debounce 200ms

---

### 6.6 訊號極性設定（雲端 → ESP32）
**負責**：Ina (API), Sophie (UI)

**Topic**：`device/{chip_id}/cmd`
**Payload**：
```json
{
  "command": "set_signal_polarity",
  "transaction_id": "uuid",
  "params": {
    "polarity": "active_low"
  }
}
```
**回應**：設備重啟並套用。

---

## 七、Infra API 規格

### 7.1 現有 API 需修正
**負責**：Ina

| API | 問題 | 修正 |
|-----|------|------|
| `POST /api/device/trigger-pulse` | topic 發到 `device/{chip_id}/command` | 改為 `device/{chip_id}/cmd` |

### 7.2 新增 API
**負責**：Ina

**`POST /api/device/trigger-settle`**
```
Header: X-Internal-Key
Body: { "chip_id": "iot002" }

→ MQTT Publish:
  Topic: device/{chip_id}/cmd
  QoS: 1
  Payload: { "command": "settle_credit", "transaction_id": "uuid" }

Response 200: { "success": true }
```

### 7.3 Listener 新增訂閱
**負責**：Ina

| 新增訂閱 | 處理邏輯 |
|---------|---------|
| `device/+/data` | type=credit_out → Redis 覆蓋（即時監控用）+ POST `/internal/device/credit-out { chip_id, cumulative_amount }` |
| `device/+/activity` | POST `/internal/device/activity { chip_id }` |

> ⚠️ Infra 傳給 Member 的是**原始累計值**（`cumulative_amount`），不是 delta。delta 由 Member 自己計算。

---

## 八、Session 生命週期

| 觸發 | 動作 |
|------|------|
| 玩家掃碼 bind | 建立 session，`last_activity_at = now()` |
| 收到 MQTT activity | 更新 `last_activity_at = now()` |
| 排程每分鐘掃描 | `last_activity_at` 超過 **120 秒** → status=timeout |
| 排程保底 | `started_at` 超過 **1200 秒（20 分鐘）** → status=timeout |
| 玩家按 unbind | status=ended |

**排程邏輯**（Member Laravel Scheduler，每分鐘執行）：
```sql
-- 主要機制：120秒無 activity
UPDATE device_sessions SET status='timeout', ended_at=NOW()
WHERE status='active' AND last_activity_at < NOW() - INTERVAL 120 SECOND;

-- 保底：20分鐘（防 GPIO 未接線永久鎖死）
UPDATE device_sessions SET status='timeout', ended_at=NOW()
WHERE status='active' AND started_at < NOW() - INTERVAL 1200 SECOND;
```

**負責**：Mina

---

## 九、WebSocket 事件

| 事件 | Channel | Payload |
|------|---------|---------|
| `DeviceCreditOut` | `member.{member_id}` | `{"chip_id":"...","ticket_count":30,"ticket_balance":1120,"token_balance":349}` |

**負責**：Mina

---

## 十、IOTwawS3 韌體修改
**負責**：Coli

新增 GPIO IN4 活動偵測：
- 腳位：IN4（PIN_IN4 = GPIO 2，目前為預留輸入）
- 接線：接遊戲機活動鍵
- 邏輯：偵測信號變化（上升沿或下降沿），debounce 200ms
- 觸發後發 MQTT `device/{chip_id}/activity { "timestamp": unix_timestamp }`，QoS 0

---

## 十一、Alliance 燒錄頁面修改
**負責**：Allie

檔案：`resources/views/devices/burning.blade.php`，`showQrPreview` 函數

```javascript
// 改前
const content = JSON.stringify({ type, chip_id: chipId, mac });

// 改後（遊戲機 type=collector）
if (type === 'collector') {
  if (!nodeId) {
    alert('請先至 Owner 後台設定此機台的機台編號（node_id），再列印 QR Code');
    return;
  }
  const content = `https://win.tg25.win/m/play?node_id=${nodeId}`;
  // 用 content 生成 QR Code
}
```

> `node_id` 從 `iotv9.devices.node_id` 取得（`device_NNN` 格式）。
> 兌幣機的 QR Code 由 iHub 生成，不在此修改。
> 錯誤提示是給 硬體供應商盟友 (Allie)在燒錄站看的，不是給玩家看的。

---

## 十二、任務分配總覽

| Agent | 任務 | 優先順序 |
|-------|------|---------|
| **Ina** | trigger-pulse 修正 topic（`command` → `cmd`） | 🔴 P1 |
| **Ina** | 新增 trigger-settle API | 🔴 P1 |
| **Ina** | Listener 補訂閱 `device/+/data`，傳 cumulative_amount 給 Member | 🔴 P1 |
| **Ina** | Listener 補訂閱 `device/+/activity`，轉發 Member | 🔴 P1 |
| **Mina** | `device_sessions` 新增 `last_activity_at`（migration） | 🔴 P1 |
| **Mina** | `wallet_transactions` 新增 `cumulative_amount`（migration） | 🔴 P1 |
| **Mina** | 新建 `device_orphan_logs` 表（migration） | 🔴 P1 |
| **Mina** | `POST /api/device/bind` 新增一人一台檢查 | 🔴 P1 |
| **Mina** | 新增 `POST /api/device/settle` | 🔴 P1 |
| **Mina** | 修改 `POST /internal/device/credit-out`（接收 cumulative_amount，算 delta，孤兒 log） | 🔴 P1 |
| **Mina** | 新增 `POST /internal/device/activity` | 🔴 P1 |
| **Mina** | Session 活動超時排程（120s + 1200s 保底） | 🔴 P1 |
| **Coli** | IOTwawS3 新增 GPIO IN4 活動偵測 | 🔴 P1 |
| **Allie** | 燒錄頁面 QR Code 改 URL 格式 | 🟡 P2 |

---

## 十三、孤兒分數說明（業務決策，2026-05-13）

**根本問題**：ESP32 採集卡無法得知遊戲機上的分數狀態，session 超時後無法判斷機台是否有殘留分數。不管超時時間設多長，孤兒分數問題都存在。

| 場景 | 結果 |
|------|------|
| session 已死，無人掃碼，有人按機台洗分鍵 | credit_out 無 session 歸屬 → 孤兒 log，彩票不入帳 |
| session 已死，玩家 B 掃碼建立新 session，洗分 | credit_out 歸入玩家 B → 殘留分數被撿走，系統無法防止 |

系統邊界：記錄孤兒 log，不補償，不介入。待累積數據後評估。

---

## 十四、參數體系

| DB 欄位 | 說明 | 可設定？ |
|---------|------|---------|
| `pulse_to_display` | 1脈衝 = 幾分 | ✅ Owner 後台 |
| `pulse_to_token` | 1脈衝 = 幾代幣 | ❌ 待 Sophie 新增後台入口（測試期間用 DB 預設值 1.00） |
| `out_pulse_to_ticket` | 1洗分脈衝 = 幾彩票 | ✅ Owner 後台 |
| `config_json.credit_options` | 開分選項（分數） | ❌ 待 Sophie 新增後台入口 |
| `config_json.credit_default` | 預設開分選項 | ❌ 待 Sophie 新增後台入口 |

---

*制定者：HQ | 版本：2.0.0 | 日期：2026-05-14*


---

## 區塊二：設備會話 (Device Session) 生命週期與狀態控制

# 遊戲機開分/洗分完整流程設計

> **版本**: 1.0.0  
> **日期**: 2026-05-11  
> **維護者**: HQ  
> **狀態**: 🟡 設計確認中，待各 Agent 實作

---

## 一、設計決策記錄

### Q1：credit_options 存在哪裡？

**決策：加入 `config_json` 欄位，格式由本文件定義。**

理由：
- `iotv9.devices.config_json` 目前全為 null，沒有任何現有規範，可以安全定義
- 不需要新增欄位，減少 migration 風險
- `parameter_templates` 系統已有完整的 `pulse_to_display`、`pulse_to_token`、`out_pulse_to_ticket`，`credit_options` 是衍生設定，放 `config_json` 語意合理
- Sophie 在 Owner 後台 m3 設備管理頁面編輯設備時，新增 `credit_options` 輸入區塊

**`config_json` 格式定義**：
```json
{
  "credit_options": [50, 100, 200, 500],
  "credit_default": 100
}
```

- `credit_options`：可選分數列表（整數陣列），必須是 `pulse_to_display` 的整數倍
- `credit_default`：預設選項，必須在 `credit_options` 內
- 若 `config_json` 為 null 或無此欄位，Member 前端使用預設值 `[100]`

---

### Q2：洗分是否需要 active session？

**決策：強制要求 active session（方案 A）。**

理由：
- 玩家必須先掃碼建立 session，才能開分（扣代幣）
- 若允許無 session 洗分，彩票無法歸屬到玩家，業務邏輯無法成立
- 正確操作順序：掃碼 → 開分 → 玩 → 退彩 → 結束 session
- 若玩家先退彩再結束 session，時序上 session 仍是 active，不會有問題
- 若玩家忘記結束 session 就離開，機台被鎖定 → 需要 **session 超時自動結束機制**（見第六節）

---

## 二、核心狀態機

```
無 session
    │
    │ 玩家掃碼 POST /api/device/bind
    ▼
session: active
    │
    │ 玩家選分確認 POST /api/device/credit（可重複）
    │ ← 扣代幣 → 發 MQTT trigger_pulse
    │
    │ 機台退彩鍵（被動）MQTT device/{chip_id}/data/credit_out
    │ ← 採集脈衝 → 入彩票（需要 active session）
    │
    │ 玩家按 [結束] POST /api/device/unbind
    ▼
session: ended
    │
    ▼
無 session（機台解鎖）
```

---

## 三、資料表設計

### 3.1 `waw_member_production.device_sessions`（Member DB，yd47）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | bigint unsigned PK | |
| `member_id` | bigint unsigned | 玩家 ID，關聯 members 表 |
| `chip_id` | varchar(50) | 遊戲機識別碼（`iotv9.devices.chip_id`） |
| `device_uuid` | varchar(100) | `iotv9.devices.device_id`（UUID），用於呼叫 Infra API |
| `status` | enum('active','ended','timeout') | session 狀態 |
| `started_at` | timestamp | 開始時間 |
| `ended_at` | timestamp nullable | 結束時間 |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

索引：
- `UNIQUE KEY (chip_id, status)` WHERE status = 'active'（確保同一機台只有一個 active session）
- `INDEX (member_id, status)`

### 3.2 `waw_member_production.device_credit_logs`（Member DB，yd47）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | bigint unsigned PK | |
| `session_id` | bigint unsigned | 關聯 device_sessions |
| `member_id` | bigint unsigned | 冗餘存，方便查詢 |
| `chip_id` | varchar(50) | 冗餘存 |
| `display_amount` | int unsigned | 開了多少分（例：100） |
| `pulse_count` | int unsigned | 發了幾個脈衝（例：10） |
| `token_cost` | decimal(10,2) | 扣了多少代幣（例：10.00） |
| `created_at` | timestamp | |

### 3.3 `iotv9.devices.config_json` 格式（Owner DB，infra）

```json
{
  "credit_options": [50, 100, 200, 500],
  "credit_default": 100
}
```

**無需新增欄位**，使用現有 `config_json` 欄位。

### 3.4 彩票入帳（已有機制）

`waw_member_production.member_wallets` + `wallet_transactions` 已存在，且已有 `machine_settle` type。

洗分入帳使用：
- `member_wallets`：`currency_type = 'TICKET'`（需確認是否已有此 currency_type，現有：CASH / COIN / POINT / TOKEN）
- `wallet_transactions`：`type = 'machine_settle'`（已有此 type）

> ⚠️ **待確認**：彩票用哪個 `currency_type`？現有四種（CASH/COIN/POINT/TOKEN），沒有 TICKET。需要 Mina 確認彩票餘額存在哪個 currency_type，或是否需要新增。

---

## 四、API 設計

### 4.1 掃碼綁定

**`POST /api/device/bind`**（Member，Bearer token）

Request：
```json
{ "chip_id": "24587cd63e14" }
```

Member 後端處理：
1. 呼叫 Infra API `GET /api/device/{chip_id}` 確認設備存在且 `status = active`
2. 查 `device_sessions` 是否有 `chip_id + status=active` → 有則回 409
3. 建立 `device_sessions`（member_id, chip_id, status=active）
4. 回傳機台資訊

Response 200：
```json
{
  "session_id": 123,
  "device": {
    "chip_id": "24587cd63e14",
    "name": "機台A",
    "pulse_to_display": 100,
    "pulse_to_token": 1.0,
    "out_pulse_to_ticket": 1.0,
    "credit_options": [50, 100, 200, 500],
    "credit_default": 100
  }
}
```

Response 409：
```json
{ "message": "此機台使用中，請移步其他機台" }
```

---

### 4.2 開分

**`POST /api/device/credit`**（Member，Bearer token）

Request：
```json
{
  "chip_id": "24587cd63e14",
  "display_amount": 100
}
```

Member 後端處理：
1. 查 `device_sessions`：chip_id + status=active，確認 member_id 屬於此玩家
2. 從 Infra API 取得設備參數（`GET /api/device/{chip_id}`，`pulse_to_display`、`pulse_to_token`）
3. 計算：`pulse_count = display_amount / pulse_to_display`
4. 計算：`token_cost = pulse_count × pulse_to_token`
5. 驗證 `display_amount` 必須是 `pulse_to_display` 的整數倍
6. 確認玩家代幣餘額 ≥ token_cost
7. **原子操作**：扣代幣 + 記錄 `device_credit_logs`
8. 呼叫 Infra API `POST /api/device/trigger-pulse`（Infra 發 MQTT）

Response 200：
```json
{
  "display_amount": 100,
  "pulse_count": 10,
  "token_cost": 10.0,
  "token_balance": 90.0
}
```

---

### 4.3 洗分（被動，Infra → Member）

**`POST /internal/device/credit-out`**（Infra → Member，X-Internal-Key）

觸發：Infra Listener 收到 `device/{chip_id}/data/credit_out`

Request：
```json
{
  "chip_id": "24587cd63e14",
  "pulse_count": 60
}
```

Member 後端處理：
1. 查 `device_sessions`：chip_id + status=active → **找不到則回 422，不入帳**
2. 從 Infra API 取得 `out_pulse_to_ticket`
3. 計算：`ticket_count = pulse_count × out_pulse_to_ticket`
4. 增加玩家彩票餘額（`ticket_transactions`）
5. WebSocket 推送 `device.credit_out` 事件

Response 200：
```json
{
  "member_id": 456,
  "ticket_count": 60,
  "ticket_balance": 1060
}
```

Response 422（無 active session）：
```json
{ "message": "no active session for this device" }
```

---

### 4.4 結束 session

**`POST /api/device/unbind`**（Member，Bearer token）

Request：
```json
{ "chip_id": "24587cd63e14" }
```

Member 後端處理：
1. 查 `device_sessions`：chip_id + status=active，確認 member_id 屬於此玩家
2. 更新 `status = ended`，`ended_at = now()`

Response 200：
```json
{ "message": "session ended" }
```

---

## 五、MQTT 規範（依 02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md）

### 5.1 開分指令（雲端 → ESP32）

**Topic**：`device/{chip_id}/command`  
**QoS**：1  
**Payload**：
```json
{ "action": "trigger_pulse", "count": 10 }
```

由 Infra 發送，Member 呼叫 Infra API 觸發。

### 5.2 洗分採集（ESP32 → 雲端）

**Topic**：`device/{chip_id}/data/credit_out`  
**QoS**：1  
**Retain**：✅  
**Payload**：
```json
{ "count": 60, "lifetime": 1234 }
```

Infra Listener 收到後，呼叫 Member `/internal/device/credit-out`。

---

## 六、Session 超時機制

**問題**：玩家忘記結束 session，機台被永久鎖定。

**設計**：
- Session 超時時間：**4 小時**（可配置）
- Member 後端排程（每 15 分鐘執行）：查找 `started_at < now() - 4h` 且 `status=active` 的 session，自動設為 `status=timeout`
- 玩家掃碼時，若發現 active session 已超時，自動結束舊 session 並建立新 session

---

## 七、WebSocket 事件

| 事件名稱 | 觸發時機 | Payload |
|---------|---------|---------|
| `device.credit_out` | 洗分入帳成功 | `{"chip_id":"...","ticket_count":60,"ticket_balance":1060}` |

頻道：`private-member.{member_id}`（需登入）

---

## 八、Infra API 需求（已查證）

> 查證日期：2026-05-11

### 8.1 現有 API 盤點（已查證 2026-05-11）

| API | 路徑 | 狀態 | 說明 |
|-----|------|------|------|
| 查設備資訊（by chip_id） | `GET /api/device/{chip_id}` | ✅ 已有 | 回傳 name、status、pulse_to_display、pulse_to_token、out_pulse_to_ticket、config_json |
| 發 trigger_pulse | `POST /api/device/trigger-pulse` | ✅ 已有 | 接收 {chip_id, count}，發 MQTT `device/{chip_id}/command` |

**Member 直接查 Infra API，不需要 Owner 介入。**

### 8.2 device_id vs chip_id（已解決）

整個開分/洗分流程只用 `chip_id`。Infra API 的 `GET /api/device/{chip_id}` 直接接受 chip_id，無需轉換。

---

## 九、Owner 後台需求（Sophie）

**m3 設備管理頁面新增**：

1. `credit_options` 編輯欄位（逗號分隔輸入，例：`50,100,200,500`）
2. `credit_default` 下拉選單（從 credit_options 選）
3. 儲存時寫入 `config_json`，格式如第一節定義
4. 驗證：每個選項必須是 `pulse_to_display` 的整數倍

> ℹ️ `GET /api/v9/devices?chip_id` 不再需要，Member 直接查 Infra API。

---

## 十、任務分配

| 任務 | 負責 Agent | 優先順序 |
|------|-----------|---------|
| 建立 `device_sessions`、`device_credit_logs` migration | Mina | 1 |
| 實作 `POST /api/device/bind`、`/credit`、`/unbind` | Mina | 1 |
| 實作 `POST /internal/device/credit-out` | Mina | 1 |
| Session 超時排程 | Mina | 2 |
| Infra Listener 訂閱 `device/+/data/credit_out` 並轉發 | Ina | 1 |
| m3 設備管理頁面新增 credit_options 編輯 | Sophie | 2 |
| Member 前端掃碼判斷 type=device 走遊戲機流程 | Mina | 1 |

---

## 十一、待確認事項

- [x] 彩票用哪個 `currency_type`？→ `CURRENCY_TICKET` 已存在於 MemberWallet.php ✅
- [x] Owner API 是否支援 `?chip_id=xxx` 查詢？→ **不再需要，改查 Infra API** ✅
- [x] WebSocket 頻道名稱？→ `member.{member_id}`（Public Channel），已在 WEBSOCKET_CHANNEL_STANDARD.md 定義 ✅

---

*制定者：HQ | 版本：1.0.0 | 日期：2026-05-11*


---

## 區塊三：人機交互與 Agent 連動調整

項目 1：MQTT Topic 修正
我的理解： 從 IOTwawS3 原始碼查證，韌體訂閱的是 device/{chip_id}/cmd，不是 command。Infra 現在發到 command，所以開分指令從來沒到達韌體。這是最根本的斷點。
做法： Ina 修改 trigger-pulse API，把 topic 從 device/{chip_id}/command 改為 device/{chip_id}/cmd。

項目 2：開分 MQTT Payload 格式
我的理解： 韌體 command_executor.c 讀的是頂層 command 和 amount 欄位。現在 Infra 發的是 {"action":"trigger_pulse","count":1}，韌體根本不認識 action 這個 key。
做法： Infra trigger-pulse 改 payload 為：
{
  "command": "assign_credit",
  "amount": 1,
  "transaction_id": "uuid"
}
### 「現在 Infra 發的是 {"action":"trigger_pulse","count":1}」這句話不準確 你再仔細查一下


項目 3：新增 trigger-settle API（Infra）
我的理解： 洗分指令格式從韌體查證：{"command":"settle_credit","transaction_id":"uuid"}，發到 device/{chip_id}/cmd。韌體收到後固定觸發 PIN_OUT2 一次，遊戲機自行執行洗分。

做法： Ina 新增 POST /api/device/trigger-settle，接收 {chip_id}，發 MQTT settle_credit 到 device/{chip_id}/cmd。

項目 4：Infra Listener 補訂閱 device/+/data
我的理解： 現在 Listener 只訂閱 kiosk/+/event 和 kiosk/+/status，完全沒有訂閱 device/+/data。所以洗分脈衝上報後直接消失，彩票永遠不會入帳。

做法： Ina 在 Listener 補訂閱 device/+/data，收到後：

type = "credit_out" → 計算 delta（累計值，需維護 Redis last_credit_out） → POST /internal/device/credit-out
type = "credit_in" → 目前忽略（Member 已在開分時扣代幣）
### 這裡我看不懂 你再仔細的說明清楚一點


項目 5：Infra Listener 補訂閱 device/+/activity
我的理解： GPIO 保活的 MQTT 訊息 device/{chip_id}/activity 需要 Infra 接收並轉發給 Member，Member 才能更新 last_activity_at。

做法： Ina 補訂閱 device/+/activity，收到後 POST /internal/device/activity { chip_id }。

項目 6：IOTwawS3 新增 GPIO IN3 活動偵測（Coli）
我的理解： 硬體規格：IN3 = PIN_IN3 = GPIO 1，目前定義為「擺錘警告」。需要確認這個腳位是否可以改用，或者用 IN4（預留）。接遊戲機的活動鍵（start/射擊/油門），偵測信號變化就發 MQTT。
### 用 IN4（預留）
做法： Coli 在 IOTwawS3 新增：
監聽 
### IN4 的信號變化（上升沿或下降沿）
debounce 200ms 防抖
觸發後發 MQTT device/{chip_id}/activity { "timestamp": ... }，QoS 0
待確認：IN3 還是 IN4？如果 IN3 已被擺錘警告佔用，要用 IN4。
### 確認用 IN4

項目 7：Member device_sessions 新增 last_activity_at
我的理解： 現有 migration 已建立 device_sessions 表，但沒有 last_activity_at 欄位。需要新增 migration。
做法： Mina 新增 migration，last_activity_at TIMESTAMP NULL，bind 時設為 now()。

項目 8：Member 新增 POST /internal/device/activity
我的理解： Infra 轉發 activity 事件後，Member 更新對應 session 的 last_activity_at。找不到 active session 時靜默忽略（不報錯，因為 session 可能已超時）。

做法： Mina 新增端點，X-Internal-Key 驗證，更新 last_activity_at = now()。

項目 9：Member 新增 POST /api/device/settle
我的理解： 玩家手機上的洗分鍵。按下後 Member 呼叫 Infra trigger-settle，Infra 發 MQTT 給韌體，韌體觸發洗分繼電器一次。彩票不在這個 API 入帳，而是等 ESP32 採集到退分脈衝後透過 credit-out 鏈路入帳。

做法： Mina 新增端點，Bearer token 驗證，確認 active session 存在，呼叫 Infra trigger-settle，回傳 {status:"queued"}。

項目 10：Member bind 新增「一人一台」檢查
我的理解： 同一個會員不能同時綁定兩台遊戲機。bind 時先查該會員是否已有其他 active device session（不限機台），有的話回 409。

做法： Mina 在 bind 邏輯最前面加一個檢查：

查 device_sessions WHERE member_id=我 AND status=active AND chip_id ≠ 這台
→ 有 → 409「您已在使用另一台機台，請先結束後再掃碼」
項目 11：Member Session 活動超時排程
我的理解： 每分鐘掃描 last_activity_at 超過 120 秒的 active session，自動設為 timeout。另外保底掃描 started_at 超過 4 小時的（防 GPIO 未接線時永久鎖死）。
### 如果前一個session是在兑幣機 的session 還存活 一掃描通訊卡的code就銷毀兑幣卡的session
### 防 GPIO 未接線時永久鎖死 改為1200秒就好 不用到4個小時 
做法： Mina 在 Laravel Scheduler 新增排程，每分鐘執行兩個 UPDATE。

項目 12：孤兒洗分 log
我的理解： /internal/device/credit-out 收到時找不到 active session，不能回 422（會讓 Infra 以為失敗），應該記錄孤兒 log 後回 200。
### /internal/device/credit-out這是API吧 不是Topic吧？
做法： Mina 修改 credit-out 邏輯，無 session 時寫入孤兒 log 表（或 warning log），回 {status:"orphan"}。
### 要做孤兒分數的統計 要有一個孤兒記錄表是吧？

項目 13：QR Code 格式（Alliance）
我的理解： Alliance 燒錄頁面的 QR Code 還是 JSON 格式 {"type":"collector","chip_id":"...","mac":"..."}，但 Member 掃碼判斷已改為認 URL 格式 https://win.tg25.win/m/play?node_id=device_001。兩邊對不上。Allie 說完成但代碼沒改。

做法： Allie 修改 burning.blade.php 的 showQrPreview 函數，改為生成 URL 格式，node_id 為 null 時顯示錯誤「請先設定機台編號」。
### 「請先設定機台編號」 是給硬體供應商看的還是給會員玩家看的？ QRCODE是貼在機台上的喔 除非 是剛燒好 有問題 工程師在辦公室測試


項目 4（看不懂）：
device/+/data 這個 topic，韌體用它上報兩種事件，用 type 欄位區分：
type = "credit_in"：玩家開分後，機台計數器跳動，ESP32 採集到脈衝，上報「我收到了 N 個開分脈衝」
### 開分是會到 N 個開分脈衝  開完分 遊戲機會自己有計數器配合跳動  esp32採集計數器脈衝 得到開分數

type = "credit_out"：玩家洗分後，機台退分計數器跳動，ESP32 採集到脈衝，上報「我收到了 N 個洗分脈衝」
### 洗分脈衝只會是一個 遊戲機自己會將機台分數歸零 其中會根據剩餘分數驅動洗分計數器 ,esp32從而採集洗分數量

洗分是靠
amount 是累計值（里程表），不是本次增量。例如：

開機後第一次洗分 50 脈衝 → amount = 50
第二次洗分 30 脈衝 → amount = 80（不是 30）
所以 Infra 收到後要計算 delta：

delta = 本次 amount - 上次記錄的 amount
這個「上次記錄的 amount」存在 Redis 裡。

### 累計值一直到寫進資料庫都不能省略 不能在途中就算出delta寫資料 因為用累計值的精髓就在紀錄累計值的上下筆,不怕漏接




項目 4（累計值不能在途中算 delta）：

你說得對，這是重要的架構決策。我之前的設計是「Infra 算 delta，只傳 delta 給 Member」，但這樣就失去了累計值的容錯優勢（這正是 LESSON_20260512_CREDIT_CUMULATIVE_VS_DELTA.md 記錄的教訓）。

正確做法：

ESP32 上報 device/{chip_id}/data
  → Infra Listener 收到
  → 原始 amount（累計值）完整轉發給 Member
  → Member 自己維護上一筆累計值，計算 delta，入帳
  → Member DB 同時存入原始累計值（直接覆蓋，不是 +=）
這樣即使中間漏一筆 MQTT，下一筆收到時 delta 自動校正，不會多算。

###  → Member DB 同時存入原始累計值（直接覆蓋，不是 +=）
是增加一筆數據吧 不是覆蓋誰吧？？ 還有還有你說的redis 我記得是v9那邊需要即時監控 在redis裡直接覆蓋上一筆累計值 你說的是這個嗎？


Redis：直接覆蓋，即時監控用
wallet_transactions：增加一筆，完整歷史記錄
device_sessions：直接覆蓋，存最新累計值供下次計算 delta

### device_sessions 這個有需要嗎？ 
2  | 42         | 小明      | iot002  | 30          | 1080 
的上一筆就是
1  | 42         | 小明      | iot002  | 50          | 1050 
有需要再一個值來減嗎



---

## 🔗 文件神經連結

### 強關聯（必讀）
- `brains/knowledge/05_business_flows/game_v0_arcade/GAME_V3_CORE_SPECIFICATION.md` - 遊戲機 3.0 系統架構與業務流程規格書。
- `brains/knowledge/02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - 技術命名與 Payload 數據負載標準規範。
