# 任務回報：TASK_20260914_INA_WS_REVERB_PRIVATE_CHANNEL

**完成時間**：2026-09-14 11:30
**執行者**：Ina (Infra)
**派發來源**：HQ（CRITICAL 級，與 Mina TASK_20260914_MINA_P0_BACKEND_SECURITY P0-3 並行）
**關聯任務**：TASK_20260914_MINA_P0_FRONTEND_UX（P0-3 PrivateChannel + UX-P1-4 MQTT heartbeat）

---

## 0. 重要澄清：Infra 端技術棧定位

派工單標題「WS Reverb Private Channel」易誤導，需先釐清架構：

| 項目 | Infra 端 (Python) | Infra 端 (Laravel/waw-iot) | Member 端 (Laravel/Mina) |
| :--- | :--- | :--- | :--- |
| Reverb | ❌ 無 | ✅ 有（`/var/www/waw-iot`，Laravel 13 + `laravel/reverb`） | ❌ 無 |
| WebSocket 廣播 | ❌ | ✅ 經由 `BROADCAST_CONNECTION=reverb` 觸發 | ✅ Member 端 Event 直接廣播 |
| Private/Presence Channel 認證 | ❌ | ⚠️ **本任務唯一要處理的點** | ✅ 需 Mina 改 Event + 前端 |
| MQTT 監聽 | ✅ `kiosk_event_listener.py`（legacy topics） | ✅ `MqttListenCommand`（legacy `device/+/status`） | 接收 Infra 轉拋 webhook |
| `/api/kiosk/heartbeat` HTTP | ✅ `api/credit-relay/routers/kiosk.py` 已存在 | ❌ | ✅ 平板→Member→Infra 鏈路 |

**結論**：Infra 端 Reverb 已在 `waw-iot` 跑著。MQTT heartbeat 唯一真理正本 = `waw/v1/.../status`（依 `MQTT_TOPIC_STANDARD.md` v2.1.0）。

---

## 1. Reverb Server 設定確認

### 1.1 現況盤點（已完成）

**服務狀態**：✅ `waw-reverb.service` active running（systemd 監聽 `127.0.0.1:6009`）

```bash
$ ss -tlnp | grep 6009
LISTEN 0 511 127.0.0.1:6009  users:(("php8.5",pid=3322003,fd=5))

$ systemctl status waw-reverb.service
● waw-reverb.service - WAW IoT Laravel Reverb Service
     Active: active (running)
```

**設定檔位置**（**已存在、不需新建**）：

| 檔案 | 內容摘要 |
| :--- | :--- |
| `/var/www/waw-iot/config/reverb.php` | Reverb server 設定（host/port/scaling/apps） |
| `/var/www/waw-iot/config/broadcasting.php` | Broadcast 連線設定（`reverb` driver 已啟用） |
| `/var/www/waw-iot/.env` | 環境變數（`REVERB_APP_ID=102468` 等三組金鑰已配置） |
| `/etc/systemd/system/waw-reverb.service` | systemd 服務定義（已啟用） |

**`.env` 關鍵設定**（截錄 `/var/www/waw-iot/.env`）：

```ini
BROADCAST_CONNECTION=reverb
REVERB_APP_ID=102468
REVERB_APP_KEY=wawreverbkey2026
REVERB_APP_SECRET=wawreverbsecret2026
REVERB_HOST="127.0.0.1"
REVERB_PORT=6009
REVERB_SCHEME=http
REVERB_SERVER_HOST=127.0.0.1
REVERB_SERVER_PORT=6009
```

### 1.2 Private Channel 與 Presence Channel 支援

✅ **Reverb 原生支援 PrivateChannel / PresenceChannel**（`laravel/reverb: *`，Laravel 13 內建）。
無需額外啟用，僅需在 **應用端**（Mina 的 Member）透過 `routes/channels.php` 加上授權邏輯。
Infra 端 Reverb 服務已就緒，**不需要修改 `reverb.php` 即可支援 Private/Presence**。

### 1.3 broadcasting auth endpoint 指向

