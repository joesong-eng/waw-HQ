# 任務回報：TASK_20260914_INA_CROSS_DB_TRIGGER_AND_DEVICE_STATUS_API

**完成時間**：2026-09-14 13:45
**執行者**：Ina (Infra Master)
**派發來源**：HQ（🔴 HIGH）
**關聯提案**：PROPOSAL_20260914_ALLIE_DEVICES_CROSS_DB_ARCHITECTURE_REFACTOR (Joe 指示)
**關聯任務**：Mina UX-P1-4 機台活動防誤踢
**狀態**：✅ 兩項皆已完工驗收通過

---

## 一、項目 1：MySQL 跨庫同步觸發器

### 1.1 觸發器設計

**位置**：`alliance_db` 資料庫內
**觸發對象**：`alliance_db.ali_device_bindings`
**事件**：`AFTER INSERT` 與 `AFTER UPDATE`
**觸發器**：
| 名稱 | 事件 | 目的 |
| :--- | :--- | :--- |
| `trg_ali_device_bindings_sync_to_iotv9` | AFTER INSERT | 新燒錄時自動同步至 iotv9.devices |
| `trg_ali_device_bindings_sync_to_iotv9_upd` | AFTER UPDATE | 改 chip_id / node_id / public_token / status 時同步 |

**同步路徑**（owner 解析）：
```
alliance_db.ali_device_bindings.order_item_id
  → alliance_db.ali_order_items.id
  → alliance_db.ali_order_items.order_id
  → alliance_db.ali_orders.id
  → alliance_db.ali_orders.owner_id
```

**同步目標**：`iotv9.devices`（INSERT ... ON DUPLICATE KEY UPDATE by chip_id）

**寫入欄位**（沿用 Allie 應用層雙寫的 schema）：
```sql
chip_id              -- LOWER(TRIM(NEW.chip_id))
public_token         -- NEW.public_token (若 NULL 則保留 iotv9 既有值)
owner_id             -- 從 ali_orders.owner_id 解析 (若 NULL 則保留既有值)
collector_owner_id   -- 同 owner_id (WAW 2.0 雙產權)
machine_owner_id     -- 同 owner_id (WAW 2.0 雙產權)
name                 -- 從 ali_products.sku_name (fallback: 'ESP32-{後4碼}')
status               -- 'pending_setup'
subscription_status  -- 'expired'
created_at           -- NOW()（僅 INSERT 時）
updated_at           -- NOW()
```

**守衛條件**：
- `NEW.chip_id` 不可為 NULL 或空字串
- `NEW.node_id` 不可為 NULL 或空字串（unbound 狀態的髒資料不會進 iotv9）
- UPDATE 觸發器只在 chip_id / node_id / public_token / status 有變化時觸發（避免重複寫入）

**與 Allie 應用層雙寫的差異**：
- ✅ Trigger 在**同一個 transaction** 內完成，保證一致性
- ✅ Trigger 解析 `order_item_id → owner_id` 而非依賴 `Order` 物件（更可靠）
- ✅ Trigger 寫入 `public_token`（同步 `OrderController::syncDevicesToCore` 漏掉的欄位）
- ✅ Trigger 對 unbound 設備有守衛（`NEW.node_id` 為 NULL 時不觸發）

### 1.2 Migration 檔案

| 檔案 | 行數 | 用途 |
| :--- | :---: | :--- |
| `db/migrations/20260914_cross_db_trigger_ali_device_to_iotv9.sql` | 145 | 觸發器 DDL |
| `db/scripts/run_cross_db_trigger_migration.py` | 76 | Migration runner（環境變數注入密碼） |

**已 commit + push**：
- Commit: `feat(db): add cross-DB trigger migration for ali_device_bindings → iotv9.devices`
- Commit: `feat(db): add migration runner for cross-DB trigger (env-based credential)`

### 1.3 部署驗證

**觸發器建立**（透過 root 帳號，env-based）：
```bash
$ export INA_DB_USER='root'
$ export INA_DB_PASSWORD='<redacted>'
$ python3 db/scripts/run_cross_db_trigger_migration.py
[*] 載入 migration: /home/ubuntu/tg25-infra/db/migrations/20260914_cross_db_trigger_ali_device_to_iotv9.sql
[*] 連線 MySQL as user=root
[*] 共 5 個 statement 將被執行
[1/5] USE `alliance_db`...
[2/5] DROP TRIGGER IF EXISTS `trg_ali_device_bindings_sync_to_iotv9`...
[3/5] CREATE TRIGGER `trg_ali_device_bindings_sync_to_iotv9` AFTER INSERT ON `ali_devi...
[4/5] CREATE TRIGGER `trg_ali_device_bindings_sync_to_iotv9_upd` AFTER UPDATE ON `ali_...
[5/5] SELECT TRIGGER_NAME, EVENT_MANIPULATION, EVENT_OBJECT_TABLE, ACTION_TIMING FRO...
[OK] Migration 執行成功
```

