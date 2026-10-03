# 任務：TASK_20261002_SOPHIE_FIX_M9_WEBSOCKET_BROADCAST_STUBS

**派發時間**：2026-10-02
**優先級**：normal（M9 即時監控 WebSocket 廣播 Stub 實作）
**負責人**：Sophie (Owner)
**關聯模組**：Owner (iot.tg25.win / yd174)

---

## 📌 任務背景與目標
依據 2026-09-30 全模組盤點報告，M9 即時監控模組目前在 MQTT 處理鏈路中存在兩處 WebSocket 廣播未實作（TODO 註解）：
1. `app/Services/MqttHeartbeatHandler.php`：心跳狀態變更時的廣播。
2. `app/Services/MqttPulseDataHandler.php`：投退幣營收脈衝發生時的廣播。

兩處需正式接入已存在的 `App\Events\DeviceUpdated` 事件，完成即時狀態與營收數據的 WebSocket 廣播派發。

---

## 📋 具體執行項目

### 1. 補全 MqttHeartbeatHandler 廣播實作
- **檔案**：`app/Services/MqttHeartbeatHandler.php`
- **方法**：`broadcastStatusUpdate(Device $device, bool $isOnline): void`
- **要求**：
  - 引入或調用 `broadcast(new \App\Events\DeviceUpdated(...))`。
  - `DeviceUpdated` 建構子簽章：`__construct(string $deviceId, array $data)`。
  - `$deviceId` 應取 `$device->chip_id ?? (string)$device->id`。
  - `$data` 包含 `status` (`'online'` / `'offline'`) 與 `last_seen_at`。
  - 保留完善 try/catch 與 `Log::error`，避免廣播失敗影響 MQTT 心跳主流程。

### 2. 補全 MqttPulseDataHandler 廣播實作
- **檔案**：`app/Services/MqttPulseDataHandler.php`
- **方法**：`broadcastRevenueUpdate(Device $device, int $revenue, int $amount): void`
- **要求**：
  - 同樣調用 `broadcast(new \App\Events\DeviceUpdated(...))`。
  - `$deviceId` 取 `$device->chip_id ?? (string)$device->id`。
  - `$data` 包含 `revenue`、`amount` 及時間戳等營收異動資訊。
  - 保留完善 try/catch 與 `Log::error`，確保資料安全寫入不受廣播異常阻斷。

---

## 🚀 部署與回報標準
1. 執行語法檢查：`php -l` 確認兩檔案無語法錯誤。
2. Commit 並推送至 `origin/main`。
3. 執行標準部署：`../../dev_tools/waw_ops.sh deploy owner`。
4. 遠端驗證：在 `yd174` 測試 `broadcast(new \App\Events\DeviceUpdated(...))` 或觸發事件，確認無例外中斷且佇列/日誌正常。
5. 完成後依標準格式回報至 `.taskflow/owner/outbox/`。
