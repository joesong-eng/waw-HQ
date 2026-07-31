# Kiosk 識別碼體系

> **最後更新**：2026-05-08 UTC+8  
> **重要性**：🔴 核心概念，所有 Agent 必須理解

---

## 概述

Kiosk 產品由多個硬體組件組成，每個組件有自己的識別碼。當組裝成完整產品後，產品本身也有一個統一的識別碼。理解這個識別碼體系是開發的基礎。

---

## 識別碼層級

### 1. 硬體層級（Hardware Level）

#### 1.1 兌幣卡（ESP32-S3 韌體：IOTkiosk_v0）

- **識別碼**：`chip_id`
- **格式**：12 位 hexadecimal（MAC 地址）
- **範例**：`aabbccddeeff`
- **用途**：
  - MQTT 通訊：`kiosk/{chip_id}/event`, `kiosk/{chip_id}/cmd`, `kiosk/{chip_id}/status`
  - 硬體狀態回報：`POST /api/kiosk/hardware-status` 的 `chip_id` 參數
  - Infra Listener 的 device cache key

#### 1.2 紙鈔機（ICT 104U）

- **識別碼**：序號（由紙鈔機廠商提供）
- **通訊方式**：透過 RS232 與兌幣卡通訊
- **用途**：硬體維修和追蹤

#### 1.3 平板（Android iHub）

- **識別碼**：`screen_mac`
- **格式**：12 位 hexadecimal（平板的 MAC 地址）
- **範例**：`112233445566`
- **用途**：
  - 平板開機時查詢 node_id：`GET /api/kiosk/node-id?screen_mac={screen_mac}`
  - Alliance 燒錄時記錄平板與 Kiosk 的綁定關係

---

### 2. 產品層級（Product Level）

#### 2.1 KIOSK 產品

當「兌幣卡 + 紙鈔機 + 平板」組裝成一個完整產品後，這個產品有自己的識別碼。

- **識別碼**：`node_id`（也稱為 `kiosk_id`）
- **格式**：`kiosk_NNN`（小寫，3 位數字）
- **範例**：`kiosk_000`, `kiosk_001`, `kiosk_123`
- **用途**：
  - **認證的標準號牌**（這是對外的唯一識別碼）
  - QR Code 內容：詳見 `02_protocols_and_standards/QRCODE_FORMAT_STANDARD.md`
  - WebSocket 頻道：`kiosk.{node_id}`, `engineering.{node_id}`
  - API 參數：`kiosk_id={node_id}`
  - Session 管理：`kiosk_sessions.kiosk_id`

#### 2.2 Kiosk 編號

- **識別碼**：`kiosk_no`
- **格式**：3 位數字（不含前綴）
- **範例**：`000`, `001`, `123`
- **用途**：
  - 顯示給用戶看的編號（例如：「Kiosk #000」）
  - 從 `node_id` 提取：`kiosk_000` → `000`

---

## 識別碼對應關係

### 資料表：`iotv9.kiosks`

```sql
CREATE TABLE iotv9.kiosks (
  id INT PRIMARY KEY AUTO_INCREMENT,
  node_id VARCHAR(20) UNIQUE NOT NULL,     -- kiosk_000
  kiosk_no VARCHAR(10) NOT NULL,           -- 000
  esp32_mac VARCHAR(12) NOT NULL,          -- aabbccddeeff (lowercase)
  screen_mac VARCHAR(12) NOT NULL,         -- 112233445566 (preserve case)
  venue_id INT,
  status ENUM('active', 'inactive'),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### 範例資料

| node_id   | kiosk_no | esp32_mac    | screen_mac   | venue_id | status |
|-----------|----------|--------------|--------------|----------|--------|
| kiosk_000 | 000      | aabbccddeeff | 112233445566 | 1        | active |
| kiosk_001 | 001      | ffeeddccbbaa | 665544332211 | 1        | active |
| kiosk_123 | 123      | 123456789abc | abcdef123456 | 2        | active |

---

## 使用原則

### 原則 1：對外識別（User-facing）

**使用 `node_id`（產品層級識別碼）**

- ✅ QR Code：`KIOSK:kiosk_000:TOKEN:xxx`
- ✅ WebSocket 頻道：`kiosk.kiosk_000`, `engineering.kiosk_000`
- ✅ API 參數：`kiosk_id=kiosk_000`
- ✅ Session 記錄：`kiosk_sessions.kiosk_id = 'kiosk_000'`
- ✅ 日誌顯示：「Kiosk #000」

**為什麼？**
- `node_id` 是產品的唯一識別碼，不會因為更換硬體而改變
- 用戶和系統都用這個識別碼來指稱特定的 Kiosk 產品

---

### 原則 2：硬體通訊（Hardware-facing）

**使用 `chip_id`（硬體層級識別碼）**

- ✅ MQTT 主題：`kiosk/{chip_id}/event`, `kiosk/{chip_id}/cmd`, `kiosk/{chip_id}/status`
- ✅ 硬體狀態 API：`POST /api/kiosk/hardware-status` 的 `chip_id` 參數
- ✅ Infra Listener：用 `chip_id` 查詢 device cache，取得 `node_id`

**為什麼？**
- MQTT 主題必須用 `chip_id`，因為韌體只知道自己的 MAC 地址
- 硬體層級的通訊不需要知道產品層級的識別碼

---

### 原則 3：查詢對應關係

#### 3.1 平板開機流程

```
1. 平板取得自己的 screen_mac
   ↓
