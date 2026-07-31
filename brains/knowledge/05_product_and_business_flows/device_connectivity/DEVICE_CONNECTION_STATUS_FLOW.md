# 設備連線狀態判斷流程規範


**[On-Demand]** — 上下文注入策略

> **版本**: v1.0.0  
> **日期**: 2026-06-17 (UTC+8)  
> **維護者**: HQ（基於 Coli 實際實作規範化）  
> **適用範圍**: IOTwawS3 (Coli)、IOTkiosk_v0 (Fio)、Infra 監控 (Ina)

## 一、設備連線狀態的業務意義

### 1.1 狀態定義
- **online**: 設備與 MQTT Broker 保持連線，可接收指令
- **offline**: 設備已斷線或異常，無法通訊
- **idle**: 設備在線但超過 90 秒無活動（僅 IOTwawS3）
- **active**: 設備在線且近期有 GPIO 活動

### 1.2 業務影響
- **營運監控**: 判斷場地設備是否正常運作
- **遠端控制**: 確保開分/洗分指令能正確傳達
- **故障排除**: 快速識別需要維修的設備
- **資料可信度**: 離線設備的資料可能不即時

## 二、技術實作流程

### 2.1 設備上線流程 (IOTwawS3)

```
1. 設備啟動 WiFi 連線
2. 建立 MQTT 連線，設定 LWT
   └─ Topic: device/{chip_id}/status
   └─ LWT Payload: "offline"
   └─ Keep-alive: 30 秒
3. 發送上線狀態
   └─ Topic: device/{chip_id}/status  
   └─ Payload: "online"
   └─ QoS: 1, Retain: 1
4. 發送設備資訊
   └─ Topic: device/{chip_id}/info
   └─ Payload: {"chip_id": "xxx", "firmware_ver": "1.0.26", ...}
   └─ QoS: 1, Retain: 1
```

### 2.2 心跳機制 (事件驅動)

```
GPIO 活動檢測 (200ms 防抖)
├─ 投幣事件: device/{chip_id}/data/credit_in
├─ 出金事件: device/{chip_id}/data/credit_out  
└─ 活動心跳: device/{chip_id}/activity
   └─ Payload: {"timestamp": 1734451340}
   └─ QoS: 0 (無需確認)
```

### 2.3 離線檢測機制

```
正常離線:
└─ 設備主動發送 device/{chip_id}/status = "offline"

異常離線:
└─ MQTT Keep-alive 超時 (30-60 秒)
   └─ Broker 自動發送 LWT: "offline"
```

## 三、故障排除指南

### 3.1 設備顯示離線但實際在線

**可能原因**:
1. Infra API 服務異常 (502 錯誤)
2. MQTT 監聽服務停止
3. Redis 連線問題
4. 設備 WiFi 不穩定

**排除步驟**:
```bash
# 1. 檢查 Infra API
curl -H 'X-Internal-Key: v9-internal-key-2026' https://api.tg25.win/api/device/online-status

# 2. 檢查 MQTT Broker 狀態  
mosquitto_sub -h mqtt.tg25.win -t "device/+/status" -v

# 3. 檢查 Redis 狀態
redis-cli keys "device:status:*"
```

---

**參考文檔**:
- `02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md`
- Coli MQTT 心跳實作報告: `IOTwawS3/_agent/REPORT_20260617_184047_TASK_20260617_MQTT_HEARTBEAT.md`
