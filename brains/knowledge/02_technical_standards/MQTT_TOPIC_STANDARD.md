# MQTT 主題標準規範 (WAW IoT MQTT Topic Standard)

> **版本**：v2.1.0 (全域統一真理正本)  
> **最後更新**：2026-09-10  
> **狀態**：🔴 **唯一最高法典 (SSOT)** — 所有 Agent 必須以此文件為唯一準則，嚴禁在各自專案中另立平行規範文件。  
> **維護者**：HQ 協調中心（brains/knowledge/ 唯一寫入權限）  
> **適用範圍**：Firmware (Fio, Coli)、Infra (Ina)、SignalHub (Sidney)、iHub (Hubie)、Owner (Sophie)、Member (Mina)

---

## 一、治理政策：消除流浪文件與自作主張

1. **唯一真理原則 (Single Source of Truth)**：
   - 本文件是 WAW 全系統 MQTT Topic 結構、萬用字元訂閱 (Wildcard)、QoS 等級、Retain 策略與 Payload 格式的唯一正本。
   - 嚴禁任何 Agent（Fio, Coli, Ina, Sidney, Hubie 等）在 `PROJECT/` 任何子目錄下自立 MQTT 規範文件（例如 `MQTT_PROTOCOL.md`、`topics.md` 等）。
   - 各專案若需引用，僅允許放置指向本文件之參照連結，嚴禁複製貼上或私自擴充定義。
2. **主題新增與變更程序**：
   - 任何非本文件定義的 Topic 或 Action，一律視為「非法未授權主題」。
   - 如因新硬體或新業務需求必須調整，必須向 HQ 提案，經審查通過並由 HQ 更新本文件後，各 Agent 方可實作。
3. **違規判定**：
   - 若 Agent 在程式碼中擅自拼接未規範的主題或自行宣告新 action，HQ 代碼審查將直接判定違規並拒絕合併。

---

## 二、系統現行兩套主題體系

WAW 系統目前處於硬體與協定現代化階段，存在兩套體系，**不可混淆**：

| 體系名稱 | 主題前綴結構 | 適用對象 | 狀態 |
| :--- | :--- | :--- | :--- |
| **WAW-USS v1.0 (主標準)** | `waw/v1/{site_id}/signal/{chip_id}/{action}` | 所有現行與未來硬體：IOTkiosk_v0 (v2.0+)、IOTwawS3 (v2.0+)、SignalHub | 🟢 **唯一強制主標準** |
| **Legacy 舊相容層** | `kiosk/{chip_id}/...` 與 `device/{chip_id}/...` | 舊版硬體相容、過渡期過往服務相容 | ⚠️ **僅供歷史相容，禁止新增任何用途** |

---

## 三、WAW-USS v1.0 新標準主題體系（主標準）

### 3.1 主題層級結構

```
waw/v1/{site_id}/signal/{chip_id}/{action}
 └──┬──┘ └──┬──┘  └──┬─┘   └──┬──┘  └──┬───┘
   (1)     (2)      (3)       (4)      (5)
```

1. `waw/v1`：全域協定前綴與版本號（固定，小寫）。
2. `{site_id}`：營運站點代碼（由雲端/Infra 統一分配，例如 `site01`, `main_arcade`）。
3. `signal`：核心命名空間（固定，代表 Layer 0 通用信號層）。
4. `{chip_id}`：ESP32 唯一識別碼，**強制規定為 12 碼大寫十六進位 MAC 位址（無冒號）**，例如 `C8F09E1A2B3C`。
5. `{action}`：動作或數據類型（僅限四種：`event`, `status`, `cmd`, `ack`）。

---

### 3.2 發布與訂閱責任矩陣 (Publish & Subscribe Matrix)

| 主題路徑 | 發布方 (Publisher) | 訂閱方 (Subscriber) | QoS | Retain | 用途說明 |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `waw/v1/{site_id}/signal/{chip_id}/event` | ESP32 採集板 | 雲端監聽器 (Ina) / 邊緣閘道 | **1** | **false** | 脈衝里程表累計值上報 (門檻即時 / 60s 定期) |
| `waw/v1/{site_id}/signal/{chip_id}/status` | ESP32 採集板 | 雲端監聽器 (Ina) / 營運監控 | **1** | **true** | 設備連線心跳、健康指標、及 LWT 遺囑 |
| `waw/v1/{site_id}/signal/{chip_id}/cmd` | 雲端後台 / iHub | 指定 ESP32 採集板 | **1** | **false** | 遠端控制下行指令 (單播，如致能/退幣/重啟) |
| `waw/v1/{site_id}/signal/{chip_id}/ack` | ESP32 採集板 | 雲端後台 / 指令發起端 | **1** | **false** | 指令執行結果確認回執 |

