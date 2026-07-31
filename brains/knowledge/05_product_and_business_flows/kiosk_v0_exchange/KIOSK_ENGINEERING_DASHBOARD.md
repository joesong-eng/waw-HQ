# Kiosk 工程測試頁設計規格

> **版本**: 2.0.0  
> **日期**: 2026-04-27  
> **狀態**: 設計確認，待分配執行

---

## 一、設計目標

讓工程師現場測試時，5 秒內看出「這台 Kiosk 有沒有問題」。

具體要回答的問題：
1. 平板有沒有在線？
2. 兌幣卡+紙鈔機有沒有就緒？
3. 投幣後這筆錢有沒有走完整條流程？

---

## 二、核心概念釐清

### 物理物件（2 個）+ 會員狀態（1 個）

| 物件 | 說明 | 資料來源 |
|------|------|---------|
| 📱 平板 (DUEGX) | Kiosk Android 端 | `kiosk_sessions.last_active_at`，>120秒=離線 |
| 💴 兌幣卡+紙鈔機 (3A78) | ESP32 kiosk_v0 + 紙鈔機，合為一體。ESP32 是紙鈔機的信號轉換器，沒有 ESP32 紙鈔機信號出不來 | `kiosk/{chip_id}/status` 的 `ba_state` |
| 🧑 會員 Session | 會員掃碼成功後建立的 session | `kiosk_sessions` 有 active session（`status='active'` 且 `kiosk_no` 對應此機台） |

> **三燈全綠 = 真正可以投幣的狀態**：硬體在線 + 紙鈔機就緒 + 會員已掃碼。
> **注意**：`device/{chip_id}/status`（ESP32 連線狀態）不在此頁面顯示，Owner 那邊已有設備監控頁面。

### 邏輯事件（1 條流程線）

投幣後的每一步都是事件，不是物件：

| 事件 | MQTT 來源 | 說明 |
|------|----------|------|
| 投幣偵測 | `kiosk/{chip_id}/event` `event_type=escrow` | 鈔票進入暫存 |
| 雲端裁決 | 後端 API 處理中 | 後端決定收或退 |
| 收鈔確認 | `kiosk/{chip_id}/event` `event_type=stacked` | 入帳 |
| 退鈔 | `kiosk/{chip_id}/event` `event_type=rejected` | 退還玩家 |

---

## 三、頁面佈局

