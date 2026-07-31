# 技術命名與數據負載標準規範 (Technical Naming & Payload Standard)

> **版本**：v3.0.0 (合併版)  
> **最後更新**：2026-06-05  
> **狀態**：🔴 **最高物理法典** - 全系統所有 Agent 必須完全遵守此規範，禁止私自創立替代變數或修改格式。  
> **適用範圍**：Firmware (Fio, Coli)、Infra (Ina)、Member (Mina)、Owner (Sophie)

---

## 一、 系統命名與變數唯一真理 (Naming Authority & Philosophy)

全系統在 API 傳遞、資料庫欄位、以及程式碼開發中，必須嚴格遵守以下命名风格，嚴禁混用 camelCase 與 snake_case：

### 1. 識別碼命名規範
* **硬體晶片 ID**：統一命名為 `chip_id` (全小寫，無冒號的 12 碼 MAC 格式，例如 `e072a1f73a78` 或模擬代碼 `iot002`)。
  - ❌ 禁用：`chipId`、`mac`、`esp32_mac`、`mac_address`。
  - ⚠️ 資料庫特殊情況：在舊有 DB 欄位中若為 `esp32_mac`，代表的即是 `chip_id`，新開發一律使用 `chip_id`。
* **邏輯機台 ID**：統一命名為 `node_id` (通常是字串)。
  - 遊戲機格式：`device_NNN` (全小寫，例如 `device_001`)。
  - 兌幣機格式：`kiosk_NNN` (全小寫，例如 `kiosk_000`)。
  - ❌ 禁用：`kiosk_id`、`deviceId`、`nodeId`。
  - ⚠️ API 參數別名：僅在 API 參數傳遞時，允許 `kiosk_id` 做為 `node_id` 的別名。
* **使用者與營運商 ID**：統一使用 `owner_id` 或 `user_id` (對應 `users.id`)。
* **交易 ID**：統一使用 `transaction_id` (格式為 UUIDv4 或是由系統生成的交易序號)。

### 2. 帳務、脈衝與指令命名
為配合 ESP32 韌體與高頻監聽器，所有涉及 MQTT 脈衝與指令的欄位，必須嚴格遵守以下命名：
* **脈衝類型**：統一命名為 `type` (值僅限 `credit_in` 入金 或 `credit_out` 出金/洗分)。
  - ❌ 禁用：`pulse_type`、`action_type`。
* **脈衝計數值**：
  - 在 `device/{chip_id}/pulse` 事件中，欄位名為 `value`。
  - 在 `assign_credit` / `simulate_pulse` 指令的 `params` 中，欄位名為 `count`。
  - 在 `device/{chip_id}/data/credit_in` 等遙測數據中，欄位名為 `count`。
  - ❌ 禁用：`pulse_count`、`pulse`、`pulses`。
* **貨幣與金額**：統一使用 `amount`。
  - ⚠️ **金額整數元原則**：在所有 API、JSON Payload 中，**台幣金額必須以「整數元」傳遞** (例如 100 代表 100 元 TWD)，不允許帶小數點 (如 `100.00`)，以保障金流與硬體換算的精確性。

---

## 二、 連接埠 (Port) 與協議統一規範

| 服務名稱 | 專案目錄 | 域名 (Domain) | 監聽 Port | 連線協議 |
| :--- | :--- | :--- | :--- | :--- |
| **waw-business (人)** | `wawOwner/wawv9` | `iot.tg25.win` | `8001` (Nginx Proxy 443) | HTTPS / Laravel Web Session |
| **waw-iot (物/採集)** | (新子專案) | `iot.tg25.win` | `8002` (Nginx Proxy 443) | HTTPS / Fast API / JSON |
| **Laravel Reverb** | `wawOwner/wawv9` | `iot.tg25.win` | `6009` | WSS (WebSocket Secure) |
| **MQTT Broker** | `tg25-infra` | `api.tg25.win` | `1883` (非加密), `8883` (SSL) | MQTT / TCP |
| **Member 玩家站** | `Member` | `win.tg25.win` | `80` (HTTP), `443` (HTTPS) | HTTPS / Web Session |
| **Alliance 代理商站** | `Alliance` | `ali.tg25.win` | `80` (HTTP), `443` (HTTPS) | HTTPS / Web Session |

### HTTP Header 內部驗證安全規範
* **內部 Webhook Header**：`X-Internal-Key: v9-internal-key-2026` (驗證 verify.internal.key 中間件)
* **平板端 API Header**：`Authorization: Bearer {ihub_token}` (驗證 verify.ihub.token 中間件)

