# 任務：TASK_20260914_MINA_INTEGRATE_DEVICE_ACTIVE_STATUS_API
**派發時間**：2026-09-14 14:20
**優先級**：HIGH
**負責人**：Mina (Member)
**來源**：
- Mina 回報 20260914_1039_REPORT_TASK_20260914_MINA_P0_SECURITY_AND_UX.md 中的 UX-P1-4 (待辦 TODO)
- Ina 完工回報 20260914_134500_REPORT_TASK_20260914_INA_CROSS_DB_TRIGGER_AND_DEVICE_STATUS_API.md

## 一、任務背景
在 UX-P1-4 中，原先 session 超時僅依賴手機端 API 互動（120 秒無操作即超時），容易誤踢正在實體機台上游玩的玩家。
Ina 已完成並部署了設備活躍狀態查詢 API，可透過 Redis 與資料庫綜合判斷機台在 300 秒內是否有活動。

---

## 二、API 對接規格

- **端點**：`GET https://api.tg25.win/api/device/{chip_id}/active-status`
- **認證 Header**：`X-Internal-Key: {config('services.infra.callback_key')}` (即 `v9-internal-key-2026`)
- **回傳範例**：
  ```json
  {
    "chip_id": "SR9ADYXPDYT1TUF7",
    "status": "online",
    "last_seen_at": "2026-09-14T05:10:20Z",
    "is_active": true,
    "source": "redis"
  }
  ```

---

## 三、具體執行項目

### 1. 後端 Session 超時檢查整合 (CheckOfflineSessions 或 Controller)
- **檔案**：`app/Console/Commands/CheckOfflineSessions.php` 及/或 `app/Http/Controllers/Api/DeviceController.php`
- **邏輯改造**：
  - 當玩家手機端在設定時間（如 180 秒）內未呼叫心跳/開分 API 時，**不要立即踢人**。
  - 先呼叫 Infra API `GET /api/device/{chip_id}/active-status`。
  - 若 `is_active === true`：表示機台端（ESP32 / MQTT）仍持續有心跳或事件活躍，**延長 Session 效期，不予踢出**。
  - 若 `is_active === false` 或機台離線：才確認結束 Session。
  - 防禦設計：若呼叫 API 超時或失敗，fallback 至原有超時機制，確保不產生永久殭屍 Session。

### 2. 前端提示或心跳協調 (play.blade.php)
- 確保 `play.blade.php` 的超時倒數或警告視圖與後端邏輯對齊，消除先前的 TODO 標註。

### 3. 本地測試、Commit 與部署
- 確保 `php -l` 語法檢查通過。
- Commit 訊息格式：`feat(device): integrate active-status API for session timeout protection (UX-P1-4)`
- 推送至 `origin/main`。
- 透過 `dev_tools/waw_ops.sh deploy mina` 部署至 `129.146.103.177` (`win.tg25.win`)。

### 4. 驗收要求
- 部署完成後，確保 `https://win.tg25.win/m/play` 運行正常。
- 回報 Commit Hash、修改檔案清單與驗收說明至 outbox。

---
**派發者**：HQ  
**派發時間**：2026-09-14 14:20
