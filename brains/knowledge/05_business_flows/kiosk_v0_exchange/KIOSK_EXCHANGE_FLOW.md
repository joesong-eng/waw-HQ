# 兌幣機物理與金流交互流程規格書 (Kiosk Physical & Financial Flow Specification)

> **版本**：v2.0.0 (合併版)  
> **最後更新**：2026-06-05  
> **狀態**：Active / Authoritative  
> **適用角色**：Mina (Member), Ina (Infra), Sophie (Owner), Fio (Firmware)

---

# 🏧 Kiosk 會員兌幣完整業務流程規範

> **版本**: 2.3.0
> **日期**: 2026-05-13
> **狀態**: ✅ 設計定稿 + 實機修復記錄
> **適用系統**: Member (`win.tg25.win`)、Infra (`api.tg25.win`)、Firmware (`IOTkiosk_v0`)、Owner (`iot.tg25.win`)
> **設計者**: HQ

---

## 一、業務概述

會員走進遊藝場，用手機掃描 iHub 平板上的 QR Code，建立「會員 ↔ 兌幣機」的 session，然後投入鈔票換取代幣。

整個流程橫跨四個系統：

| 系統 | 職責 |
|------|------|
| **Member** | 會員身份驗證、session 管理、escrow 裁決、代幣入帳 |
| **Infra** | MQTT 監聽、webhook 轉發、MQTT 指令代發 |
| **Firmware (Fio)** | 紙鈔機 RS232 通訊、escrow 事件上報、等待雲端裁決 |
| **Owner** | 兌幣機設定管理（換算比例） |

---

## 二、架構決策（HQ 已拍板）

| 決策 | 結論 |
|------|------|
| 代幣換算比例 | **場地層級**設定，存於 `iotv9.venues.token_value_twd`，由 Owner 後台 M4 場地管理設定。`kiosks.token_rate` 欄位保留但不使用（廢棄）。 |
| MQTT 指令發送方 | Member 透過 Infra API 代發，Member 不直接持有 MQTT 憑證 |
| Escrow 裁決方式 | **人工確認**（HQ 決策，2026-05-08）：Infra Listener 收到 escrow → call Member webhook → Member 回傳 `pending` 並廣播 `KioskEscrowPending` → iHub 平板顯示確認按鈕 → 人工按確認 → iHub 呼叫 `POST api.tg25.win/api/kiosk/escrow/confirm` → Infra 橋接到 Member → Member 發 MQTT stack 指令 |
| MQTT 格式 | 統一使用新格式 `kiosk/{id}/event`，舊格式 `bill/detected`、`bill/confirmed` 廢棄不用 |

---

## 三、前置條件

在會員兌幣流程開始前，以下條件必須已就緒：

| 條件 | 負責方 | 資料位置 |
|------|--------|---------|
| 兌幣卡已燒錄並與平板配對 | Alliance (Allie) | `iotv9.kiosks`（`screen_mac`, `esp32_mac`） |
| 換算比例已設定 | Owner (Sophie) | `iotv9.venues.token_value_twd`（M4 場地管理設定） |
| 平板已安裝 iHub APK 並在線 | iHub (Hubie) | `waw_member_production.kiosk_sessions.last_active_at` |
| 兌幣卡 MQTT 已連線，`ba_state = DISABLED` | Firmware (Fio) | `kiosk/{chip_id}/status` |

> 注意：兌幣卡開機預設為 DISABLED（Fail-Safe），等待 Member 發 enable 才亮綠燈。

---

## 四、完整流程

### 4.1 流程圖

```
會員開啟 win.tg25.win
    ↓
打開掃描器
    ↓
掃描 iHub 平板 QR Code
    ↓
Member 驗證 QR Code（kiosk_id + screen_mac）
    ↓
    ├─ 機台忙碌（已有 active session）→ 回傳 409，提示「使用中」
    ├─ 平板離線 → 回傳 503，提示「平板離線」
    └─ 驗證通過 ↓
    ↓
Member 建立 kiosk_session（member_id ↔ kiosk_id）
    ↓
Member 呼叫 Infra MQTT API → 發送 enable 指令
    ↓
Infra 發布 kiosk/{chip_id}/cmd → {"action":"enable"}
    ↓
韌體收到 enable → ba_state = IDLE（🟢 綠燈）
    ↓
會員投入鈔票
    ↓
韌體驗鈔 → 進入 ESCROW 狀態
    ↓
韌體發布 kiosk/{chip_id}/event → {"event_type":"escrow","amount":100}
    ↓
Infra Listener 收到 escrow 事件
    ↓
Infra 呼叫 Member Webhook → POST /internal/kiosk/escrow
    ↓
Member 查詢 kiosk_session → 回傳 pending，廣播 KioskEscrowPending
    ↓
iHub 平板顯示確認按鈕（人工確認，HQ 決策）
    ↓
iHub 按確認 → POST api.tg25.win/api/kiosk/escrow/confirm
    ↓
Infra 橋接 → POST win.tg25.win/api/kiosk/escrow/confirm
    ↓
Member 呼叫 Infra MQTT API → 發送 stack 指令
    ↓
Infra 發布 kiosk/{chip_id}/cmd → {"action":"stack"} 或 {"action":"reject"}
    ↓
韌體執行收鈔或退鈔
    ↓
韌體發布 kiosk/{chip_id}/event → {"event_type":"stacked"} 或 {"event_type":"rejected"}
    ↓
Infra Listener 收到 stacked 事件
    ↓
Infra 呼叫 Member Webhook → POST /internal/kiosk/stacked
    ↓
Member 查換算比例 → 代幣入帳 → 寫入交易記錄
    ↓
（會員可繼續投幣，重複上述流程）
    ↓
會員離開 → Member 結束 kiosk_session
    ↓
Member 呼叫 Infra MQTT API → 發送 disable 指令
    ↓
韌體收到 disable → ba_state = DISABLED（🔴 紅燈）
```

---

## 五、資料庫設計

### 5.1 `iotv9.kiosks`（Owner 管理，Alliance 寫入綁定）

```sql
-- 現有表，新增 token_rate 欄位
ALTER TABLE kiosks ADD COLUMN token_rate DECIMAL(10,4) NOT NULL DEFAULT 1.0000
    COMMENT '換算比例：1 元 TWD = N 代幣，例如 1.0000 表示 100 元 = 100 代幣';
```

| 欄位 | 說明 |
|------|------|
| `id` | 兌幣機 ID |
| `screen_mac` | iHub 平板 MAC（QR Code 識別用） |
| `esp32_mac` | 兌幣卡 MAC（MQTT chip_id） |
| `token_rate` | 換算比例（新增），由 Owner 後台設定 |

### 5.2 `waw_member_production.kiosk_sessions`（Member 管理）

