================================================================================

<!-- ===== START OF CHATGPT_CONTEXT.md ===== -->

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

<!-- ===== END OF CHATGPT_CONTEXT.md ===== -->


<!-- ===== START OF CHATGPT_ARCHITECTURE.md ===== -->

# WAW 系統架構與拓撲全解析 (CHATGPT_ARCHITECTURE.md)

> **文件身分**：WAW 專案架構深探文件 (專供 ChatGPT 深度解析)  
> **關聯總索引**：`knowledge/CHATGPT_CONTEXT.md` (實體位置: `brains/knowledge/CHATGPT_CONTEXT.md`)  
> **最後校驗日期**：2026-09-24  
> **維護權限**：HQ (協調中心唯一寫入)  
> **狀態標記準則**：【已實作】/【已驗證】/【已設計但尚未實作】/【計畫中】/【未確認】

---

## 1. 全域實體拓撲與主機職責架構

WAW (wawIoT) 是一套軟硬體高度整合的遊藝場/街機與物聯網點數清算管理平台。全系統部署於 Oracle Cloud 基礎設施與本地邊緣節點，並受嚴格的遠端運維治理規範約束。

### 1.1 伺服器主機與別名對照表 (SSOT) 【已驗證】

所有伺服器均位於 Oracle Cloud，所有 Agent 與協調者禁止使用原始 IP 或預設 Port 22 直連，必須使用 SSH 別名。

| 主機 SSH 別名 | 實體 IP 位址 | SSH 端口 | 使用者 | 憑證路徑 | 負責 Agent | 託管站點 / 核心服務 | 伺服器實體目錄 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`yd174`**<br>(別名: `v9`, `Owner`, `blc`) | 129.153.116.174 | 39022 | ubuntu | `~/.ssh/id_rsa` | **Sophie**<br>**Sidney** | • **Owner 營運後台** (`iot.tg25.win`)<br>• **SignalHub 信號中心** (`signal.tg25.win`) | `/www/wwwroot/iot.tg25.win`<br>`/www/wwwroot/signal.tg25.win` |
| **`yd177`**<br>(別名: `mina`, `ihub`, `yd47`) | 129.146.103.177 | 39022 | ubuntu | `~/.ssh/id_rsa` | **Mina**<br>**Hubie** | • **Member 會員前端** (`win.tg25.win`)<br>• **iHub 平板 API** (`ihub.tg25.win`) | `/www/wwwroot/win.tg25.win`<br>`/www/wwwroot/ihub.tg25.win` |
| **`yd16`**<br>(別名: `alliance`) | 137.131.50.16 | 39022 | ubuntu | `~/.ssh/id_rsa` | **Allie** | • **Alliance 聯盟/燒錄後台** (`ali.tg25.win`) | `/www/wwwroot/ali.tg25.win` |
| **`infra`**<br>(別名: `db`) | 141.148.165.50 | 39022 | ubuntu | `~/.ssh/id_rsa` | **Ina** | • **Central MySQL (`iotv9`)**<br>• **MQTT Broker (Mosquitto TLS)**<br>• MQTT 信號監聽器 (Daemon) | `/home/ubuntu/tg25-infra` |
| **`bessie202`**<br>(別名: `HQ`, `PM`) | 132.226.87.202 | 39022 | ubuntu | `~/.ssh/id_rsa` | **HQ** | • HQ Taskflow 派工總控<br>• Redis Pub/Sub 神經網路 | `/home/ubuntu` |

### 1.2 網路與安全拓撲規則 【已驗證】
1. **非標準 SSH 端口**：所有 VPS 統一使用 Port **39022**，絕對禁止直連預設 Port 22。
2. **連線唯一憑據**：強制使用本機 `~/.ssh/config` 別名連線（如 `ssh yd174`），嚴禁在命令列使用 Raw IP 或明文密碼。
3. **資料庫集中隔離**：
   - Web 伺服器（`yd174`, `yd177`, `yd16`）本機**不存放業務資料庫**。
   - 核心 MySQL `iotv9` 僅託管於 `infra` (141.148.165.50)。各 Web 專案透過內部安全通道或 Port 3308 穿透連線。在 Web 伺服器本地執行 `mysql` 指令必屬錯誤。
4. **HTTPS / TLS 加密**：
   - 外部流量由 Cloudflare CDN / SSL 代理，對內反向代理至 Nginx。
   - MQTT 通訊採用 MQTTS (TLS v1.2/1.3) Port **8883**，ESP32 韌體內建 Let's Encrypt / DigiCert 憑證包進行伺服器身分驗證。
5. **本機代碼純淨原則**：
   - 本機（Mac）僅用於寫代碼與 Git 版本控制。
   - 嚴禁本機執行 `php artisan migrate`、本地 `pnpm run build`、本地 MySQL / Redis / MQTT 測試。所有驗證必須在對應 VPS 上透過 `waw_ops.sh` 執行。

---

## 2. 系統分層架構 (System Layered Architecture)

系統橫跨五個核心抽象層級，實現硬體、通訊、平台與業務應用的解耦：

