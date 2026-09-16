# 任務：TASK_20260914_MINA_P0_BACKEND_SECURITY
**派發時間**：2026-09-14 11:00
**優先級**：CRITICAL（緊急安全）
**負責人**：Mina (Member)
**來源**：20260914_093000_REPORT_MEMBER_FULL_CODE_AUDIT.md

## 任務描述

以下是 6 項 P0 後端安全漏洞 + 5 項 P1 安全相關邏輯修復，全部為後端 PHP，你可獨立完成。

---

## P0 後端安全漏洞（6 項）

### P0-1：AuthController 後門無環境保護
- 檔案：app/Http/Controllers/Api/AuthController.php
- 問題：TEST_MODE_886937271782 magic string 可在 production 繞過 Firebase 驗證登入
- 修復：加入 app()->environment('local', 'staging') 守衛
- 預估：10 分鐘

### P0-2：LINE Login 憑證硬編碼
- 檔案：app/Http/Controllers/Api/LineLoginController.php
- 問題：clientId = '2009625522'、clientSecret = '20f443a0498bcdbfb1e24906f40704e3' 直接寫死
- 修復：移至 .env（LINE_CLIENT_ID、LINE_CLIENT_SECRET），config/services.php 新增 line 段落，Controller 改用 config()
- 注意：Git 歷史清理與 LINE Console Secret rotation 由 HQ 協調 Owner 處理，你只需完成程式碼部分
- 預估：30 分鐘

### P0-3：WebSocket 頻道全為 Public Channel
- 檔案：app/Events/MemberPointsUpdated.php、DeviceCreditOut.php、SessionTerminated.php、KioskSessionUpdated.php、MemberBoundToKiosk.php、KioskEscrowPending.php、KioskRejected.php
- 問題：所有事件使用 Channel（Public），任何人可監聽會員餘額變動、洗分結果、Session 終止等
- 修復：
  1. Member 相關事件改為 PrivateChannel
  2. Kiosk 平板頻道改為 PresenceChannel（需認證）
  3. routes/channels.php 加入頻道授權邏輯
  4. 前端 echo.js 加入 Sanctum token 認證
- 注意：Reverb 端設定由 HQ 協調 Ina 處理，你先完成 Member 端程式碼
- 預估：2-3 小時

### P0-4：Engineering 指令端點無認證
- 檔案：routes/api.php → EngineeringController::kioskCommand()
- 問題：/api/engineering/kiosk/cmd 無任何 auth middleware，任何人可遠端重啟/OTA 所有 Kiosk
- 修復：加入 Sanctum + admin role 檢查，或 X-Internal-Key 驗證
- 預估：15 分鐘

### P0-5：SSL 憑證驗證全面關閉
- 檔案：app/Http/Controllers/Api/DeviceController.php、KioskController.php
- 問題：所有對 Infra 的 HTTP 呼叫 'verify' => false，允許 MITM 攔截 X-Internal-Key、會員資料
- 修復：配置正確 CA 憑證路徑，設 'verify' => true 或指向系統 CA bundle
- 預估：30 分鐘

### P0-6：內部金鑰比對使用 === 而非 hash_equals()
- 檔案：DeviceController.php、CallbackController.php、EngineeringController.php、KioskController.php
- 問題：$key === config('services.infra.callback_key') 可被時序攻擊逐字元破解
- 修復：全部替換為 hash_equals(config('services.infra.callback_key'), $key)
- 預估：20 分鐘（約 8 處替換）

---

## P1 安全相關邏輯修復（5 項，與 P0 同批處理）

### P1-1：幣別常數不一致 — Kiosk 餘額顯示永遠為 0
- 問題：MemberBoundToKiosk 查詢 currency_type = 'POINT' 但系統常數是 'COIN'；AuthController 建立 'CASH' 錢包無人使用；BillAcceptorService 用 ['COIN','TOKEN','POINT']
- 修復：全局搜索 'POINT'、'TOKEN'、'CASH' 字串硬編碼，統一替換為 MemberWallet::CURRENCY_COIN / CURRENCY_TICKET，移除 CASH 錢包建立邏輯
- 預估：1 小時

### P1-2：MemberController 交易查詢無權限驗證
- 檔案：app/Http/Controllers/Api/MemberController.php
- 問題：$memberId = $request->query('member_id') 未驗證是否為當前用戶，任何登入會員可查他人交易
- 修復：$memberId = $request->user()->id;（忽略前端傳入）
- 預估：10 分鐘

### P1-3：CheckOfflineSessions 描述與實作不符
- 檔案：app/Console/Commands/CheckOfflineSessions.php
- 問題：描述 3 分鐘但實際 60 秒就終止 Session
- 修復：統一為 180 秒
- 預估：5 分鐘

### P1-4：CallbackController::settle() 潛在 NPE
- 檔案：app/Http/Controllers/Api/CallbackController.php
- 問題：$wallet->increment('balance', $amount) 若 $wallet 為 null 直接 500 Error，在 DB::transaction 中可能導致金額遺失
- 修復：加 null check + firstOrCreate fallback
- 預估：15 分鐘

### P1-6：KioskController::sessionStatus() 更新心跳導致殭屍 Session
- 檔案：app/Http/Controllers/Api/KioskController.php
- 問題：不管 session 有沒有 member 都更新 last_active_at，殭屍 session 永遠不過期
- 修復：僅在 $session->member_id 不為 null 時更新 last_active_at
- 預估：10 分鐘

### P1-7：database/database.sqlite 進了 Git
- 問題：SQLite 資料庫本體被版控追蹤
- 修復：git rm --cached database/database.sqlite，加入 .gitignore
- 預估：5 分鐘

---

## 執行要求

1. 依序執行：P0-1 -> P0-4 -> P0-6 -> P0-5 -> P0-2 -> P1-2 -> P1-3 -> P1-4 -> P1-6 -> P1-7 -> P1-1 -> P0-3
2. P0-3（WebSocket PrivateChannel）放在最後，因為改動面最大且前端需配合
3. 每項修復完成後 commit，commit message 格式：fix(security): P0-1 AuthController backend guard
4. 不接受口頭報告，完成後回報 commit hash + 修改檔案清單至 outbox
5. 若 P0-3 需要前端 echo.js 配合，在同一任務中一併處理
6. LINE Secret rotation 與 Reverb 設定不在你的範圍，HQ 另行協調

---

**派發者**：HQ
**派發時間**：2026-09-14 11:00