```sql
ALTER TABLE kiosk_sessions
    ADD COLUMN kiosk_no      BIGINT NULL        COMMENT 'iotv9.kiosks.id（V9 外鍵）',
    ADD COLUMN member_id     BIGINT NULL        COMMENT '綁定的會員 ID，NULL 表示無人使用',
    ADD COLUMN esp32_mac     VARCHAR(50) NULL   COMMENT '兌幣卡 MAC',
    ADD COLUMN status        ENUM('active','ended') DEFAULT 'active',
    ADD COLUMN started_at    TIMESTAMP NULL,
    ADD COLUMN ended_at      TIMESTAMP NULL;
```

> ⚠️ 原有 `kiosk_id` (varchar) 保留不動，現有資料為 `K01`、`kiosk_001` 等字串格式，不可轉型。`kiosk_no` 為新增欄位，關聯 `iotv9.kiosks.id`。

### 5.3 `waw_member_production.kiosk_transactions`（新建）

```sql
CREATE TABLE kiosk_transactions (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id      BIGINT NOT NULL        COMMENT 'kiosk_sessions.id',
    member_id       BIGINT NOT NULL        COMMENT '會員 ID',
    esp32_mac       VARCHAR(50) NOT NULL   COMMENT '兌幣卡 MAC',
    amount_twd      INT NOT NULL           COMMENT '鈔票面額（元）',
    token_value_twd DECIMAL(10,2) NOT NULL COMMENT '當時換算比例快照（來自 venues.token_value_twd，1 代幣 = N 元）',
    tokens_credited INT NOT NULL           COMMENT '入帳代幣數',
    event_timestamp BIGINT NOT NULL        COMMENT '韌體事件 timestamp（冪等用）',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_event (esp32_mac, event_timestamp)  -- 防止重複入帳
);
```

---

## 六、QR Code 規範

> **⚠️ 本章節僅供快速參考，完整規範請查閱：**  
> **`brains/knowledge/02_technical_standards/QRCODE_FORMAT_STANDARD.md`**

### 6.1 QR Code 格式（引用規範）

**標準格式**：
```
https://win.tg25.win/kiosk?id={node_id}&token={session_token}
```

**詳細說明**：
- 格式定義：`QRCODE_FORMAT_STANDARD.md` §一、格式規範 → §1.1 兌幣機 QR Code
- 生成方規範：`QRCODE_FORMAT_STANDARD.md` §四、生成與讀取規範 → §4.1 → 生成方：iHub
- 讀取方規範：`QRCODE_FORMAT_STANDARD.md` §四、生成與讀取規範 → §4.1 → 讀取方：Member
- 部署順序：`QRCODE_FORMAT_STANDARD.md` §五、部署順序規範

**本流程中的使用**：
- iHub 平板每 90 秒向 Infra 請求新 token，更新 QR Code
- 會員用手機掃描後，跳轉到 Member 系統兌幣頁面
- token 過期時間：90 秒

### 6.2 URL 參數處理流程

手機相機掃到 QR Code 後：
```
https://win.tg25.win/kiosk?id=kiosk_001&token=xxx
  ↓
web.php /kiosk 路由：讀 ?id= 或 ?kiosk=（向下相容）
  ↓
302 重導向 → /?token=xxx&kiosk=kiosk_001
  ↓
welcome.blade.php 情境 C：讀 ?kiosk=，存入 sessionStorage
  ↓
登入後自動執行 bindToKiosk(kiosk_001, xxx)
```

APP 內掃碼（onScanSuccess）：
```
掃到 URL → 解析 searchParams.get('id') || searchParams.get('kiosk')
  ↓
直接執行 bindToKiosk(kioskId, token)
```

### 6.3 QR Code 更新頻率

- iHub 平板每 90 秒向 Infra 請求新 token，更新 QR Code
- token 過期後掃碼會回傳 422「QR Code 已過期」
- 安全性依賴：會員必須登入 Member 才能掃碼，同一台機器同時只能有一個 active session（409 防重複）

---

## 七、API 規範

### 7.1 Member 掃碼 API

```
POST /api/kiosk/scan
Headers: Authorization: Bearer {member_token}
Body:
{
  "screen_mac": "STB-T1BQTYBDUEGX",
  "kiosk_id": 1
}

Response 200（成功）:
{
  "session_id": 123,
  "kiosk_name": "兌幣機 #1",
  "esp32_mac": "e072a1f73a78",
  "token_rate": 1.0,
  "status": "ready"
}

Response 409（機台忙碌）:
{
  "error": "kiosk_busy",
  "message": "此兌幣機正在使用中"
}

Response 503（平板離線）:
{
  "error": "tablet_offline",
  "message": "平板目前離線，請聯繫工作人員"
}

Response 422（兌幣卡離線）:
{
  "error": "kiosk_unavailable",
  "message": "兌幣機目前無法使用"
}
```

**掃碼驗證邏輯（依序）**：
1. 確認 `kiosk_id` 存在於 `iotv9.kiosks`，取得 `esp32_mac` 和 `token_rate`
2. 確認此 kiosk 目前沒有 active session（防雙重佔用）
3. 確認平板在線（`kiosk_sessions.last_active_at` 在 120 秒內）
4. 確認兌幣卡 MQTT 在線且 `ba_state != FAULT`（查 `kiosk/{chip_id}/status` Retain 訊息）
5. 建立 kiosk_session，呼叫 Infra MQTT API 發送 enable

### 7.2 Member 結束 Session API

> **呼叫方**：iHub 平板透過 Infra bridge 呼叫，不帶 Bearer token。

**Infra bridge 端點**（iHub 呼叫）：
```
POST api.tg25.win/api/kiosk/session/{session_id}/end
Headers: X-Internal-Key: v9-internal-key-2026
Body: { "reason": "ihub_manual" | "ihub_force_ended" | "ihub_timeout" }
```

**Member 端點**（Infra bridge 轉發）：
```
POST win.tg25.win/api/kiosk/session/{session_id}/end
Headers: X-Internal-Key: v9-internal-key-2026
Body: { "reason": "ihub_manual" | "ihub_force_ended" | "ihub_timeout" }

Response 200:
{
  "status": "ended",
  "total_tokens_credited": 300
}
```

**結束邏輯**：
1. 驗證 `X-Internal-Key`（不是 Bearer token，因為是 iHub 發的）
2. 確認 session 存在且狀態為 active
3. 更新 status = ended，ended_at = now()
4. 呼叫 Infra MQTT API 發送 `{"action":"disable"}` 到 `kiosk/{chip_id}/cmd`
5. 廣播 `.KioskSessionEnded` 到 `kiosk.{node_id}`

### 7.3 Infra MQTT 代發 API

```
POST api.tg25.win/internal/mqtt/publish
Headers: X-Internal-Key: {internal_key}
Body:
{
  "topic": "kiosk/e072a1f73a78/cmd",
  "payload": {"action": "stack"},
  "qos": 2
}

Response 200:
{
  "status": "published"
}
```

### 7.4 Member Webhook（Infra → Member）

#### Escrow 事件