---

## 三、 MQTT 主題命名與結構規範

### 3.1 主題層級結構
```
{category}/{chip_id}/{function}
```
- `category`: `kiosk` (兌幣卡) 或 `device` (通用 ESP32/遊戲機通訊卡)
- `chip_id`: ESP32 的 MAC address (全小寫，無冒號的 12 碼)
- `function`: 功能類型 (status / event / cmd / command / data 等)

### 3.2 兌幣卡主題（kiosk_v0 / IOTkiosk_v0）
* **上行主題 (ESP32 -> 雲端)**：
  - `kiosk/{chip_id}/status` | QoS 1, Retain | 連線後立即 + 每 60 秒回報。
  - `kiosk/{chip_id}/event` | QoS 2 | 鈔票暫存 (Escrow)、收鈔確認 (Stacked) 或退鈔 (Rejected)。
  - `device/{chip_id}/status` | QoS 1, Retain | LWT 遺言上線/下線 ("online" / "offline")。
* **下行主題 (雲端 -> ESP32)**：
  - `kiosk/{chip_id}/cmd` | QoS 2 | 控制收鈔行為：`{"action": "enable" | "disable" | "stack" | "reject"}`。

### 3.3 通訊卡主題（game_v0 / IOTwawS3）
* **上行主題 (ESP32 -> 雲端)**：
  - `device/{chip_id}/status` | QoS 1, Retain | 心跳狀態。
  - `device/{chip_id}/pulse` | QoS 1 | 物理脈衝事件，Payload：`{"type": "credit_in" | "credit_out", "value": 1}`。
  - `device/{chip_id}/data/credit_in` | QoS 1, Retain | 累計入金脈衝數，Payload：`{"count": 1234, "lifetime": 5678}`。
* **下行主題 (雲端 -> ESP32)**：
  - `device/{chip_id}/command` | QoS 1 | 下發控制指令：
    - 開分：`{"command": "assign_credit", "transaction_id": "...", "params": {"count": 5}}`
    - 洗分：`{"command": "settle_credit", "transaction_id": "..."}`
    - 模擬採集脈衝 (測試用)：`{"command": "simulate_pulse", "transaction_id": "...", "params": {"type": "credit_in", "count": 5}}`

---

## 四、 核心 API Payload 與 JSON 格式規範

### 1. 兌幣卡 Escrow 鈔票暫存事件 (MQTT -> API)
* **事件 Payload**：
  ```json
  {
    "event_type": "escrow",
    "amount": 100,
    "timestamp": 1713253800
  }
  ```

### 2. 遊戲機上報脈衝事件 (Ina -> waw-iot -> waw-business)
* **端點**：`POST /api/v1/event/pulse`
* **Payload**：
  ```json
  {
    "type": "credit_in",
    "value": 5,
    "timestamp": 1713253815
  }
  ```

### 3. 帳務稽核與上報 (iHub -> waw-business)
* **端點**：`POST /api/v1/audit/report`
* **Payload**：
  ```json
  {
    "node_id": "device_001",
    "total_revenue": 15870,
    "timestamp": 1780709000
  }
  ```

### 4. 機台參數模板同步 (waw-business -> waw-iot)
* **端點**：`GET /api/internal/device/{chip_id}/params`
* **回應 (Response)**：
  ```json
  {
    "chip_id": "e072a1f73a78",
    "pulse_to_token": 10,
    "pulse_to_display": 1,
    "signal_polarity": "active_low",
    "ticket_mode": "disabled"
  }
  ```

---

## 🔗 文件神經連結

### 強關聯（必讀）
> 使用或修改本規範時，必須先閱讀以下文件

- `brains/knowledge/NAMING_AUTHORITY.md` - 名稱定義來源表，確認基本識別碼定義。
- `brains/knowledge/03_system_architecture_designs/V9_SYSTEM_SPLITTING_DESIGN.md` - V9 系統拆分遷移設計書，了解雙子專案與 Nginx 路由邊界。

### 中關聯（建議讀）
- `brains/knowledge/05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` - 兌幣機 MQTT 物理與金流交互流程。

### 排除混淆
- `brains/knowledge/05_product_and_business_flows/kiosk_v0_exchange/KIOSK_UX_AND_SCREEN_DESIGN.md` - 用戶端 UX UI，無涉底層 Payload 與 Naming 強制限制。
