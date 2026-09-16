# ttest@tg25.win 2026-09-14 活動稽核報告

> 報告人：Sidney（SignalHub 負責人）
> 查詢時間：2026-09-15 10:08 (UTC+8)
> 觸發原因：Joe 口頭交付——「我已將 ttest 帳密交給小猴團隊測試，查昨天做了哪些事」
> 守則：只讀查詢，**未動任何代碼、配置檔、DB 資料**

---

## 1. 帳號身份確認

| 項目 | 值 |
| --- | --- |
| email | `ttest@tg25.win` |
| user_id | **11** |
| name | 李董團隊 |
| role | owner |
| phone | 0988-168-168 |
| 帳號建立 | 2026-09-04 05:21:49 |
| 最後更新 | 2026-09-10 06:31:54 |

⚠️ `users` 表**沒有** `last_login_at` / `last_login_ip` 欄位，因此從 DB 無法直接證明「誰、何時、用哪個 IP 登入」。

---

## 2. Laravel DB 層審計（signal.tg25.win / DB=iotv9）

跨多張審計表查詢 `user_id = 11` × `2026-09-14`：

| 審計表 | 9/14 總筆數 | user_id=11 命中 |
| --- | --- | --- |
| device_audit_logs | 0 | 0 |
| venue_audit_logs | 0 | 0 |
| device_command_logs | 0 | 0 |
| debt_collection_logs | 0 | 0 |
| ali_product_audit_logs | 0 | n/a |
| subscription_audit_logs | 0 | n/a |
| message_logs | 0 | n/a |
| settlement_logs | 0 | n/a |
| webhook_events（線上遊戲商回調池） | 0 | n/a |
| sessions（Laravel session） | 0 | 0 |

**結論**：DB 內建的應用層審計表 9/14 完全沒有 ttest 的登錄。
代表：SignalHub 站點目前沒有「使用者操作軌跡」留存機制，只能靠 nginx access log 反推。

---

## 3. nginx access log 反推的「動作清單」（UTC+8）

資料來源：`/www/wwwlogs/signal.tg25.win.log`（過濾掉 bot / wordpress 探掃 / 重複輪詢）

### 3.1 寫入操作（POST/PATCH/PUT/DELETE）

| 時間 | 方法 | 路徑 | 狀態碼 | 推斷動作 |
| --- | --- | --- | --- | --- |
| 10:28:48~50 | POST | `/mock/callback/mode` | 200 | 切換 Mock Callback 收接器模式（連按 3 次） |
| **14:10:13** | GET | `/login` | 200 | 進入登入頁 |
| **14:10:36** | POST | `/login` | 302 | **正式登入成功**（302→`/signal-hub/webhooks`） |
| **14:24:12** | PATCH | `/api/v9/signal-hub/webhooks/2` | 200 | **編輯 webhook #2**（可能是改 secret 或重置失敗計數） |
| 14:36:37 / 14:40:35 / 14:40:47 / 14:42:57 / 15:13:08 / 15:24:37 | POST | `/api/v9/signal-hub/webhooks/2/test` | 200 | **對 webhook #2 按了 6 次「測試發送」按鈕** |
| 15:32:21 / 16:25:55 / 16:32:20 / 16:52:53 / 17:22:59 / 17:30:27 | POST | `/api/v9/signal-hub/simulator/gpio` | 201 | **模擬器觸發 GPIO 信號 6 次**（用 `/signal-hub/simulator` 介面） |
| 16:44:57 | POST | `/api/v9/signal-hub/webhooks/2/test` | 200 | 第 7 次測試 |

### 3.2 頁面瀏覽時序（去重）

| 區間 | 主要動作 |
| --- | --- |
| 08:54 | 首次開啟 `/signal-hub/guide`（公開的開發者指南頁） |
| 08:58~09:00 | `/signal-hub/webhooks` 頁 + `pending-devices` API |
| 09:42~09:47 | 大規模輪詢 `/mock/callback/logs`（每 ~2 秒一次，>150 次），可見另一個瀏覽器分頁持續監看小猴 callback 是否送達 |
| 14:13 | `profiles` / `simulator` / `guide` / `pins(profiles/33)` / `events?profile_id=33` 反覆操作 |
| 14:24 | `PATCH /webhooks/2` 後立刻 `GET /webhooks` 確認 |
| 15:33~15:35 | `simulator` ↔ `deliveries` 切換，**查看 webhook #2 delivery #236 的結果頁** |
| 15:52~16:25 | 多次在 `profiles/33`（實體通訊卡 #01）切換 simulator/profiles/webhooks/deliveries |
| 16:25 | 從 `/signal-hub/simulator` 進入 `/signal-hub/guide`，再進 webhooks |
| 16:32 / 17:30 | 模擬器觸發 GPIO 後立刻切到 deliveries 看派送紀錄 |

