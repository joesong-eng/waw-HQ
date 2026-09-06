# 遊戲機通訊卡識別碼體系

> **版本**: 1.0.0
> **日期**: 2026-05-12 (UTC+8)
> **韌體**: `IOTwawS3`（game_v0）
> **對應文件**: 兌幣卡識別碼見 `brains/knowledge/05_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md`

---

## 識別碼層級

### 硬體層級

| 識別碼 | 格式 | 範例 | 用途 |
|--------|------|------|------|
| `chip_id` | 12位小寫hex（MAC address） | `e072a1f73a78` | MQTT 主題、硬體通訊 |

- MQTT 主題：`device/{chip_id}/data`、`device/{chip_id}/command`
- DB 欄位：`iotv9.devices.chip_id`（UNIQUE）
- **不對外暴露**（不放在 QR Code 裡）

### 產品層級

| 識別碼 | 格式 | 範例 | 用途 |
|--------|------|------|------|
| `node_id` | `device_NNN`（小寫，3位數字） | `device_001`, `device_042` | QR Code、API、Session、對外識別 |

- DB 欄位：`iotv9.devices.node_id`（UNIQUE，待新增）
- QR Code：`https://win.tg25.win/m/play?node_id=device_001`
- API 參數：`node_id=device_001`
- Session 記錄：`device_sessions.node_id`

---

## 對應關係

```
iotv9.devices
  node_id: device_001   ← 產品層級，對外識別
  chip_id: e072a1f73a78 ← 硬體層級，MQTT 通訊
```

掃碼流程：
```
QR Code（node_id）
    ↓
Member 呼叫 GET /api/device/by-node/{node_id}
    ↓
Infra 查 iotv9.devices，回傳 chip_id、name、參數
    ↓
Member 用 chip_id 發 MQTT trigger_pulse
```

---

## 使用原則

| 場景 | 使用 |
|------|------|
| QR Code 內容 | `node_id`（`device_NNN`） |
| MQTT 主題 | `chip_id`（MAC） |
| API 參數（對外） | `node_id` |
| Session 記錄 | `node_id` |
| Infra Listener 內部 | `chip_id` |

---

## 與兌幣機識別碼對照

| 項目 | 兌幣機（kiosk_v0） | 遊戲機（game_v0） |
|------|------------------|-----------------|
| 韌體 | `IOTkiosk_v0` | `IOTwawS3` |
| MQTT 前綴 | `kiosk/` | `device/` |
| node_id 格式 | `kiosk_NNN` | `device_NNN` |
| DB 表 | `iotv9.kiosks` | `iotv9.devices` |
| 識別碼文件 | `05_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` | 本文件 |

---

## 待實作

- [ ] `iotv9.devices` 新增 `node_id` 欄位（Sophie / Ina）
- [ ] Infra 新增 `GET /api/device/by-node/{node_id}` API（Ina）
- [ ] Alliance 燒錄列印改用 `node_id` 格式 URL（Allie）
- [ ] Member `device_sessions` 表改用 `node_id`（Mina）

---

*維護者：HQ | 版本：1.0.0 | 2026-05-12*
