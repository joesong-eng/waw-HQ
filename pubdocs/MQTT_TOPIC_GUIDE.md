# MQTT 主題規範速查

> **適用對象**：所有 Agent  
> **最後更新**：2026-08-16  
> **版本**：v1.0

---

## 📡 主題命名規範

### 基本格式
```
{prefix}/{device_type}/{device_id}/{action}
```

### 前綴 (prefix)
- `v9/` - 正式環境
- `dev/` - 開發環境
- `test/` - 測試環境

### 設備類型 (device_type)
- `kiosk` - 兌幣卡 (IOTkiosk_v0)
- `game` - 遊戲採集卡 (IOTwawS3)
- `tablet` - Android 平板 (iHub)

---

## 🔄 常用主題

### 兌幣卡 (Kiosk)
```
v9/kiosk/{device_id}/status      # 狀態回報
v9/kiosk/{device_id}/command     # 接收指令
v9/kiosk/{device_id}/diagnostic  # 診斷資訊
v9/kiosk/{device_id}/ota         # OTA 更新
```

### 遊戲採集卡 (Game)
```
v9/game/{device_id}/status       # 狀態回報
v9/game/{device_id}/signal       # 遊戲信號
v9/game/{device_id}/command      # 接收指令
v9/game/{device_id}/diagnostic   # 診斷資訊
```

### 平板 (Tablet)
```
v9/tablet/{device_id}/status     # 狀態回報
v9/tablet/{device_id}/command    # 接收指令
```

---

## 📨 訊息格式

### Status 訊息範例
```json
{
  "device_id": "KIOSK001",
  "timestamp": "2026-08-16T07:00:00Z",
  "online": true,
  "firmware_version": "v1.4.0",
  "ip_address": "192.168.1.100"
}
```

### Command 訊息範例
```json
{
  "command": "reboot",
  "timestamp": "2026-08-16T07:00:00Z",
  "params": {}
}
```

---

## 🔐 權限控制 (ACL)

### 兌幣卡權限
- 可發布：`v9/kiosk/{自己的device_id}/#`
- 可訂閱：`v9/kiosk/{自己的device_id}/command`

### 後端服務權限
- 可訂閱：`v9/+/+/status`（所有設備狀態）
- 可發布：`v9/+/+/command`（所有設備指令）

---

## ⚠️ 注意事項

1. **device_id 必須唯一**：全系統不可重複
2. **使用 QoS 1**：確保訊息至少送達一次
3. **設定 LWT (Last Will)**：設備斷線時自動通知
4. **保留訊息 (Retained)**：status 主題使用，確保新訂閱者可立即取得最新狀態
5. **時間戳格式**：統一使用 ISO 8601 UTC 時間

---

## 📚 詳細文檔

更詳細的 MQTT 協議說明請參考：
- `brains/knowledge/02_technical_standards/MQTT_TOPIC_STANDARD.md`

---

**維護者**：HQ  
**建立日期**：2026-08-16

