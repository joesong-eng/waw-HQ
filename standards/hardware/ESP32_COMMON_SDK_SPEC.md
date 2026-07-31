# ESP32 共用核心 SDK (wawIoT-Core SDK) 技術規格與分工標準

> **文件版本**：v1.0  
> **建立日期**：2026-05-31  
> **制定者**：HQ（多 Agent 協調中心）  
> **適用範圍**：IOTwawS3 (game_v0) 與 IOTkiosk_v0 (kiosk_v0) 韌體開發

---

## 壹、 背景與目的

為了降低 wawIoT 系統的大規模部署成本，並確保遊藝場現場不同機台設備之間的互聯互通，本專案旗下兩款基於 **ESP32-S3** 的硬體通訊卡：
1. **IOTwawS3**（遊戲機採集控制卡，由 Coli 主導開發）
2. **IOTkiosk_v0**（兌幣紙鈔機控制卡，由 Fio 主導開發）

將全面採用 **「統一核心底座 (Base) + 專屬業務功能 (Plus)」** 的雙層架構。相同且通用的基礎模組（傳染式配網、MQTT TLS 安全通訊、OTA 分區升級）將封裝為一個共用的核心 SDK（暫稱 `wawIoT-Core SDK`），僅計算一次開發成本，由兩位韌體 Agent 協作開發並共享，以最大化節省預算並確保現場通訊協議的 100% 相容性。

---

## 貳、 雙層架構設計

```mermaid
graph TD
    subgraph Shared Core Layer [共用核心底座 - wawIoT-Core SDK]
        A[Wi-Fi Manager & 傳染式配網] --> B[MQTT TLS 安全通訊]
        B --> C[OTA 自動升級與防變磚機制]
        C --> D[統一 NVS 存取與日誌管理]
    end

    subgraph Specific Plus Layer [各自專屬 PLUS 功能]
        E["IOTwawS3 (Coli)<br>+ 高頻脈衝採集 (UI1/UI2)<br>+ 毫秒級安全脈衝輸出 (Pulse)<br>+ 機台狀態監測"]
        F["IOTkiosk_v0 (Fio)<br>+ RS232 紙鈔機通訊協議<br>+ ba_state 交易狀態機與斷電保護<br>+ 離線收鈔與交易記錄緩衝"]
    end

    Shared Core Layer --> E
    Shared Core Layer --> F
```

---

## 參、 共享核心模組規格 (The "Base")

### 1. Wi-Fi Manager & 傳染式配網 (Mesh-like Provisioning)
解決大型場域（如遊樂場）上百台設備手動配網繁瑣的痛點。

*   **基礎 Wi-Fi 連線**：支援 WPA2/WPA3 個人版安全模式，具備自動斷線重連與 AP 掃描機制。
*   **子機模式 (Sub-node Mode)**：
    *   設備上電後，若偵測無 Wi-Fi 網路或連網失敗達 **5 次**，自動切換為「子機配網模式」。
    *   啟動專屬的廣播監聽（基於 ESP-NOW 或 UDP Multicast），等待母機廣播配網憑證。
*   **母機傳染模式 (Master Broadcast Mode)**：
    *   已成功連網的設備作為「母機」。母機連網成功後的 **前 15 分鐘**，或經由特定實體按鍵觸發後，自動進入廣播狀態。
    *   母機將目前儲存的 SSID 與 Password 進行加密後廣播，自動「感染」周遭處於子機配網模式的設備。
*   **傳輸安全規範**：
    *   廣播憑證**嚴禁明文傳輸**。
    *   必須實作基於預共享金鑰（Pre-Shared Key）的 **AES-128-GCM 加密加密通道**，並包含時間戳與 Random Nonce 以防止重放攻擊（Replay Attack）與憑證側錄。

