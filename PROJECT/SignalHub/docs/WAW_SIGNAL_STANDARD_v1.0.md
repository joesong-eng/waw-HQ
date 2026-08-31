# WAW ESP32 信號採集開放標準規格書 (v1.0)

- **標準名稱**：WAW IoT Universal Signal Standard (WAW-USS)
- **版本編號**：v1.0
- **標準維護機構**：WAW 標準局（SignalHub / Sidney）
- **發布日期**：2026-08-31
- **適用範圍**：所有接入 WAW 體系之 ESP32-S3 / ESP32 採集板、IoT 韌體、第三方相容硬體

---

## 1. 核心哲學與定位

1. **WAW 是標準不是應用**：WAW 信號採集層不對具體產業做任何業務假設（不論是夾娃娃機、自動販賣機、洗車機、充電樁、門禁系統、農業感測器等）。
2. **Layer 0 信號接入標準**：定義硬體採集介面、信號傳輸協定、累計里程表機制，提供高可靠、抗斷網、自帶防重放與補償機制的通用信號層。
3. **向下相容原則**：本規格書所定義之硬體腳位編號、MQTT Topic 與 JSON Payload 格式一旦發布，未經標準局核准不得做破壞性修改。

---

## 2. 8 腳位硬體通道標準 (Hardware Pin Standard)

採集卡提供 8 組標準通用通道（Universal Channels）：4 組輸入通道 (UI1~UI4) 與 4 組輸出通道 (UO1~UO4)。

| 腳位代碼 | 方向 (Direction) | 預設硬體電氣特性 | 推薦用途 | 信號模式支援 |
| :--- | :--- | :--- | :--- | :--- |
| **UI1** | Input (輸入) | 光耦隔離 / PCNT 硬體脈衝計數器 | 核心計數 / 投幣 / 脈衝輸入 | Counter (里程表), Toggle, Event |
| **UI2** | Input (輸入) | 光耦隔離 / PCNT 硬體脈衝計數器 | 次要計數 / 出貨 / 退幣 | Counter (里程表), Toggle, Event |
| **UI3** | Input (輸入) | 光耦隔離 / GPIO 中斷 | 狀態感測 / 警報 / 開門開箱 | Toggle, Event, Counter |
| **UI4** | Input (輸入) | 光耦隔離 / GPIO 中斷 | 輔助感測 / 故障回報 / 模式開關 | Toggle, Event, Counter |
| **UO1** | Output (輸出) | 繼電器 / 達林頓開路輸出 (Open Drain) | 投幣致能 / 核心控制 | Pulse Output, Level Output |
| **UO2** | Output (輸出) | 繼電器 / 達林頓開路輸出 (Open Drain) | 出幣控制 / 啟動開關 | Pulse Output, Level Output |
| **UO3** | Output (輸出) | MOS / 繼電器輸出 | 燈光 / 警報蜂鳴器 / 狀態指示 | Pulse Output, Level Output |
| **UO4** | Output (輸出) | MOS / 繼電器輸出 | 預留控制輸出 | Pulse Output, Level Output |

### 2.1 腳位代碼規範
- 系統內部與 API 嚴格採用大小寫敏感代碼：UI1, UI2, UI3, UI4, UO1, UO2, UO3, UO4。
- 腳位自訂意義（如：UI1 = "總投幣金額", pulse_ratio = 10）由雲端平台 **Signal Profile (信號設定檔)** 定義，韌體端僅負責忠實上報原始通道數據。

---

## 3. PCNT 硬體計數與里程表機制 (Cumulative Meter Mode)

為徹底解決「設備斷網期間脈衝丟失」與「網路重傳導致重複計費」問題，WAW 全面強制採用 **車輛里程表 (Odometer) 累計模式**。

### 3.1 工作原理
1. **硬體級計數**：ESP32 內部啟用硬體脈衝計數器模組 (PCNT - Pulse Counter)，不受 CPU 負載或 FreeRTOS 排程影響，微秒級脈衝精準捕捉。
2. **單調遞增累計值 (Monotonic Cumulative Counter)**：
   - 韌體內部對每個輸入通道維護一個 64 位元無符號整數累計值 raw_value。
   - 上報時**永不上報單次脈衝數（Delta）**，而是上報**當前總累計計數值**。
3. **雲端增量結算 (Cloud-side Delta Calculation)**：
   - 雲端收到事件流水時，計算公式：
     delta_value = current_raw_value - last_raw_value
   - 若發生斷網重連，韌體恢復連線後上報最新累計值，雲端自動一筆結算斷網期間所累積之所有增量，絕不漏算。
