# 名稱定義來源表 (Naming Authority)

> **版本**: 2.0.0
> **日期**: 2026-05-11 (UTC+8)
> **維護者**: HQ（唯一寫入權）

---

## 使用方式

討論、設計、任務派發時，遇到不確定的名稱，在本表找到定義來源，去那份文件查正確寫法。

- **找得到** → 去定義來源文件查，用文件裡的名稱
- **找不到** → 停下來，向 HQ 申請定義，補入本表後才能使用
- **禁止猜測、禁止暫時替代名稱**

---

## 名稱定義來源

### 韌體

| 名稱 | 定義來源 | 說明 |
|------|---------|------|
| `IOTkiosk_v0` | `.kiro/steering/identity.md` | 紙鈔機收鈔卡韌體完整名稱 |
| `kiosk_v0` | `.kiro/steering/identity.md` | `IOTkiosk_v0` 的代號 |
| `IOTwawS3` | `.kiro/steering/identity.md` | 遊戲機通訊卡韌體完整名稱 |
| `game_v0` | `.kiro/steering/identity.md` | `IOTwawS3` 的代號 |

### 識別碼

| 名稱 | 定義來源 | 格式 |
|------|---------|------|
| `chip_id` | `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` | 12位小寫hex，無冒號，例：`e072a1f73a78` |
| `node_id`（兌幣機） | `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` | `kiosk_NNN`（全小寫），例：`kiosk_000` |
| `node_id`（遊戲機） | `05_product_and_business_flows/game_v0_arcade/DEVICE_IDENTIFICATION_SYSTEM.md` | `device_NNN`（全小寫），例：`device_001` |
| `kiosk_id` | `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` | `node_id` 的別名，API 參數欄位名 |
| `screen_mac` | `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` | 平板 MAC |
| `esp32_mac` | `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` | 同 `chip_id`，DB 欄位名稱 |
| `kiosk_no` | `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` | 3位數字，例：`000`，顯示用 |

### MQTT 主題與 Payload 欄位

| 名稱 | 定義來源 |
|------|---------|
| 所有 MQTT 主題格式 | `02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` |
| `event_type` 可能值 | `02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` |
| `ba_state` 可能值 | `02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` |
| `action`（cmd/command）可能值 | `02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` |

### WebSocket 頻道與事件

| 名稱 | 定義來源 |
|------|---------|
| 所有頻道名稱與事件名稱 | `02_protocols_and_standards/WEBSOCKET_CHANNEL_STANDARD.md` |

### API 端點

| 名稱 | 定義來源 |
|------|---------|
| Infra API 端點 | `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` 第七節 |
| Member API 端點 | `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` 第七節 |
| iHub Server API 端點 | `.kiro/specs/bill-acceptor-simulator/design.md` |
| `X-Internal-Key` header | `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` | 內部服務間驗證（Member ↔ Infra webhook），值：`v9-internal-key-2026` |
| `X-API-Key`（Infra device API） | `iotv9.auth_keys`（id=4，key_code=`v9_backend_token_2026`） | 呼叫 `api.tg25.win/api/device/...` 用，值：`v9_backend_token_2026` |
| `reason`（session end）可能值 | `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` |

### 資料庫表

| 名稱 | 定義來源 | 所在 DB |
|------|---------|---------|
| `iotv9.kiosks` | `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` | infra（Owner DB） |
| `iotv9.devices` | `05_product_and_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md` | infra（Owner DB） |
| `waw_member_production.kiosk_sessions` | `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` | yd47（Member DB） |
| `waw_member_production.kiosk_transactions` | `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` | yd47（Member DB） |
| `waw_member_production.device_sessions` | `05_product_and_business_flows/game_v0/05_product_and_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md` | yd47（Member DB） |
| `waw_member_production.device_credit_logs` | `05_product_and_business_flows/game_v0/05_product_and_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md` | yd47（Member DB） |
| `waw_member_production.member_wallets` | `05_product_and_business_flows/game_v0/05_product_and_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md` | yd47（Member DB） |
| `waw_member_production.wallet_transactions` | `05_product_and_business_flows/game_v0/05_product_and_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md` | yd47（Member DB） |
| `iotv9.venues` | `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` | infra（Owner DB） |

