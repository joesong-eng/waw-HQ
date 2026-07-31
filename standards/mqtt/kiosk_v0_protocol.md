# IOTkiosk_v0 MQTT 通訊協議規範

**文件版本：** v2.1 (實作對齊版)  
**更新日期：** 2026-05-09  
**適用韌體：** IOTkiosk_v0 (v1.5.4+)  

---

## 1. Broker 配置

| 項目 | 值 |
|------|-----|
| **Host** | `mqtt.tg25.win` |
| **Port** | `8883` |
| **TLS** | 雙向憑證（CA + client.crt + client.key）|
| **Client ID** | `{chip_id}` (MAC 地址 12 碼小寫) |
| **Keepalive** | 30 秒 |

---

## 2. 通訊架構說明

根據 **V9 體系規範**，本設備已全面移除 `waw/`、`up/`、`down/` 與 `v9/` 前綴。

---

## 3. 主題 (Topics) 總覽

| 階段 | Topic | 方向 | QoS | Retain | 說明 |
|-------|------|-----|--------|------|------|
| **1. 狀態心跳** | `kiosk/{id}/status` | Up | 1 | Yes | 每 25 秒上報 ba_state/error (全大寫) |
| **2. 金流事件** | `kiosk/{id}/event` | Up | 2 | No | escrow, stacked, rejected (小寫) |
| **3. 下達指令** | `kiosk/{id}/cmd` | Down | 2 | No | stack, reject, enable, disable... (小寫) |
| **4. 指令回報** | `device/{id}/command/response` | Up | 1 | No | 指令執行結果回報 (ok/busy/fail) |
| **5. 設備資訊** | `device/{id}/info` | Up | 1 | Yes | 版本資訊、OTA 完工通知 |
| **6. 在線 LWT** | `device/{id}/status` | LWT | 1 | Yes | online / offline |
| **7. 診斷數據** | `device/{id}/diagnostic` | Up | 1 | No | 每 5 分鐘上報 RSSI/Heap/Uptime |
| **8. 偵錯 Log** | `kiosk/{id}/debug` | Up | 0 | No | 原始 Debug 字串廣播 |

---

## 4. 訊息格式 (Payloads)

### 4.1 金流事件 (`kiosk/{id}/event`)
採用扁平化 JSON 格式。
*   **Escrow**: `{"event":"escrow","event_id":"...","amount":100,"timestamp":...}`
*   **Stacked**: `{"event":"stacked","event_id":"...","amount":100,"timestamp":...}`
*   **Rejected**: `{"event":"rejected","reason":"timeout",...}`

### 4.2 狀態心跳 (`kiosk/{id}/status`)
```json
{
  "ba_state": "IDLE",
  "ba_error": "NONE",
  "lifetime_total": 12500,
  "lifetime_count": 15,
  "timestamp": 1715181600
}
```
*   `ba_state`: `IDLE`, `ESCROW`, `STACKING`, `REJECTING`, `DISABLED`, `FAULT` (全大寫)
*   `ba_error`: `NONE`, `BILL_JAM`, `MOTOR_FAILURE`, `STACKER_OPEN`, `COMM_FAILURE` 等 (全大寫)

### 4.3 遠端指令 (`kiosk/{id}/cmd`)
格式：`{"action": "stack", "req_id": "..."}`
*   `action`: `stack`, `reject`, `enable`, `disable`, `reboot`, `ota_update` (全小寫)

### 4.4 指令回報 (`device/{id}/command/response`)
格式：`{"transaction_id":"...","command_type":"...","status":"ok"}`

---

## 5. 維護接口 (AP Mode)

當長按按鈕進入配網模式時，裝置提供以下 HTTP API (SSID: `IOTWAW_{id}`, IP: `192.168.22.22`):
*   `GET /scan-results`: 回傳 WiFi 掃描列表。
*   `POST /save-config`: 儲存 `{"ssid":"...","pwd":"..."}` 並重啟。

---

## 6. 核心參數與超時行為 (Fail-Safe)

*   **Escrow 超時**：後台 15 秒未回應則自動執行 `reject`。
*   **Hold 間隔**：Escrow 期間每 2 秒向紙鈔機發送一次 `Hold`。
*   **MQTT 斷線**：Escrow 狀態下偵測到斷線則立即退鈔。

---
*最後更新於 2026-05-09，對齊 IOTkiosk_v0 實作配置。*
