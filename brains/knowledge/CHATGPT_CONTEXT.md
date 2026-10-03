# WAW 專案全域上下文與技術導航手冊 (CHATGPT_CONTEXT.md)

> **文件身分**：WAW 全系統最高導航地圖與核心上下文 (Master Context & Neural Index)  
> **專用對象**：ChatGPT 與後續協同開發之 AI Agent  
> **編寫角色**：WAW 協調中心 (HQ)  
> **最後審定日期**：2026-09-24  
> **權威等級**：🔴 最高指導與入口文件 (Single Point of Entry)  
> **狀態標記規範**：【已實作】/【已驗證】/【已設計但尚未實作】/【計畫中】/【未確認】

---

## 導讀指引：如何使用這套上下文系統

本文件是讓 ChatGPT **迅速理解整個 WAW 專案實體全貌的總地圖 (The Map)**。  
為了避免超長文本導致模型遺忘或細節丟失，專案採用**模組化分層架構**：

- **本文件 (`CHATGPT_CONTEXT.md`)**：提供宏觀全局視圖、核心哲學、邊界鐵律、狀態盤點、重要決策、名詞權威字典與總導航。
- **深入細節技術文件 (The Deep Dives)**：
  1. `knowledge/CHATGPT_ARCHITECTURE.md`：伺服器主機拓撲、端口、安全、Nginx 反代、雙模型邊界與資料庫治理。
  2. `knowledge/CHATGPT_FIRMWARE.md`：ESP32-S3 / WROOM 採集板、腳位映射 (Pinout)、PCNT 硬體計數、極性自適應、USB CDC 雙軌與 OTA。
  3. `knowledge/CHATGPT_DATA_FLOW.md`：五大信號與數據流向時序圖（SignalHub、主板歸零、傳統街機掃碼、兌幣機暫存、碼表日結）。
  4. `knowledge/CHATGPT_BUSINESS_LOGIC.md`：脈衝真理定律、整數代幣體系、開洗分結算、雙重月租訂閱、三層會話防護與防弊機制。
  5. `knowledge/CHATGPT_ISSUES.md`：跨文檔現存矛盾對照表、技術債、凍結程式碼、已知 Bug 與給 ChatGPT 的避坑紅線。

---

## 1. 專案總覽 (Project Overview)

### 1.1 WAW 是什麼？
WAW (wawIoT) 是一套專為實體遊藝場、電玩娛樂城、街機與物聯網計數設備打造的**端到端數位化管理、信號中繼與金融級清算平台**。  
它串聯了傳統非聯網機台、現代電腦型 (PC-Based) 連網遊戲機、自動紙鈔兌幣機、雲端 SaaS 後台、玩家行動端錢包以及第三方收銀 POS 系統。

### 1.2 解決什麼行業痛點？
1. **傳統機台黑盒子與防弊審計痛點**：
   - 傳統街機無聯網能力，帳目依賴人工抄寫機械碼表，存在私自開分、偷投幣、調表作弊與員工內鬼等嚴重弊端。
   - WAW 透過帶有光耦隔離的專用 ESP32 採集卡，硬體層直連按鈕與碼表，將每次投幣、退幣、開分、洗分即時轉換為加密物聯網信號上雲。
2. **多方利益分配與資產所有權解耦**：
   - 遊藝場常見「場地主（出店面）」與「機台主（出機器）」合作分潤，過去人工對帳曠日廢時且易生糾紛。
   - WAW 建立多租戶分成合約體系，依據每日每台機器的真實物理淨營收自動產生對帳單。
3. **異質系統與第三方遊戲商對接難題**：
   - 市面上有無數遊戲開發商（例如小猴系統）與不同年代的遊戲機板，協議各異。
   - WAW 制定了 **WAW-USS (Universal Signal Standard)** 通用信號標準，採集卡作為透明中繼，透過 Webhook 與 Type-C 串列埠雙軌輸出，讓第三方遊戲商能在 3 秒內完成點數結算。