```
POST win.tg25.win/internal/kiosk/escrow
Headers: X-Internal-Key: {internal_key}
Body:
{
  "chip_id": "e072a1f73a78",
  "amount": 100,
  "timestamp": 1713253800
}

Response 200（裁決結果）:
{
  "action": "stack"   // 或 "reject"
}
```

> ⚠️ **時序要求**：Infra 從收到 escrow 到收到 Member 回應，整體必須在 **4 秒內**完成（預留 1 秒給 Infra 轉發 MQTT 指令，總計 5 秒韌體 Fail-Safe）。

**Member 裁決邏輯**：
```
1. 以 chip_id 查詢 kiosk_sessions，找到 active session
2. 確認 session 對應的 member_id
3. 裁決：
   ├─ session 存在且 active → "stack"
   ├─ session 不存在 → "reject"（無人使用）
   ├─ 會員帳戶異常（凍結等）→ "reject"
   └─ 金額超過單次上限（預設 10,000 元）→ "reject"
```

#### Stacked 事件

```
POST win.tg25.win/internal/kiosk/stacked
Headers: X-Internal-Key: {internal_key}
Body:
{
  "chip_id": "e072a1f73a78",
  "amount": 100,
  "timestamp": 1713253805
}

Response 200:
{
  "status": "credited",
  "tokens_credited": 100
}
```

**Member 入帳邏輯**：
```
1. 以 chip_id 查詢 active session，取得 member_id 和 session_id
2. 以 (chip_id + timestamp) 做冪等檢查，防止重複入帳
3. 透過 kiosk → venue 查詢 venues.token_value_twd（快照存入交易記錄）
4. tokens = floor(amount / token_value_twd)
   例：100 元 / 1.00 = 100 代幣（目前測試場地設定值）
5. 增加 member.token_balance
6. 寫入 kiosk_transactions
```

#### Rejected 事件

```
POST win.tg25.win/internal/kiosk/rejected
Headers: X-Internal-Key: {internal_key}
Body:
{
  "chip_id": "e072a1f73a78",
  "amount": 100,
  "reason": "timeout",   // "timeout" | "rejected_by_server" | "hardware"
  "timestamp": 1713253810
}

Response 200:
{
  "status": "noted"
}
```

---

## 八、Session 生命週期

| 狀態 | 觸發條件 | 動作 |
|------|---------|------|
| 建立 | 會員掃碼成功 | 寫入 kiosk_sessions，發 enable |
| 活躍 | 每次 stacked 事件 或 會員心跳 | 更新 last_active_at / member_last_seen_at，重置 60 秒計時器 |
| 自動結束 | 最後一次 stacked 後 60 秒無新投幣 | 顯示結算畫面，10 秒後自動確認，status=ended，發 disable |
| 會員離線結束 | 60 秒未收到會員心跳 | status=ended，發 disable |
| 主動結束 | 會員點擊「確認結束」 | status=ended，發 disable，顯示結算畫面 |

**超時機制**：Member 排程每分鐘掃描一次，找出 `last_active_at` 超過 10 分鐘的 active session，強制結束並發 disable（最後防線）。

**會員離線偵測機制**：
- `kiosk_sessions` 新增 `member_last_seen_at TIMESTAMP NULL` 欄位
- 會員掃碼成功後，前端每 30 秒打一次 `POST /api/kiosk/session/{id}/heartbeat`
- 後端更新 `member_last_seen_at = now()`
- 排程每分鐘掃描：`member_last_seen_at` 超過 60 秒且 session 為 active → 結束 session，發 disable
- 會員主動關閉頁面時，`beforeunload` 事件觸發 `POST /api/kiosk/session/{id}/end`（best-effort）

---

## 八之一、會員端畫面狀態機

掃碼成功後，`win.tg25.win` 前端依序顯示以下畫面：

### 狀態 A：等待投幣
```
┌─────────────────────────────────┐
│  ⚠️ 請勿離開頁面                 │
│                                 │
│  請投入紙鈔                      │
│  100 / 500 / 1000 元            │
│                                 │
│  [結束兌換]                      │
└─────────────────────────────────┘
```
- 計時器：尚未啟動
- 觸發條件：掃碼成功後進入

### 狀態 B：投幣中（每次 stacked 後）
```
┌─────────────────────────────────┐
│  ⚠️ 請勿離開頁面                 │
│                                 │
│  ✅ +100 代幣                    │  ← 動畫提示
│  本次累計：200 代幣              │
│  目前餘額：350 代幣              │
│                                 │
│  60 秒後自動結束 [倒數]          │
│  [繼續投幣] [結束兌換]           │
└─────────────────────────────────┘
```
- 計時器：每次 stacked 重置為 60 秒
- 代幣餘額：透過 Reverb WebSocket 即時更新

### 狀態 C：結算確認

**有兌換（exchangeAccumulated > 0）**：
```
┌─────────────────────────────────┐
│  ✅ 兌換完成                     │
│                                 │
│  本次兌換：200 代幣              │
│  目前餘額：350 代幣              │
│                                 │
│  8 秒後自動返回                  │
│  [立即返回主頁]                  │
└─────────────────────────────────┘
```

**無兌換（exchangeAccumulated = 0，玩家取消）**：
```
┌─────────────────────────────────┐
│  ✕ 已取消兌換                   │
│                                 │
│  本次未兌換任何代幣              │
│                                 │
│  8 秒後自動返回                  │
│  [立即返回主頁]                  │
└─────────────────────────────────┘
```

- 觸發條件：收到 `.KioskSessionEnded` WebSocket 事件
- 8 秒後自動返回主頁

### 代幣即時更新機制
每次 stacked 事件後：
1. Member 入帳，透過 Reverb 推送 `KioskSessionUpdated` 事件
2. 前端收到後：更新餘額顯示 + 顯示「+X 代幣」動畫 + 重置 60 秒計時器

---

## 九、錯誤處理規範

### 9.1 裁決超時

| 情況 | 處理方式 |
|------|---------|
| Member Webhook 4 秒內未回應 | Infra 記錄錯誤，不發任何指令；韌體 5 秒後自動退鈔（Fail-Safe） |
| Infra MQTT API 發送失敗 | Member 記錄錯誤，不重試（鈔票已被韌體退回） |

### 9.2 重複 Escrow 事件

- Member 以 `(chip_id + timestamp)` 做冪等判斷
- 同一筆已裁決的 escrow 不重複處理，直接回傳原裁決結果

### 9.3 Stacked 重複入帳防護

- `kiosk_transactions` 表有 `UNIQUE KEY (esp32_mac, event_timestamp)`
- 重複 stacked 事件 INSERT 會觸發 duplicate key，Member 捕捉後回傳 200 但不重複入帳

### 9.4 Session 不存在時收到 Escrow

- 韌體在 enable 狀態才能收鈔
- 若 session 已結束，Member 應已發 disable；若仍收到 escrow（極端情況），一律 reject

### 9.5 MQTT 斷線時有 Escrow 懸停

- 韌體斷線時自動退鈔（Fail-Safe，韌體自行處理）
- Member 不需要額外處理