### 2. MQTT TLS 安全通訊與保活機制
*   **安全加密**：全面基於 MbedTLS 實作 TLSv1.2/v1.3 加密連線，使用憑證雙向驗證（Client Certificate & Server CA）。
*   **保活機制**：MQTT Keep-Alive 設為 **120 秒**。實作優雅的 Last Will (遺言主題) 以即時回報設備非正常離線狀態。
*   **心跳與診斷**：標準化上報心跳包（每 5 分鐘一次），回報系統 Uptime、Free Heap 及 WiFi RSSI，主題規格嚴格遵守 [02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md](file:///Users/ilawusong/Documents/sysWawIot/HQ/brains/knowledge/02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md)。
*   **連線狀態機**：統一實作「退避重試（Exponential Backoff）」機制，在連線失敗時遞增等待時間（例如 1s, 2s, 4s, 8s... 最大至 60s），避免因伺服器重啟造成大量設備瞬間重連的 DDoS 效應。

### 3. OTA 自動升級與 NVS 分區保護
*   **安全分區 (Partition Table)**：
    *   統一採用雙分區架構：`ota_0` (App) 與 `ota_1` (App)，以及專屬的 `nvs` 存取分區和憑證儲存分區。
*   **OTA 自動更新**：
    *   背景異步檢查與下載，在不干擾設備前端運行的情況下完成韌體傳輸。
    *   檢驗下載包之 MD5/SHA256 數位簽章，確保韌體來源合法。
*   **防變磚回滾 (Rollback Mechanism)**：
    *   新韌體寫入重啟後，必須在 **60 秒內** 成功連上 MQTT Broker 並發送診斷心跳，否則 Bootloader 判定該版本異常，自動回滾至上一正常執行版本。

---

## 肆、 專屬 PLUS 業務模組規格 (The "Plus")

### 1. IOTwawS3 遊戲採集控制卡 (Coli 負責)
*   **高頻訊號採集 (Sense)**：UI1 (入金)、UI2 (出金) 高頻脈衝硬體中斷捕捉，結合軟體防抖演算法（Debounce Filter），避免馬達雜訊引發的錯帳。
*   **訊號極性自適應 (Adaptation)**：支援開機自動偵測靜止電位（500ms 延遲 + 5次取樣防呆），並支援透過 MQTT `set_signal_polarity` 遠端覆寫與 NVS 持久化，以適配 active_high/low 不同極性主板。
*   **指令輸出控制 (Pulse)**：接收雲端/本機下行命令後，輸出毫秒級開洗分脈衝，並包含實體 Watchdog 超時斷開安全防呆機制。
*   **狀態監測 (Sense/Fault)**：獨立擺錘防搖晃偵測與故障警報腳位監聽。

### 2. IOTkiosk_v0 兌幣紙鈔控制卡 (Fio 負責)
*   **紙鈔機 RS232 通訊控制**：基於 UART 實作標準紙鈔機協議（含 Checksum 驗證）。
*   **交易交易狀態機 (ba_state)**：精密維護紙鈔暫存確認 (ESCROW)、進鈔、退鈔、卡鈔及錢箱滿狀態。
*   **斷電保護與狀態保存**：利用 ESP32 的 NVS 或 RTC 記憶體，在進鈔中間狀態遇上異常斷電時，重啟後能安全恢復前次狀態或退鈔，絕不容許吃錢/錯帳。
*   **離線金流緩衝**：在斷網狀態下，允許離線收鈔，並於網路恢復後按時間戳補發事件（QoS 2 保證送達）。

---

## 伍、 開發與分工落實方案

### 1. 職責與協作劃分

為了節省費用並發揮最大綜效，核心底座模組將採用 **「一人主導、共同驗收、降價共享」** 的模式：

*   **核心 SDK (Base) 主導開發者**：**Coli**
    *   Coli 負責實作 `wawIoT-Core SDK`（包含傳染式配網、MQTT TLS、OTA 保全）。
    *   提供乾淨的 C API/介面，供 Fio 接入。
*   **SDK 整合與 PLUS 開發者**：**Fio**
    *   Fio 負責審查核心 SDK 的介面，並將其引進 `IOTkiosk_v0` 專案中。
    *   Fio 專注於開發其極具難度的「RS232 紙鈔機狀態機、離線金流快取與斷電保護功能」。
*   **協調與規範監督**：**HQ**
    *   HQ 負責制定 ESP-NOW 廣播配網的加密協議格式、密鑰發放管理，並為雙方整合提供測試憑證與 MQTT 標準主題定義。

### 2. 開發預算調整方案

基於共用核心一次性開發費用的原則，調整後的商務架構建議如下：

| 專案 / 模組 | 原報價 (TWD) | 調整後報價 (TWD) | 調整說明 |
| :--- | :--- | :--- | :--- |
| **Coli (IOTwawS3)** | $125,000 | **$125,000** | 維持不變。包含：共用 `wawIoT-Core SDK` 開發費 ($65,000) 及遊戲卡專屬 PLUS 開發費 ($60,000)。 |
| **Fio (IOTkiosk_v0)** | $180,000 | **$135,000** | **省下 $45,000 TWD**。扣除重疊的底層 Wi-Fi、MQTT 與 OTA 重複開發成本，僅保留 RS232 控制、斷電保護、極端壓力測試與核心 SDK 整合費用。 |
| **總預算** | **$305,000** | **$260,000** | **為業主實質節省 $45,000 元整 (15% 預算降幅)**，且獲得統一的高整合度系統！ |

---

## 🔗 文件神經連結

### 強關聯（必讀）
> 開發 `wawIoT-Core SDK` 或整合至各自專案前，必須先閱讀以下文件
- [02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md](file:///Users/ilawusong/Documents/sysWawIot/HQ/brains/knowledge/02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md) - 心跳診斷與事件上報的 Topic 命名規範
- [05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md](file:///Users/ilawusong/Documents/sysWawIot/HQ/brains/knowledge/05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md) - 兌幣卡紙鈔機控制模組的詳細業務流程與時間戳防錯

### 中關聯（建議讀）
> 了解硬體接口對應與網路佈局
- [hardware_pulse_mapping.md](file:///Users/ilawusong/Documents/sysWawIot/HQ/brains/knowledge/02_protocols_and_standards/HARDWARE_PULSE_MAPPING.md) - 遊戲卡數位 I/O 對應規格

### 排除混淆
> 與底層通訊架構無關的應用層邏輯
- [05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md](file:///Users/ilawusong/Documents/sysWawIot/HQ/brains/knowledge/05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md) - 雖然也是兌幣業務，但屬於上層伺服器與玩家前端的 API 調用，非韌體底層 SDK 設計範疇

---

*制定者：HQ | 版本：1.0 | 最後更新：2026-05-31*
