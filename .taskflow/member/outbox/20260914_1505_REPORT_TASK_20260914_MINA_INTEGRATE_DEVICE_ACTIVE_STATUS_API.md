# 回報：TASK_20260914_MINA_INTEGRATE_DEVICE_ACTIVE_STATUS_API

**完成時間**：2026-09-14 15:05
**負責人**：Mina (Member)
**來源任務**：TASK_20260914_MINA_INTEGRATE_DEVICE_ACTIVE_STATUS_API
**Commit**：`e56390d`

---

## 執行內容

### 1. DeviceController — 新增 fetchDeviceActiveStatus 方法 + checkSession 整合

**檔案**：`app/Http/Controllers/Api/DeviceController.php`

- 新增 `private function fetchDeviceActiveStatus(string $chipId): array|null` 方法
  - 呼叫 Infra `GET /api/device/{chip_id}/active-status`
  - 帶 5 秒超時，失敗時返回 null（fallback）
- 修改 `checkSession()` 超時邏輯：
  - 呼叫 `fetchDeviceActiveStatus()` 查詢機台活躍狀態
  - 若 `is_active === true`：超時延長至 300 秒 + 更新 `last_activity_at` 防止誤踢
  - 若 `is_active === false` 或 API 失敗：使用原本 180 秒超時邏輯

### 2. CheckOfflineSessions — Cron 踢人前先查機台活躍狀態

**檔案**：`app/Console/Commands/CheckOfflineSessions.php`

- 新增 `DeviceSession` 模型查詢，處理 game_v0 設備 session 超時
- 新增 `private function checkDeviceActive(string $chipId): bool` 方法
  - 呼叫 Infra active-status API
  - `is_active === true`：延長 session（`last_activity_at = now()`）
  - API 失敗：fallback 為 false（保守終止，防止殭屍 session）
- 日誌記錄每個延長/終止的 session

### 3. 前端對齊

**檔案**：`resources/views/play.blade.php`、`app/Http/Controllers/Api/DeviceController.php`

- 移除 UX-P1-4 TODO 標註
- 服務協議文字從「180 秒無遊戲活動」改為「300 秒無機台活動將自動結束遊戲」
- 前端 `agreementText` 同步更新

---

## 驗證結果

| 項目 | 結果 |
| :--- | :--- |
| 本機 `php -l` 語法檢查 | ✅ 無錯誤 |
| 遠端 `php -l` 語法檢查 | ✅ 無錯誤 |
| Git Push | ✅ `c11a78f..e56390d` |
| 遠端部署 | ✅ `waw_ops.sh deploy mina` 成功 |
| 首頁 | ✅ 200 |
| Play 頁 | ✅ 200 |
| Cron 命令測試 | ✅ `Terminated 0 sessions, extended 0 active-device sessions.` |
| Infra active-status API | ✅ `{"chip_id":"SR9ADYXPDYT1TUF7","status":"offline","is_active":false,"source":"iotv9.machines"}` |

## 防禦設計說明

1. **API 超時 fallback**：`fetchDeviceActiveStatus()` 和 `checkDeviceActive()` 都設 5 秒超時；若 Infra 不可達，fallback 為 false（終止 session），確保不產生永久殭屍 session
2. **雙層檢查**：即時（`checkSession` API）+ 定時（`CheckOfflineSessions` Cron）都整合 active-status 查詢
3. **延長而非豁免**：活躍機台的 session 只是延長超時，不是永久豁免；若機台隨後離線，下次 Cron 仍會終止

---

**回報人**：Mina
**回報時間**：2026-09-14 15:05

