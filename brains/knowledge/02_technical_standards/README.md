# 02_technical_standards — 協定與標準

本目錄文件為強制規範，不可隨意修改。任何變更必須經 HQ 提案。

## 文件清單

| 文件 | 核心內容 | 查閱時機 |
|------|---------|---------| 
| MQTT_TOPIC_STANDARD.md 🔴 | **MQTT 主題唯一正本**：兩套體系 (WAW-USS v1.0 新標準 + Legacy 相容層)、所有 Action/QoS/Retain/Payload 規範 | 開發任何 MQTT 相關功能前（必讀） |
| TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md 🔴 | 識別碼命名、API Payload、Port/協議規範、帳務命名 | 開發 API / DB 欄位命名前 |
| WEBSOCKET_CHANNEL_STANDARD.md 🔴 | WebSocket 頻道名稱、事件名稱、Payload 格式 | 開發任何 WebSocket 相關功能前 |
| HARDWARE_PULSE_MAPPING.md | 脈衝轉換架構、機台參數（pulse_to_token 等）、情境推演 | 開發遊戲機脈衝計算功能前 |
| HARDWARE_WIRING_TERMINOLOGY_CLARIFICATION.md 🔴 | 硬體接線術語對照、傳統/電腦遊戲機接線差異、UI/UO 腳位邏輯 | 硬體接線、採集卡安裝、接線除錯前 |
| ESP32_COMMON_SDK_SPEC.md | ESP32 共用 SDK 規範 | 開發韌體功能前 |
| PULSE_BASED_DATA_FLOW.md | 脈衝資料流設計、事件處理邏輯 | 開發脈衝相關功能前 |
| SIGNAL_FLOW_MONITOR.md | 信號流可視化設計（待實作） | 除錯分散式通信流時參考 |
| QRCODE_FORMAT_STANDARD.md | QR Code 格式規範 | 開發 QR Code 相關功能前 |
| USER_IDENTITY_VALIDATION_STANDARD.md | 用戶身份驗證標準 | 開發身份驗證功能前 |
| WAW_SIGNAL_SEMANTIC_SPECIFICATION.md | WAW 信號語意規格 | 開發信號語意相關功能前 |
| SIGNAL_WEBHOOK_AND_SERIAL_STANDARD_v2.md | SignalHub Webhook 與 Serial 通訊規範 | 開發 Webhook 或 Serial 功能前 |

## 核心規則

1. **MQTT_TOPIC_STANDARD.md 是 MQTT 主題的唯一真理**，不允許在任何 PROJECT 子目錄中另立 MQTT 主題定義文件
2. **TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md** 是識別碼命名的唯一真理，發現不一致以此為準
3. 兩種韌體主題不可混淆：kiosk/{chip_id}/ (IOTkiosk_v0 舊相容) vs waw/v1/{site_id}/signal/{chip_id}/ (WAW-USS v1.0 主標準)
4. 任何主題或事件名稱變更，必須先更新這裡的文件，再通知所有 Agent
5. 硬體接線時務必參考 HARDWARE_WIRING_TERMINOLOGY_CLARIFICATION.md，避免混淆「開分按鈕」與「開分數字表」

## 流浪文件警告

以下 PROJECT 子目錄文件為早期各 Agent 自行撰寫，**已被本目錄文件取代**，僅作代碼參考，不得視為規範正本：

- PROJECT/SignalHub/docs/WAW_SIGNAL_STANDARD_v1.0.md → 參見 MQTT_TOPIC_STANDARD.md
- PROJECT/IOTkiosk_v0/docs/MQTT_PROTOCOL.md → 參見 MQTT_TOPIC_STANDARD.md
- PROJECT/IOTkiosk_v0/docs/IHUB_INTEGRATION.md → 參見 MQTT_TOPIC_STANDARD.md
- PROJECT/IOTwawS3/PULSE_COLLECTION_STANDARD.md → 參見 MQTT_TOPIC_STANDARD.md
- PROJECT/Infra/mqtt/README.md（主題章節）→ 參見 MQTT_TOPIC_STANDARD.md（舊版 Legacy 體系）