```
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 4: 使用者與第三方業務層 (Partner, Cashier, Member, Venue Owner)      │
│  - Member 前端 (win.tg25.win) / Owner 後台 (iot.tg25.win)               │
│  - SignalHub 合作夥伴後台 (signal.tg25.win) / 第三方 POS (小猴收銀系統)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP(S) / WebSocket / Webhook
┌───────────────────────────────────▼────────────────────────────────────┐
│ Layer 3: 核心後端業務服務層 (Laravel Applications & Central DB)           │
│  - Owner API / Member API / SignalHub API / Alliance API               │
│  - 核心資料庫: Central MySQL (iotv9 @ infra), Member DB (yd47)          │
│  - 非同步佇列與任務調度 (Redis Queue, Horizon, crontab scheduler)        │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ Internal API / Webhook (X-Internal-Key)
┌───────────────────────────────────┴────────────────────────────────────┐
│ Layer 2: 基礎設施與信號中繼層 (Infra & Message Routing)                   │
│  - Mosquitto MQTT Broker (Port 8883 TLS @ infra)                       │
│  - MQTT Signal Listener (監聽 raw pulse 並寫入 DB / 轉發 Webhook)       │
│  - WebSocket Server (Pusher / Laravel WebSockets / Reverb)             │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ MQTT (MQTTS 8883) / USB CDC Serial
┌───────────────────────────────────┴────────────────────────────────────┐
│ Layer 1: 邊緣硬體與韌體層 (Edge Hardware & Firmware)                     │
│  - IOTwawS3 (Coli): ESP32-S3 遊戲採集卡 (PCNT 脈衝計數 + 雙軌輸出)      │
│  - IOTkiosk_v0 (Fio): ESP32-S3 / WROOM 兌幣通訊卡 (RS232 鈔票機控制)     │
│  - iHub (Hubie): 工控 Android 平板 (展示 QR Code, 兌幣 Escrow 人工確認) │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ 光耦隔離 GPIO / RS232 / 繼電器
┌───────────────────────────────────┴────────────────────────────────────┐
│ Layer 0: 實體遊藝機台與計數設備 (Physical Arcade Machine & Meters)        │
│  - PC-Based 聯網街機 (開分按鈕, 洗分按鈕, 實體電磁計數表 UI3/UI4)       │
│  - 傳統單機機板 (投退幣脈衝, 瑪莉機, 輪盤機, 框體)                       │
│  - ICT 104U 紙鈔接收機 (Pulse / RS232 協議)                             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 兩大機台營運模型邊界 (CRITICAL ARCHITECTURAL BOUNDARY)

在理解 WAW 架構時，**最致命的錯誤**就是混淆「電腦型網路遊戲機」與「傳統單機投幣機」。兩者在硬體定位、信號意義與金流邏輯上完全不同：

### 3.1 模型 A：電腦型聯網遊戲機 (PC-Based Online Game Machine)
- **代表專案**：`SignalHub` (Sidney) + `IOTwawS3` (Coli)
- **機台架構**：遊戲運行於專用電腦（PC 主機），機台內部的點數增減、遊戲規則、賠率與清算**100% 由遊戲商後端伺服器控制**。
- **採集卡定位**：**透明邊緣中繼器 (Transparent Relay)**。採集卡**絕不介入**遊戲業務邏輯，不換算點數，不修改機台記憶體。
- **兩條完全獨立的信號通道**：
  1. 🔴 **事件觸發通道 (UI1 / UI2)**：
     - **物理事件**：吧台服務員收取現金後，按下實體「開分」或「洗分」按鈕。
     - **採集卡行為**：偵測到按鍵閉合，發布事件 `delta: 1` 與當前累計里程表 `raw_value`。
     - **核心鐵律**：採集卡**不知道金額**、**不做比例換算 (Pulse Ratio)**、**不產生金額**！
     - **點數確認**：由第三方遊戲商伺服器在收到 Webhook 後，於 3 秒內透過 Callback 或 HTTP 回傳 `actual_points`。
  2. 🔵 **碼表脈衝通道 (UI3 / UI4)**：
     - **物理事件**：機台若裝有機械碼表（電磁計數器），馬達轉動產生的方波脈衝。
     - **採集卡行為**：硬體 PCNT 計數器採集物理脈衝數（累加 raw_value）。
     - **用途**：僅作為營業日結、防弊審計與對帳依據，**絕對禁止與開洗分按鍵混為一談**！

### 3.2 模型 B：傳統單機機板型 (Standalone Arcade / game_v0 / kiosk_v0)
- **代表專案**：`Owner` (Sophie) + `Member` (Mina) + `IOTkiosk_v0` (Fio) / `IOTwawS3` (Coli 舊模式)
- **機台架構**：傳統單機（如瑪莉機、水果盤、輪盤）。無聯網遊戲伺服器，投幣即時產生機台硬體脈衝。
- **採集卡定位**：**主控與觸發終端**。
- **開分機制**：玩家掃描機台 QR Code，手機點選扣除 1 代幣；Member 後台呼叫 Infra API 發送 MQTT 指令；ESP32 驅動繼電器 (PIN_OUT1) 模擬投幣脈衝送入機板。
- **脈衝比例換算**：此模式下嚴格遵守 `pulse_to_token` 換算比例（如 2 脈衝 = 1 代幣），此比例由場地主在 Owner 後台統一設定。

---

## 4. 資料庫架構與實體關聯 (Database Architecture & Governance)

系統包含兩套主要的關聯式資料庫系統：

### 4.1 核心業務資料庫：`iotv9` (MySQL 8 / MariaDB @ infra)
由 **Ina (Infra)** 獨佔 DDL 變更權限。

#### 核心實體結構：
1. **場地實體：`venues`** 【已驗證】
   - 記錄場地名稱、地址、聯絡人、代幣價值 (`token_value_twd`)。
   - 規範：全域統一使用 `venue`，廢棄舊規格書中的 `store` 命名。
2. **設備資產：`devices`** 【已驗證】
   - 實體採集卡與硬體對應表。
   - 關鍵欄位：`id` (內部整數 PK), `chip_id` (12 碼十六進位 MAC), `owner_id` (機主 FK), `venue_id` (場地 FK), `status`, `last_seen_at`。
   - **重大架構決策 (2026-09-04)**：完全移除 `machine_number` 與 `machine_name` 欄位，設備端只負責識別「我是誰 (`chip_id`)」。
3. **兌幣機設備：`kiosks`** 【已驗證】
   - 兌幣卡硬體表，綁定 `esp32_mac` (同 chip_id)、`screen_mac` (iHub 平板 MAC)、`venue_id`。
4. **SignalHub 專用表群 (2026-09 Migration 完成)** 【已驗證】：
   - `signal_profiles`：信號配置檔案（店主針對不同機型設定腳位定義、Webhook 目標、Serial 致能狀態）。
   - `signal_pin_mappings`：腳位映射表（定義 UI1~UI4 對應之事件代碼，如 `credit_in`, `credit_out`, `coin_meter`）。
   - `signal_stat_rules`：日結統計規則（加減公式配置）。
   - `signal_webhooks`：第三方 Webhook 推送端點配置與密鑰。
   - `signal_webhook_deliveries`：信號派送審計日誌（包含 `delivery_id`, `raw_value`, `delta_value`, `cleared_points` / `actual_points`, `status`, `retry_count`）。
5. **部署與分成交易：`device_deployments`, `device_transactions`** 【已實作】
   - 記錄機台在場地的進出場歷史，支援動態分潤計算 (`owner_share`, `venue_owner_share`)。

### 4.2 會員與會話資料庫：`waw_member_production` (MySQL @ yd177)
由 **Mina (Member)** 負責維護。
1. **`device_sessions`**：傳統機台遊戲掃碼會話表（記錄 `session_token`, `member_id`, `chip_id`, `status`, `started_at`, `ended_at`）。
2. **`kiosk_sessions`**：兌幣機掃碼連線會話表（記錄會員與紙鈔機的互動狀態）。
3. **`member_wallets`**：會員虛擬錢包表。
   - 貨幣類型：`CASH` (現金), `TOKEN` (遊戲代幣), `POINT` (點數), `TICKET` (彩票)。
   - **數值規範**：代幣與彩票一律為整數 (`INT`)，絕對不使用小數。
4. **`wallet_transactions`**：會員錢包變動交易日誌。

---

## 5. 通訊協定與安全架構 (Communication & Security)

### 5.1 MQTT 通訊規範 (WAW-USS v1.0) 【已實作 / 驗證中】
- **Broker 位置**：`direct-mqtt.tg25.win:8883` (TLS 加密)。
- **主題結構**：`waw/v1/{site_id}/signal/{chip_id}/{action}`
  - `action = event`：硬體事件與脈衝里程表上報 (QoS 1, Retain false)。
  - `action = status`：在線心跳、狀態回報與 LWT 遺囑 (QoS 1, Retain true)。
  - `action = cmd`：雲端下行單播控制指令 (QoS 1, Retain false)。
  - `action = ack`：硬體接收指令後之回執 (QoS 1, Retain false)。

### 5.2 邊緣雙軌輸出 (Dual-Mode Output) 【已實作】
針對現場無網際網路或要求極致低延遲的場地，採集卡支援雙軌並行輸出：
1. **雲端軌道 (Cloud Path)**：ESP32 透過 Wi-Fi 發布 MQTT 封包至雲端 Broker。
2. **地端軌道 (Local Path)**：ESP32 透過 USB-CDC / Type-C 虛擬串列埠，以 115200 鮑率直接向現場收銀 PC 發送單行 JSON，並接收 PC 回傳之 `cleared_points`。

### 5.3 跨服務內部驗證 (Service-to-Service Auth) 【已驗證】
- **內部 Webhook 通訊**：Member ↔ Infra ↔ SignalHub 內部 API 呼叫，必須在 HTTP Header 附帶：
  `X-Internal-Key: v9-internal-key-2026`
- **Infra 設備 API 授權**：呼叫 `api.tg25.win/api/device/...` 時，附帶：
  `X-API-Key: v9_backend_token_2026`
- **第三方 Webhook 簽名防偽 (HMAC-SHA256)**：
  - Header：`X-WAW-Signature: sha256={hash}`
  - 簽名計算方式：使用共享密鑰對 `timestamp + "." + raw_payload` 進行雜湊，防止重放攻擊 (Replay Attack)。

### 5.4 WebSocket 頻道架構 (WebSocket Channel Standard) 【已驗證】
由 Pusher 或 Laravel WebSockets 廣播即時事件給前端：
1. **機台即時頻道**：`waw-device.{chip_id}`
   - 事件：`DeviceStatusChanged` (在離線狀態切換)、`CreditAssigned` (開分完成回報)、`CreditSettled` (洗分結算回報)。
2. **兌幣機即時頻道**：`kiosk.{kiosk_id}`
   - 事件：`KioskEscrowPending` (紙鈔吸入，等待平板人工確認)、`KioskBillStacked` (紙鈔入箱成功)、`KioskSessionTimeout` (會話逾期結束)。
3. **場地大看板頻道**：`private-venue.{venue_id}.dashboard`
   - 事件：`LiveOdometerUpdate` (機械碼表數字跳動)、`DailyRevenueSnapshot` (當日營收快照)。

### 5.5 遠端部署與運維標準 (Deployment SOP) 【已驗證】
全專案由根目錄 `dev_tools/waw_ops.sh` 總控：
- 派工指令：`./dev_tools/waw_ops.sh task <agent> <task_id> "<desc>" [priority]`
- 遠端部署：`./dev_tools/waw_ops.sh deploy <agent>` (自動執行遠端 Git pull、composer install、artisan optimize、Nginx 重載)
- 狀態監控：`./dev_tools/waw_ops.sh status` (檢查各 Agent inbox/outbox 堆疊)
- 遠端執行：`./dev_tools/waw_ops.sh remote <agent> "<command>"` (在目標 VPS 執行指令)

<!-- ===== END OF CHATGPT_ARCHITECTURE.md ===== -->


<!-- ===== START OF CHATGPT_FIRMWARE.md ===== -->

# WAW 韌體架構與邊緣硬體深度指南 (CHATGPT_FIRMWARE.md)

> **文件身分**：WAW 專案韌體與邊緣硬體深探文件 (專供 ChatGPT 深度解析)  
> **關聯總索引**：`knowledge/CHATGPT_CONTEXT.md` (實體位置: `brains/knowledge/CHATGPT_CONTEXT.md`)  
> **最後校驗日期**：2026-09-24  
> **維護權限**：HQ (協調中心唯一寫入)  
> **狀態標記準則**：【已實作】/【已驗證】/【已設計但尚未實作】/【計畫中】/【未確認】

---

## 1. 硬體平台與 MCU 選型全貌

WAW 系統的邊緣硬體主要由兩種核心物聯網通訊採集板卡構成，均基於樂鑫 (Espressif) 架構開發，並採用 PlatformIO 搭配 ESP-IDF 原生框架進行編譯與管理。

### 1.1 兩大硬體工程與對應 Agent 【已驗證】

| 韌體工程目錄 | 負責 Agent | 核心功能定位 | 目標硬體板卡 | 記憶體與 Flash 規格 | 當前穩定版本 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`PROJECT/IOTwawS3`** | **Coli** | 遊戲機信號採集卡 (PC-Based / 傳統街機) | **ESP32-S3-DevKitC-1**<br>(Dav Master S3 專用定製板) | 16MB Flash (OPI/OPI)<br>內建 2MB/8MB PSRAM | **v2.0.5** 【已編譯驗證】 |
| **`PROJECT/IOTkiosk_v0`** | **Fio** | 兌幣機通訊中繼卡 (紙鈔機 RS232 橋接) | 1. **ESP32-S3** (主流)<br>2. **ESP32-WROOM-32** (相容) | S3: 8MB Flash<br>WROOM: 4MB Flash | **v1.5.4** (S3)<br>**v1.3.5** (WROOM) |

### 1.2 實體硬體設計細節 (Dav Master ESP32-S3) 【已驗證】
- **硬體版本標識**：Dav_s3-9194-03 / Dav Master ESP32-S3-2 (硬體佈線圖見知識庫 `Dav_Master_ESP32_S3_2.pdf` 及實體相片 `Dav_s3-9194-03.jpeg`)。
- **電氣隔離架構**：
  - 輸入端採用高速**光耦隔離器 (Optocoupler Isolation)**，完全阻絕遊藝機台內部高壓干擾與靜電突波 (ESD)。
  - 光耦輸入為**反邏輯 (Inverted Logic)**：當外部機台信號接通（按鈕按下或碼表接地）時，ESP32 輸入腳位讀取到低電位 (`0`)；無信號時為高電位 (`1`)。HAL 抽象層自動將其反轉為 `true = 有信號`。
  - 輸出端採用光耦驅動之固態繼電器 (SSR) 或達靈頓電晶體，模擬實體開洗分脈衝短接。

---

## 2. 硬體腳位定義 (Pinout SSOT)

根據 `PROJECT/IOTwawS3/platformio.ini` 與 `PROJECT/IOTkiosk_v0/platformio.ini` 之最高編譯參數定義，腳位分配如下：

### 2.1 IOTwawS3 (Coli - 遊戲採集卡) 腳位映射表 【已驗證】

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ESP32-S3 Dav Master                             │
│                                                                        │
│   [Sense 輸入 (光耦隔離)]                [Pulse 輸出 (繼電器/控制)]       │
│   UI1 (GPIO 1)  : SENSE_CREDIT_IN       OUT1 (GPIO 45) : PULSE_ADD      │
│   UI2 (GPIO 2)  : SENSE_CREDIT_OUT      OUT2 (GPIO 46) : PULSE_WASH     │
│   UI3 (GPIO 13) : SENSE_FAULT (碼表/防盜) OUT3 (GPIO 47) : PULSE_OUT3     │
│   UI4 (GPIO 14) : SENSE_ACTIVITY (活動)  OUT4 (GPIO 48) : PULSE_OUT4     │
│                                                                        │
│   [系統周邊]                             [通訊介面]                       │
│   LED_SYS (GPIO 11) : 系統指示燈(共陽極)   USB CDC : 內建 USB-Serial-JTAG   │
│   BUTTON_CONFIG (GPIO 21) : 配網重置鍵   I2C_SDA (GPIO 15) / SCL (GPIO 16)│
└────────────────────────────────────────────────────────────────────────┘
```