### 遊戲機識別碼（game_v0 專用）

> `iotv9.devices` 表中有多個 ID 欄位，**不可混用**：

| 名稱 | 格式 | 用途 | 定義來源 |
|------|------|------|---------|
| `chip_id` | 12位小寫hex，例：`iot002` | QR Code、MQTT 主題、所有 API 傳遞 | `05_product_and_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md` |
| `iotv9.devices.id` | 整數 PK | Owner 後台內部，不對外暴露 | `05_product_and_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md` |
| `device_uuid` | UUID | Infra device_registration 系統，**與開分/洗分流程無關** | `05_product_and_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md` |

**結論**：開分/洗分流程全程只用 `chip_id`。Infra `POST /api/credit` 的 `device_id` 欄位接受的就是 `chip_id`。

### 錢包幣種（currency_type）

| 值 | 說明 | 定義來源 |
|----|------|---------|
| `CASH` | 現金餘額 | `waw_member_production.member_wallets` 實際資料 |
| `COIN` | 代幣（舊） | `waw_member_production.member_wallets` 實際資料 |
| `POINT` | 點數 | `waw_member_production.member_wallets` 實際資料 |
| `TOKEN` | 代幣（新，開分用） | `waw_member_production.member_wallets` 實際資料 |
| `TICKET` | 彩票（洗分入帳用） | `05_product_and_business_flows/game_v0/05_product_and_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md`（新增） |

### Agent 與專案

| 名稱 | 定義來源 |
|------|---------|
| 所有 Agent 名稱與職責 | `.kiro/steering/identity.md` |

---

## 已知文件不一致（待修正）

| 文件 | 問題 | 正確值 | 查證來源 |
|------|------|--------|---------|
| `02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` | `node_id` 格式寫成 `KIOSK_001`（大寫） | `kiosk_001`（全小寫） | 實際 DB：`iotv9.kiosks`，2026-05-11 查證 |

---

## 待拍板名稱

| 說明 | 狀態 |
|------|------|
| `kiosk_v0` 業務域的目錄名稱（`05_product_and_business_flows/` 子目錄） | ⏳ 待拍板 |
| `game_v0` 業務域的目錄名稱（`05_product_and_business_flows/` 子目錄） | ⏳ 待拍板 |

---

*維護者：HQ | 建立：2026-05-11 | 版本：2.0.0*

---

## 🔗 文件神經連結

### 被引用（本文件是基礎節點）
> 以下文件都依賴本文件的命名規則

- `02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - 使用 chip_id
- `02_protocols_and_standards/WEBSOCKET_CHANNEL_STANDARD.md` - 使用 node_id
- `02_protocols_and_standards/QRCODE_FORMAT_STANDARD.md` - 使用 node_id
- `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` - 詳細說明 chip_id vs node_id
- `04_ops_and_deployments/INFRASTRUCTURE_REFERENCE.md` - 使用 SSH 別名、DB 名稱

### 強關聯（必讀）
> 了解識別碼的詳細使用場景

- `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` - Kiosk 識別碼體系詳解
- `.kiro/steering/identity.md` - Agent 名稱與職責定義

### 中關聯（建議讀）
> 查看識別碼在實際流程中的使用

- `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` - node_id 用於 API 和 WebSocket
- `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` - chip_id 用於 MQTT

### 排除混淆
> 常見的命名混淆

- `chip_id` ≠ `node_id`（硬體層級 vs 產品層級）
- `kiosk_id` = `node_id`（只是 API 參數的欄位名）
- `esp32_mac` = `chip_id`（只是 DB 欄位名）
