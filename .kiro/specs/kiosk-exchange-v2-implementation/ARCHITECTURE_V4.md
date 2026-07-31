# Kiosk Exchange v4 Architecture

> **版本**: v4 (2026-05-09)  
> **狀態**: 實作中  
> **目標**: sim-bill 與真實韌體走完全相同的 MQTT 鏈路

---

## 完整鏈路圖

### 真實韌體鏈路

```
真實韌體 (IOTkiosk_v0)
    │
    ▼ 發 MQTT event (escrow)
MQTT broker (mqtt.tg25.win:8883)
    │
    ▼ Infra Listener 訂閱 kiosk/+/event
Infra Listener
    │
    ▼ POST /internal/kiosk/escrow
Member API (win.tg25.win)
    │
    ├─► 廣播 WebSocket .KioskEscrowPending
    │       │
    │       ▼
    │   iHub 平板顯示確認畫面
    │       │
    │       ▼ 人工按「確認入帳」
    │   POST /api/kiosk/escrow/confirm
    │       │
    │       ▼
    └─► callInfraMqtt
            │
            ▼ POST /api/internal/mqtt/publish
        Infra API (api.tg25.win)
            │
            ▼ MQTT publish kiosk/{chip_id}/cmd
        MQTT broker
            │
            ▼ 真實韌體訂閱 kiosk/{chip_id}/cmd
        真實韌體吞鈔
            │
            ▼ 發 MQTT event (stacked)
        MQTT broker
            │
            ▼ Infra Listener 訂閱
        Infra Listener
            │
            ▼ POST /internal/kiosk/stacked
        Member API 入帳
            │
            ▼ 廣播 WebSocket .KioskSessionUpdated
        iHub 顯示入帳成功
```

---

### sim-bill 鏈路（v4 目標）

```
sim-bill 前端 (https://ihub.tg25.win/sim-bill/)
    │
    │ 用戶點擊「100」按鈕
    ▼
POST /api/simulator/bill (proxy to Infra)
    │
    ▼ 發 MQTT event (escrow)
MQTT broker (mqtt.tg25.win:8883)
    │
    ▼ Infra Listener 訂閱 kiosk/+/event
Infra Listener
    │
    ▼ POST /internal/kiosk/escrow
Member API (win.tg25.win)
    │
    ├─► 廣播 WebSocket .KioskEscrowPending
    │       │
    │       ▼
    │   iHub 平板顯示確認畫面
    │       │
    │       ▼ 人工按「確認入帳」
    │   POST /api/kiosk/escrow/confirm
    │       │
    │       ▼
    └─► callInfraMqtt
            │
            ▼ POST /api/internal/mqtt/publish
        Infra API (api.tg25.win)
            │
            ▼ MQTT publish kiosk/test-esp32/cmd
        MQTT broker
            │
            ├─► 真實韌體訂閱 kiosk/{chip_id}/cmd（如果有）
            │
            └─► iHub Server (Node.js) 訂閱 kiosk/test-esp32/cmd
                    │
                    ▼ SSE 推給 sim-bill 前端
                sim-bill 前端收到 {"action":"stack"}
                    │
                    ▼ 模擬吞鈔動作（STACKING → STACKED）
                    ▼ POST /api/simulator/bill (發 stacked 事件)
                MQTT broker
                    │
                    ▼ Infra Listener 訂閱
                Infra Listener
                    │
                    ▼ POST /internal/kiosk/stacked
                Member API 入帳
                    │
                    ▼ 廣播 WebSocket .KioskSessionUpdated
                iHub 顯示入帳成功
```

---

## 關鍵差異

| 項目 | 真實韌體 | sim-bill (v4) |
|------|---------|--------------|
| **投幣觸發** | 實體鈔票插入 | 前端按鈕點擊 |
| **escrow 事件** | 韌體發 MQTT | 前端 POST → Infra proxy → MQTT |
| **收到 stack 指令** | 韌體訂閱 MQTT | iHub Server 訂閱 MQTT → SSE 推給前端 |
| **吞鈔動作** | RS232 控制紙鈔機 | 前端狀態機模擬 |
| **stacked 事件** | 韌體發 MQTT | 前端 POST → Infra proxy → MQTT |

---

## v4 vs v3 差異

### v3（舊版，已廢棄）

```
iHub 按確認
    ↓ POST /api/kiosk/escrow/confirm
Member API
    ↓ 廣播 WebSocket infra.cmd
sim-bill 前端訂閱 WebSocket
    ↓ 收到 {"action":"stack"}
模擬吞鈔
```

**問題**：sim-bill 走 WebSocket，真實韌體走 MQTT，兩條不同的鏈路，無法驗證真實行為。

### v4（新版，實作中）

```
iHub 按確認
    ↓ POST /api/kiosk/escrow/confirm
Member API
    ↓ callInfraMqtt
Infra MQTT publish
    ↓ MQTT broker
    ├─► 真實韌體訂閱 kiosk/{chip_id}/cmd
    └─► iHub Server 訂閱 kiosk/test-esp32/cmd
            ↓ SSE 推給 sim-bill 前端
        sim-bill 前端收到 → 模擬吞鈔
```

**優點**：sim-bill 跟真實韌體走完全相同的 MQTT 鏈路，只是 sim-bill 多了一層 SSE 橋接（因為瀏覽器不能直接連 MQTT）。

---

## 實作狀態

- [x] 真實韌體鏈路：已完成並測試通過（Fio）
- [x] iHub 平板：已完成並測試通過（Hubie）
- [x] Member API：已完成並測試通過（Mina）
- [x] Infra Listener：已完成並測試通過（Ina）
- [ ] **sim-bill MQTT 鏈路**：實作中（Hubie，msg id=35）

---

## 驗收標準

1. sim-bill 投幣 → iHub 顯示確認畫面（✅ 已通過）
2. iHub 按確認 → sim-bill 在 2 秒內吞鈔（⏳ 待驗證）
3. sim-bill 吞鈔完成 → Member 入帳 → iHub 顯示成功（⏳ 待驗證）
4. 整個流程延遲 < 3 秒（⏳ 待驗證）

---

*文件建立：2026-05-09 (UTC+8) | HQ*
