# 任務回報：TASK_20260913_INA_PUBLIC_TOKEN_SCHEMA_AND_RESOLVER

**完成時間**：2026-09-14 00:05  
**執行者**：Ina (Infra Master)  
**指導規範**：`brains/knowledge/02_technical_standards/QRCODE_FORMAT_STANDARD.md` (v2.0.0)  
**狀態**：✅ 完工驗收通過  

---

## 📋 執行項目與成果

### 1. 資料庫 Schema 變更與索引建立
已建立標準 Migration 檔案 `db/migrations/20260913_add_public_token_schema.sql` 並在遠端 DB 執行完畢：
- **`alliance_db.ali_device_bindings`**：
  - 新增欄位 `public_token VARCHAR(64) NULL AFTER node_id`
  - 建立唯一索引 `UNIQUE KEY unq_public_token (public_token)`
- **`iotv9.ali_device_bindings`**：
  - 同步維護鏡像表欄位與唯一索引
- **`iotv9.devices`**：
  - 新增欄位 `public_token VARCHAR(64) NULL AFTER chip_id`
  - 建立唯一索引 `UNIQUE KEY unq_devices_public_token (public_token)`

### 2. 舊資料一次性補填
撰寫並執行補填腳本 `db/scripts/backfill_public_tokens.py`：
- `alliance_db.ali_device_bindings`：7 筆舊資料補填 32 碼隨機 token。
- `iotv9.devices`：19 筆舊資料補填 32 碼隨機 token。
- 補填完成後無 NULL 遺漏，無 duplicate key 衝突。

### 3. API 端點實作與加速
- 服務修復：修正 `api/credit-relay/routers/device.py` 歷史語法錯誤，使 Credit API 穩定運行。
- 新增端點：`GET /api/device/by-token/{token}`
  - 認證相容：支援 `X-Internal-Key` 及 `X-API-Key` 驗證（包含 Member 站使用的 `v9_backend_token_2026`）。
  - 回傳結構：與現有 `by-node/{node_id}` 完全對齊（`DeviceParamsResponse`）。
  - 緩存加速：查詢成功後自動以 Redis `v9:device:token:{token}` 寫入快取，TTL 60 秒。

---

## 🔍 驗收測試證明

1. **認證失敗測試**：
   - 無 Key / 錯誤 Key 呼叫 `GET /api/device/by-token/{token}` 均正確回傳 `401 Unauthorized`。
2. **不存在 Token 測試**：
   - 帶正確 Key 呼叫不存在的 Token 回傳 `404 Not Found`。
3. **正常查詢測試**：
   - 透過本機與 Member VPS (`win.tg25.win`) 呼叫 `https://141.148.165.50/api/device/by-token/18253400ef7843c284d53dedcbde4910`：
     - 回傳 `HTTP 200 OK`
     - 回傳 JSON 欄位包含 `chip_id`, `node_id`, `name`, `status`, `pulse_to_display`, `pulse_to_token`, `out_pulse_to_ticket`。
4. **Redis 快取驗證**：
   - 執行 `redis-cli get 'v9:device:token:18253400ef7843c284d53dedcbde4910'`，確認快取命中且 TTL 正確倒數。

