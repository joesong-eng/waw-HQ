# IOTkiosk — iHub 整合對接規格

**文件版本：** v2.1 (實作對齊版)  
**日期：** 2026-05-09  
**適用韌體：** IOTkiosk_v0 (v1.5.4+)  
**MQTT Broker：** `mqtt.tg25.win:8883`（TLS/MQTTS）

---

## 概述

IOTkiosk 裝置負責控制紙鈔機（TP Series，104U Protocol），透過 MQTT 與後台（iHub）雙向通訊，實現遠端收鈔授權、故障通報、帳務同步與系統診斷等功能。

**⚠️ 重要規範：**
根據 `AI_CONTEXT.md` 最新標準，已全面移除 `v9/`、`waw/`、`up/` 與 `down/` 前綴。所有 Kiosk 專屬主題皆以 `kiosk/{kiosk_id}/` 或 `device/{kiosk_id}/` 開頭。

---

## 一、上行 Topic（ESP32 → iHub 訂閱）

### 1.1 紙鈔機事件 (Events)
```
Topic: kiosk/{kiosk_id}/event
QoS:   2
```
*   **`escrow`**: 偵測到鈔票，等待指令。後台需在 15 秒內回應。
*   **`stacked`**: 吃鈔完成確認。帳務入帳的唯一憑據。
*   **`rejected`**: 退鈔確認 (reason: `manual`, `timeout`, `hardware`)。

### 1.2 設備狀態心跳 (Status)
```
Topic: kiosk/{kiosk_id}/status
QoS:   1, Retain
發送時機：每 25 秒定時推送
```
*   範例：`{"ba_state":"IDLE","ba_error":"NONE","lifetime_total":12500,...}`
*   注意：`ba_state` 與 `ba_error` 為**全大寫**字串。

### 1.3 指令執行回報 (Response)
```
Topic: device/{kiosk_id}/command/response
QoS:   1
```
當後台發送指令到 `kiosk/{id}/cmd` 後，裝置會在此 Topic 回報結果：
*   格式：`{"transaction_id":"...","command_type":"...","status":"ok"}`

### 1.4 設備資訊與 OTA 通知 (Info)
```
Topic: device/{kiosk_id}/info
QoS:   1, Retain
```
包含版本資訊。OTA 完成後會發布：`{"ota":"success","pending_reboot":true}`。

### 1.5 系統診斷資料 (Diagnostic)
```
Topic: device/{kiosk_id}/diagnostic
QoS:   1 (每 5 分鐘推送)
```
提供 `free_heap`, `rssi`, `uptime` 等內部數據。

---

## 二、下行 Topic（iHub → ESP32）

### 2.1 標準指令 (Command)
```
Topic: kiosk/{kiosk_id}/cmd
QoS:   2
```
格式：`{"action": "stack", "req_id": "..."}`
*   `action` 可選值：`stack`, `reject`, `enable`, `disable`, `reboot`, `ota_update`。

---

## 三、維護接口 (Maintenance)

### 3.1 AP 配網模式 (Provisioning)
當裝置進入配網模式時（長按按鈕），會開啟名為 `IOTWAW_{chip_id}` 的 WiFi 熱點。
*   **IP 地址**：`192.168.22.22`
*   **Web API**：
    *   `GET /scan-results`: 掃描附近 WiFi。
    *   `POST /save-config`: 儲存 SSID 與密碼 (Payload: `{"ssid":"...","pwd":"..."}`)。
    *   `POST /exit-ap`: 結束配網並重啟。

---

## 四、核心流程與防呆

1. **Escrow 超時**：後台 15 秒未回應則自動退鈔。
2. **斷線保護**：Escrow 狀態下 MQTT 斷線則立即退鈔。
3. **對帳真值**：`lifetime_total` 是 NVS 儲存的唯一對帳真值。

---
*文件更新於 2026-05-09，對齊 IOTkiosk_v0 實作碼。*