⚠️ **目前 Reverb 只綁 127.0.0.1，未對外暴露**。`/etc/nginx/sites-enabled/` 沒有任何 `location` 代理到 `:6009`。

| Endpoint | 用途 | 目前狀態 |
| :--- | :--- | :--- |
| `POST /broadcasting/auth`（在 Member 端） | 前端用 Sanctum token 認證 Private/Presence Channel | Mina 應在 Member `routes/channels.php` + 確認 broadcasting driver |
| 外部 Reverb 連線 | 瀏覽器 `wss://...` 連入 | ❌ 未暴露（**本任務不在處理範圍**） |

**Ina 端不需要改 broadcasting 認證路徑**——auth endpoint 是 Member 端的事情（Member 是 Event 發送方）。
Reverb Server 只要 listening 即可，認證流程由 Laravel 應用層處理（`Broadcast::channel()` 授權 callback）。

### 1.4 配合 Mina 需要的設定同步

Mina 若要在 Member 端用 Reverb，**必須確保 Member 端的 `REVERB_*` 設定與 Infra 端相同 app key/secret**，
否則 Pusher protocol 簽章會失敗。目前我**未在 Member 主機檢查**（那是 Mina 的領地），
建議 Mina 端在 `config/broadcasting.php` 設定指向 Infra：

```php
'reverb' => [
    'driver' => 'reverb',
    'key'    => env('REVERB_APP_KEY'),     // 與 Infra 端相同: wawreverbkey2026
    'secret' => env('REVERB_APP_SECRET'),  // 與 Infra 端相同: wawreverbsecret2026
    'app_id' => env('REVERB_APP_ID'),      // 與 Infra 端相同: 102468
    'options' => [
        'host'   => env('REVERB_HOST'),    // 對外 host（待 Mina 確認）
        'port'   => env('REVERB_PORT', 443),
        'scheme' => env('REVERB_SCHEME', 'https'),
        'useTLS' => true,
    ],
],
```

> ⚠️ **重大提醒**：Mina 必須透過 wss 加密連到 Reverb，**不能從外部直接打 6009**。建議走 `api.tg25.win` + nginx reverse proxy（待 HQ 決策是否要對外暴露）。

### 1.5 修改的設定檔清單（本任務）

**無**。Reverb 服務、.env、reverb.php、broadcasting.php 皆已正確配置，**Ina 端無需異動**。

---

## 2. MQTT Heartbeat Topic 確認

### 2.1 唯一真理正本（依 `MQTT_TOPIC_STANDARD.md` v2.1.0）

🔴 **Mina 派工單中假設的 `waw/kiosk/{kiosk_id}/heartbeat` topic 不存在！**
正確的 topic pattern 為 **WAW-USS v1.0 主標準**：

| 屬性 | 值 |
| :--- | :--- |
| **Topic pattern** | `waw/v1/{site_id}/signal/{chip_id}/status` |
| **QoS** | `1` |
| **Retain** | `true` |
| **Publisher** | ESP32 採集板（設備端） |
| **Subscriber** | 雲端監聽器 (Ina) / 營運監控 |
| **用途** | 設備連線心跳、健康指標、及 LWT 遺囑 |

範例 payload（`status=online`，週期上報）：

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

LWT（斷線遺言）：

```json
{
  "status": "offline",
  "chip_id": "C8F09E1A2B3C",
  "timestamp": 1725088800
}
```

> **重要差異**：規範正本**無 `session_id` 也無 `game_active` 欄位**。如果 Mina UX-P1-4 需要 `game_active`，
> 需在 event topic（`/event`，投幣/開分）中獲取，不能從 status heartbeat 推斷。

### 2.2 Infra 端 Listener 訂閱狀態（盤點結果）

Infra 端**有兩個 listener**並行運作，訂閱的 topic 與寫入位置都不同：

#### A. `kiosk_event_listener.py`（Python，systemd 服務 `mqtt-listener.service`）