**推斷**：至少 1 人（Mac/Windows 雙瀏覽器）在 14:10 登入 ttest，密集操作 webhook #2 + simulator/profiles/33（實體通訊卡 #01）的 GPIO 觸發，並透過 mock callback 與 deliveries 兩處驗證結果。

### 3.3 webhook #2 派送結果（DB 實證）

- 目標：`https://vtuu-api.hoya999.com/callback/thoya999`
- secret_key：`waw_sec_rpvnnodqp2j9hj48fj55fgru`（owner_id=11，即 ttest）
- profile 33 = 「實體通訊卡 #01」

| Delivery | 時間 | pin | event | 結果 |
| --- | --- | --- | --- | --- |
| #236 | 07:32:19 | UI3 | counter | ❌ **401 Unauthorized（Invalid signature）→ expired after 5 retries** |
| #237 | 08:25:51 | UI3 | counter | ❌ 401 / expired |
| #238 | 08:32:17 | UI3 | counter | ❌ 401 / expired |
| #239 | 08:52:51 | UI4 | event | ❌ 401 / expired |
| **#240** | **09:22:58** | UI3 | counter | ✅ **200 success** |
| **#241** | **09:30:27** | UI4 | event | ✅ **200 success** |

> 推測小猴在 14:24 那次 `PATCH /webhooks/2` 是**重置 / 修正 secret** 後才讓後續測試 200 通過。
> `last_success_at = 2026-09-14 09:30:27`、`last_failure_at = 2026-09-14 08:52:53` 已寫回 webhook 表。

### 3.4 對應的 Laravel log 警報

`storage/logs/laravel-2026-09-14.log` 共 32 行，**全部為 `production.ALERT`**：
`Webhook delivery #236/#237/#238/#239 expired 5 retries, {"webhook_id":2,"profile_id":33}`
錯誤訊息：`{"message":"Invalid signature"}` → 指向 `https://vtuu-api.hoya999.com/callback/thoya999`

> 對應的 4 次「小猴測試」其實是：模擬器 POST /simulator/gpio 觸發事件 → SignalHub 派 webhook #2 → 對方回 401 → Laravel 寫 ALERT
> **這些 ALERT 是系統自己記錄的，與小猴按「測試發送」無關**

### 3.5 設備與機台

- **profile 33** = 「實體通訊卡 #01」（signal_profiles，industry_tag=線上遊戲，is_active=1）
- 綁定 **device 42**：chip_id `3c0f02d09118`、name「採集卡 (3c0f02d09118)`、pulse_ratio=10、pulse_to_display=100
- 仍有真機上報：`devices.last_seen_at = 2026-09-14 14:29:51`，is_online=0（14:29 後離線）
- `subscription_status = expired`（小猴測試用的訂閱已過期）

---

## 4. 結論與待辦

### 4.1 小猴昨天做了什麼？（一句話）

登入 ttest 後，密集測試 webhook #2 與實體通訊卡 #01（device 42）的模擬器 GPIO 觸發 → Webhook 派送 → 小猴 callback 收接流程。期間經歷 4 次 401 Invalid signature 失敗 → 14:24 用 PATCH 重置 webhook #2（推測改 secret）→ 後續模擬器測試持續派送，webhook #2 `last_success_at=09:30:27`，沒有更新到 14:xx 測試結果；可推斷 14:xx 按「測試發送」按鈕時 webhook 目標也回 200（否則會有 5 次重試 ALERT，實際 ALERT 只到 08:52:53 止）。

### 4.2 隱含風險

1. ⚠️ **沒有 user activity audit trail**：SignalHub 目前沒在使用者操作層寫審計 log，所有「誰做了什麼」只能靠 nginx log 反推 IP/UA/路徑，無法直接證明「是 ttest 本人 vs. 小猴」。
2. ⚠️ **webhook #2 secret 已被修改過**：secret_key `waw_sec_rpvnnodqp2j9hj48fj55fgru` 是修改後的值，原始值未留存；如需回滾請先備份目前值。
3. ⚠️ **device 42 已離線 + 訂閱過期**：若小猴今天還要繼續測，會卡在訂閱檢查。

### 4.3 建議下一步（待 Joe 裁示）

- 是否補上 `device_audit_logs` 寫入點（SignalHubController / WebhookController / SimulatorController 都需要埋點）
- 是否要保存 webhook secret 修改前後的歷史
- device 42 訂閱是否要協助續期

---

**聲明**：本報告僅基於讀取遠端 nginx access log、Laravel log 與 DB 唯讀查詢（`SELECT`）。未修改任何檔案、未部署任何 commit、未重啟任何服務。