- **歷史腳位變更註記**：早期版本曾使用 GPIO 19/20 作為輸入，但因與 ESP32-S3 原生 USB-Serial-JTAG 腳位衝突，已在 2026-06 重構中移至 **GPIO 1 與 GPIO 2**。

### 2.2 IOTkiosk_v0 (Fio - 兌幣卡) 雙平台腳位對照表 【已驗證】

| 腳位功能 | S3 DevKitC (8MB) | WROOM-32 (4MB 舊相容環境) | 備註說明 |
| :--- | :--- | :--- | :--- |
| **PIN_IN1** (投幣/紙鈔脈衝) | **GPIO 1** | **GPIO 13** | 光耦輸入 |
| **PIN_IN2** (退幣信號) | **GPIO 2** | **GPIO 14** | 光耦輸入 |
| **PIN_IN3** (機台故障/防盜) | **GPIO 13** | **GPIO 27** | 震動擺錘 / 門碰開關 |
| **PIN_IN4** (備用輸入) | **GPIO 14** | **GPIO 33** | 備用 |
| **PIN_OUT1** (開分/出幣) | **GPIO 45** | **GPIO 15** | 繼電器驅動 |
| **PIN_OUT2** (洗分/致能) | **GPIO 46** | **GPIO 2** | 繼電器驅動 |
| **PIN_LED_SYS** | **GPIO 11** | **GPIO 2** | 系統狀態燈 |
| **PIN_BUTTON_CONFIG** | **GPIO 21** | **GPIO 0** | 配網鍵 (BOOT Pin) |
| **PIN_I2C_SDA / SCL** | **GPIO 15 / 16** | **GPIO 21 / 22** | OLED / 外部感應器 |

---

## 3. 韌體核心模組架構 (Firmware Subsystems)

韌體採用高度解耦的模組化架構，基於 FreeRTOS 多工任務與事件佇列 (Event Queue) 運作：

```
  [硬體中斷 / PCNT]  ──> [signal_collector]  ──> [event_bus]
                                                     │
       ┌─────────────────────────────────────────────┼─────────────────────────────────────────────┐
       ▼                                             ▼                                             ▼
 [mqtt_service]                              [usb_cdc_comm]                               [command_executor]
 (TLS 8883 MQTT)                           (Type-C 虛擬串列埠)                            (執行開洗分繼電器輸出)
```

### 3.1 訊號採集模組 (`signal_collector`) 【已實作】
- **硬體脈衝計數器 (PCNT)**：
  - 核心脈衝採集（UI1~UI4）全面採用 ESP32 內部專用硬體計數單元 `pcnt_unit`，完全脫離軟體輪詢 (Polling)，在 100kHz 以下脈衝零漏失。
  - 具備硬體濾波器 (Glitch Filter)，濾除 10~50 微秒以內的機械彈跳與高頻噪訊。
- **里程表式累計機制 (Raw Accumulator)**：
  - 軟體維護 64 位元累計器 `raw_value`，紀錄自通電開機以來的累積總脈衝數。
  - 每次觸發時計算增量 `delta_value`。即使網路瞬斷，重連後後端依然可根據前後兩次 `raw_value` 差值完美補齊數據，杜絕掉分。

### 3.2 訊號極性自適應演算法 (Polarity Auto-Detection) 【已驗證】
- **背景問題**：遊藝場機台訊號極性不統一：
  - **King Apple (大蘋果/皇冠機)**：常態為高電位 (`1`)，按鈕閉合時短接拉低 (`0`)，屬**下降沿觸發 (Active Low)**。
  - **Huga (野蠻遊戲)**：常態為低電位 (`0`)，按鈕閉合時短接送電 (`1`)，屬**上升沿觸發 (Active High)**。
- **開機自適應流程**：
  1. 開機延遲 200ms 等待線路電位穩定。
  2. 對 `PIN_SENSE_IN1` 連續取樣 3~5 次。
  3. 若均為高電位，判定為 King Apple 機型，動態配置 PCNT 為下降沿觸發；反之判定為 Huga，配置為上升沿觸發。
  4. 識別結果寫入 NVS 保存，並透過 MQTT `info` 主題呈報給雲端。
  5. **支援雲端覆寫**：後端可下發 `set_signal_polarity` MQTT 指令，強制設定指定極性。

### 3.3 雙軌通訊模組 (`usb_cdc_comm`) 【已驗證】
- **硬體基礎**：使用 ESP32-S3 原生內建之 `usb_serial_jtag` 控制器，無須外掛 CH340 / CP2102 轉接晶片。
- **零阻塞發送架構**：
  - 採用 FreeRTOS Queue (`s_tx_queue`) 緩衝機制。
  - 當採集到脈衝時，以 `timeout=0` 非阻塞推送入佇列。若 USB 未連接或緩衝區滿，直接丟棄該輸出，**絕對不卡死 GPIO 脈衝計數或核心業務迴圈**。
- **收銀 PC 回呼解析**：
  - 背景 Task 監聽 Type-C 串列埠接收緩衝區，按換行符 (`
`) 切割單行 JSON。
  - 內建 `cJSON` 解析器，提取 `cleared_points` 與 `delivery_id`，驗證成功後透過 `event_bus` 推送 `EVT_USB_CLEARED_POINTS`。

### 3.4 零配置配網連動 (`wifi_sync_service`) 【已實作】
為了解決遊藝場數十台採集卡逐一手機配網極度耗時的痛點，設計了「母機-子機同步機制」：
1. **母機 (IOTkiosk_v0 兌幣卡)** 配網成功後，開放為期 15 分鐘的配對廣播視窗。
2. **子機 (IOTwawS3 遊戲卡)** 開機若檢測到 NVS 無 WiFi 設定，自動啟動背景掃描。
3. 搜尋隱藏 SSID 前綴 `WAW_SYNC_*`，連入 AP（密碼：`waw_secure_proxy`），連線 TCP Port `8266`。
4. 送出握手暗號 `IOT_KIOSK_V0_SECRET_2024`，自動接收 JSON 格式之場地 WiFi SSID、密碼與 MQTT 參數，寫入 NVS 後自動重啟 (`esp_restart`)，達成整場批次自動配網。

### 3.5 兌幣機狀態機與紙鈔機通訊 (`IOTkiosk_v0`) 【已驗證】
在兌幣卡中，ESP32 透過 UART (RS232 電平轉換) 與 ICT 104U 紙鈔機通訊，嚴格實作 Fail-Safe 狀態機：
1. **`DISABLED` (開機預設/保護態)**：
   - 綠色投幣指示燈熄滅，紙鈔機馬達拒絕吸鈔。必須等待雲端 Member 派發 `enable` 指令後方進入 `IDLE` 態。
2. **`ACCEPTING` / `ESCROW` (暫存態)**：
   - 會員投入鈔票，紙鈔機驗偽通過並卡入暫存閘門。
   - 韌體回報 `escrow` 事件（含面額，如 100/500/1000 元）。
   - 紙鈔機進入保持狀態，等待雲端在 30 秒內裁決。
3. **`STACKING` (入箱裁決)**：
   - 收到雲端下發 `stack` 指令，紙鈔機馬達滾動壓入錢箱。
   - 偵測到壓箱光耦閉合後，上報 `bill_stacked` 成功事件，Member 隨即完成代幣入帳。
4. **`REJECTING` (退鈔裁決)**：
   - 若超時無確認或收到 `reject` 指令，馬達反轉將鈔票吐還給用戶。

---

## 4. 通訊協定與資料格式 (Data Formats)

### 4.1 USB CDC 串列埠通訊協定 【已驗證】
- **實體參數**：115200 8-N-1，Type-C 連線。
- **採集卡發送格式 (Pulse Event)**：
  ```json
  {"delivery_id":982341,"event":"credit_in","chip_id":"df1e4c4b1105","pin":"UI1","raw":10582,"delta":1,"ts":1725339600}
  ```
  > **架構決策確認**：依據 2026-09-04 決策，已徹底移除 `machine` / `machine_number` 欄位。