### 1.3 目前專案實際做到什麼程度？
- **實體硬體**：【已驗證】定製款 ESP32-S3 Dav Master 採集板與通訊板已完成兩代硬體 PCB 迭代，支援 4 入 4 出光耦隔離，實機運行於測試場地。
- **韌體端**：【已驗證】IOTwawS3 (Coli, v2.0.5) 與 IOTkiosk_v0 (Fio, v1.5.4) 均已通過 PlatformIO 本地編譯驗證，具備 PCNT 脈衝硬體累積、開機信號極性自適應、USB CDC 單行 JSON 串列輸出與 WiFi 跨母機同步。
- **雲端與基礎設施**：【已實作 / 運行中】
  - 核心 MySQL `iotv9` 於 Oracle Cloud 專用 DB 伺服器 (`infra`) 穩定運行，SignalHub 5 張核心業務表遷移完畢。
  - Mosquitto MQTT Broker (TLS 8883) 與監聽 Daemon 正常運作。
  - Owner (Sophie, `iot.tg25.win`)、SignalHub (Sidney, `signal.tg25.win`)、Member (Mina, `win.tg25.win`)、Alliance (Allie, `ali.tg25.win`) 四大獨立 Laravel 站點已部署並在線。
- **進行中工作**：
  - SignalHub 與第三方遊戲系統（小猴）之端對端端點串接與壓力測試。
  - 設備日結自動化與營業月結報表產生器。
- **尚未完成 / 未來規劃**：
  - 對外開放之標準開發者 Portal (OpenAPI 3.0、多語言 Webhook 驗簽 SDK)。
  - 剝離 WAW 內部業務邏輯的開源版本 ESP32 MQTT 韌體。

---

## 2. 整體系統架構精要 (Architecture Summary)

> *完整網路拓撲、主機別名與安全防護機制，請參閱 `knowledge/CHATGPT_ARCHITECTURE.md`。*

系統整體拓撲由邊緣端至雲端高度垂直整合：

```
[實體機台/按鍵/碼表]
       │ (光耦隔離 GPIO / RS232)
       ▼
[ESP32 邊緣採集板 (Coli/Fio)] ──(USB CDC 串列埠)──> [現場收銀 PC (第三方 POS)]
       │
       │ (MQTTS Port 8883 TLS 加密)
       ▼
[Oracle Cloud VPS: infra]
  ├── Mosquitto MQTT Broker (direct-mqtt.tg25.win:8883)
  ├── MQTT Signal Listener (Python Daemon 守護進程)
  └── 核心業務資料庫: Central MySQL (iotv9)
       │
       ├─────────────────────────┬─────────────────────────┐
       │ (X-Internal-Key)        │ (Port 3308 內部連線)     │
       ▼                         ▼                         ▼
[VPS: yd174]               [VPS: yd177]              [VPS: yd16]
  • Owner 營運後台            • Member 會員前端          • Alliance 代理商後台
  • SignalHub 信號中樞        • iHub 平板 API            • 出貨燒錄管理
       │                         │
       ▼                         ▼
[第三方遊戲商 (小猴)]       [玩家手機 / 工控平板]
```

### 2.1 兩大機台營運模型邊界 (絕對紅線，嚴禁混淆)
1. **電腦型聯網遊戲機 (PC-Based / SignalHub)**：
   - 遊戲運行於專用電腦，點數與玩法由遊戲商雲端控制。
   - 採集卡是**透明中繼**：UI1/UI2 開洗分鍵按下只通報 `delta_value: 1` 與流水號，**絕對不計算金額，不做 pulse_ratio 換算**！實際金額由遊戲商在 3 秒內透過 Webhook 回傳之 `actual_points` 決定。
   - UI3/UI4 採集實體電磁計數器脈衝，僅供日結防弊對帳。
2. **傳統單機機板型 (Standalone / game_v0)**：
   - 無電腦遊戲商，玩家透過 Member 掃碼扣代幣，Infra 發送 MQTT 指令，採集卡驅動繼電器模擬投幣脈衝。此模式嚴格遵循 `pulse_to_token` 換算比例。

---

## 3. 韌體精要 (Firmware Summary)

> *完整編譯參數、HAL 驅動、零配置 WiFi 同步細節，請參閱 `knowledge/CHATGPT_FIRMWARE.md`。*

- **MCU 核心**：ESP32-S3-WROOM-1 (DevKitC-1)，16MB Flash，支援原生 USB-Serial-JTAG。
- **專利級輸入架構**：4 組高速光耦輸入（UI1~UI4，反邏輯），硬體計數單元 (PCNT) 脫離 CPU 輪詢，耐受 100kHz 高頻脈衝。
- **開機極性自適應**：開機取樣 IN1 電平，自動識別 King Apple (Active Low) 或 Huga (Active High) 機型，動態切換計數邊沿並存入 NVS。
- **邊緣雙軌輸出 (Dual-Mode)**：
  - 雲端軌：發布至 `waw/v1/{site_id}/signal/{chip_id}/event` (QoS 1)。
  - 地端軌：Type-C USB CDC 零阻塞輸出單行 JSON，並接收本地收銀系統回傳之 `cleared_points`。