---

## 十、跨系統責任邊界

| 功能 | 負責方 | 說明 |
|------|--------|------|
| QR Code 顯示 | iHub (Hubie) | 平板顯示靜態 QR Code |
| 掃碼 API | Member (Mina) | 建立 session，呼叫 Infra 發 enable |
| Escrow 裁決 | Member (Mina) | 查 session，決定 stack/reject |
| 代幣入帳 | Member (Mina) | 收到 stacked webhook 後入帳 |
| MQTT 監聽 | Infra (Ina) | 訂閱 `kiosk/+/event`，轉發 webhook |
| MQTT 指令代發 | Infra (Ina) | 提供 `/internal/mqtt/publish` API |
| 紙鈔機控制 | Firmware (Fio) | 執行 stack/reject，上報事件 |
| 換算比例設定 | Owner (Sophie) | Owner 後台設定 `iotv9.kiosks.token_rate` |
| 綁定關係維護 | Alliance (Allie) | 寫入 `iotv9.kiosks`（screen_mac, esp32_mac） |
| DB Schema 變更 | Infra (Ina) | 執行 ALTER TABLE，確認不破壞現有功能 |

---

## 十一、MQTT 主題（本流程使用）

依據 `brains/knowledge/02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md`：

| Topic | 方向 | QoS | 用途 |
|-------|------|-----|------|
| `kiosk/{chip_id}/cmd` | 雲端 → 韌體 | 2 | enable / disable / stack / reject |
| `kiosk/{chip_id}/event` | 韌體 → 雲端 | 2 | escrow / stacked / rejected |
| `kiosk/{chip_id}/status` | 韌體 → 雲端 | 1 | ba_state 心跳（掃碼前確認用） |

舊格式 `kiosk/{id}/bill/detected`、`kiosk/{id}/bill/confirmed` **已廢棄，Fio 不發送**。

---

## 十二、實作任務清單

| # | 任務 | 負責 Agent | 前置條件 | 狀態 |
|---|------|-----------|---------|------|
| 1 | 換算比例設定頁 | Sophie | 無 | ✅ 已完成（`venues.token_value_twd` 已存在，Owner M4 場地管理 Edit Modal 已可設定） |
| 2 | `kiosk_sessions` 新增 member 相關欄位 | Ina | 確認現有 schema | ⏳ |
| 3 | 新建 `kiosk_transactions` 表 | Ina | 無 | ⏳ |
| 4 | Infra 實作 `POST /internal/mqtt/publish` API | Ina | 無 | ⏳ |
| 5 | Infra Listener 新增 webhook 轉發邏輯 | Ina | 任務 4 完成 | ⏳ |
| 6 | Member 實作掃碼 API + session 管理 | Mina | 任務 2、4 完成 | ⏳ |
| 7 | Member 實作 escrow webhook + 裁決邏輯 | Mina | 任務 5 完成 | ⏳ |
| 8 | Member 實作 stacked webhook + 入帳邏輯 | Mina | 任務 3、7 完成 | ⏳ |
| 9 | Member 實作 session 超時排程 | Mina | 任務 6 完成 | ⏳ |
| 10 | Fio 移除舊格式發送，只保留新格式 | Fio | 任務 5 完成 | ⏳ |

### 技術債記錄
- `venues.token_value_twd` 欄位名稱將幣別硬編進去，未來支援多幣別時需重構為 `token_value` + 獨立幣別欄位。功能完成後再處理。

---

## 十三、相關文件

- `brains/knowledge/05_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` — 韌體層完整時序規範
- `brains/knowledge/02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` — MQTT 主題唯一真理
- `brains/knowledge/05_business_flows/kiosk_v0_exchange/KIOSK_ENGINEERING_DASHBOARD.md` — 工程測試頁設計
- `brains/knowledge/hardware_pulse_mapping.md` — 硬體脈衝與虛擬資產對應

---

---

## 十四、2026-04-30 實機修復記錄（三燈號通關）

### 問題背景

工程測試頁 `win.tg25.win/engineering/kiosk` 有三個燈號：
- 📱 平板（`last_active_at` 在 120 秒內）
- 💴 兌幣卡+紙鈔機（`ba_state` + 有 active session）
- 🧑 會員 Session（`kiosk_sessions` 有 active + `kiosk_no` 對應）

### 修復過程

#### 問題 1：WebSocket 頻道大小寫不一致

**現象**：掃碼成功後 iHub 平板畫面不跳轉。

**根因**：Member 廣播頻道用小寫 `kiosk.kiosk_001`，iHub 監聽大寫 `kiosk.KIOSK_001`。

**修復**：統一規範，**所有 WebSocket 廣播頻道一律小寫**。
- Member：`MemberBoundToKiosk`、`KioskSessionUpdated`、`KioskSessionEnded` 全部改為 `strtolower(kiosk_id)`
- iHub：訂閱時加 `.toLowerCase()`

**規範**：`kiosk.{kiosk_id}` 頻道名稱永遠小寫，不得使用大寫。

---

#### 問題 2：QR Code token 每次心跳都換，導致掃碼失敗

**現象**：掃碼後出現「QR Code 已過期或無效」。

**根因**：`KioskSession::refreshToken()` 每次 iHub 心跳（90 秒）都換新 token，但 QR Code 上顯示的是舊 token，`bind()` 用舊 token 查 DB 查不到。

**修復**：`refreshToken` 改為只有 token 過期後才換新的：
```php
if (!$session->token_expires_at || $session->token_expires_at->isPast()) {
    $updateData['token'] = Str::random(32);
    $updateData['token_expires_at'] = now()->addSeconds(90);
}
```

**同時**：`bind()` 的 session 查詢改為以 `kiosk_id + status='active' + member_id IS NULL` 查詢，token 只做次要驗證（確認 QR Code 屬於這台機器），不再作為查詢 key。

---

#### 問題 3：bind 成功但前端瞬間顯示錯誤 modal

**現象**：bind 成功，toast 顯示「Flow: SID:739 | CID:kiosk_001 | View:exchange」，但同時出現「儲值機連線失敗 / QR Code 已過期」。

**根因**：`bindToKiosk` 的 `finally` 區塊將 `loadingKiosk = false`，Vue 重新渲染時 `kioskBindResult` 是 null、`loadingKiosk` 是 false，modal 的 `v-else` 瞬間顯示錯誤畫面（競態條件）。

**修復**：bind 成功後立刻 `showKioskModal.value = false`，不等 `finally`。

---

#### 問題 4：Laravel Scheduler 未設定，殭屍 session 累積

**現象**：每次掃碼成功後 session 60 秒就被殺，紙鈔機退鈔。

**根因**：
1. Laravel Scheduler 沒有加入 crontab，`closeIdleSessions` 從未執行
2. 殭屍 session（`member_id` 有值但已無人使用）累積，下次掃碼被 409 擋