訂閱的 topics（行 31-37）：
```python
TOPIC_FILTER = [
    ("kiosk/+/event", 2),       # Legacy 舊體系
    ("kiosk/+/status", 2),      # ← 這就是 heartbeat！Legacy 舊體系
    ("device/+/data", 1),
    ("device/+/data/diagnostic", 1),
    ("device/+/activity", 0),
    ("device/+/status", 2),     # ← 另一條 heartbeat（Legacy）
]
```
**動作**：`handle_status_update()` 將 status payload **轉拋到 Member webhook**（`POST {MEMBER_BASE_URL}/status`）。
**未寫入 DB，也未寫入 Redis**。

#### B. `MqttListenCommand.php`（Laravel，`waw-iot` 專案）

訂閱的 topics（`/var/www/waw-iot/app/Console/Commands/MqttListenCommand.php` 行 76-83）：
```php
$topics = [
    'device/+/register' => 1,
    'device/+/status'   => 1,    // ← heartbeat
    'device/+/event'    => 1,
    // TODO [HQ-20260910]: 待補充 WAW-USS v1.0 訂閱
    // 'waw/v1/+/signal/+/event'  => 1,
    // 'waw/v1/+/signal/+/status' => 1,
];
```
**動作**：`handleStatus()` → `MqttListenerService::handleDeviceHeartbeat($chipId, $status)`
  - 更新 `iotv9.machines` 的 `last_seen_at`（依 AI_CONTEXT.md 坑 #17：只更新時間，不改 status）
  - 寫入 Redis（key pattern: `v9:machine:{chip_id}:status`，TTL 86400s）
  - **有 `getDeviceStatusFromRedis($chipId)` service method 可用**

### 2.3 ⚠️ WAW-USS v1.0 心跳尚未被任一 listener 訂閱！

這是**目前已知的技術債**（`MqttListenCommand.php` 的 TODO 標記）：

```
// TODO [HQ-20260910]: 需新增 WAW-USS v1.0 主題訂閱
// 正式規範見 brains/knowledge/02_technical_standards/MQTT_TOPIC_STANDARD.md 第四章
// 應補充：'waw/v1/+/signal/+/event' => 1 及 'waw/v1/+/signal/+/status' => 1
```

> **對 Mina UX-P1-4 的影響**：目前 ESP32 設備（v2.0+ 韌體）若用 `waw/v1/.../status` 上報心跳，**Infra 端不會收到**。
> 需要先補上 WAW-USS v1.0 訂閱邏輯（屬於 Infra 內部技術債清理，可列為後續 P2 任務）。
> **短期內 Mina 仍可走 legacy topic**（kiosk/+/status）但需 Member 端配合對應 schema。

### 2.4 Member 端需要的 API：機台活躍狀態查詢

Mina UX-P1-4（超時踢人邏輯）需要查詢「某台 kiosk 最後活動時間」。
**目前 Infra 端沒有對外的 HTTP endpoint 查 heartbeat**。

**選項評估**：

| 選項 | 優點 | 缺點 | 建議 |
| :--- | :--- | :--- | :--- |
| A. 新增 Infra API `GET /internal/device/{chip_id}/status`（從 Redis 讀） | 30 分鐘內可上線，複用 `getDeviceStatusFromRedis` | 需在本任務範圍外額外動工 | ✅ **本任務建議補上** |
| B. Member 直接查 `iotv9.kiosks.last_active_at`（或 updated_at） | 零 Infra 改動 | heartbeat 與 kiosk 配對不嚴謹（chip_id ≠ kiosk_id） | ⚠️ 暫行方案 |
| C. Member 訂閱 MQTT `kiosk/+/status` 自行處理 | 即時性高 | Member 需加 mqtt client，架構複雜化 | ❌ 不建議 |

**Ina 端將在 P0-3 配套工作中補上選項 A**（見第 4 節「建議後續任務」）。

---

## 3. SSL 憑證配合

### 3.1 Infra API SSL 狀態（已驗證）

✅ **所有 tg25.win 對外 domain 均使用 Google Trust Services 簽發的有效憑證**。

| Domain | Subject | Issuer | 效期 |
| :--- | :--- | :--- | :--- |
| `api.tg25.win` | `CN=tg25.win` | `C=US, O=Google Trust Services, CN=WE1` | 2026-09-10 ~ **2026-12-09** |
| `win.tg25.win` | `CN=tg25.win` | `C=US, O=Google Trust Services, CN=WE1` | 2026-09-10 ~ 2026-12-09 |
| `mqtt.tg25.win` | `CN=tg25.win` | `C=US, O=Google Trust Services, CN=WE1` | 2026-09-10 ~ 2026-12-09 |

