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