**修復**：在 yd47 加入 crontab：
```
* * * * * cd /www/wwwroot/win.tg25.win && php artisan schedule:run >> /dev/null 2>&1
```

---

#### 問題 5：heartbeat 未打進來，session 60 秒後被排程殺掉

**現象**：掃碼成功進入等待投幣畫面，60 秒後 session 被自動結束，紙鈔機退鈔。

**根因**：`pingHeartbeat` 裡 `if (!exchangeSessionId.value) return` 一直 return，heartbeat 從未打出去。（調查中）

**狀態**：🔍 調查中（2026-04-30）

---

### 關鍵規範更新

| 規範 | 內容 |
|------|------|
| WebSocket 頻道 | 一律小寫，`kiosk.{strtolower(kiosk_id)}` |
| QR Code token | 只有過期才換，不是每次心跳都換 |
| bind() 查詢 | 用 `kiosk_id + active + member_id IS NULL`，token 只做次要驗證 |
| Laravel Scheduler | yd47 已設定 crontab，每分鐘執行 |
| Infra 端點 header | `/api/internal/mqtt/publish` 用 `X-Internal-Key`；iHub 呼叫用 `X-Internal-Key` |

---

*設計者: HQ | 日期: 2026-04-30 | 版本: 2.2.0*

---

## 🔗 文件神經連結

### 強關聯（必讀）
> 修改兌幣流程代碼前，必須先閱讀以下文件