- **現場電腦回傳格式 (Cashier ACK)**：
  ```json
  {"status":"success","delivery_id":982341,"cleared_points":500}
  ```

### 4.2 MQTT WAW-USS v1.0 格式 【已實作】
- **事件發布主題**：`waw/v1/{site_id}/signal/{chip_id}/event` (QoS 1)
  ```json
  {
    "chip_id": "DF1E4C4B1105",
    "pin": "UI1",
    "event_type": "credit_in",
    "raw_value": 10582,
    "delta_value": 1,
    "occurred_at": 1725339600
  }
  ```
- **狀態與遺囑主題**：`waw/v1/{site_id}/signal/{chip_id}/status` (QoS 1, Retain true)
  ```json
  {
    "chip_id": "DF1E4C4B1105",
    "state": "online",
    "fw_ver": "2.0.5",
    "wifi_rssi": -58,
    "ip": "192.168.1.105",
    "polarity": "active_low"
  }
  ```
  > **LWT 遺囑機制**：連線時預埋遺囑封包 `{"chip_id":"DF1E4C4B1105","state":"offline"}`，斷線由 Broker 立即廣播。

---

## 5. 狀態管理、NVS 儲存與 OTA 更新

### 5.1 NVS (非揮發性儲存) 分區規劃 【已驗證】
- `wifi_config`：SSID、密碼、靜態 IP (可選)。
- `mqtt_config`：Broker 位址、Port、Client ID、Auth Token。
- `pulse_odometer`：四個通道的歷史脈衝累計底數（每隔 100 脈衝或關機預警時寫入，減緩 Flash 損耗）。
- `hardware_flags`：開機極性偵測結果、測試模式開關。

### 5.2 雙分區 OTA 機制 (Dual-Partition A/B Update) 【已驗證】
- 分區表採用 `partitions_ota.csv`：包含 `otadata`、`app0` (Slot 1)、`app1` (Slot 2)。
- 支援 HTTPS 安全下載新版韌體。下載完成後校驗 SHA-256，標記新分區為待啟動。
- **防變磚保護 (Rollback Protection)**：若重啟後在新韌體中發生 Crash 或 30 秒內未成功連上 MQTT，ESP-IDF 自動回滾至舊版分區。


---

## 6. FreeRTOS 多工任務與核心分配矩陣 (Task Allocation Matrix) 【已實作】

ESP32-S3 具備雙核心 Tensilica Xtensa 32-bit LX7 CPU，韌體實作嚴格的核心綁定與優先級隔離：

| Task 名稱 | 優先級 (Priority) | 堆疊深度 (Stack Size) | 綁定核心 (Core) | 職責與阻塞特性 |
| :--- | :---: | :---: | :---: | :--- |
| **\`main\`** | 1 | 8192 Bytes | Core 0 | 系統開機初始化、硬體自我檢測 (POST)、NVS 讀取 |
| **\`signal_collector\`** | 5 (最高) | 4096 Bytes | Core 1 | 捕獲 PCNT 硬體脈衝中斷、30ms 按鍵防抖狀態機、向 Event Bus 推送事件 (零阻塞) |
| **\`event_bus\`** | 4 | 4096 Bytes | Core 1 | 系統內部事件分發、解耦採集端與網路端 |
| **\`usb_cdc\`** | 2 | 4096 Bytes | Core 0 | 監聽 Type-C 虛擬串列埠、解析單行 JSON 回呼、非阻塞 TX 輸出 |
| **\`mqtt_task\`** | 3 | 8192 Bytes | Core 0 | MQTTS (TLS 8883) 網路維持、發送事件、處理雲端控制指令 |
| **\`fault_monitor\`** | 2 | 2048 Bytes | Core 1 | 監控 UI3 擺錘震動與機台防盜接點 (200ms 防抖) |
| **\`button_monitor\`** | 2 | 2048 Bytes | Core 1 | 監控 PIN_BUTTON_CONFIG (長按 3 秒發布重置配網事件) |
| **\`led_indicator\`** | 1 | 2048 Bytes | Core 0 | 驅動 PIN_LED_SYS 閃爍模式 (快閃=配網中, 慢閃=連線中, 常亮=正常運作) |

---

## 7. ICT 104U 紙鈔接收機通訊協議詳解 (kiosk_v0 專用) 【已驗證】

在 \`PROJECT/IOTkiosk_v0\` 中，ESP32 透過 UART1 與 ICT 104U 進行 RS232 通訊 (9600 Baud, 8-E-1 偶校驗)：

### 7.1 紙鈔面額十六進位對照表
- \`0x40\`：新台幣 100 元 (NT$ 100)
- \`0x41\`：新台幣 200 元 (NT$ 200)
- \`0x42\`：新台幣 500 元 (NT$ 500)
- \`0x43\`：新台幣 1,000 元 (NT$ 1,000)
- \`0x44\`：新台幣 2,000 元 (NT$ 2,000)

### 7.2 控制指令位元組序列
- **致能吸鈔 (Enable)**：ESP32 發送 \`0x3E\`，104U 回應 \`0x3E\`，綠燈亮起。
- **禁能吸鈔 (Disable)**：ESP32 發送 \`0x5E\`，104U 綠燈熄滅，拒收所有紙鈔。
- **裁決暫存 (Escrow Hold)**：104U 驗偽合格後將紙鈔停留在入鈔口，並發送面額代碼 (如 \`0x40\`)。
- **壓入錢箱 (Stack)**：收到雲端確認後，ESP32 發送 \`0x02\` (ACK/Stack)，104U 馬達啟動壓箱，閉合後回報 \`0x10\` (Stacked)。
- **退回紙鈔 (Reject)**：超時或手動取消時，ESP32 發送 \`0x0F\` (Reject)，馬達反轉將鈔票吐出。

<!-- ===== END OF CHATGPT_FIRMWARE.md ===== -->


<!-- ===== START OF CHATGPT_DATA_FLOW.md ===== -->

# WAW 完整資料流程與端對端時序全解析 (CHATGPT_DATA_FLOW.md)

> **文件身分**：WAW 專案資料流向深探文件 (專供 ChatGPT 深度解析)  
> **關聯總索引**：`knowledge/CHATGPT_CONTEXT.md` (實體位置: `brains/knowledge/CHATGPT_CONTEXT.md`)  
> **最後校驗日期**：2026-09-24  
> **維護權限**：HQ (協調中心唯一寫入)  
> **狀態標記準則**：【已實作】/【已驗證】/【已設計但尚未實作】/【計畫中】/【未確認】

---

## 1. 核心資料流程總覽

WAW 系統的資料流程依照業務型態區分為兩大體系、四條獨立管道：
1. **流程一：SignalHub 電腦型街機開洗分流 (PC-Based Online Flow - Event Trigger)**
2. **流程二：SignalHub 遊戲主板分數歸零通報流 (Session End Inbound Flow)**
3. **流程三：傳統街機手機掃碼開分流 (Traditional Arcade Scan & Credit Flow - game_v0)**
4. **流程四：兌幣機紙鈔暫存與入箱兌換流 (Kiosk Escrow & Exchange Flow - kiosk_v0)**
5. **流程五：機械碼表脈衝稽核與日結流 (Mechanical Counter Auditing - UI3/UI4)**

---

## 2. 流程一：SignalHub 電腦型街機開洗分流程 (核心旗艦流程)

本流程適用於電腦型街機（如聯網捕魚機、老虎機、推幣機），服務員收取玩家現金後，按下吧台開分或洗分實體鍵。

### 2.1 物理事件到雲端轉發時序 【已驗證】

```
[吧台實體按鈕] 
       │ 1. 服務員按下按鍵 (短接 100ms)
       ▼
[光耦隔離輸入 (UI1/UI2)]
       │ 2. 電平反轉 (下降沿/上升沿)
       ▼
[ESP32-S3 (Coli 韌體)]
       │ 3. PCNT 計數器捕獲中斷，軟體累加 raw_value，設定 delta_value = 1
       │ 4. 生成流水 delivery_id (例: 982341)
       ├────────────────────────────────────────────────────────┐
       │ (雲端軌道: Wi-Fi MQTTS)                                 │ (地端軌道: USB CDC 串列埠)
       ▼                                                        ▼
[Mosquitto Broker @ infra (Port 8883)]              [現場收銀 PC (第三方 POS)]
       │ 5. 發布至 waw/v1/{site}/signal/{chip_id}/event          │ 5a. 收到單行 JSON
       ▼                                                        ▼
[Infra MQTT Listener (Python Daemon)]               [收銀軟體處理]
       │ 6. 監聽封包，驗證 chip_id                               │ 6a. 3秒內回寫 Serial
       │ 7. POST internal/signal/event                          ▼
       ▼                                            [ESP32 接收 cleared_points]
[SignalHub 後端 (signal.tg25.win @ yd174)]                       (完成地端結算)
       │ 8. 驗證 X-Internal-Key
       │ 9. 寫入 iotv9.signal_events (原始物理事件流水)
       │ 10. 查詢 signal_pin_mappings 與 signal_webhooks
       │ 11. 建立 iotv9.signal_webhook_deliveries (狀態: pending)
       │ 12. 透過非同步佇列調度 Webhook 發送
       ▼
[第三方遊戲伺服器 (小猴系統)]
       │ 13. 接收帶有 X-WAW-Signature 簽名之 Webhook POST
       │ 14. 遊戲伺服器在 3 秒內決定實際點數 (actual_points)
       ▼
[雙向確認完成 (Two-Way Settlement)]
  - 同步模式：小猴在 Webhook HTTP Response 直接回傳 JSON (含 actual_points: 500)
  - 非同步模式：小猴呼叫 POST /v9/signal-hub/callback-ack 異步回報
       ▼