---

### 3.3 萬用字元訂閱規範 (Wildcard Subscription Rules)

雲端服務與邊緣端訂閱時，必須遵守精確萬用字元規範，**嚴禁隨意使用 `#`**：

#### 1. 全域雲端監聽器 (Infra Ina Daemon / SignalHub Listener)
* **信號事件監聽**：
  ```
  waw/v1/+/signal/+/event      (QoS 1)
  ```
  - 第一個 `+` 匹配所有 `site_id`。
  - 第二個 `+` 匹配所有 `chip_id`。
  - 結尾明確指定 `/event`，絕不混入 status 或 cmd。
* **設備在線與遺言狀態監聽**：
  ```
  waw/v1/+/signal/+/status     (QoS 1)
  ```

#### 2. 單一站點邊緣閘道 / 店內 iHub
* 僅監聽該站點轄下設備：
  ```
  waw/v1/{site_id}/signal/+/event    (QoS 1)
  waw/v1/{site_id}/signal/+/status   (QoS 1)
  ```

#### 3. 韌體硬體端 (ESP32)
* **只允許精確單播訂閱**：
  ```
  waw/v1/{site_id}/signal/{chip_id}/cmd    (QoS 1)
  ```
* ⚠️ **硬體安全鐵律**：ESP32 韌體端**絕對禁止**訂閱帶有 `+` 或 `#` 的主題，避免接收到全場廣播造成記憶體耗盡或誤動作。

---

### 3.4 標準 Payload 規格

#### 1. 信號事件上報 (`action = event`)
* **Topic**：`waw/v1/{site_id}/signal/{chip_id}/event`
* **QoS**：`1`，**Retain**：`false`
* **時機**：
  1. 門檻觸發：任何輸入腳位累計計數值變更時立即推送。
  2. 週期同步：無事件時每 60 秒定期推送全通道快照。

```json
{
  "version": "1.0",
  "chip_id": "C8F09E1A2B3C",
  "device_id": 1024,
  "msg_id": "msg-1725088800123-000001",
  "timestamp": 1725088800123,
  "signals": {
    "UI1": { "raw_value": 15280, "mode": "counter", "state": 1 },
    "UI2": { "raw_value": 305,   "mode": "counter", "state": 0 },
    "UI3": { "raw_value": 12,    "mode": "toggle",  "state": 1 },
    "UI4": { "raw_value": 0,     "mode": "event",   "state": 0 },
    "UO1": { "state": 0 },
    "UO2": { "state": 0 },
    "UO3": { "state": 1 },
    "UO4": { "state": 0 }
  }
}
```

* **欄位規定**：
  - `version`：字串，固定為 `"1.0"`。
  - `chip_id`：12 碼大寫無冒號 MAC 位址。
  - `device_id`：整數（可為 null 或由雲端指派之設備 ID）。
  - `msg_id`：字串，格式為 `msg-{timestamp毫秒}-{序號6碼}`，用於端到端去重。
  - `timestamp`：13 位 Unix Epoch 毫秒整數。
  - `signals`：固定包含 4 組輸入（`UI1`~`UI4`）與 4 組輸出（`UO1`~`UO4`）。
    - `raw_value`：64 位元無符號整數里程表（單調遞增，永不上報單次 Delta）。
    - `mode`：通道模式，僅限 `"counter"`, `"toggle"`, `"event"`。
    - `state`：即時電位，`0` 為 Low，`1` 為 High。

#### 2. 設備在線狀態與遺言 (`action = status`)
* **Topic**：`waw/v1/{site_id}/signal/{chip_id}/status`
* **QoS**：`1`，**Retain**：`true`

* **在線上報 / 週期心跳**：
```json
{
  "status": "online",
  "chip_id": "C8F09E1A2B3C",
  "firmware_version": "2.0.0",
  "ip": "192.168.1.150",
  "rssi": -58,
  "uptime_seconds": 86400,
  "timestamp": 1725088800
}
```

* **LWT 斷線遺言 (Broker 自動代發)**：
```json
{
  "status": "offline",
  "chip_id": "C8F09E1A2B3C",
  "timestamp": 1725088800
}
```