- `../../02_technical_standards/QRCODE_FORMAT_STANDARD.md` - QR Code 格式規範，掃碼流程的唯一真理
- `../../02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - MQTT 主題規範，MQTT 通訊的唯一真理
- `../../02_technical_standards/WEBSOCKET_CHANNEL_STANDARD.md` - WebSocket 頻道規範，即時通訊的唯一真理
- `05_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` - 識別碼體系，理解 chip_id/node_id/kiosk_id 的區別
- `05_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` - 紙鈔機互動流程，理解 escrow/stack/reject 時序

### 中關聯（建議讀）
> 了解完整業務流程，建議閱讀

- `05_business_flows/kiosk_v0_exchange/KIOSK_UX_AND_SCREEN_DESIGN.md` - 三螢幕 UX 流程，理解會員端、平板端、工程端的互動
- `../../04_deployment_operations/INFRASTRUCTURE_REFERENCE.md` - 基礎設施參考，理解 DB 架構和 API 端點
- `../../01_agent_governance/AGENT_RESPONSIBILITY_BOUNDARIES.md` - Agent 職責邊界，了解 Member/Infra/Firmware 的分工

### 弱關聯（參考）
> 可選閱讀，提供額外背景

- `05_business_flows/kiosk_v0_exchange/KIOSK_ENGINEERING_DASHBOARD.md` - 工程測試頁設計，測試和調試工具
- `../../04_deployment_operations/DEPLOYMENT_GUIDE.md` - 部署指南，部署 Member/Infra 專案

### 排除混淆
> 容易混淆但實際無關的文件

- `../game_v0_arcade/05_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md` - 遊戲機流程，不同的業務域（遊戲機開分 vs 兌幣機兌幣）
- `../game_v0_arcade/qrcode_url_unification_plan.md` - 遊戲機 QR Code，格式不同（`/m/play?node_id=` vs `/kiosk?id=`）


---

## 附錄：紙鈔機 (Bill Acceptor) 底層物理交互與硬體指令

# 🏧 Kiosk 紙鈔機完整互動流程分析

> **版本**: 1.0.0  
> **日期**: 2026-04-27  
> **範圍**: ESP32-S3 ↔ ICT 104U 紙鈔機 ↔ MQTT 雲端  
> **狀態**: 權威規範

> ⚠️ **MQTT 主題規範請以 `brains/knowledge/02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` 為唯一真理。本文件第 8 節的主題列表必須與該文件保持一致。**

## 📋 目錄
1. [系統啟動流程](#1-系統啟動流程)
2. [待機狀態維護](#2-待機狀態維護)
3. [收鈔完整流程](#3-收鈔完整流程)
4. [異常處理機制](#4-異常處理機制)
5. [狀態機轉換圖](#5-狀態機轉換圖)

---

## 1. 系統啟動流程

### 1.1 開機初始化序列

| 步驟 | 時間 | ESP32 動作 | 紙鈔機狀態 | MQTT 動作 | 說明 |
|------|------|-----------|-----------|----------|------|
| 1 | T+0ms | `app_main()` 啟動 | 上電中 | - | 系統入口 |
| 2 | T+50ms | NVS 初始化 | 上電中 | - | 載入持久化數據 |
| 3 | T+100ms | GPIO 初始化 | 上電中 | - | 配置所有 I/O 腳位 |
| 4 | T+150ms | WiFi STA 啟動 | 上電中 | - | 連接 WiFi |
| 5 | T+200ms | 收到 `0x80` (Power Up 1) | 啟動中 | - | 紙鈔機第一次握手 |
| 6 | T+250ms | 收到 `0x8F` (Power Up 2) | 等待回應 | - | 紙鈔機第二次握手 |
| 7 | T+300ms | 發送 `0x02` (ACK) | 握手完成 | - | 確認握手 |
| 8 | T+500ms | **發送 `0x5E` (Disable)** | **🔒 禁用** | - | **預設禁止模式** |
| 9 | T+800ms | 設定狀態 `BA_STATE_DISABLED` | 🔴 紅燈 | - | 拒絕收鈔 |
| 10 | T+2s | WiFi 取得 IP | 🔴 紅燈 | - | 網路就緒 |
| 11 | T+3s | MQTT 連線成功 | 🔴 紅燈 | 連線 | TLS 握手完成 |
| 12 | T+3.5s | 訂閱 `kiosk/{chip_id}/cmd` | 🔴 紅燈 | 訂閱 QoS 2 | 接收雲端指令 |
| 13 | T+4s | 發布 `device/{chip_id}/status = "online"` | 🔴 紅燈 | 發布 Retain | 上線通知 |
| 14 | T+4.5s | 發布 `device/{chip_id}/info` | 🔴 紅燈 | 發布 Retain | 設備資訊 |
| 15 | T+5s | 啟動 Poll 定時器 (每 3 秒) | 🔴 紅燈 | - | 定期查詢狀態 |

### 1.2 開機後的預設狀態

```
┌─────────────────────────────────────┐
│  ESP32 狀態: BA_STATE_DISABLED      │
│  紙鈔機狀態: 🔴 紅燈 (Inhibited)     │
│  MQTT 狀態: ✅ 已連線                │
│  收鈔功能: ❌ 禁用 (Fail-Safe)       │
└─────────────────────────────────────┘
```

**設計理念**: 預設禁止模式 (Fail-Safe)，防止網路未就緒時誤收鈔票。

---

## 2. 待機狀態維護

### 2.1 啟用收鈔功能

| 步驟 | 觸發條件 | ESP32 動作 | 紙鈔機反應 | MQTT 訊息 | 時間 |
|------|---------|-----------|-----------|----------|------|
| 1 | 雲端下發指令 | - | - | 收到 `{"action":"enable"}` | T+0ms |
| 2 | 解析 JSON | `command_executor` 處理 | - | - | T+10ms |
| 3 | 呼叫 `bill_acceptor_enable()` | 發送 `0x3E` (Enable) | - | - | T+20ms |
| 4 | 等待確認 | - | 收到 `0x3E` (Enabled) | - | T+100ms |
| 5 | 更新狀態 | `BA_STATE_IDLE` | 🟢 綠燈亮起 | - | T+150ms |
| 6 | 日誌記錄 | `ESP_LOGI("紙鈔口已解鎖")` | 允許投幣 | - | T+200ms |

### 2.2 定期 Poll 機制

| 時間間隔 | ESP32 動作 | 紙鈔機回應 | 目的 |
|---------|-----------|-----------|------|
| 每 3 秒 | 發送 `0x0C` (Poll) | `0x2F` (Status OK) | 確認連線正常 |
| 每 3 秒 | 發送 `0x0C` (Poll) | `0x3E` (Enabled) | 確認啟用狀態 |
| 每 3 秒 | 發送 `0x0C` (Poll) | `0x5E` (Inhibited) | 確認禁用狀態 |

### 2.3 心跳上報

| 時間間隔 | MQTT Topic | Payload 內容 | QoS | 目的 |
|---------|-----------|-------------|-----|------|
| 每 25 秒 | `kiosk/{id}/status` | `{"ba_state":"IDLE","ba_error":"NONE","lifetime_total":1258700}` | 1 | 狀態監控（`BA_STATUS_INTERVAL_MS=25000`，小於 MQTT Keepalive 30s） |
| 每 5 分鐘 | `device/{id}/diagnostic` | `{"uptime":3600,"free_heap":180000,"wifi":{"rssi":-65}}` | 1 | 系統診斷 |

---

## 3. 收鈔完整流程

### 3.1 Escrow 流程詳細步驟

| 步驟 | 時間 | 觸發事件 | ESP32 動作 | 紙鈔機狀態 | RS232 訊號 | MQTT 訊息 | 說明 |
|------|------|---------|-----------|-----------|-----------|----------|------|
| **階段 1: 偵測** |
| 1 | T+0ms | 玩家投入 100 元 | - | 驗鈔中 | - | - | 紙鈔進入驗鈔通道 |
| 2 | T+500ms | 驗鈔完成 | 收到 `0x81` (Bill Validated) | 驗鈔通過 | RX: `0x81` | - | 確認為真鈔 |
| 3 | T+600ms | 面額識別 | 收到 `0x40` (Type 1) | Escrow 暫存 | RX: `0x40` | - | 識別為 100 元 |
| 4 | T+700ms | 更新狀態 | `BA_STATE_ESCROW` | ⏸️ 紙鈔懸停 | - | - | 進入暫存狀態 |
| 5 | T+800ms | 記錄面額 | `s_escrow_amount = 100` | ⏸️ 等待指令 | - | - | 暫存金額 |
| **階段 2: 雲端通報** |
| 6 | T+900ms | 發布 Escrow 事件 | `mqtt_publish_escrow_event(100)` | ⏸️ 等待指令 | - | 發布到 `kiosk/{id}/event` | QoS 2 |
| 7 | T+1000ms | 發布舊格式 (相容) | `mqtt_publish_bill_detected()` | ⏸️ 等待指令 | - | 發布到 `kiosk/{id}/bill/detected` | QoS 1 |
| 8 | T+1s~6s | 等待雲端裁決 | 定期發送 `0x18` (Hold) | ⏸️ 延長等待 | TX: `0x18` (每秒) | - | 防止自動退鈔 |

**Escrow 事件 Payload (新格式)**:
```json
{
  "event_type": "escrow",
  "amount": 100,
  "timestamp": 1713253800
}
```

**Bill Detected Payload (舊格式)**:
```json
{
  "kiosk_id": "a0b1c2d3e4f5",
  "denomination": 100,
  "lifetime_total": 1258600,
  "current_session_id": "session_abc",
  "timestamp": 1712000000
}
```

### 3.2 雲端裁決 - 收鈔路徑

| 步驟 | 時間 | 觸發事件 | ESP32 動作 | 紙鈔機動作 | RS232 訊號 | MQTT 訊息 | 說明 |
|------|------|---------|-----------|-----------|-----------|----------|------|
| **階段 3A: 收鈔 (Stack)** |
| 9A | T+2s | 雲端下發收鈔指令 | - | ⏸️ 等待指令 | - | 收到 `{"action":"stack"}` | 後端確認收鈔 |
| 10A | T+2.1s | 解析指令 | `command_executor` 處理 | ⏸️ 等待指令 | - | - | 識別為 stack |
| 11A | T+2.2s | 呼叫收鈔函數 | `bill_acceptor_accept()` | ⏸️ 等待指令 | - | - | 執行收鈔邏輯 |
| 12A | T+2.3s | 發送收鈔指令 | 發送 `0x02` (Accept) | 開始吞鈔 | TX: `0x02` | - | 物理收鈔開始 |
| 13A | T+3s | 紙鈔落入錢箱 | 收到 `0x10` (Stacking) | 💰 入箱中 | RX: `0x10` | - | 物理入箱確認 |
| 14A | T+3.5s | 更新計數器 | `lifetime_total += 100` | ✅ 完成 | - | - | NVS 持久化 |
| 15A | T+3.6s | 更新計數器 | `lifetime_count += 1` | ✅ 完成 | - | - | 張數計數 |
| 16A | T+3.7s | 發布 Stacked 事件 | `mqtt_publish_stacked_event(100, "success")` | ✅ 完成 | - | 發布到 `kiosk/{id}/event` | QoS 2 |
| 17A | T+3.8s | 發布舊格式 (相容) | `mqtt_publish_bill_confirmed()` | ✅ 完成 | - | 發布到 `kiosk/{id}/bill/confirmed` | QoS 2 |
| 18A | T+4s | 恢復待機 | `BA_STATE_IDLE` | 🟢 綠燈 | - | - | 準備下一筆 |

**Stacked 事件 Payload (新格式)**:
```json
{
  "event_type": "stacked",
  "amount": 100,
  "status": "success",
  "timestamp": 1713253805
}
```

**Bill Confirmed Payload (舊格式)**:
```json
{
  "kiosk_id": "a0b1c2d3e4f5",
  "denomination": 100,
  "lifetime_total": 1258700,
  "lifetime_count": 3551,
  "status": "stacked",
  "timestamp": 1712000005
}
```

### 3.3 雲端裁決 - 退鈔路徑

| 步驟 | 時間 | 觸發事件 | ESP32 動作 | 紙鈔機動作 | RS232 訊號 | MQTT 訊息 | 說明 |
|------|------|---------|-----------|-----------|-----------|----------|------|
| **階段 3B: 退鈔 (Reject)** |
| 9B | T+2s | 雲端下發退鈔指令 | - | ⏸️ 等待指令 | - | 收到 `{"action":"reject"}` | 後端拒絕收鈔 |
| 10B | T+2.1s | 解析指令 | `command_executor` 處理 | ⏸️ 等待指令 | - | - | 識別為 reject |
| 11B | T+2.2s | 呼叫退鈔函數 | `bill_acceptor_reject()` | ⏸️ 等待指令 | - | - | 執行退鈔邏輯 |
| 12B | T+2.3s | 發送退鈔指令 | 發送 `0x0F` (Reject) | 開始吐鈔 | TX: `0x0F` | - | 物理退鈔開始 |
| 13B | T+3s | 紙鈔吐還玩家 | 收到 `0x11` (Returning) | ↩️ 退鈔中 | RX: `0x11` | - | 物理退鈔確認 |
| 14B | T+3.5s | 發布 Rejected 事件 | `mqtt_publish_stacked_event(100, "rejected")` | ✅ 完成 | - | 發布到 `kiosk/{id}/event` | QoS 2 |
| 15B | T+4s | 恢復待機 | `BA_STATE_IDLE` | 🟢 綠燈 | - | - | 準備下一筆 |

### 3.4 超時自動退鈔 (Fail-Safe)

| 步驟 | 時間 | 觸發條件 | ESP32 動作 | 紙鈔機動作 | RS232 訊號 | MQTT 訊息 | 說明 |
|------|------|---------|-----------|-----------|-----------|----------|------|
| 1 | T+6s | 5 秒內未收到指令 | 檢測超時 | ⏸️ 等待指令 | - | - | Fail-Safe 觸發 |
| 2 | T+6.1s | 自動退鈔 | `bill_acceptor_reject()` | ⏸️ 等待指令 | - | - | 保護玩家權益 |
| 3 | T+6.2s | 發送退鈔指令 | 發送 `0x0F` (Reject) | 開始吐鈔 | TX: `0x0F` | - | 物理退鈔 |
| 4 | T+7s | 紙鈔吐還 | 收到 `0x11` (Returning) | ↩️ 退鈔完成 | RX: `0x11` | - | 防止吃錢 |
| 5 | T+7.5s | 發布超時事件 | `mqtt_publish_timeout_event()` | ✅ 完成 | - | 發布到 `kiosk/{id}/event` | 記錄異常 |
| 6 | T+8s | 恢復待機 | `BA_STATE_IDLE` | 🟢 綠燈 | - | - | 系統恢復 |

---

## 4. 異常處理機制

### 4.1 MQTT 斷線處理

| 階段 | 檢測條件 | ESP32 動作 | 紙鈔機動作 | 說明 |
|------|---------|-----------|-----------|------|
| 1 | MQTT 連線中斷 | 觸發 `EVT_MQTT_DISCONNECTED` | 維持當前狀態 | 事件通知 |
| 2 | 立即反應 | 發送 `0x5E` (Disable) | 🔴 紅燈 | **立即禁用收鈔** |
| 3 | 狀態更新 | `BA_STATE_DISABLED` | 拒絕收鈔 | 防止吃錢 |
| 4 | 如果有 Escrow | 自動發送 `0x0F` (Reject) | ↩️ 退鈔 | 保護玩家 |
| 5 | 重連嘗試 | WiFi 重連機制啟動 | 🔴 紅燈 | 每 3 秒重試 |
| 6 | 重連成功 | MQTT 重新連線 | 🔴 紅燈 | 等待 enable 指令 |

### 4.2 紙鈔機故障處理

| 錯誤代碼 | 名稱 | ESP32 動作 | MQTT 上報 | 處理建議 |
|---------|------|-----------|----------|---------|
| `0x29` | Bill Reject | 記錄日誌 | `{"ba_error":"REJECT"}` | 正常拒收 |
| `0x22` | Bill Jam | 發送 `0x5E` (Disable) | `{"ba_error":"JAM"}` | 卡鈔，需手動排除 |
| `0x25` | Sensor Error | 發送 `0x5E` (Disable) | `{"ba_error":"SENSOR"}` | 感應器異常，需清潔 |
| `0x2F` | Status OK | 清除錯誤 | `{"ba_error":"NONE"}` | 恢復正常 |

### 4.3 WiFi 斷線處理

| 階段 | 重試次數 | 間隔時間 | ESP32 動作 | 紙鈔機狀態 |
|------|---------|---------|-----------|-----------|
| 1 | 1~5 次 | 3 秒 | 快速重連 | 🔴 紅燈 (已禁用) |
| 2 | 5 次後 | 30 秒 | 慢速重連 | 🔴 紅燈 (已禁用) |
| 3 | 連續失敗 ≥5 次 | - | 啟動子機同步模式 | 🔴 紅燈 (已禁用) |
| 4 | 重連成功 | - | MQTT 重新連線 | 等待 enable 指令 |

---

## 5. 狀態機轉換圖

### 5.1 ESP32 狀態機

```
                    ┌─────────────┐
                    │   INIT      │ 開機初始化
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
              ┌────▶│  DISABLED   │◀────┐ 預設禁止模式
              │     └──────┬──────┘     │
              │            │ enable     │ disable / 斷線
              │            ▼            │
              │     ┌─────────────┐     │
              │     │    IDLE     │─────┘ 待機 (綠燈)
              │     └──────┬──────┘
              │            │ 偵測到鈔票
              │            ▼
              │     ┌─────────────┐
              │     │   ESCROW    │ 暫存等待
              │     └──────┬──────┘
              │            │
              │      ┌─────┴─────┐
              │      │           │
              │      ▼           ▼
              │  ┌────────┐  ┌────────┐
              │  │ STACK  │  │ REJECT │
              │  └───┬────┘  └───┬────┘
              │      │           │
              │      └─────┬─────┘
              │            │
              └────────────┘