**觸發器清單驗證**：
```sql
SELECT TRIGGER_SCHEMA, TRIGGER_NAME, EVENT_OBJECT_TABLE, ACTION_TIMING, EVENT_MANIPULATION, DEFINER
  FROM information_schema.TRIGGERS
 WHERE TRIGGER_SCHEMA = 'alliance_db';

-- 結果：
-- alliance_db | trg_ali_device_bindings_sync_to_iotv9     | ali_device_bindings | AFTER | INSERT | root@localhost
-- alliance_db | trg_ali_device_bindings_sync_to_iotv9_upd | ali_device_bindings | AFTER | UPDATE | root@localhost
```

### 1.4 回測驗收（在 production DB 內，ROLLBACK 不污染資料）

使用真實 `order_item_id=13`（關聯 `ali_orders.id=10, owner_id=11`）做 INSERT 測試：

```sql
START TRANSACTION;
INSERT INTO alliance_db.ali_device_bindings (order_item_id, device_id, chip_id, node_id, public_token, status, created_at, updated_at)
VALUES (13, 'TEST_DEVICE_001', 'TEST_CHIP_20260914', 'node_TEST_CHIP_20260914', 'test_token_20260914_abc', 'burned', NOW(), NOW());

-- 查 iotv9.devices（觸發器應自動寫入）
SELECT chip_id, public_token, owner_id, collector_owner_id, machine_owner_id, status, subscription_status, name, created_at, updated_at FROM devices WHERE chip_id = 'TEST_CHIP_20260914';
```

**結果**：
```json
{
  "chip_id": "test_chip_20260914",
  "public_token": "test_token_20260914_abc",
  "owner_id": 11,
  "collector_owner_id": 11,
  "machine_owner_id": 11,
  "status": "pending_setup",
  "subscription_status": "expired",
  "name": "<ali_products.sku_name>",
  "created_at": "2026-09-14 05:02:44",
  "updated_at": "2026-09-14 05:02:44"
}
```

| 測試項 | 結果 |
| :--- | :---: |
| Step 1 INSERT 觸發 | ✅ owner=11, status=pending_setup, sub=expired, name 取自 sku_name |
| Step 2 UPDATE public_token | ✅ 觸發同步，public_token 已更新 |
| Step 3 ROLLBACK 隔離 | ✅ 0 筆（無污染） |
| Step 4 守衛: chip_id NULL | ✅ devices 無增加 |
| Step 5 守衛: node_id NULL | ✅ TEST_CHIP_NODENULL 0 筆 |

### 1.5 給 Allie 的後續動作（待 HQ 通報）

- 🔴 **可立即拔除應用層雙寫**：
  - `app/Http/Controllers/DeviceController.php` 第 200-227 行 `commitRegistration()` 內的 `core()->table('devices')->updateOrInsert(...)`
  - `app/Http/Controllers/OrderController.php` 第 604-655 行 `syncDevicesToCore()` 整個方法
- ⚠️ **保留**：應用層錯誤處理（try/catch + Log）改為僅觸發 trigger 後的驗證查詢
- ✅ **無需修改 Alliance DB schema**

---

## 二、項目 2：設備狀態查詢 API

### 2.1 Endpoint 設計

**路徑**：`GET /api/device/{chip_id}/active-status`

> ⚠️ **路徑微調說明**：派工單原訂 `GET /api/device/{chip_id}/status`，但 `routers/device.py` 已佔用 `/{device_id}/status`（README.md 與 test_kiosk_curl.sh 引用中）。為避免 FastAPI 路由衝突，**改為 `/{chip_id}/active-status`**，語意更精準（避免與既有 `/{device_id}/status` 混淆）。

