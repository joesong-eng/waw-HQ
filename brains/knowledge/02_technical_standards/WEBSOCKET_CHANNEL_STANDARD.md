# WebSocket 頻道命名標準

> **最後更新**：2026-05-08 UTC+8  
> **重要性**：🔴 核心標準，所有 Agent 必須遵守  
> **適用範圍**：Member 專案的 Reverb WebSocket Server

---

## 概述

本文件定義 V9 系統中所有 WebSocket 頻道的命名規範、事件類型、Payload 格式。**所有 Agent 在實作 WebSocket 相關功能時，必須先查閱本文件，不得自行發明新的頻道名稱或事件格式。**

---

## 頻道命名規範

### 規則 1：頻道前綴

| 前綴 | 用途 | 範例 | 訂閱者 |
|------|------|------|--------|
| `kiosk.{kiosk_id}` | Kiosk 產品的業務頻道 | `kiosk.kiosk_000` | iHub 平板、sim-bill |
| `engineering.{kiosk_id}` | Kiosk 工程監控頻道 | `engineering.kiosk_000` | 工程頁面 |
| `member.{member_id}` | 會員個人頻道 | `member.12345` | 會員 APP |

### 規則 2：識別碼格式

- **kiosk_id**：必須使用 `node_id` 格式（例如：`kiosk_000`），不是 `chip_id`
- **member_id**：會員的數字 ID（例如：`12345`）

### 規則 3：頻道類型

- **Public Channel**：使用 `Echo.channel()`，不需要認證
- **Private Channel**：使用 `Echo.private()`，需要認證
- **Presence Channel**：使用 `Echo.join()`，需要認證且追蹤在線用戶

**目前所有頻道都是 Public Channel**，除非有特殊需求，否則不使用 Private/Presence Channel。

---

---

## ⚠️ 事件名稱黃金規則

> **這是最容易出錯的地方，必須嚴格遵守。**

### 規則 1：前端監聽名稱 vs 後端廣播名稱

Laravel 的 `broadcastAs()` 決定前端監聽時用的名稱：

| 後端 Event Class | `broadcastAs()` 回傳值 | 前端監聽寫法 |
|-----------------|----------------------|------------|
| `MemberBoundToKiosk` | `'MemberBoundToKiosk'` | `.listen('.MemberBoundToKiosk', ...)` |
| `KioskEscrowPending` | `'KioskEscrowPending'` | `.listen('.KioskEscrowPending', ...)` |
| `KioskSessionUpdated` | `'KioskSessionUpdated'` | `.listen('.KioskSessionUpdated', ...)` |
| `KioskSessionEnded` | `'KioskSessionEnded'` | `.listen('.KioskSessionEnded', ...)` |
| `KioskRejected` | `'KioskRejected'` | `.listen('.KioskRejected', ...)` |
| `MemberPointsUpdated` | `'MemberPointsUpdated'` | `.listen('.MemberPointsUpdated', ...)` |
| `KioskInfraCmd` | `'infra.cmd'` | `.listen('infra.cmd', ...)` |
| `EngineeringSignalEvent` | `'signal'` | `.listen('signal', ...)` |

**注意**：Laravel 廣播事件時，前端監聽名稱前面會自動加 `.`（點）。
- `broadcastAs()` 回傳 `'MemberBoundToKiosk'` → 前端用 `.listen('.MemberBoundToKiosk', ...)`
- `broadcastAs()` 回傳 `'infra.cmd'` → 前端用 `.listen('infra.cmd', ...)` （已含點，不再加）

### 規則 2：新增事件的強制流程

**嚴禁自行命名事件名稱。** 新增任何 WebSocket 事件必須：

1. **HQ 先定義**：在本文件「頻道定義」章節中，明確寫出：
   - 事件名稱（`broadcastAs()` 的回傳值）
   - 廣播頻道
   - Payload 格式
   - 訂閱者（哪些前端需要監聽）

2. **後端實作**：`broadcastAs()` 必須與本文件定義完全一致

3. **前端實作**：`.listen()` 的事件名稱必須與本文件定義完全一致

4. **交叉驗證**：實作完成後，必須對照本文件確認名稱一致

### 規則 3：命名格式規範

| 類型 | 格式 | 範例 |
|------|------|------|
| Laravel Event（PascalCase） | `PascalCase` | `MemberBoundToKiosk` |
| 系統指令事件（小寫點分隔） | `system.action` | `infra.cmd` |
| 工程監控事件（小寫點分隔） | `category.action` | `member.bind`, `firmware.idle` |

**嚴禁混用格式**：Event Class 名稱（如 `KioskInfraCmd`）不等於廣播名稱。`broadcastAs()` 的回傳值才是前端監聽的名稱。

---

## 頻道定義

### 1. kiosk.{kiosk_id}

**用途**：Kiosk 產品的業務邏輯頻道，用於會員綁定、投幣流程、指令下發等核心業務。

**訂閱者**：
- iHub 平板（真實硬體）
- sim-bill（模擬器）
- Member 前端（手機）