```

### 5.2 紙鈔機狀態

```
┌──────────┐  Power Up   ┌──────────┐
│ POWER_UP │────────────▶│ DISABLED │ 🔴 紅燈
└──────────┘             └─────┬────┘
                               │ Enable
                               ▼
                         ┌──────────┐
                    ┌───▶│   IDLE   │ 🟢 綠燈
                    │    └─────┬────┘
                    │          │ Bill Validated
                    │          ▼
                    │    ┌──────────┐
                    │    │  ESCROW  │ ⏸️ 暫存
                    │    └─────┬────┘
                    │          │
                    │    ┌─────┴─────┐
                    │    │           │
                    │    ▼           ▼
                    │ ┌────────┐  ┌────────┐
                    │ │STACKING│  │RETURNING│
                    │ └───┬────┘  └───┬────┘
                    │     │           │
                    └─────┴───────────┘
```

---

## 6. 關鍵時序要求

| 項目 | 時間要求 | 說明 |
|------|---------|------|
| 雲端指令響應 | **≤ 5 秒** | 超時自動退鈔 (Fail-Safe) |
| Hold 指令間隔 | 每 1 秒 | 延長 Escrow 等待時間 |
| Poll 查詢間隔 | 每 3 秒 | 維持 RS232 連線 |
| 心跳上報間隔 | 每 **25 秒** | MQTT 狀態監控（`BA_STATUS_INTERVAL_MS=25000`，小於 Keepalive 30s） |
| 診斷上報間隔 | 每 5 分鐘 | 系統健康檢查 |
| MQTT Keepalive | 30 秒 | 斷線檢測 |
| LWT 觸發時間 | 30~60 秒 | 斷線後自動發布 offline |

---

## 7. 金流安全機制

### 7.1 入帳唯一依據

**規則**: 只有收到 `bill/confirmed` 且 `status = "stacked"` 才可入帳

| 事件 | 是否入帳 | 原因 |
|------|---------|------|
| `bill/detected` | ❌ 否 | 僅為偵測通知，尚未確認 |
| `bill/confirmed` + `status="stacked"` | ✅ 是 | 物理入箱確認 |
| `bill/confirmed` + `status="rejected"` | ❌ 否 | 已退鈔給玩家 |

### 7.2 Lifetime Total 自癒邏輯

**原理**: 使用累計總額的差值計算，防止漏包

```python
# 後端計算邏輯
current_total = 1258700  # 本次上報
previous_total = 1258600  # 上次記錄
gap = current_total - previous_total  # 100

