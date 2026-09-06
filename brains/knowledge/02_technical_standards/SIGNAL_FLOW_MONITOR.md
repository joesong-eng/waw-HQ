# Signal Flow Monitor — 通信流可視化框架

> **版本**: 1.0.0
> **日期**: 2026-05-07
> **狀態**: 設計定稿，待實作
> **設計者**: HQ

---

## 一、核心概念

### 問題背景

分散式系統最難除錯的地方不是「程式壞了」，而是「訊號在哪個節點消失了」。

V9 系統橫跨韌體、MQTT、Infra、Member、iHub 五個系統，一條入帳流要經過 8+ 個節點。任何一個節點的名稱對不上（`chip_id` 用錯、`kiosk_id` 格式不一致），整條流就斷掉，而且完全沒有錯誤訊息。

### 解法

**Signal Flow Monitor**：讓每一條通信流的每一個節點都可視化。

- 有訊號流過 → 節點閃亮（脈衝燈）
- 同時顯示訊號裡帶的實際名稱值
- 與預期值比對 → 綠色（吻合）/ 紅色（不符）
- 裸眼就能看出哪個節點斷了、哪個名稱對不上

---

## 二、視覺設計

### 節點

每個節點顯示三樣東西：

```
┌─────────────────┐
│  Infra Listener │  ← 節點名稱（固定）
│  chip_id:       │  ← 欄位名稱（固定）
│  test-esp32 🟢  │  ← 實際收到的值（動態）+ 比對結果
│  💓 剛剛        │  ← 脈衝燈 + 時間戳
└─────────────────┘
```

### 脈衝燈行為

- 收到訊號：亮起（白色或對應顏色）
- 2 秒內：慢慢暗掉（CSS transition）
- 超過 30 秒無訊號：節點變灰，顯示「X 秒前」

### 名稱標籤顏色

| 顏色 | 意義 |
|------|------|
| 🟢 綠 | 與預期值吻合 |
| 🔴 紅 | 與預期值不符（這就是 bug 所在） |
| ⚫ 灰 | 未設定預期值，僅顯示 |

### 邊（箭頭）

節點之間的箭頭也有狀態：
- 訊號流過時：箭頭閃亮（動畫）
- 正常：灰色靜態
- 超時未流過：紅色虛線

---

## 三、V9 系統通信流清單

### 流 1：紙鈔機入帳流（已設計）

```
[iHub平板]──心跳──▶[Member後台]
    │
    │ 掃碼
    ▼
[Member bind]──enable──▶[Infra MQTT]──▶[韌體]
                                           │
                                      投幣 escrow
                                           │
                                           ▼
[Member裁決]◀──webhook──[Infra Listener]◀──[韌體 escrow]
    │
    │ stack/reject
    ▼
[Infra MQTT]──cmd──▶[韌體]──stacked──▶[Infra Listener]──webhook──▶[Member入帳]
```

**關鍵名稱對齊點：**

| 節點 | 欄位 | 預期值（kiosk_000） |
|------|------|-------------------|
| iHub 平板心跳 | `kiosk_id` | `kiosk_000` |
| Infra Listener | `chip_id` | `test-esp32` |
| Infra → Member webhook | `kiosk_id` | `kiosk_000` |
| Member 裁決 | `chip_id` | `test-esp32` |
| MQTT cmd | topic | `kiosk/test-esp32/cmd` |

---

### 流 2：遊戲機脈衝流

```
[遊戲機投幣]──RS232──▶[通訊卡 IOTwawS3]──MQTT credit_in──▶[Infra Listener]──▶[Owner/Member 入帳]
```

**關鍵名稱：** `chip_id`、`device_id`、`credit_in count`、`lifetime`

---

### 流 3：設備上線流

```
[ESP32 開機]──MQTT device/{id}/status=online──▶[Infra Listener]──▶[Owner 設備狀態]
```

**關鍵名稱：** `chip_id`、`firmware_ver`、`ba_state`

---

### 流 4：OTA 更新流

```
[Owner 後台]──API──▶[Infra]──MQTT device/{id}/command──▶[韌體下載更新]──▶[回報結果]
```

**關鍵名稱：** `chip_id`、`url`、`version`

---

### 流 5：會員掃碼綁定流

```
[會員掃 QR]──POST /api/kiosk/scan──▶[Member]──WebSocket──▶[iHub 畫面跳轉]
                │
                └──Infra enable──▶[韌體 IDLE]
```