**廣播的事件**（完整對照表）：

| 事件名稱（前端監聽） | `broadcastAs()` | Event Class | 觸發時機 | Payload 關鍵欄位 | 訂閱者 |
|-------------------|----------------|-------------|---------|----------------|--------|
| `.MemberBoundToKiosk` | `MemberBoundToKiosk` | `MemberBoundToKiosk` | 會員掃碼綁定成功 | `status: 'bound'`, `session_id`, `kiosk_id`, `member` | iHub, sim-bill |
| `.KioskEscrowPending` | `KioskEscrowPending` | `KioskEscrowPending` | 收到投幣事件 | `event_id`, `amount`, `tokens`, `member` | iHub, Member前端 |
| `.KioskSessionUpdated` | `KioskSessionUpdated` | `KioskSessionUpdated` | 入帳成功 | `tokens_credited`, `member_balance`, `status` | iHub, Member前端 |
| `.KioskSessionEnded` | `KioskSessionEnded` | `KioskSessionEnded` | Session 結束 | `session_id`, `kiosk_id` | iHub, Member前端 |
| `infra.cmd` | `infra.cmd` | `KioskInfraCmd` | 後端下發 stack/reject 指令 | `action: 'stack'/'reject'`, `chip_id` | iHub, sim-bill |

**訂閱範例**：
```javascript
echo.channel(`kiosk.${kioskId}`)
  .listen('.MemberBoundToKiosk', (e) => { /* status === 'bound' */ })
  .listen('.KioskEscrowPending', (e) => { /* 顯示確認畫面 */ })
  .listen('.KioskSessionUpdated', (e) => { /* 更新餘額 */ })
  .listen('.KioskSessionEnded', (e) => { /* 結束 session */ })
  .listen('infra.cmd', (e) => { /* e.action === 'stack'/'reject' */ });
```

---

### 2. engineering.{kiosk_id}

**用途**：Kiosk 工程監控頻道，用於 Signal Flow Monitor、硬體狀態監控、除錯資訊。

**訂閱者**：
- 工程頁面（`win.tg25.win/engineering/kiosk`）

**廣播的事件**（完整對照表）：

| 事件名稱（前端監聽） | `broadcastAs()` | Event Class | 觸發時機 |
|-------------------|----------------|-------------|---------|
| `signal` | `signal` | `EngineeringSignalEvent` | 所有 Signal Flow Monitor 節點 |

> 工程頁面用 `event.node` 欄位區分訊號類型：
> `tablet.heartbeat`, `member.bind`, `infra.enable`, `member.escrow_received`, `infra.escrow`, `member.decision`, `infra.cmd`, `member.credited`, `member.noted`, `member.heartbeat`, `firmware.idle`

**Whisper 事件**（不經過後端）：

| Whisper 名稱 | 發送者 | Payload |
|-------------|--------|---------|
| `tablet-heartbeat` | iHub 平板 | `{ device_id, kiosk_id, timestamp }` |

---

### 3. member.{member_id}

**用途**：會員個人頻道，用於推送個人通知、錢包變動、訂單狀態等。

**訂閱者**：
- 會員 APP（LINE LIFF）

**廣播的事件**：

| 事件名稱（前端監聽） | `broadcastAs()` | Event Class | 觸發時機 | Payload 關鍵欄位 |
|-------------------|----------------|-------------|---------|----------------|
| `wallet.updated` | `wallet.updated` | — | 錢包餘額變動 | `{ balance, currency_type, change_amount }` |
| `order.created` | `order.created` | — | 訂單建立 | `{ order_id, amount, status }` |
| `notification` | `notification` | — | 系統通知 | `{ title, message, type }` |
| `.DeviceCreditOut` | `DeviceCreditOut` | `DeviceCreditOut` | 遊戲機洗分入帳 | `{ chip_id, ticket_count, ticket_balance }` |

**訂閱範例**：
```javascript
// 會員 APP
const memberId = 12345;
echo.channel(`member.${memberId}`)
  .listen('wallet.updated', (event) => {
    // 更新錢包顯示
  })
  .listen('.DeviceCreditOut', (event) => {
    // 顯示 +{ticket_count} 彩票動畫
    // 更新 ticket_balance
  });
```

---

## 事件命名規範

### 規則 1：事件名稱前綴

| 前綴 | 說明 | 範例 |
|------|------|------|
| `.EventName` | Laravel Event Class 名稱（以 `.` 開頭） | `.MemberBoundToKiosk` |
| `system.action` | 系統層級事件（小寫，用 `.` 分隔） | `tablet.heartbeat`, `member.bind` |
| `EventName` | 自訂事件（PascalCase） | `KioskSessionEnded` |

### 規則 2：Payload 格式

所有事件的 Payload 必須是 **JSON 物件**，包含以下基本欄位：