if gap > 0:
    # 自動補齊遺失的金額
    user.token_balance += gap
```

### 7.3 NVS 持久化

**保護機制**: 所有計數器持久化於 NVS，防止斷電遺失

| NVS Key | 說明 | 更新時機 |
|---------|------|---------|
| `life_total` | 累計總額 (TWD) | 每次 Stacked |
| `life_count` | 累計張數 | 每次 Stacked |
| `credit_in` | 入金計數 | 每次脈衝 |
| `credit_out` | 出金計數 | 每次脈衝 |

---

## 8. MQTT 主題總覽

> **版本：2.0** | 更新：2026-04-28 | 統一簡化主題命名

### 8.1 上行主題 (ESP32 → 雲端)

| Topic | QoS | Retain | 觸發時機 | Payload 範例 |
|-------|-----|--------|---------|-------------|
| `kiosk/{id}/event` | 2 | ❌ | Escrow / Stacked / Rejected | `{"event_type":"escrow","amount":100}` |
| `kiosk/{id}/status` | 1 | ✅ | 連線後立即 + 每 **25 秒**心跳 | `{"ba_state":"IDLE","ba_error":"NONE","lifetime_total":1258700}` |
| `device/{id}/status` | 1 | ✅ | 上線/下線 | `"online"` / `"offline"` |
| `device/{id}/info` | 1 | ✅ | 上線時 | `{"chip_id":"aabbcc","firmware_ver":"0.1.0"}` |
| `device/{id}/diagnostic` | 1 | ❌ | 每 5 分鐘 | `{"uptime":3600,"free_heap":180000}` |

### 8.2 下行主題 (雲端 → ESP32)

| Topic | QoS | 指令範例 | 說明 |
|-------|-----|---------|------|
| `kiosk/{id}/cmd` | 2 | `{"action":"enable"}` | 啟用收鈔 |
| `kiosk/{id}/cmd` | 2 | `{"action":"disable"}` | 禁用收鈔 |
| `kiosk/{id}/cmd` | 2 | `{"action":"stack"}` | 確認收鈔 |
| `kiosk/{id}/cmd` | 2 | `{"action":"reject"}` | 拒絕收鈔 |
| `device/{id}/command` | 1 | `{"action":"ota_update"}` | OTA 更新 |
| `device/{id}/command` | 1 | `{"action":"reboot"}` | 重啟設備 |

### 8.3 設計原則

1. **主題分離**：不同類型訊息使用不同主題，便於精準訂閱
2. **Retain 策略**：狀態類訊息 Retain，事件類訊息不 Retain
3. **QoS 分級**：關鍵金流事件用 QoS 2，狀態心跳用 QoS 1
4. **命名簡潔**：`kiosk/` 專屬兌幣卡，`device/` 通用所有 ESP32

---

## 9. 參考文檔

- **硬體協議**: `pubdocs/esp-kiosk/14_ict_104u_protocol_details.md`
- **MQTT 協議**: `pubdocs/esp-kiosk/03_mqtt_protocol.md`
- **系統架構**: `pubdocs/esp-kiosk/02_architecture.md`
- **硬體約束**: `pubdocs/esp-kiosk/04_hardware_constraints.md`
- **實作報告**: `pubdocs/esp-kiosk/MISSION_01_IMPLEMENTATION.md`
- **產品概述**: `pubdocs/esp-kiosk/01_product_overview.md`

---

**版權聲明**: 本文件為 WAW V9 系統內部技術規範，未經授權不得外傳。

---

## 🔗 文件神經連結

### 強關聯（必讀）
> 修改韌體或 MQTT 通訊代碼前，必須先閱讀以下文件

- `../../02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - MQTT 主題規範，本文件第 8 節必須與該文件保持一致
- `05_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` - 識別碼體系，理解 chip_id 在 MQTT 主題中的使用
- `05_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` - 會員兌幣流程，理解雲端如何處理 escrow/stack/reject

### 中關聯（建議讀）
> 了解完整系統架構，建議閱讀

- `../../04_deployment_operations/INFRASTRUCTURE_REFERENCE.md` - 基礎設施參考，理解 Infra MQTT Listener 的部署
- `../../01_agent_governance/AGENT_RESPONSIBILITY_BOUNDARIES.md` - Agent 職責邊界，了解 Firmware (Fio) 的職責範圍

### 弱關聯（參考）
> 可選閱讀，提供額外背景

- `05_business_flows/kiosk_v0_exchange/KIOSK_UX_AND_SCREEN_DESIGN.md` - 三螢幕 UX 流程，理解整體用戶體驗
- `05_business_flows/kiosk_v0_exchange/KIOSK_ENGINEERING_DASHBOARD.md` - 工程測試頁設計，測試韌體功能

### 排除混淆
> 容易混淆但實際無關的文件

- `../game_v0_arcade/05_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md` - 遊戲機流程，使用不同的韌體（IOTwawS3）和 MQTT 主題（`device/+/`）
- `../../02_technical_standards/WEBSOCKET_CHANNEL_STANDARD.md` - WebSocket 頻道規範，韌體不使用 WebSocket（只用 MQTT）

---

## 🔗 文件神經連結

### 強關聯（必讀）
- `brains/knowledge/02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - 技術命名與 Payload 數據負載標準規範，確保 API 與變數命名一致。
- `brains/knowledge/05_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` - 兌幣機識別碼與綁定體系。

### 中關聯（建議讀）
- `brains/knowledge/05_business_flows/kiosk_v0_exchange/KIOSK_UX_AND_SCREEN_DESIGN.md` - 兌幣機 UI 與三螢幕顯示設計。
