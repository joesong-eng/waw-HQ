# 執行回報：徹底拔除 v8 遺留廣播與清理殭屍檔案

**回報時間**：2026-10-01 (台北時間)  
**執行者**：Ina (Infra Master)  
**指揮鏈**：HQ  
**狀態**：✅ 部署完成並驗證通過  
**關聯 commit**：`0cb538b` (tg25-infra: `main`)

---

## 1. 問題成因與調查結果

- **背景**：Sophie 回報有未知外部來源（`python-requests`）持續向 `wawv8.tg25.win/api/internal/broadcast/device-update` 發送 POST 請求，由於 v8 站點已停用，造成 Nginx 大量產生 404 報錯。
- **根本原因**：
  - 經查為 `infra` (141.148.165.50) 上運行的 MQTT 監聽服務 (`mqtt/scripts/listener.py`) 遺留之雙軌廣播邏輯。
  - 腳本預設配置包含：
    - `BROADCAST_API_URL = "https://wawv8.tg25.win/api/internal/broadcast/device-update"`
    - `BROADCAST_ENABLED = True`
  - 每當接收到機台 `coin_in`、`payout` 或 `alarm` 訊號時，系統除執行 v9 廣播外，亦呼叫 `trigger_broadcast()` 透過 `requests.post` 重試 3 次連線 v8，產生延遲與 404 請求。
  - v8 廣播與現行 v9 營運 (`iot.tg25.win`) 完全獨立，移除後對 v9 零負面影響。

---

## 2. 處置與清理範圍 (共 11 檔案變更，刪除 5,702 行)

### 2.1 核心程式碼修復 (`mqtt/scripts/listener.py`)
1. **移除 v8 廣播配置與函式**：
   - 刪除 `BROADCAST_API_URL`、`BROADCAST_API_KEY`、`BROADCAST_ENABLED`。
   - 刪除 `trigger_broadcast()`。
2. **移除冗餘 legacy 呼叫**：
   - `on_message` 中移除 `handle_credit_in`、`handle_credit_out` 與 `update_device_status` 呼叫。
   - 移除 `handle_alarm` 中的 v8 廣播呼叫。
   - 將狀態變更的心跳更新直接統一由 `update_device_heartbeat()` 處理。

### 2.2 刪除殘留備份與殭屍檔案
- `mqtt/scripts/listener.py.backup_20260819` (刪除)
- `mqtt/scripts/listener.py.backup_before_arrears` (刪除)
- `mqtt/scripts/listener.py.backup_phase6` (刪除)
- `mqtt/scripts/listener.py.example` (刪除)
- `mqtt/scripts/listener_fix.patch` (刪除)
- `mqtt/scripts/migrate_iot_to_v9.py` (刪除)

### 2.3 規格文檔與輔助腳本同步
- `db/credentials/ALL_CREDENTIALS.md`：刪除 `wawv8.tg25.win` 廢棄資料庫連線資訊。
- `mqtt/README.md`：移除 v8 廣播說明。
- `db/scripts/create_device_registration_tables.sql`：清除註解中對 `wawv8` 的依賴描述。
- `mqtt/scripts/iot002-monitor.py`：API 金鑰更新為 v9 標準。

---

## 3. 部署與即時日誌驗證

1. **代碼發布**：
   - 本機 Commit `0cb538b` 並推送到 GitHub 遠端倉庫 `main`。
2. **遠端同步與服務重啟**：
   - `infra` VPS (`/home/ubuntu/tg25-infra`) 同步至最新 commit。
   - `mqtt-listener` 服務重新啟動成功（`systemctl is-active` -> `active`）。
3. **運作監控驗證 (`/var/log/mqtt-listener.log`)**：
   - 監聽器正常處理設備上報訊息。
   - 僅存在發送至 `iot.tg25.win` 之 `[v9] [BROADCAST_SEND]` 與 `Broadcast OK` 日誌。
   - 針對 `wawv8.tg25.win` 的 `[BROADCAST_ATTEMPT]`、逾時重試及 404 報錯已徹底消失。