4. **溢位與重置保護**：
   - 64 位元累計值足以支撐數萬年連續運轉。
   - 若偵測到設備被人工手動清零或韌體重刷（current_raw_value < last_raw_value），雲端自動記錄異常校準事件（Calibration Reset），並以新基準點重新累計。

---

## 4. MQTT 傳輸協定規範 (MQTT Protocol Standard)

### 4.1 Broker 連線與安全性
- **Broker 位址**：由 Infra (Ina) 統一配置，支援 TLS (Port 8883) 與 TCP (Port 1883)。
- **Client ID**：waw-esp32-{chip_id}（例：waw-esp32-C8F09E1A2B3C）。
- **遺囑消息 (LWT - Last Will and Testament)**：
  - Topic: waw/v1/{site_id}/signal/{chip_id}/status
  - Payload: {"status": "offline", "timestamp": 1725088800}
  - Retain: true, QoS: 1

### 4.2 MQTT Topic 結構

根據 WAW 全域標準規範，SignalHub 主題路徑定義如下：

```
waw/v1/{site_id}/signal/{chip_id}/{action}
```

| Action | 方向 | QoS | 說明 |
| :--- | :--- | :--- | :--- |
| **event** | ESP32 -> 雲端 | 1 | 信號累計值與變更事件上報（即時/定期） |
| **status** | ESP32 -> 雲端 | 1 | 設備健康度、上線/離線心跳 (Heartbeat) |
| **cmd** | 雲端 -> ESP32 | 1 | 遠端控制指令（如驅動 UO 輸出、重設採集頻率） |
| **ack** | ESP32 -> 雲端 | 1 | 指令執行回執與結果 |

---

## 5. JSON Payload 格式標準

### 5.1 信號事件上報 (action = event)
- **Topic**：waw/v1/{site_id}/signal/{chip_id}/event
- **上報時機**：
  1. 門檻觸發：任一 UI 累計值增加時立即發送。
  2. 定期心跳上報：無事件時每 60 秒同步一次當前全通道里程表快照。

```json
{
  "version": "1.0",
  "chip_id": "C8F09E1A2B3C",
  "device_id": 1024,
  "msg_id": "msg-20260831-000189",
  "timestamp": 1725088800123,
  "signals": {
    "UI1": {
      "raw_value": 15280,
      "mode": "counter",
      "state": 1
    },
    "UI2": {
      "raw_value": 305,
      "mode": "counter",
      "state": 0
    },
    "UI3": {
      "raw_value": 12,
      "mode": "toggle",
      "state": 1
    },
    "UI4": {
      "raw_value": 0,
      "mode": "event",
      "state": 0
    },
    "UO1": {
      "state": 0
    },
    "UO2": {
      "state": 0
    },
    "UO3": {
      "state": 1
    },
    "UO4": {
      "state": 0
    }
  }
}
```

### 5.2 欄位定義說明
- version (string, required): 協定版本，固定為 "1.0"。
- chip_id (string, required): ESP32 晶片 MAC / 唯一識別碼（12 位大寫十六進位字元）。
- device_id (integer, optional): 平台指派之設備 ID。
- msg_id (string, required): 訊息唯一識別碼（用於防重放與端對端去重）。
- timestamp (integer, required): Unix Epoch 毫秒級時間戳 (13 位整數)。
- signals (object, required): 通道物件，包含 UI1 ~ UI4 與 UO1 ~ UO4。
  - raw_value (int64): 該輸入腳位自上電或總歷史之單調累計計數值。
  - mode (string): 當前通道工作模式（counter / toggle / event / value）。
  - state (integer): 當前腳位即時電位狀態（0 為 Low，1 為 High）。

---

## 6. 雲端處理與入庫保證
1. **Infra (Ina) 入庫**：MQTT Broker 接收到 event 後，由後端背景 Daemon 寫入 signal_events 資料表。
2. **增量運算**：
   - 依據 chip_id + pin_code 撈取上一筆最新 raw_value。
   - 計算 delta_value = current_raw_value - last_raw_value。
   - 根據綁定的 signal_pin_mappings.pulse_ratio 計算 converted_value = delta_value * pulse_ratio。
3. **Webhook 廣播**：若該店主配置有 signal_webhooks，觸發非同步 Webhook 推送。