- **重大架構修正 (2026-09-04)**：所有韌體輸出之 JSON 徹底移除 `machine` / `machine_number`，硬體層僅上報設備 `chip_id`。

---

## 4. 資料流程精要 (Data Flow Summary)

> *端對端時序圖與各封包格式，請參閱 `knowledge/CHATGPT_DATA_FLOW.md`。*

以最核心的 **SignalHub 開分流程** 為例：
```
機台實體按鈕按下
  ──> 光耦電平跳變
  ──> ESP32 PCNT 累加 raw_value，生成 delivery_id
  ──> MQTTS 發送至 direct-mqtt.tg25.win:8883
  ──> Infra Listener 監聽並 POST 至 SignalHub (internal/signal/event)
  ──> SignalHub 寫入 signal_events 並建立 signal_webhook_deliveries (pending)
  ──> 透過非同步佇列調用 Webhook POST 至第三方系統 (附帶 HMAC-SHA256 簽名)
  ──> 第三方伺服器在 3 秒內回傳 HTTP 200 {"status":"success","actual_points":500}
  ──> SignalHub 更新 delivery 狀態為 success，cleared_points 記為 500
  ──> WebSocket 即時推播至店主大看板
```

---

## 5. 開洗分與清算邏輯精要 (Business & Financial Logic)

> *完整財務定律、分成公式與三層防護機制，請參閱 `knowledge/CHATGPT_BUSINESS_LOGIC.md`。*

1. **脈衝即物理真理 (Pulse is Truth)**：原始脈衝里程表 `raw_value` 是不可推翻的底層依據。
2. **代幣必須為整數 (Tokens are Integers)**：`TOKEN` 與 `TICKET` 資料庫欄位必須為 `INT`，嚴禁小數。
3. **快照留存 (Snapshot Storage)**：每筆交易鎖定當前換算比例，歷史帳務永久可追溯。
4. **斷網防漏帳 (Odometer Delta Algorithm)**：斷網期間由硬體 PCNT 累計，連線後後端以 `新 raw_value - 舊 raw_value` 差值自動補正，零掉單。
5. **會話三層保護**：Layer 1 ESP32 物理 120 秒無活動定時器 -> Layer 2 雲端 5 分鐘心跳 -> Layer 3 MQTT LWT 毫秒級斷線遺囑。

---

## 6. 目前硬體與軟體狀態盤點 (Status Matrix)

### 6.1 目前硬體狀態 【客觀實體】
- **Dav Master ESP32-S3 板卡**：【已驗證】實體打樣完成，具備 4 入 4 出光耦隔離、Type-C 介面、外接 WiFi 天線座。
- **ICT 104U 紙鈔接收機**：【已驗證】透過 RS232 電平轉換板與 IOTkiosk_v0 串接，支援新台幣 100/500/1000 元防偽識別與暫存壓箱。
- **iHub 工控 Android 平板**：【已驗證】7 吋 / 10 吋 Android 工控平板，安裝 iHub APK，具備動態 QR Code 展示與觸控互動。

### 6.2 目前軟體狀態 【模組盤點】
- **【已完成 / 穩定運行】**：
  - 核心資料庫 `iotv9` (MySQL 8) 架構治理。
  - Owner 後台：機台列表、場地管理、信號入口選單。
  - SignalHub：Profile 設定檔、腳位映射、日結規則、Webhook 派送與重試、小猴 Mock 驗證工具。
  - Member 前端：掃碼開分、代幣餘額扣款。
  - Firmware：IOTwawS3 v2.0.5、IOTkiosk_v0 v1.5.4。
- **【測試中】**：
  - SignalHub 與實體機台、真實小猴 POS 系統之端對端聯調。
  - 遠端隊列 Worker 自動重啟與錯誤自癒機制。
- **【未完成 / 計畫中】**：
  - 場地月租 (1500) 與機台月租 (300) 的自動扣款與帳單出帳排程。
  - 對外開發者 API Key 自助申請與計費平台。

---

## 7. Agent 分工職責表 (Agent Division of Labor)

全專案採用多 Agent 協同體系，由 **HQ (協調中心)** 統一發號施令，嚴禁跨專案私自修改代碼：

