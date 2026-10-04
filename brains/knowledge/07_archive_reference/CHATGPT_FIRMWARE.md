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