[SignalHub 結算落地]
       │ 15. 更新 signal_webhook_deliveries (cleared_points = actual_points, status = success)
       │ 16. 廣播 WebSocket 事件至店主即時大看板
```

### 2.2 關鍵資料封包細節

#### (A) ESP32 上報 MQTT Event Payload
```json
{
  "chip_id": "DF1E4C4B1105",
  "pin": "UI1",
  "event_type": "credit_in",
  "raw_value": 10582,
  "delta_value": 1,
  "occurred_at": 1725339600
}
```

#### (B) SignalHub 轉發第三方 Webhook Payload
```json
{
  "delivery_id": 982341,
  "event": "credit_in",
  "chip_id": "df1e4c4b1105",
  "pin_code": "UI1",
  "raw_value": 10582,
  "delta_value": 1,
  "occurred_at": "2026-09-24T12:00:00+08:00"
}
```
> **架構決策驗證**：已徹底不傳輸 `machine_number` 與 `machine_name`。

#### (C) 第三方回覆 Payload (必須在 3 秒內抵達)
```json
{
  "status": "success",
  "delivery_id": 982341,
  "actual_points": 500
}
```

---

## 3. 流程二：SignalHub 遊戲主板分數歸零通報流 (Session End)

當玩家離場或遊戲結束，電腦型機台內部分數歸零時，遊戲主控程式主動向 SignalHub 呈報，用於計算該位玩家的在席遊玩時長與營收對帳。

```
[遊戲主板 / 小猴程式] (檢測到遊戲內存分數從 >0 變為 0)
       │
       │ POST https://signal.tg25.win/api/v9/signal-hub/inbound/session-end
       │ Header: Content-Type: application/json
       ▼
[SignalHub Inbound Controller]
       │ 1. 驗證 chip_id 歸屬與有效性
       │ 2. 記錄 session_end 事件至資料庫
       │ 3. 計算並更新最後遊戲時長 (last_played_duration_seconds)
       │ 4. 觸發營收結算統計規則 (signal_stat_rules)
       ▼