**認證**：`X-Internal-Key`（值 = `v9-internal-key-2026`，與 Mina 既有 `/api/kiosk/heartbeat` 呼叫一致）
> ⚠️ **認證微調說明**：派工單原訂 `X-Internal-Key / X-API-Key` 皆可，實作改用 `verify_infra_key`（即 `X-Internal-Key`），原因：
> 1. `verify_api_key` 是查 `auth_keys` 表（DB 內的 key pool），Mina 從未使用
> 2. `verify_infra_key` 對應 `settings.infra_key`，與 Mina 既有的 `/api/kiosk/heartbeat` 同一把 key
> 3. Member 端 `infraHttp()` 預設 header 為 `X-Internal-Key`（見 `Member/app/Http/Controllers/Api/KioskController.php`）

**回傳 Schema**：
```json
{
  "chip_id": "SR9ADYXPDYT1TUF7",
  "status": "online | stale | offline | unknown",
  "last_seen_at": "2026-09-14T05:09:44Z",
  "is_active": true,
  "source": "redis | iotv9.machines | iotv9.devices"
}
```

**狀態判斷邏輯**：
| 條件 | status | is_active |
| :--- | :---: | :---: |
| Redis 有值且 timestamp 在 300s 內 | `online` | `true` |
| Redis 有值且 timestamp 在 1h 內 | `stale` | `false` |
| Redis 有值但超過 1h 或 LWT=offline | `offline` | `false` |
| 兩邊都查無資料 | `unknown` (404) | n/a |

**查詢優先順序**（快取優先）：
1. Redis: `v9:machine:{chip_id_upper}:status`（由 `waw-iot/MqttListenerService::storeStatusToRedis` 寫入）
2. MySQL fallback: `iotv9.machines.last_seen_at`
3. MySQL fallback: `iotv9.devices.last_seen_at`

### 2.2 程式碼

**新增檔案**：
| 檔案 | 行數 | 用途 |
| :--- | :---: | :--- |
| `api/credit-relay/services/device_status_service.py` | 201 | 設備活躍度查詢 service |
| `api/credit-relay/routers/device_status.py` | 99 | HTTP endpoint 路由 |

**修改檔案**：
| 檔案 | 變更 |
| :--- | :--- |
| `api/credit-relay/main.py` | 加入 `device_status` router import 與註冊 |

**已 commit + push**：
- `feat(api): add GET /api/device/{chip_id}/active-status endpoint`
- `fix(api): use verify_infra_key (X-Internal-Key) for device status endpoint`

### 2.3 部署與重啟

```bash
cd /home/ubuntu/tg25-infra
git pull origin main
sudo systemctl restart credit-api
# 服務 healthy: HTTP 200 on /api/health
```

### 2.4 完整測試（curl 範例與 JSON 回傳結果）

**T1: 不存在的 chip_id**：
```bash
$ curl -H 'X-Internal-Key: v9-internal-key-2026' \
       'http://127.0.0.1:8084/api/device/UNKNOWN_CHIP_9999/active-status'
HTTP 404
{"detail":{"success":false,"error":"DEVICE_NOT_FOUND",
  "message":"找不到設備 UNKNOWN_CHIP_9999（Redis、iotv9.machines、iotv9.devices 都無記錄）"}}
```

**T2: 真實設備（從 MySQL fallback 路徑）**：
```bash
$ curl -H 'X-Internal-Key: v9-internal-key-2026' \
       'http://127.0.0.1:8084/api/device/sr9adyxpdyt1tuf7/active-status'
HTTP 200
{"chip_id":"SR9ADYXPDYT1TUF7","status":"offline",
 "last_seen_at":"2026-09-14T02:57:59Z","is_active":false,
 "source":"iotv9.machines"}
```

**T3: 無認證**：
```bash
$ curl 'http://127.0.0.1:8084/api/device/sr9adyxpdyt1tuf7/active-status'
HTTP 422
{"detail":[{"type":"missing","loc":["header","X-Internal-Key"],...}]}
```

**T4: 錯誤 key**：
```bash
$ curl -H 'X-Internal-Key: WRONG_KEY' \
       'http://127.0.0.1:8084/api/device/sr9adyxpdyt1tuf7/active-status'
HTTP 401
{"detail":{"success":false,"error":"UNAUTHORIZED","message":"X-Internal-Key (Infra) 無效"}}
```

**T5: 無效 chip_id 格式（含空格）**：
```bash
$ curl -H 'X-Internal-Key: v9-internal-key-2026' \
       'http://127.0.0.1:8084/api/device/BAD-CHIP%20ID/active-status'
HTTP 400
{"detail":{"success":false,"error":"INVALID_CHIP_ID",
  "message":"chip_id 格式不符: BAD-CHIP ID（僅允許英數底線，1~64 字）"}}
```