**關鍵名稱：** `screen_mac`、`kiosk_id`、`member_id`、WebSocket 頻道名稱

---

## 四、套件化設計

### 目標

任何一條通信流，只需要宣告式定義，套件自動處理可視化。

### API 設計

```javascript
// 定義一條流
const flow = new SignalFlow({
  name: "紙鈔機入帳流",
  nodes: [
    {
      id: "tablet",
      label: "iHub 平板",
      expects: { kiosk_id: "kiosk_000" }
    },
    {
      id: "member_heartbeat",
      label: "Member 後台（心跳）",
      expects: { kiosk_id: "kiosk_000" }
    },
    {
      id: "infra_listener",
      label: "Infra Listener",
      expects: { chip_id: "test-esp32", node_id: "kiosk_000" }
    },
    {
      id: "member_webhook",
      label: "Member Webhook",
      expects: { chip_id: "test-esp32" }
    },
    {
      id: "member_decision",
      label: "Member 裁決",
      expects: { action: "stack" }
    },
    {
      id: "firmware_stacked",
      label: "韌體 stacked",
      expects: { event_type: "stacked", amount: 100 }
    },
    {
      id: "member_credited",
      label: "Member 入帳",
      expects: { tokens_credited: 100 }
    }
  ],
  edges: [
    "tablet → member_heartbeat",
    "firmware_escrow → infra_listener",
    "infra_listener → member_webhook",
    "member_webhook → member_decision",
    "member_decision → infra_mqtt",
    "infra_mqtt → firmware_stacked",
    "firmware_stacked → infra_listener",
    "infra_listener → member_credited"
  ],
  // 資料來源：Member WebSocket
  source: {
    type: "websocket",
    channel: "engineering.kiosk_000",
    // 事件 → 節點 mapping
    eventMap: {
      "tablet.heartbeat":    "tablet",
      "infra.escrow":        "infra_listener",
      "member.escrow":       "member_webhook",
      "member.decision":     "member_decision",
      "firmware.stacked":    "firmware_stacked",
      "member.credited":     "member_credited"
    }
  }
})

// 掛載到 DOM
flow.mount("#signal-flow-panel")
```

### 套件輸出

```
flow.on("mismatch", (node, field, expected, actual) => {
  // 名稱不符時觸發，可以發警報
  console.error(`[${node}] ${field}: 預期 ${expected}，實際 ${actual}`)
})

flow.on("timeout", (node, seconds) => {
  // 節點超過 N 秒無訊號
})
```

---

## 五、技術實作方向

### 前端

- 純 JavaScript 套件，無框架依賴
- CSS 動畫處理脈衝效果（`@keyframes pulse`）
- SVG 或 CSS Grid 繪製節點和箭頭
- WebSocket 訂閱 Member Reverb

### 後端（Member）

每個關鍵事件發生時，廣播一個標準格式的 WebSocket 事件到 `engineering.{kiosk_id}` 頻道：

```json
{
  "node": "infra_listener",
  "timestamp": 1713253800,
  "data": {
    "chip_id": "test-esp32",
    "node_id": "kiosk_000",
    "amount": 100
  }
}
```

### 擴展性

- 新增一條流 = 新增一個 `SignalFlow` 定義
- 不需要改後端，只需要後端在對應事件時廣播
- 可以同時顯示多條流（例如同時監控兩台機台）

---

## 六、商業價值

這個套件解決的問題在 IoT 領域非常普遍：

- 設備 ↔ 雲端通信除錯
- 多系統整合測試
- 現場維運人員快速定位問題

現有商業工具（Datadog、Grafana）太重，不適合現場快速除錯。這個套件輕量、即時、針對業務流程設計。

**未來可能的應用：**
- 開源為獨立套件
- 整合進 V9 運維後台
- 提供給其他 IoT 系統使用

---

## 七、實作優先順序

| 階段 | 內容 | 前置條件 |
|------|------|---------|
| Phase 1 | 紙鈔機入帳流（hardcoded） | engineering 頁面已有 WebSocket |
| Phase 2 | 抽成 SignalFlow 套件 | Phase 1 驗證可行 |
| Phase 3 | 支援多條流同時顯示 | Phase 2 完成 |
| Phase 4 | 遊戲機脈衝流、設備上線流 | Phase 3 完成 |
| Phase 5 | 開源 / 獨立部署 | Phase 4 穩定 |

---

*設計者: HQ | 日期: 2026-05-07 | 版本: 1.0.0*