```json
{
  "timestamp": 1778123456,  // Unix timestamp（選填）
  "kiosk_id": "kiosk_000",  // 相關的 kiosk_id（選填）
  "member_id": 12345,       // 相關的 member_id（選填）
  // ... 其他業務欄位
}
```

### 規則 3：狀態欄位命名

| 欄位名稱 | 用途 | 可能值 |
|---------|------|--------|
| `status` | 業務狀態 | `'bound'`, `'active'`, `'ended'` |
| `result` | 操作結果 | `'success'`, `'failed'` |
| `action` | 動作類型 | `'stack'`, `'reject'`, `'confirm'` |

---

## 實作檢查清單

在實作任何 WebSocket 功能前，必須確認：

- [ ] 我使用的頻道名稱是否在本文件中定義？
- [ ] 我使用的事件名稱是否在本文件中定義？
- [ ] 我使用的 Payload 格式是否符合規範？
- [ ] 我使用的是 `node_id`（kiosk_000）還是 `chip_id`（test-esp32）？
- [ ] 我使用的是 Public Channel（`Echo.channel()`）還是其他類型？
- [ ] 我的事件監聽邏輯是否檢查了正確的欄位（`status` vs `result`）？

---

## 常見錯誤

### ❌ 錯誤 1：頻道名稱錯誤

```javascript
// ❌ 錯誤：自己發明頻道名稱
echo.channel('simulator.kiosk_000');

// ✅ 正確：使用標準頻道
echo.channel('kiosk.kiosk_000');
```

### ❌ 錯誤 2：使用 chip_id 而非 node_id

```javascript
// ❌ 錯誤：使用硬體識別碼
echo.channel('kiosk.test-esp32');

// ✅ 正確：使用產品識別碼
echo.channel('kiosk.kiosk_000');
```

### ❌ 錯誤 3：事件欄位檢查錯誤

```javascript
// ❌ 錯誤：檢查不存在的欄位
.listen('.MemberBoundToKiosk', (event) => {
  if (event.result === 'success') { ... }
});

// ✅ 正確：檢查正確的欄位
.listen('.MemberBoundToKiosk', (event) => {
  if (event.status === 'bound') { ... }
});
```

### ❌ 錯誤 4：使用錯誤的頻道類型

```javascript
// ❌ 錯誤：使用 Presence Channel（需要認證）
echo.join('kiosk.kiosk_000');

// ✅ 正確：使用 Public Channel
echo.channel('kiosk.kiosk_000');
```

---

## 新增頻道或事件的流程

如果需要新增頻道或事件，必須遵循以下流程：

1. **提案**：向 HQ 提交提案，說明新頻道/事件的用途、訂閱者、Payload 格式
2. **審核**：HQ 審核提案，確認不與現有頻道/事件衝突
3. **更新文件**：HQ 更新本文件，加入新的定義
4. **通知 Agent**：HQ 透過 HQ Message Hub 通知所有相關 Agent
5. **實作**：Agent 根據文件實作，不得偏離規範

**嚴禁自行發明新的頻道名稱或事件格式。**

---

## 參考文件

- `05_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md`：識別碼體系（chip_id vs node_id）
- `02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md`：MQTT 主題命名規範
- `kiosk_exchange_v2/design.md`：Kiosk Exchange v2 設計文件

---

## 總結

**核心原則**：

1. **業務邏輯** → 訂閱 `kiosk.{kiosk_id}`
2. **工程監控** → 訂閱 `engineering.{kiosk_id}`
3. **會員通知** → 訂閱 `member.{member_id}`
4. **使用 node_id**，不是 chip_id
5. **使用 Public Channel**，不是 Private/Presence
6. **檢查正確的 Payload 欄位**（`status` vs `result`）

**不確定時，先查本文件，再問 HQ，不要猜測。**

---

## 🔗 文件神經連結

### 強關聯（必讀）
> 修改 WebSocket 頻道或事件前，必須先閱讀

- `../NAMING_AUTHORITY.md` - 識別碼命名規則（node_id 用於 WebSocket 頻道）
- `../05_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` - node_id vs chip_id 詳解

### 中關聯（建議讀）
> 了解 WebSocket 在業務流程中的使用

- `../05_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` - 兌幣流程中的 WebSocket 事件
- `02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - Infra 將 MQTT 轉為 WebSocket
- `QRCODE_FORMAT_STANDARD.md` - iHub 掃碼後監聽 WebSocket
- `../04_deployment_operations/INFRASTRUCTURE_REFERENCE.md` - Member Reverb 配置

### 弱關聯（參考）
> 提供額外背景

- `../05_business_flows/kiosk_v0_exchange/KIOSK_UX_AND_SCREEN_DESIGN.md` - 三端 UX 流程
- `../04_deployment_operations/DEPLOYMENT_GUIDE.md` - Member 部署步驟

### 排除混淆
> 容易誤以為相關，但實際無關

- WebSocket 使用 `node_id`（產品層級），不使用 `chip_id`（硬體層級）
- WebSocket 頻道名稱與 MQTT 主題無關（不同的通訊協議）