| Agent 名稱 | 管轄專案目錄 | 職責邊界與成果 |
| :--- | :--- | :--- |
| **HQ** | `brains/knowledge/`<br>`dev_tools/` | • 全域架構規劃、知識庫維護（唯一寫入權限）<br>• `waw_ops.sh` 派工中樞、全域決策裁決 |
| **Sophie** | `PROJECT/Owner` | • 營運商/場地主管理後台 (`iot.tg25.win` @ yd174)<br>• 完成 M1~M4 模組、信號設定入口、場地營運儀表板 |
| **Sidney** | `PROJECT/SignalHub` | • 信號中心獨立站點 (`signal.tg25.win` @ yd174)<br>• 完成 4 大核心頁面、腳位映射、Webhook 轉發、相容小猴回調 |
| **Mina** | `PROJECT/Member` | • 玩家會員端 PWA/前端 (`win.tg25.win` @ yd177)<br>• 完成掃碼開分、會話維護、虛擬錢包扣款 |
| **Ina** | `PROJECT/Infra` | • 基礎設施、資料庫與通訊 (@ infra)<br>• 維護 `iotv9` Central DB、MQTT Broker、內部 Listener Daemon |
| **Allie** | `PROJECT/Alliance` | • 聯盟與燒錄出貨後台 (`ali.tg25.win` @ yd16)<br>• 設備韌體配對、條碼出貨（`burning.blade.php` 凍結維護） |
| **Hubie** | `PROJECT/iHub` | • 兌幣機 Android 工控 APK<br>• 完成 QR Code 展示、紙鈔暫存人工確認畫面 |
| **Coli** | `PROJECT/IOTwawS3` | • 遊戲機 ESP32-S3 採集卡韌體 (v2.0.5)<br>• 完成 PCNT 硬體脈衝累積、極性自適應、USB CDC 雙軌輸出 |
| **Fio** | `PROJECT/IOTkiosk_v0`| • 兌幣機通訊卡韌體 (v1.5.4)<br>• 完成 ICT 104U RS232 橋接、Escrow 狀態機、母機 WiFi 同步廣播 |

---

## 8. 重要技術決策總表 (Key Technical Decisions)

| 決策日期 | 決策主題 | 決策內容與技術考量 | 影響專案 |
| :--- | :--- | :--- | :--- |
| **2026-09-04** | **廢除機台編號** | **徹底移除 `machine_number` / `machine_name`**。<br>考量：硬體層專注識別我是誰 (`chip_id`)；USB CDC 無法從雲端同步名稱；避免兩套編號混淆。 | Coli, Sidney |
| **2026-09-03** | **開洗分雙軌輸出** | **同時支援 MQTTS 雲端軌與 Type-C 地端串列軌**。<br>考量：適應現場完全無外網之封閉場地，達到毫秒級即時通報。 | Coli, Sidney |
| **2026-08-03** | **術語標準化 Phase 1** | **全面統一使用 `venue` (廢棄 store) 與 `device` (暫代 machine)**。<br>考量：消弭資料庫與程式碼中 store/venue 與 device/machine 混用亂象。 | 全體 Agent |
| **2026-06-19** | **脈衝核心三定律** | **確立「脈衝即真理、代幣為整數、比例留快照」**。<br>考量：奠定金融級對帳基礎，杜絕小數點浮點誤差與歷史帳目失真。 | 全體 Agent |
| **2026-05-08** | **紙鈔暫存人工確認** | **兌幣機 Escrow 採人工按鈕確認入箱機制**。<br>考量：避免玩家誤投假鈔或取消投幣產生爭議，提升現場交易安全性。 | Fio, Mina, Hubie |
| **2026-09-21** | **燒錄介面重構凍結** | **凍結 Alliance `burning.blade.php` 拆分計畫**。<br>考量：該畫面牽涉出貨流水線高風險業務，未經 Joe 核可嚴禁更動。 | Allie |

---

## 9. 知識庫核心文件索引與導航 (Knowledge Index)

以下為 `brains/knowledge/` 中最權威之基礎文檔導引：

### 最高指導法典 (MANDATORY STANDARDS)
- `brains/knowledge/NAMING_AUTHORITY.md`：全系統名稱、識別碼格式、DB 欄位唯一權威正本。
- `brains/knowledge/02_technical_standards/MQTT_TOPIC_STANDARD.md`：MQTT 主題規範 (WAW-USS v1.0) 唯一正本。
- `brains/knowledge/04_deployment_operations/VPS_TOPOLOGY_CARD.md`：主機拓撲、SSH 別名與連線紅線禁令。
- `brains/knowledge/02_technical_standards/PULSE_BASED_DATA_FLOW.md`：脈衝資料流與整數代幣規範。
- `brains/knowledge/02_technical_standards/WAW_SIGNAL_SEMANTIC_SPECIFICATION.md`：信號通道物理語義標準。

