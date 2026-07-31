# 02_protocols_and_standards — 協定與標準

本目錄文件為強制規範，不可隨意修改。任何變更必須經 HQ 提案。

## 文件清單

| 文件 | 核心內容 | 查閱時機 |
|------|---------|---------|
| `02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` 🔴 | MQTT 主題格式、Payload 規範、QoS/Retain 策略、ACL | 開發任何 MQTT 相關功能前 |
| `WEBSOCKET_CHANNEL_STANDARD.md` 🔴 | WebSocket 頻道名稱、事件名稱、Payload 格式 | 開發任何 WebSocket 相關功能前 |
| `HARDWARE_PULSE_MAPPING.md` | 脈衝轉換架構、機台參數（pulse_to_token 等）、情境推演 | 開發遊戲機脈衝計算功能前 |
| `02_protocols_and_standards/SIGNAL_FLOW_MONITOR.md` | 信號流可視化設計（待實作） | 除錯分散式通信流時參考 |

## 核心規則

- `02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` 是唯一真理，發現不一致以此為準
- 兩種韌體主題不可混淆：`kiosk/{chip_id}/`（kiosk_v0）vs `device/{chip_id}/`（game_v0）
- 任何主題或事件名稱變更，必須先更新這裡的文件，再通知所有 Agent