#### 3. 遠端下行指令 (`action = cmd`)
* **Topic**：`waw/v1/{site_id}/signal/{chip_id}/cmd`
* **QoS**：`1`，**Retain**：`false`

```json
{
  "req_id": "cmd-20260910-0001",
  "action": "pulse_output",
  "params": {
    "pin": "UO1",
    "duration_ms": 100,
    "count": 1
  },
  "timestamp": 1725088800
}
```
* 核准的 `action` 清單：`stack`, `reject`, `hold`, `enable`, `disable`, `pulse_output`, `reboot`。

#### 4. 指令回執 (`action = ack`)
* **Topic**：`waw/v1/{site_id}/signal/{chip_id}/ack`
* **QoS**：`1`，**Retain**：`false`

```json
{
  "req_id": "cmd-20260910-0001",
  "action": "pulse_output",
  "status": "ok",
  "message": "Pulse executed on UO1",
  "timestamp": 1725088801
}
```

---

## 四、Legacy 相容主題體系（僅保留，禁止擴充）

> ⚠️ **警告**：以下主題為第一代舊系統殘留，新開發嚴禁使用。僅供過渡期現有韌體相容接收。

### 4.1 兌幣卡 (IOTkiosk_v0 v1.x)
| 主題 | 方向 | QoS | Retain | 說明 |
| :--- | :--- | :---: | :---: | :--- |
| `kiosk/{chip_id}/event` | ESP32 → 雲端 | 2 | false | Escrow / Stacked / Rejected 事件 |
| `kiosk/{chip_id}/status` | ESP32 → 雲端 | 1 | true | 心跳狀態 |
| `kiosk/{chip_id}/cmd` | 雲端 → ESP32 | 2 | false | 收鈔控制指令 |
| `device/{chip_id}/info` | ESP32 → 雲端 | 1 | true | 版本與時區資訊 |

### 4.2 遊戲機通訊卡 (IOTwawS3 v1.x)
| 主題 | 方向 | QoS | Retain | 說明 |
| :--- | :--- | :---: | :---: | :--- |
| `device/{chip_id}/register` | ESP32 → 雲端 | 1 | false | 初次註冊 |
| `device/{chip_id}/status` | ESP32 → 雲端 | 1 | true | 舊版心跳 |
| `device/{chip_id}/pulse` | ESP32 → 雲端 | 1 | false | 脈衝事件 |
| `device/{chip_id}/data/credit_in` | ESP32 → 雲端 | 1 | true | 入金累計數據 |
| `device/{chip_id}/command` | 雲端 → ESP32 | 1 | false | 下行指令 |
| `device/{chip_id}/command/response` | ESP32 → 雲端 | 1 | false | 指令回應 |

---

## 五、雲端監聽器實作清單（Infra Ina 任務基準）

Infra 服務端的 MQTT Listener 必須在轉型期內同時訂閱以下兩個分組：

### 5.1 主標準訂閱（核心業務）
1. `waw/v1/+/signal/+/event` (QoS 1) → 寫入 `signal_events`，計算 Delta，觸發 Webhook
2. `waw/v1/+/signal/+/status` (QoS 1) → 更新設備在線狀態與最後連線時間

### 5.2 Legacy 舊系統相容訂閱（維護模式）
1. `kiosk/+/event` (QoS 2)
2. `kiosk/+/status` (QoS 1)
3. `device/+/register` (QoS 1)
4. `device/+/status` (QoS 1)
5. `device/+/pulse` (QoS 1)

---

## 六、命名與參數強制規範

1. **Client ID 規範**：
   - ESP32 設備端：強制為 `waw-esp32-{chip_id}`（例：`waw-esp32-C8F09E1A2B3C`）。
   - 雲端監聽器：強制為 `waw-infra-listener-{hostname}-{pid}`。
2. **大小寫規範**：
   - 主題中所有路徑層級（`waw`, `v1`, `signal`, `event`, `status`, `cmd`, `ack`）一律全小寫。
   - 硬體腳位代碼（`UI1`~`UI4`, `UO1`~`UO4`）一律全大寫。
   - MAC 位址（`chip_id`）一律 12 位大寫十六進位字元。
3. **禁止事項**：
   - 嚴禁自創主題名（如 `waw/v1/+/event`、`device/{id}/signal` 等）。
   - 嚴禁在專案資料夾內撰寫任何以規範自居的 MQTT 文件。