### 業務與流程規格 (Business Flows)
- `brains/knowledge/05_business_flows/DECISION_REMOVE_MACHINE_NUMBER_2026-09-04.md`：移除機台編號決策記錄。
- `brains/knowledge/05_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md`：兌幣機完整金流規範。
- `brains/knowledge/05_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md`：傳統街機開洗分與會話規格。
- `brains/knowledge/03_system_architecture/WAW_2.0_ARCHITECTURE_SPEC.md`：WAW 2.0 人-店-機解耦架構。

---

## 10. 全域專用名詞與識別碼字典 (Glossary)

| 名詞 / 識別碼 | 標準格式範例 | 物理/業務語義 | 權威定義來源 |
| :--- | :--- | :--- | :--- |
| **`chip_id`** | `df1e4c4b1105` (12碼十六進位) | ESP32 實體晶片 MAC 位址，硬體唯一身分標識 | `NAMING_AUTHORITY.md` |
| **`node_id`** | `device_001` / `kiosk_001` (全小寫) | 產品層級之設備編號，用於 QR Code 網址與對外展示 | `NAMING_AUTHORITY.md` |
| **`venue_id`** | 整數 PK (例如 `1`) | 實體遊藝場地/店面 ID (嚴禁使用 store_id) | `NAMING_AUTHORITY.md` |
| **`delivery_id`** | 6 位以上整數 (例如 `982341`) | 採集卡事件全域唯一自增序號，用於 Webhook/Serial 冪等性結算 | `usb_cdc_comm.c` |
| **`raw_value`** | 64 位元整數 (例如 `10582`) | 類似汽車里程表，自開機或出廠以來的累積總脈衝數 | `signal_collector.c` |
| **`delta_value`** | 整數 (按鍵為 `1`, 碼表為 `N`) | 本次硬體事件相較於前一次的脈衝增量 | `signal_collector.c` |
| **`actual_points`** | 整數 (例如 `500`) | 第三方遊戲商在 Webhook 回應中回傳之真實開洗分點數 | `CallbackAckController.php` |
| **`cleared_points`** | 整數 | 資料庫歷史欄位名，在 SignalHub 中與 actual_points 互通 | `SignalWebhookDelivery.php` |
| **`UI1 ~ UI4`** | 硬體引腳代號 | 光耦隔離輸入通道 (Sense)：UI1 開分, UI2 洗分, UI3 碼表/防盜, UI4 活動 | `platformio.ini` |
| **`OUT1 ~ OUT4`** | 硬體引腳代號 | 繼電器輸出通道 (Pulse)：OUT1 開分觸發, OUT2 洗分觸發 | `platformio.ini` |
| **`Escrow`** | 業務狀態 | 紙鈔機驗鈔完成但尚未壓箱之「暫存保持態」 | `KIOSK_EXCHANGE_FLOW.md` |

---

## 11. 給 ChatGPT 的重要避坑指南 (Common Misconceptions)

> **⚠️ 當 ChatGPT 閱讀本專案或提供建議時，最容易犯以下錯誤，請務必自我校驗：**

1. ❌ **不要假設可以在本地執行測試或建立資料庫**：
   - 本地環境純為代碼寫作，沒有 MySQL、Redis 或 MQTT 服務。任何建議「在本地 run test、migrate、或 build」都是違規的。
2. ❌ **不要將 PC-Based 電腦遊戲機當成傳統瑪莉機計算比例**：
   - 服務員按下開分鍵 (UI1)，上報的只是觸發事件 (`delta: 1`)。**不要**乘以 pulse_ratio 來算點數！實際點數是由小猴遊戲商伺服器在回調中提供的 `actual_points`。
3. ❌ **不要在代碼或規格中加回 `machine_number`**：
   - 該欄位已於 2026-09-04 正式拍板完全移除，硬體與 Webhook 絕不帶機台自訂名稱。
4. ❌ **不要使用預設 SSH Port 22 或直連 Raw IP**：
   - 全專案主機強制走 Port **39022**，並依賴 `~/.ssh/config` 的主機別名 (`yd174`, `yd177`, `yd16`, `infra`)。
5. ❌ **不要使用浮點數存放代幣**：
   - 代幣 (`TOKEN`) 與彩票 (`TICKET`) 必須是 `INT` 整數。
6. ❌ **不要碰 Alliance 的 `burning.blade.php`**：
   - 該檔案已被 Joe 凍結，嚴禁重構。