2. 呼叫 GET /api/kiosk/node-id?screen_mac={screen_mac}
   ↓
3. Infra 查詢 iotv9.kiosks，回傳 node_id 和 esp32_mac
   ↓
4. 平板儲存 node_id 和 esp32_mac，用於後續通訊
```

#### 3.2 MQTT 事件處理流程

```
1. 韌體發布 MQTT 事件到 kiosk/{chip_id}/event
   ↓
2. Infra Listener 接收事件
   ↓
3. Listener 用 chip_id 查詢 device cache，取得 node_id
   ↓
4. Listener 轉發到 Member API，參數包含 kiosk_id (node_id)
   ↓
5. Member 用 kiosk_id 查詢 session，處理業務邏輯
```

---

## 常見錯誤

### ❌ 錯誤 1：混淆 node_id 和 chip_id

```javascript
// ❌ 錯誤：用 chip_id 訂閱 WebSocket
echo.channel(`kiosk.${chip_id}`);

// ✅ 正確：用 node_id 訂閱 WebSocket
echo.channel(`kiosk.${node_id}`);
```

### ❌ 錯誤 2：用 node_id 發布 MQTT

```python
# ❌ 錯誤：用 node_id 發布 MQTT
mqtt_client.publish(f"kiosk/{node_id}/cmd", payload)

# ✅ 正確：用 chip_id 發布 MQTT
mqtt_client.publish(f"kiosk/{chip_id}/cmd", payload)
```

### ❌ 錯誤 3：格式錯誤

```javascript
// ❌ 錯誤：node_id 格式錯誤
const nodeId = 'N-000';  // 應該是 kiosk_000

// ❌ 錯誤：chip_id 格式錯誤
const chipId = 'AA:BB:CC:DD:EE:FF';  // 應該是 aabbccddeeff（無冒號）

// ✅ 正確
const nodeId = 'kiosk_000';
const chipId = 'aabbccddeeff';
```

---

## 模擬器配置

### sim-bill（紙鈔機模擬器）

sim-bill 模擬的是 **產品層級**，所以：

```javascript
// 配置
const CONFIG = {
  CHIP_ID: 'test-esp32',      // 模擬的 chip_id
  KIOSK_ID: 'kiosk_000',      // 產品的 node_id（不是 N-000！）
};

// WebSocket 訂閱
echo.channel(`engineering.${CONFIG.KIOSK_ID}`);  // engineering.kiosk_000

// API 呼叫
fetch('/api/simulator/bill', {
  body: JSON.stringify({
    chip_id: CONFIG.CHIP_ID,    // 硬體識別碼
    amount: 100
  })
});
```

---

## 檢查清單

在實作任何功能時，問自己：

- [ ] 我使用的是 `node_id` 還是 `chip_id`？
- [ ] 這個識別碼用在什麼層級？（產品層級 vs 硬體層級）
- [ ] 格式是否正確？（`kiosk_000` vs `aabbccddeeff`）
- [ ] 是否需要查詢對應關係？（`screen_mac` → `node_id` → `chip_id`）

---

## 參考文件

- `kiosk_exchange_v2/requirements.md`：Requirement 1（識別碼規範）
- `kiosk_exchange_v2/design.md`：識別碼對應關係
- `02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md`：MQTT 主題命名規範
- `alliance_burning_pairing_guide.md`：硬體燒錄和配對流程

---

## 總結

**記住這個核心概念**：

```
硬體層級（chip_id）  →  用於 MQTT 通訊
     ↓ 對應關係（iotv9.kiosks）
產品層級（node_id）  →  用於業務邏輯、用戶識別、WebSocket
```

**認證的標準號牌是 `node_id`（例如 `kiosk_000`），不是 `chip_id`。**

---

## 🔗 文件神經連結

### 強關聯（必讀）
> 修改識別碼相關代碼前，必須先閱讀以下文件

- `../../NAMING_AUTHORITY.md` - 名稱定義來源索引，確保使用正確的識別碼格式
- `../../02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - MQTT 主題規範，chip_id 用於 MQTT 通訊
- `../../02_protocols_and_standards/WEBSOCKET_CHANNEL_STANDARD.md` - WebSocket 頻道規範，node_id 用於 WebSocket 頻道
- `../../02_protocols_and_standards/QRCODE_FORMAT_STANDARD.md` - QR Code 格式規範，node_id 用於 QR Code

### 中關聯（建議讀）
> 了解完整業務流程，建議閱讀

- `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` - 兌幣流程，識別碼在業務流程中的使用
- `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` - 紙鈔機互動流程，chip_id 與 node_id 的轉換
- `../../04_ops_and_deployments/INFRASTRUCTURE_REFERENCE.md` - 基礎設施參考，iotv9.kiosks 資料表位置

### 弱關聯（參考）
> 可選閱讀，提供額外背景

- `05_product_and_business_flows/kiosk_v0_exchange/KIOSK_UX_AND_SCREEN_DESIGN.md` - 三螢幕 UX 流程，平板如何使用 node_id
- `../../01_agent_governance_rules/AGENT_RESPONSIBILITY_BOUNDARIES.md` - Agent 職責邊界，了解哪個 Agent 負責識別碼管理

### 排除混淆
> 容易混淆但實際無關的文件

- `../game_v0_arcade/05_product_and_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md` - 遊戲機流程，使用不同的識別碼體系（device_id，不是 kiosk_id）
- `../game_v0_arcade/qrcode_url_unification_plan.md` - 遊戲機 QR Code，使用 node_id 但格式不同（`/m/play?node_id=`）