驗證指令（本機執行）：
```bash
$ echo | openssl s_client -servername api.tg25.win -connect api.tg25.win:443 \
  2>/dev/null | openssl x509 -noout -subject -issuer -dates
subject=CN=tg25.win
issuer=C=US, O=Google Trust Services, CN=WE1
notBefore=Sep 10 20:27:07 2026 GMT
notAfter=Dec  9 21:27:04 2026 GMT
```

**結論**：Mina 端可安全將 `verify` 從 `false` 改為 `true`，**無需提供 CA bundle**（憑證由系統 CA 信任鏈覆蓋）。

### 3.2 ⚠️ 唯一例外：MQTT 內部連線使用自簽憑證

`/home/ubuntu/tg25-infra/waw-iot/app/Console/Commands/MqttListenCommand.php` 行 51：
```php
->setTlsSelfSignedAllowed(true); // VPS 自簽證書
```
這是 **server→broker**（Infra→mqtt.tg25.win）端點的 MQTT TLS，**與 Member→Infra 的 HTTPS 無關**，
Mina 改 P0-5 的 SSL verify 不受影響。

---

## 4. 建議後續任務（列入下個 sprint）

| 編號 | 項目 | 預估工時 | 優先級 |
| :--- | :--- | :--- | :--- |
| T1 | 在 `MqttListenCommand.php` 補上 `waw/v1/+/signal/+/status` 訂閱（消除技術債） | 2-3 小時（含 handler） | P2 |
| T2 | 新增 `GET /internal/device/{chip_id}/status` endpoint（從 Redis 讀，給 Member UX-P1-4 用） | 1 小時 | P1 |
| T3 | 評估 Reverb 對外暴露方案（nginx reverse proxy wss://api.tg25.win → 127.0.0.1:6009） | 2 小時（含 nginx + 憑證） | P2，需 HQ 決策 |
| T4 | Member 端 `REVERB_*` 環境變數同步（與 Infra 端共用 app key/secret） | 0.5 小時（Mina 自處理） | P1 |

---

## 5. 本次任務實際異動清單

**無**。本任務為盤點與回報性質，Infra 端設定已正確。
若 Mina 改 P0-3 需要 Ina 端新增 endpoint，請派發新工單（建議直接綁定 T2）。

---

## 6. 結論

✅ **P0-3 Reverb Private/Presence Channel**：Infra 端 Reverb 服務已支援，**無需異動設定**。Mina 端完成 Member 程式碼改動後，Reverb 即可正確處理 PrivateChannel 認證（透過 `routes/channels.php` 的 `Broadcast::channel()` callback）。

✅ **MQTT Heartbeat Topic**：唯一真理正本 = `waw/v1/{site_id}/signal/{chip_id}/status`（payload: `{status, chip_id, firmware_version, ip, rssi, uptime_seconds, timestamp}`，**無 session_id 與 game_active 欄位**）。Mina 派工單的 `waw/kiosk/{kiosk_id}/heartbeat` 假設錯誤。

✅ **Infra 端 listener 寫入位置**：
  - Python `kiosk_event_listener.py`：轉拋 Member webhook（不寫 DB/Redis）
  - Laravel `MqttListenCommand.php`：寫 `iotv9.machines.last_seen_at` + Redis `v9:machine:{chip_id}:status`

✅ **SSL 憑證**：`api.tg25.win` 使用 Google Trust Services 有效憑證（2026-12-09 到期），Mina 可直接將 `verify=false` 改為 `true`，**無需 CA bundle**。

⚠️ **技術債警告**：`waw/v1/+/signal/+/status` 主標準 topic **尚未被任一 Infra listener 訂閱**，需 T1 任務補上。

---

**回報者**：Ina
**回報時間**：2026-09-14 11:30
**派工單狀態**：✅ 已完成（盤點性質，無程式碼異動）