[HTTP 200 回應] {"status": "accepted", "session_id": "sess_884912"}
```

---

## 4. 流程三：傳統街機手機掃碼開分流程 (game_v0)

此模式針對傳統單機投幣機（如瑪莉機、輪盤、框體），機台本身無聯網 PC，完全由 WAW 採集卡充當投幣器模擬中樞。

```
[玩家手機] 掃描機台貼附之 QR Code (https://win.tg25.win/m/play?node_id=device_001)
       │
       ▼
[Member 前端 (win.tg25.win)]
       │ 1. 建立/恢復 device_sessions (檢查一人一台限制)
       │ 2. 玩家在手機介面點擊「開分 1 代幣」
       │ 3. 檢查 member_wallets 代幣餘額 (必須 >= 1)
       │ 4. 凍結代幣 (-1 TOKEN, status = pending)
       │ 5. 依據場地配置換算脈衝 (例: pulse_to_token = 0.5 -> 2 脈衝)
       ▼
[Member 後端]
       │ 6. 呼叫 Infra 內部觸發端點
       │ POST https://api.tg25.win/api/device/trigger-pulse
       │ Header: X-Internal-Key: v9-internal-key-2026
       │ Payload: {"chip_id": "iot002", "count": 2, "action": "assign_credit"}
       ▼
[Infra API (api.tg25.win)]
       │ 7. 發布 MQTT 指令
       │ Topic: device/{chip_id}/cmd
       │ Payload: {"command": "assign_credit", "params": {"count": 2}}
       ▼
[ESP32 採集卡 (Coli)]
       │ 8. 收到 cmd 指令
       │ 9. 驅動 PIN_OUT1 (GPIO 45) 產生 2 次方波脈衝 (高電位 50ms, 低電位 50ms)
       ▼
[實體機台主板] 投幣引腳接收到 2 下短接，機台螢幕分數跳動增加
       │
       ▼
[實體碼表反饋 (UI3)] 機台電磁計數器跳動，ESP32 PCNT 累加 raw_value 並發布 MQTT event 回雲端
       │
       ▼
[Member 後端收到反饋] 解除代幣凍結，標記交易為 success
```

---

## 5. 流程四：兌幣機紙鈔暫存與入箱兌換流 (kiosk_v0)

本流程涵蓋現金紙鈔防偽、雙向安全暫存 (Escrow) 與代幣充值。

```
[玩家] 走近兌幣機，手機掃描 iHub 工控平板上動態產生的 QR Code
       │
       ▼
[Member 系統] 建立 kiosk_sessions (綁定會員與 kiosk_001)，狀態進入 ACTIVE
       │
       ▼
[Member API] 透過 Infra 派發 MQTT 指令給兌幣卡
       │ Topic: kiosk/{chip_id}/cmd
       │ Payload: {"command": "enable"}
       ▼
[ESP32 兌幣卡 (Fio)]
       │ 驅動紙鈔機 (ICT 104U) 亮起綠色投幣指示燈，脫離 DISABLED 保護態
       │
[玩家投鈔] 投入一張新台幣 100 元紙鈔
       │
       ▼
[紙鈔機 104U]
       │ 1. 馬達捲入紙鈔，光學/磁性防偽驗證通過
       │ 2. 停留在 Escrow 閘門位置，不壓入錢箱
       │ 3. 透過 RS232 回報 ESP32: bill_accepted, bill_value = 100
       ▼
[ESP32 兌幣卡]
       │ 發布 MQTT 事件: kiosk/{chip_id}/event
       │ Payload: {"event_type": "escrow", "amount": 100, "currency": "TWD"}
       ▼
[Infra Listener] 轉發 Webhook 給 Member
       ▼
[Member 後端]
       │ 1. 建立 pending 交易
       │ 2. 廣播 WebSocket 事件 KioskEscrowPending 至 iHub 平板頻道
       ▼
[iHub 平板介面]
       │ 螢幕彈出提示：「收到 100 元，將充值 100 代幣，請按確認」
       │
[人工按鈕確認] 現場服務員或玩家在平板螢幕點擊【確認入箱】
       │
       ▼
[iHub 平板] POST https://api.tg25.win/api/kiosk/escrow/confirm
       ▼
[Member 後端] 驗證成功，透過 Infra 發布 MQTT: {"command": "stack"}
       ▼
[ESP32 兌幣卡] 透過 RS232 發送壓箱指令至 104U
       │
       ▼
[紙鈔機 104U] 馬達轉動將 100 元壓入防盜保險箱，光耦閉合
       │ 回報 ESP32: bill_stacked
       ▼
[ESP32 兌幣卡] 發布 MQTT: {"event_type": "bill_stacked", "amount": 100}
       ▼
[Member 後端]
       │ 1. 寫入 member_wallets 增加 100 TOKEN (整數)
       │ 2. 寫入 wallet_transactions 審計流水
       │ 3. 結束 kiosk_sessions
```

---

## 6. 流程五：機械碼表脈衝稽核與日結流 (UI3/UI4)

為了杜絕現場人員私自拔線、偷投幣、或作弊器干擾，系統維持獨立的硬體機械碼表稽核流：

```
[實體入幣/出幣機械碼表]
       │
       │ 機台內部每次計數器轉動產生一個方波
       ▼
[ESP32 UI3 (GPIO 13) / UI4 (GPIO 14)]
       │
       │ 硬體 PCNT 自動累計 raw_value (無任何軟體運算阻礙)
       │ 定期 (每 60 秒或累積 50 脈衝) 發布 MQTT event
       ▼
[Infra Listener & Central DB (iotv9)]
       │
       │ 記錄於 iotv9.signal_events，保留原始 raw_value 里程表
       ▼
[日結清算腳本 (Daily Reconciliation Batch)]
       │
       │ 每日凌晨 04:00 自動執行：
       │ 計算：碼表增量 (Delta Meter) = 本日 raw_value 結尾 - 昨日 raw_value 結尾
       │ 計算：開分結算總額 (Total Actual Points) = SUM(actual_points from Webhooks)
       │
       ▼
[比對稽核]
  - 若 (Delta Meter * 換算比例) == Total Actual Points ──> 【綠燈：對帳無誤】
  - 若 (Delta Meter * 換算比例) != Total Actual Points ──> 【紅燈：報警，存在漏帳或偷開分】
```


---

## 7. Webhook 重試機制與死信保護 (Retry Policy & Dead Letter) 【已實作】

SignalHub 針對第三方遊戲商 (如小猴) 實作強韌的重試機制，由 Laravel 隊列 (\`ProcessWebhookDelivery\` Job) 統一調度：

### 7.1 三段式階梯重試時序 (0s, 3s, 6s)
1. **第一次嘗試 (T + 0s)**：採集卡事件抵達後，非同步佇列立即嘗試向第三方 Webhook URL 發送 POST。
2. **第二次嘗試 (T + 3s)**：若遭遇網路逾時 (Timeout > 3s)、HTTP 5xx 錯誤或連線被拒，系統等待 3 秒後觸發第一次重試。
3. **第三次嘗試 (T + 9s)**：若仍未收到正確 HTTP 200 回應，系統再等待 6 秒進行第二次重試。
4. **標記失敗與死信 (Failed / Dead Letter)**：連續 3 次失敗後，該筆派送紀錄標記為 \`status: failed\`，寫入失敗錯誤日誌 (\`error_message\`)，並觸發運維警報。

### 7.2 店主手動批量重試端點
店主或工程師可透過後台介面或 API 針對失敗紀錄進行單筆或批量重試：
- 單筆重試：\`POST /api/v9/signal-hub/deliveries/{id}/retry\`
- 批量重試：\`POST /api/v9/signal-hub/deliveries/batch-retry\`

---

## 8. 端點呼叫範例與 cURL 查驗速查 (API cURL Cheatsheet) 【已驗證】

### 8.1 內部信號寫入端點 (MQTT Listener -> SignalHub)
\`\`\`bash
curl -X POST "https://signal.tg25.win/api/internal/signal/event" \
  -H "Content-Type: application/json" \
  -H "X-Internal-Key: v9-internal-key-2026" \
  -d '{
    "chip_id": "df1e4c4b1105",
    "pin": "UI1",
    "event_type": "credit_in",
    "raw_value": 10582,
    "delta_value": 1,
    "occurred_at": 1725339600
  }'
\`\`\`

### 8.2 異步結算回執端點 (第三方 POS -> SignalHub)
\`\`\`bash
curl -X POST "https://signal.tg25.win/api/v9/signal-hub/callback-ack" \
  -H "Content-Type: application/json" \
  -d '{
    "delivery_id": 982341,
    "status": "success",
    "actual_points": 500
  }'
\`\`\`

### 8.3 遊戲主板分數歸零端點 (遊戲電腦 -> SignalHub)
\`\`\`bash
curl -X POST "https://signal.tg25.win/api/v9/signal-hub/inbound/session-end" \
  -H "Content-Type: application/json" \
  -d '{
    "chip_id": "df1e4c4b1105",
    "event": "session_end",
    "reason": "points_cleared_to_zero",
    "last_played_duration_seconds": 348,
    "occurred_at": "2026-09-24T12:00:00+08:00"
  }'
\`\`\`

<!-- ===== END OF CHATGPT_DATA_FLOW.md ===== -->


<!-- ===== START OF CHATGPT_BUSINESS_LOGIC.md ===== -->

# WAW 業務邏輯、開洗分與清算對帳核心規格 (CHATGPT_BUSINESS_LOGIC.md)

> **文件身分**：WAW 專案業務與清算邏輯深探文件 (專供 ChatGPT 深度解析)  
> **關聯總索引**：`knowledge/CHATGPT_CONTEXT.md` (實體位置: `brains/knowledge/CHATGPT_CONTEXT.md`)  
> **最後校驗日期**：2026-09-24  
> **維護權限**：HQ (協調中心唯一寫入)  
> **狀態標記準則**：【已實作】/【已驗證】/【已設計但尚未實作】/【計畫中】/【未確認】

---

## 1. 核心金流三大不可違背定律 (Core Financial Tenets)

全系統所有業務邏輯、開洗分與資料庫設計，受以下三大基礎定律約束：

### 1.1 定律一：脈衝即真理 (Pulse is Physical Truth) 【已驗證】
- ESP32 邊緣硬體透過光耦與 PCNT 採集的物理脈衝，是全系統**唯一不可篡改的真理依據**。
- 所有在前端螢幕、手機 App 或後台報表看到的「代幣數」、「點數」、「台幣金額」，本質上都是對「物理脈衝」進行換算後的**投影顯示**。
- **儲存原則**：資料庫必須永久保存原始累計脈衝數 (`raw_value`) 與單次變更量 (`delta_value`)。

### 1.2 定律二：代幣必為整數 (Tokens are Integers) 【已驗證】
- 遊藝場會員錢包內的代幣 (`TOKEN`) 與彩票 (`TICKET`) 只能是整數（例如：持有 50 枚代幣，絕對不允許 50.5 枚）。
- **資料庫欄位強制規範**：所有涉及代幣、彩票的資料表欄位，必須使用 `INT` 或 `BIGINT`。
- **紅線禁令**：❌ 絕對嚴禁使用 `DECIMAL(16,2)` 或浮點數存放代幣餘額！

### 1.3 定律三：比例快照留存 (Snapshot Storage) 【已驗證】
- 換算比例（如 `pulse_to_token`, `token_value_twd`）可能會隨時間或場地促銷活動而調整。
- **審計原則**：每一筆開洗分交易或日結快照，必須在寫入時將「當下生效的換算比例」完整保存至交易快照欄位中。日後即使場地換算比例改變，歷史帳目仍可精確還原，杜絕帳務混亂。

---

## 2. 開洗分業務邏輯矩陣 (Credit In & Credit Out)

如前所述，電腦型聯網機台與傳統單機在開洗分邏輯上存在本質差別：

### 2.1 電腦型聯網機台開洗分 (SignalHub 模式) 【已實作】
- **開分 (Credit In / UI1)**：
  - **觸發源**：實體按鈕短接（服務員現場操作）。
  - **採集卡職責**：上報 `delta_value: 1` 與 `raw_value`，產生唯一 `delivery_id`。
  - **金額決定方**：**100% 由第三方遊戲伺服器決定**。SignalHub 轉發 Webhook 後，第三方伺服器比對現場 POS 收銀記錄，於回覆中填入實際點數 `actual_points: 500`。
  - **結算寫入**：SignalHub 收到回覆後，將 `actual_points` 寫入 `signal_webhook_deliveries.cleared_points`。
- **洗分 (Credit Out / UI2)**：
  - **觸發源**：實體洗分鍵按下。
  - **採集卡職責**：上報 `delta_value: 1`。
  - **結算流向**：第三方遊戲商回傳玩家在機台上的結算剩餘分數（例如 `actual_points: 3250`），吧台依此金額支付現金或發放彩票。

### 2.2 傳統街機手機掃碼開洗分 (game_v0 模式) 【已設計 / 部份驗證】
- **開分 (Member -> ESP32 OUT1)**：
  - 會員手機扣除 1 代幣。
  - 系統依據場地設定 `pulse_to_token = 0.5` 計算出應給予機台 2 個物理脈衝。
  - Infra 發送 MQTT 指令 `assign_credit`，ESP32 驅動繼電器連發 2 下方波。
- **洗分 (Member -> ESP32 OUT2)**：
  - 玩家在手機上點選「結束遊戲並洗分」。
  - 系統發送 MQTT `settle_credit`，ESP32 觸發機台 PIN_OUT2 洗分按鈕。
  - 機台退幣馬達或退幣計數器啟動，每跳動一下在 UI4 採集到一個反饋脈衝。
  - Member 依據反饋脈衝數，以 1:1 或約定比例將彩票 (`TICKET`) 退還至會員錢包。

---

## 3. 貨幣與代幣體系 (Currency Hierarchy)

在 `waw_member_production.member_wallets` 中支援五種貨幣類型：

| 貨幣代碼 | 貨幣名稱 | 數值型態 | 用途與流向 | 換算基準 |
| :--- | :--- | :--- | :--- | :--- |
| **`CASH`** | 法定現金 | DECIMAL(10,2) | 玩家儲值的新台幣餘額 (TWD) | 1.00 TWD |
| **`TOKEN`** | 遊戲代幣 | **INT (整數)** | 專用於機台開分投幣 | 由場地設定 (例: 10元 = 1枚) |
| **`POINT`** | 活動點數 | INT (整數) | 促銷、簽到贈送點數 | 平台行銷用 |
| **`TICKET`** | 遊戲彩票 | **INT (整數)** | 機台洗分退回或出彩之點數 | 可於櫃檯兌換禮品或回存 |
| **`COIN`** | 實體硬幣 (舊) | INT (整數) | 早期相容欄位，現行流程已凍結 | 歷史記錄 |

---

## 4. 營運分潤、拆帳與訂閱模型 (Revenue Sharing & Subscription)

WAW 2.0 徹底廢除了傳統「機台與場地硬編碼綁定」模式，改為動態部署與分成合約：

### 4.1 三方角色與資產權利
1. **場地擁有者 (Venue Owner / 店主)**：
   - 擁有實體店面 (`venues`)。
   - 負責負擔店面租金、水電、現場吧台人員。
2. **機台擁有者 (Machine Owner / 機主)**：
   - 擁有實體採集卡與機台硬體資產 (`devices`)。
   - 負責機台採購、硬體保養與維修。
3. **平台方 (WAW HQ)**：
   - 提供雲端物聯網通訊、清算對帳平台與運維支持。

### 4.2 營收拆帳計算 (Split Formula)
當機台部署於某場地並產生營收時，依據 `device_deployments` 或分成協議計算：
- **淨營收 (Net Revenue)** = 總開分金額 - 總洗分金額
- **場地主分成** = `Net Revenue * venue_owner_share` (例如 40%)
- **機台主分成** = `Net Revenue * owner_share` (例如 60%)
- 每一筆帳務均記錄於 `device_transactions` 作為每月出帳憑證。

### 4.3 雙重月租訂閱控制 (Dual Subscription Model) 【已設計】
- **場地月租**：每月 NT$ 1,500。解鎖店面營運進階功能（交班系統、LINE 即時警報、全店營收大看板）。
- **機台月租**：每台每月 NT$ 300。
  - **欠費軟性限制 (Soft Restriction)**：若機台主欠繳月租，系統**不切斷**機台的 MQTT 連線與玩家現場開分（避免引起現場客訴糾紛）；但系統會每日自動按日折算月租，累加至機台主之欠款帳單中，並限制其後台提現功能。

---

## 5. 會話生命週期與三層容錯防護 (Session Lifecycle & 3-Layer Protection)

為了防止「玩家開分後未玩即離開」、「惡意佔用機台」或「斷網造成資金卡死」，實作三層會話守護機制：

```
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 1: ESP32 本地活動定時器 (120 秒物理無活動監測)                     │
│  - 韌體內部計時器。機台按鈕每次閉合或搖桿晃動 (PIN_SENSE_ACTIVITY)，      │
│    計時器立即重置為 120 秒。                                            │
│  - 若連續 120 秒無任何硬體信號，韌體自動發布 session_timeout MQTT 封包。 │
├────────────────────────────────────────────────────────────────────────┤
│ Layer 2: 雲端診斷心跳守護 (5 分鐘 Heartbeat)                            │
│  - 採集卡每 5 分鐘主動上報 status 健康診斷包。                          │
│  - 雲端排程每分鐘掃描，若超過 10 分鐘無心跳，標記設備連線異常。          │
├────────────────────────────────────────────────────────────────────────┤
│ Layer 3: MQTT LWT (Last Will and Testament) 瞬斷遺囑                    │
│  - 採集卡於 TCP 握手時向 Mosquitto Broker 註冊遺囑。                    │
│  - 一旦硬體遭惡意拔除電源或斷網，Broker 毫秒級向雲端發布 offline 遺囑。  │
│  - 雲端立即凍結該機台進行中的 session，防止他人盜用。                   │
└────────────────────────────────────────────────────────────────────────┘
```

### 5.1 孤兒分數處置 (Orphan Credit Handling)
- **業務現象**：現場偶有玩家開分後，因突發狀況未洗分直接離場，機台留有剩餘分數。
- **處置方針**：
  - 系統寫入 `device_orphan_logs`。
  - 依據遊藝場實體營運慣例，視為「現場操作遺留」，系統記錄稽核但不予補償，下位玩家投幣或服務員洗分時將作為日結沖銷依據。

---

## 6. 資料遺失防範與異常偵測 (Fault Tolerance & Anti-Fraud)

### 6.1 斷網零漏失：里程表差值算法 (Odometer Delta Algorithm)
傳統系統若斷網，中途發生的投幣事件全部丟失。WAW 採集卡採用類似汽車機械里程表的 `raw_value`：
- 斷網期間，硬體 PCNT 持續計數，累加 `raw_value`。
- 恢復連線後，上報當前最新 `raw_value`。
- 後端演算法：
  ```
  遺漏補償脈衝數 (Lost Pulses) = 當前 raw_value - 資料庫最後記錄 raw_value
  ```
- 後端一次性將補償脈衝寫入日誌，完美保障總帳零誤差。

### 6.2 冪等性防重複結算 (Idempotency Key)
- 每一筆採集卡事件附帶全域唯一自增之 `delivery_id` (6 碼以上數字)。
- 後端資料庫在 `signal_webhook_deliveries` 對 `delivery_id` 設置 `UNIQUE` 索引。
- 重複抵達的 Webhook 重試封包將被直接識別並回傳現有結算結果，杜絕重複加分或重複扣款。

### 6.3 密鑰驗簽與重放攻擊防護 (HMAC-SHA256 Anti-Replay)
- 所有第三方 Webhook 包含 `X-WAW-Signature` 與 `occurred_at` 時間戳。
- 接收端必須校驗時間戳誤差在 300 秒（5 分鐘）以內，超過則視為無效過期請求。
- 雜湊簽名由伺服器與第三方各自計算並進行常數時間比對 (`hash_equals`)，阻絕中間人竄改 (Tampering)。


---

## 7. 核心資料庫結構規格 (Database DDL Specifications) 【已驗證】

### 7.1 場地表 (\`iotv9.venues\`)
\`\`\`sql
CREATE TABLE \`venues\` (
  \`id\` bigint unsigned NOT NULL AUTO_INCREMENT,
  \`name\` varchar(191) NOT NULL COMMENT '場地/店面名稱',
  \`address\` varchar(191) DEFAULT NULL COMMENT '實體地址',
  \`token_value_twd\` decimal(8,2) NOT NULL DEFAULT '10.00' COMMENT '每枚代幣對應新台幣價值',
  \`owner_id\` bigint unsigned NOT NULL COMMENT '場地所有人 users.id',
  \`subscription_status\` enum('active','arrears','expired') NOT NULL DEFAULT 'active',
  \`subscription_expires_at\` datetime DEFAULT NULL,
  \`created_at\` timestamp NULL DEFAULT NULL,
  \`updated_at\` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (\`id\`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
\`\`\`

### 7.2 設備資產表 (\`iotv9.devices\`)
\`\`\`sql
CREATE TABLE \`devices\` (
  \`id\` bigint unsigned NOT NULL AUTO_INCREMENT,
  \`chip_id\` varchar(32) NOT NULL COMMENT '12碼十六進位 MAC (例: df1e4c4b1105)',
  \`node_id\` varchar(32) DEFAULT NULL COMMENT '產品編號 (例: device_001)',
  \`venue_id\` bigint unsigned DEFAULT NULL COMMENT '當前部署場地',
  \`owner_id\` bigint unsigned DEFAULT NULL COMMENT '機台擁有者 users.id',
  \`status\` enum('active','offline','maintenance') NOT NULL DEFAULT 'offline',
  \`last_seen_at\` datetime DEFAULT NULL,
  \`created_at\` timestamp NULL DEFAULT NULL,
  \`updated_at\` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (\`id\`),
  UNIQUE KEY \`uniq_chip_id\` (\`chip_id\`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
\`\`\`

### 7.3 信號派送審計表 (\`iotv9.signal_webhook_deliveries\`)
\`\`\`sql
CREATE TABLE \`signal_webhook_deliveries\` (
  \`id\` bigint unsigned NOT NULL AUTO_INCREMENT,
  \`delivery_id\` bigint unsigned NOT NULL COMMENT '全域唯一自增序號',
  \`device_id\` bigint unsigned NOT NULL,
  \`profile_id\` bigint unsigned NOT NULL,
  \`event_type\` varchar(32) NOT NULL COMMENT 'credit_in, credit_out 等',
  \`pin_code\` varchar(16) NOT NULL COMMENT 'UI1 ~ UI4',
  \`raw_value\` bigint unsigned NOT NULL COMMENT '硬體累計脈衝里程表',
  \`delta_value\` int unsigned NOT NULL DEFAULT '1',
  \`cleared_points\` bigint DEFAULT NULL COMMENT '實際結算點數 (同 actual_points)',
  \`status\` enum('pending','success','failed') NOT NULL DEFAULT 'pending',
  \`retry_count\` tinyint unsigned NOT NULL DEFAULT '0',
  \`occurred_at\` datetime NOT NULL,
  \`created_at\` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (\`id\`),
  UNIQUE KEY \`uniq_delivery_id\` (\`delivery_id\`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
\`\`\`

### 7.4 會員錢包表 (\`waw_member_production.member_wallets\`)
\`\`\`sql
CREATE TABLE \`member_wallets\` (
  \`id\` bigint unsigned NOT NULL AUTO_INCREMENT,
  \`member_id\` bigint unsigned NOT NULL,
  \`currency_type\` enum('CASH','TOKEN','POINT','TICKET','COIN') NOT NULL,
  \`balance\` bigint NOT NULL DEFAULT '0' COMMENT '代幣/彩票強制整數 INT',
  \`frozen_balance\` bigint NOT NULL DEFAULT '0' COMMENT '開分中凍結餘額',
  \`created_at\` timestamp NULL DEFAULT NULL,
  \`updated_at\` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (\`id\`),
  UNIQUE KEY \`uniq_member_currency\` (\`member_id\`,\`currency_type\`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
\`\`\`

<!-- ===== END OF CHATGPT_BUSINESS_LOGIC.md ===== -->


<!-- ===== START OF CHATGPT_ISSUES.md ===== -->

# WAW 專案技術債、文檔矛盾、已知問題與風險禁忌 (CHATGPT_ISSUES.md)

> **文件身分**：WAW 專案問題、矛盾與風控深探文件 (專供 ChatGPT 深度解析)  
> **關聯總索引**：`knowledge/CHATGPT_CONTEXT.md` (實體位置: `brains/knowledge/CHATGPT_CONTEXT.md`)  
> **最後校驗日期**：2026-09-24  
> **維護權限**：HQ (協調中心唯一寫入)  
> **狀態標記準則**：【已實作】/【已驗證】/【已設計但尚未實作】/【計畫中】/【未確認】

---

## 1. 跨文檔與跨 Agent 現存矛盾對照表 (CRITICAL DISCREPANCIES)

在閱讀 `brains/knowledge/` 與各 Agent 歷史專案文檔時，存在數處文檔衝突。**此處直接列出客觀事實與衝突來源，請勿自行腦補或妄下定論**：

### 1.1 矛盾一：機台編號 (`machine_number` / `machine_name`) 的去留
- **舊規格文檔**：
  - `02_technical_standards/SIGNAL_WEBHOOK_AND_SERIAL_STANDARD_v2.md`
  - `03_system_architecture/SIGNALHUB_HARDWARE_WEBHOOK_INTEGRATION_SPEC_v2.md`
  - *內容*：規格中定義 Serial JSON 與 Webhook Payload 必須包含 `machine_number` 與 `machine_name`。
- **權威決策文檔**：
  - `05_business_flows/DECISION_REMOVE_MACHINE_NUMBER_2026-09-04.md`
  - *內容*：2026-09-04 由 HQ + Joe 拍板**徹底廢除**該欄位！硬體只負責識別我是誰 (`chip_id`)，不得在韌體維護業務名稱。
- **代碼現況**：
  - Coli 韌體 (`IOTwawS3` v1.0.28 / v2.0.5) 與 Sidney 後台已移除此欄位。
- **ChatGPT 易踩雷區**：嚴禁建議在韌體或 Webhook 中重新加回 `machine_number`！

---

### 1.2 矛盾二：晶片識別碼 (`chip_id`) 的大小寫規範
- **文檔 A**：`brains/knowledge/NAMING_AUTHORITY.md`
  - *規範*：12 位**小寫**十六進位無冒號字串（例如 `df1e4c4b1105`），資料庫主鍵與 API 參數均為小寫。
- **文檔 B**：`02_technical_standards/MQTT_TOPIC_STANDARD.md` (v2.1.0 第 3.1 節)
  - *規範*：MQTT 主題中的 `{chip_id}` 強制規定為 12 位**大寫**十六進位（例如 `C8F09E1A2B3C`）。
- **當前代碼狀態**：
  - 韌體在發布 MQTT 時轉為大寫，但在資料庫存儲與 Web API 中多保留小寫。
- **處置建議**：後端系統在接收或比對 `chip_id` 時，必須強制透過 `strtolower()` 或不區分大小寫進行正規化比對。

---

### 1.3 矛盾三：兌幣機識別碼 (`node_id`) 大小寫
- **文檔 A**：`02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md`
  - *內容*：曾誤寫為大寫 `KIOSK_001`。
- **文檔 B**：`NAMING_AUTHORITY.md` (第 2.1 節)
  - *內容*：明確標記文檔 A 為錯誤，實際 DB (`iotv9.kiosks`) 與標準一律為**全小寫** `kiosk_001`。

---

### 1.4 矛盾四：結算點數名稱 (`actual_points` vs `cleared_points`)
- **外部文檔**：給合作夥伴（小猴）的文件規定回傳 `actual_points`。
- **內部資料庫**：`signal_webhook_deliveries` 資料表歷史欄位為 `cleared_points`。
- **韌體端**：`PROJECT/IOTwawS3/src/modules/usb_cdc_comm.c` 目前解析之 JSON 欄位為 `cleared_points`。
- **解決現況**：Sidney 在 `SignalWebhookDelivery.php` 建立了 Accessor/Mutator 雙向映射，並在 `CallbackAckController.php` 中同時兼容 `actual_points` 與 `cleared_points`。

---

### 1.5 矛盾五：場地命名 (`venue` vs `store`)
- **文檔 A**：`03_system_architecture/WAW_2.0_ARCHITECTURE_SPEC.md` (早期草案)
  - *內容*：使用 `stores` 表與 `store_id` 欄位。
- **文檔 B**：`NAMING_AUTHORITY.md` (Phase 1 統一命名規範)
  - *內容*：正式廢除 `store`，全系統一律統一為 **`venue`**，實體表為 `iotv9.venues`，外鍵為 `venue_id`。

---

### 1.6 矛盾六：設備命名 (`device` vs `machine`)
- **文檔 A**：`WAW_2.0_ARCHITECTURE_SPEC.md`
  - *內容*：使用 `machines` 表。
- **文檔 B**：`NAMING_AUTHORITY.md` (Phase 1 規範)
  - *內容*：Phase 1 期間一律命名為 **`device`** (`iotv9.devices`)，關聯表為 `device_deployments`。待未來 Phase 2 大遷移時才會升級為 `machine`。

---

### 1.7 矛盾七：MQTT Broker 位址漂移與 Cloudflare 穿透 (direct-mqtt vs mqtt) 【重度文檔過時證物】
- **代碼實況與真相 (Ground Truth)**：
  - **IOTwawS3 (Coli v2.0.5)**: PROJECT/IOTwawS3/src/services/mqtt_service.c 第 165 行明確寫死：
    snprintf(broker_uri, sizeof(broker_uri), "mqtts://direct-mqtt.tg25.win:8883");
    platformio.ini 亦編譯 -DMQTT_BROKER_HOST=\"direct-mqtt.tg25.win\".
  - **SignalHub (Sidney)**: PROJECT/SignalHub/config/services.php 第 59 行預設為：
    'broker' => env('MQTT_BROKER', 'direct-mqtt.tg25.win').
- **過時殘留代碼 (技術債)**：
  - **IOTkiosk_v0 (Fio v1.5.4)**: PROJECT/IOTkiosk_v0/src/services/mqtt_service.c 第 181 行仍殘留舊代碼：
    .address.uri = "mqtts://mqtt.tg25.win:8883".
- **大面積文檔過時 (Documentation Drift)**：
  - brains/knowledge/04_deployment_operations/INFRASTRUCTURE_REFERENCE.md、SYSTEM_ENTRYPOINTS_AND_DOMAINS.md、MQTT_LISTENER_README.md 等歷史文檔，通篇寫為 mqtt.tg25.win:8883。
- **底層技術原因**：
  - mqtt.tg25.win 啟用了 Cloudflare CDN 橘色雲朵代理。Cloudflare 標準代理僅放行 HTTP/HTTPS/WebSocket (Port 443 等)，會直接阻斷或丟棄未經過 Spectrum 的純 TCP MQTTS (Port 8883) 流量！
  - 為了讓 ESP32 實體硬體與後端能直連 Oracle Cloud VPS (infra, 141.148.165.50)，9 月起正式啟用未經 CDN 代理的灰雲直連域名 direct-mqtt.tg25.win。
  - 舊域名 mqtt.tg25.win 目前僅能用於瀏覽器端網頁終端的 WebSocket 轉發 (wss://mqtt.tg25.win/mqtt-ws/)。
- **給 ChatGPT 的重大啟示**：brains/knowledge/ 中 2026-08 以前的舊文檔存在嚴重漂移。凡遇域名與硬體通訊，必須以 direct-mqtt.tg25.win 為唯一真理，不可信任舊文檔的 mqtt.tg25.win:8883！

---

## 2. 目前軟體各模組狀態盤點 (Software Status Matrix)

| 專案目錄 | 負責 Agent | 當前狀態 | 已完成核心模組 | 測試中模組 | 未完成 / 規劃中模組 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Owner** | Sophie | 運行中 | M1 登入、M2 儀表板、M3 設備列表、M4 場地管理、信號設定入口選單 | 訂閱月租出帳自動化、多角色權限細分 | 自動生成月結報表、LINE 官方警報發送 |
| **SignalHub** | Sidney | 核心就緒 | 4 大核心頁面、腳位映射、日結規則、Webhook 派送重試、小猴 Mock 測試 | 端對端實際機台連動、動態 IP 簽名校驗 | 第三方開發者平台 (API Key 申請與計費) |
| **Member** | Mina | 運行中 | 會員登入、錢包餘額、掃碼開分、交易日誌 | 即時退幣彩票入帳 | 多幣種即時兌換、社群活動模組 |
| **Infra** | Ina | 運行中 | `iotv9` Central DB 維護、MQTT Broker (Mosquitto TLS)、內部 API 橋接 | MQTT Listener 高併發壓測 | DB 自動雙向備份與災難復原演練 |
| **Alliance** | Allie | 運行中 | 採集卡設備配對、韌體出貨燒錄進度、QR Code 標籤列印 | 批次出貨異常捕獲 | 代理商獨立分銷與對帳系統 |
| **iHub** | Hubie | 運行中 | Android 工控 APK、QR Code 動態展示、Escrow 暫存人工確認 | 斷網本地快取離線展示 | 平板本機自動 OTA 更新 |
| **IOTwawS3** | Coli | 穩定版 | PCNT 脈衝計數、極性自適應、USB CDC 串列雙軌輸出、母機 WiFi 同步 | 長期高頻抗干擾穩定度 | 移除 WAW 業務之純開源版本韌體 |
| **IOTkiosk_v0** | Fio | 穩定版 | ICT 104U RS232 通訊、Escrow 狀態機、母機配網廣播服務 | 新版紙鈔機協定相容 | 多國貨幣紙鈔機自動識別 |

---

## 3. 已知技術債與凍結區 (Technical Debts & Freezes)

1. **Alliance `burning.blade.php` 代碼凍結** 【絕對紅線】：
   - `PROJECT/Alliance` 中負責燒錄配對與 QR 標籤的 `burning.blade.php` 邏輯極為複雜脆弱。
   - **Joe 最高指示**：**凍結該檔案的重構拆分**，嚴禁任何 Agent 私自重構或拆除該檔案。
2. **遠端 PHP Redis 擴展缺失**：
   - 部分 Oracle VPS 上的 PHP CLI 未編譯原生 Redis 擴展，導致執行特定 Artisan 指令時出現 `Class "Redis" not found`。解決方式：使用 `predis` 或確保使用標準 cache store。
3. **MQTT Broker 雙位址問題**：
   - 歷史專案中同時存在 `mqtt.tg25.win` 與 `direct-mqtt.tg25.win`，未來需統一指向同一 Broker 負載均衡器。
4. **遠端 `fileinfo` 擴展警報**：
   - 遠端 Laravel 部署時曾出現 `fileinfo` 擴展警告，雖不影響核心 API 運作，但需列入環境維護排程。

---

## 4. 給 ChatGPT 的核心紅線與避坑指南 (CRITICAL PITFALLS FOR CHATGPT)

如果另一個 AI (ChatGPT) 參與 WAW 專案開發，**最容易因常識推論而提出致命錯誤建議**。以下為絕對紅線：

1. ❌ **禁止建議在本地執行任何測試、構建或 DB 遷移**：
   - 錯誤建議：「請在本地執行 `php artisan migrate` 或 `pnpm run build`」。
   - 真相：WAW 本地純為 Git 代碼庫，無本地資料庫與 Node 編譯環境，所有驗證必須透過 `waw_ops.sh` 在遠端 VPS 執行。
2. ❌ **禁止將 PC-Based 電腦遊戲機的開分按鈕當作脈衝計算金額**：
   - 錯誤建議：「UI1 按鈕按下時，將 delta 乘上 pulse_ratio 得到加分金額」。
   - 真相：UI1 只是通知事件 (delta=1)，點數 100% 由第三方遊戲伺服器在 Webhook 回覆中提供！
3. ❌ **禁止建議用 Raw IP 或 Port 22 連線 VPS**：
   - 錯誤建議：「請使用 `ssh ubuntu@129.153.116.174`」。
   - 真相：全域端口為 **39022**，且強制使用 SSH 別名 (`ssh yd174`)。
4. ❌ **禁止在資料庫或代碼中加入 `machine_number`**：
   - 真相：2026-09-04 已全面刪除該概念，所有設備層只認 `chip_id`。
5. ❌ **禁止使用小數 (Float/Decimal) 儲存代幣與彩票**：
   - 真相：所有代幣與彩票餘額必須為整數 (`INT`)。

<!-- ===== END OF CHATGPT_ISSUES.md ===== -->