```
┌─────────────────────────────────────────────────────────────────┐
│  Kiosk 工程測試頁          [選擇綁定組合 ▼]  [重新整理]          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────┐  ┌─────────────────┐ │
│  │                                      │  │                 │ │
│  │  【物件狀態】                         │  │   事件 Log      │ │
│  │  📱 DUEGX    💴 3A78    🧑 會員      │  │  (終端機風格)   │ │
│  │  ● 在線      ● IDLE     ● 已掃碼     │  │                 │ │
│  │                                      │  │                 │ │
│  │  【事件流程】                         │  │                 │ │
│  │  [投幣]→[暫存]→[裁決]→[入帳✅]       │  │                 │ │
│  │   ⚫    🟠閃   ⚫      ⚫             │  │                 │ │
│  │                                      │  │                 │ │
│  │  最後一筆：100元 | 07:41 | stacked   │  │                 │ │
│  └──────────────────────────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**比例**：主面板 65% | Log 面板 35%

---

## 四、綁定選擇器

```
綁定組合：
┌──────────────────────────────────────────────┐
│  📱 STB-T1BQTYBDUEGX  ↔  💴 E072A1F73A78   │
│  [DUEGX]                   [3A78]            │
└──────────────────────────────────────────────┘
```

**規則**：
- 從 `iotv9.kiosks` 表讀取已綁定的組合
- 未綁定的設備不顯示
- 可切換不同綁定組合

---

## 五、物件燈號定義

### 📱 平板燈號

| 燈號 | 顏色 | 條件 |
|------|------|------|
| ● | 🟢 綠 | `last_active_at` 在 120 秒內 |
| ● | 🔴 紅 | `last_active_at` 超過 120 秒 |
| ● | ⚫ 灰 | 從未連線 |

### 💴 兌幣卡+紙鈔機燈號

> 燈號同時反映 `ba_state` 與 session 狀態，**有 session 且 IDLE 才亮綠**。

| 燈號 | 顏色 | 條件 | 說明 |
|------|------|----------|------|
| ● | 🟢 綠 | `ba_state = IDLE` **且** 有 active session | 可以投幣 |
| ◐ 閃 | 🟠 橘 | `ba_state = ESCROW` | 鈔票懸停，等待裁決 |
| ↻ | 🔵 藍 | `ba_state = STACKING` | 吞鈔中 |
| ↩ | 🟡 黃 | `ba_state = REJECTING` | 退鈔中 |
| ● | 🔴 紅 | `ba_state = DISABLED` 或無 active session | 禁用中（等待掃碼） |
| ● | 🔴 紅 | `ba_state = FAULT` | 故障 |

### 🧑 會員 Session 燈號

| 燈號 | 顏色 | 條件 | 說明 |
|------|------|------|------|
| ● | 🟢 綠 | `kiosk_sessions` 有 active session | 會員已掃碼，session 建立中 |
| ● | ⚫ 灰 | 無 active session | 等待會員掃碼 |

> **三燈全綠才允許投幣**：📱 平板在線 + 💴 兌幣卡 IDLE（有 session）+ 🧑 會員已掃碼。

---

## 六、事件流程節點

| 節點 | 觸發條件 | 顏色 |
|------|---------|------|
| 投幣 | `ba_state` 從 IDLE → ESCROW | 🟢 |
| 暫存 | 收到 `escrow` 事件 | 🟠 閃爍 |
| 裁決 | 後端 API 處理中 | 🔵 |
| 入帳 ✅ | 收到 `stacked` 事件 | 🟢 |
| 退鈔 ↩️ | 收到 `rejected` 事件 | 🟡 |

---

## 七、Log 面板

```
07:41:23 [MQTT] ← kiosk/3a78/status  ba_state=ESCROW
07:41:24 [MQTT] ← kiosk/3a78/event   escrow amount=100
07:41:25 [API]  → POST /api/kiosk/bill-detected
07:41:26 [API]  ← {"action":"accept","credited":100}
07:41:27 [MQTT] → kiosk/3a78/cmd     {"action":"stack"}
07:41:29 [MQTT] ← kiosk/3a78/event   stacked status=success
07:41:29 [✅]   入帳完成 +100 元
```

Log 顏色規則：

| 前綴 | 顏色 |
|------|------|
| `[MQTT] ←` | 🟦 藍（收到） |
| `[MQTT] →` | 🟩 綠（發送） |
| `[API] →` | 🟨 黃（請求） |
| `[API] ←` | 🟧 橘（回應） |
| `[✅]` | 🟢 綠 |
| `[❌]` | 🔴 紅 |

---

## 八、資料來源確認（已由 Infra 確認）

| 資料 | DB | 表 | 欄位 |
|------|----|----|------|
| 綁定關係 | `iotv9` | `kiosks` | `screen_mac`, `esp32_mac` |
| 平板在線 | `waw_member_production` | `kiosk_sessions` | `last_active_at` |
| 兌幣卡狀態 | MQTT | `kiosk/{chip_id}/status` | `ba_state` |
| 收鈔事件 | MQTT | `kiosk/{chip_id}/event` | `event_type`, `amount` |
| 會員 Session | `waw_member_production` | `kiosk_sessions` | `status='active'` + `kiosk_no` 對應機台 |

> **綁定寫入**：由 Alliance 的 `POST /api/devices/pair` 完成，同步寫入 `iotv9.kiosks`（2026-04-27 已實作）

---

## 九、任務分配

### Phase 1：後端 API（MemberOps）

| API | 說明 |
|-----|------|
| `GET /api/engineering/bindings` | 從 `iotv9.kiosks` 讀取已綁定組合 |
| `GET /api/engineering/tablet-status/{screen_mac}` | 查 `kiosk_sessions.last_active_at` |

驗收：Postman 測試通過

### Phase 2：MQTT 橋接（InfraOps）

| 監聽主題 | 推送事件 |
|---------|---------|
| `kiosk/{chip_id}/status` | `kiosk.ba_state` |
| `kiosk/{chip_id}/event` | `kiosk.bill_event` |

驗收：WebSocket 連線後，投幣時前端能收到事件

### Phase 3-A：頁面骨架（MemberOps）

- 路由 `/engineering/kiosk`
- 綁定選擇器（呼叫 Phase 1 API）
- 兩欄佈局骨架

驗收：頁面可載入，選擇器有資料

### Phase 3-B：物件燈號（MemberOps）

- 平板燈號（查 `last_active_at`）
- 兌幣卡+紙鈔機燈號（WebSocket `ba_state`）
- 🧑 會員 Session 燈號（查 `kiosk_sessions` 是否有 active session 對應此機台）

驗收：三個燈號能即時反映狀態變化；掃碼成功後第三個燈亮綠

### Phase 3-C：事件流程 + Log（MemberOps）

- 事件流程節點動畫
- Log 終端機面板

驗收：投幣後節點依序亮起，Log 有記錄

---

## 十、執行順序

Phase 1 和 Phase 2 可以並行，Phase 3 依序執行。

| 步驟 | 負責 | 前置條件 |
|------|------|---------|
| Phase 1 | MemberOps | 無 |
| Phase 2 | InfraOps | 無 |
| Phase 3-A | MemberOps | Phase 1 完成 |
| Phase 3-B | MemberOps | Phase 2 完成 |
| Phase 3-C | MemberOps | Phase 3-B 完成 |

---

*設計者: HQ | 日期: 2026-04-27 | 版本: 2.0.0*