**T6: 模擬 Redis 寫入後查詢（從 Redis 命中路徑）**：
```bash
$ redis-cli SET 'v9:machine:SR9ADYXPDYT1TUF7:status' \
    '{"chip_id":"SR9ADYXPDYT1TUF7","status":"online","timestamp":1789362620}' EX 300
OK

$ curl -H 'X-Internal-Key: v9-internal-key-2026' \
       'http://127.0.0.1:8084/api/device/sr9adyxpdyt1tuf7/active-status'
HTTP 200
{"chip_id":"SR9ADYXPDYT1TUF7","status":"online",
 "last_seen_at":"2026-09-14T05:10:20Z","is_active":true,
 "source":"redis"}
```

**T7: 從外部 HTTPS 端點（api.tg25.win）測試**：
```bash
$ curl -H 'X-Internal-Key: v9-internal-key-2026' \
       'https://api.tg25.win/api/device/sr9adyxpdyt1tuf7/active-status'
HTTP 200
{"chip_id":"SR9ADYXPDYT1TUF7","status":"online",...}  # 從 Redis 命中
```

### 2.5 給 Mina 的接軌指引

**會員端可立即使用**（範例 PHP）：
```php
// 在 KioskController 或 SessionService 加入
$response = Http::withHeaders([
    'X-Internal-Key' => config('services.infra.callback_key'),
])->timeout(3)->get(
    config('services.infra.base_url') . "/api/device/{$kiosk->chip_id}/active-status"
);

if ($response->successful()) {
    $status = $response->json();
    // $status['is_active'] === true 表示機台在 300 秒內有活動
    // 用於 UX-P1-4: 不只看手機端 API 活動，也看機台端 MQTT heartbeat
}
```

---

## 三、本次任務實際異動清單

### 新增檔案（已 commit + push）
1. `db/migrations/20260914_cross_db_trigger_ali_device_to_iotv9.sql` (145 行)
2. `db/scripts/run_cross_db_trigger_migration.py` (76 行)
3. `api/credit-relay/services/device_status_service.py` (201 行)
4. `api/credit-relay/routers/device_status.py` (99 行)

### 修改檔案（已 commit + push）
1. `api/credit-relay/main.py`（+2 行：import + include_router）

### 遠端服務異動
1. `alliance_db` 資料庫：新增 2 個 trigger（INSERT + UPDATE）
2. `credit-api` systemd 服務：重啟（已 active，新 endpoint 60 個 path 中可見）

---

## 四、結論

✅ **項目 1 跨庫 Trigger**：已在 `alliance_db` 部署 2 個 trigger，回測 INSERT / UPDATE / 守衛 / ROLLBACK 全部通過，**待 HQ 通報 Allie 拔除應用層雙寫**。

✅ **項目 2 設備狀態 API**：`GET /api/device/{chip_id}/active-status` 已上線，從內部（127.0.0.1:8084）與外部（api.tg25.win）均測試通過，**Mina 可立即接軌用於 UX-P1-4**。

⚠️ **路徑與認證微調**：
- 路徑：`/{chip_id}/status` → `/{chip_id}/active-status`（避開與 device.py 的 `/{device_id}/status` 衝突）
- 認證：使用 `X-Internal-Key`（`verify_infra_key`），與 Mina 既有的 `/api/kiosk/heartbeat` 同一把 key

📋 **Mina UX-P1-4 接軌提示**：
- 用 `X-Internal-Key` header（值在 Member 端 `config('services.infra.callback_key')`）
- 端點：`https://api.tg25.win/api/device/{chip_id}/active-status`
- 判斷 `is_active === true` 表示機台 300 秒內有活動
- 失敗時（404/500）應 fall back 到原本的 120s timeout 邏輯

📋 **Allie 拔除雙寫提示**：
- 移除 `DeviceController.php:200-227` 的 `core()->table('devices')->updateOrInsert(...)`
- 移除 `OrderController.php:604-655` 的 `syncDevicesToCore()` 整個方法
- 無需修改 Alliance DB schema
- 測試：建立新訂單 + 燒錄，確認 `iotv9.devices` 自動有對應記錄

---

**回報者**：Ina
**回報時間**：2026-09-14 13:45
**派工單狀態**：✅ 已完成驗收
