# sysWawIot 全系統五大矛盾修復計劃 (SYSTEM_FIX_PLAN_20260528)
**日期**: 2026-05-28  
**制訂者**: hHQ (HHQM)  
**狀態**: 🔄 等待 Agents 諮詢評估中  

針對稽核報告中發現的 5 個核心微服務邊界與資料庫命名分裂 Bug，特制訂此修復計劃，派發給各模組 Agent 進行可行性評估。

---

## 🎯 五大 Bug 診斷與修復方案

### 🔴 【Bug 1】前端 Token 污染 (Front-end Token Pollution)
- **受影響模組**：`Member` (Mina), `iHub` (Hubie)
- **問題現象**：
  手機 Line 掃 iHub QR Code（`win.tg25.win/kiosk?kiosk=...&token=...`）redirect 到首頁時，前端誤把 URL 中的 iHub session `token` 當作 Line 登入的 `member_token` 存入 localStorage 的 `token` 鍵中。這造成後續所有需要 member_token 的 API 呼叫（如 `POST /api/kiosk/bind`）回傳 401，且污染了用戶登入狀態。
- **修復方案**：
  1. **Member 後端 & 前端 (Mina)**：將 iHub 的參數由 `token` 改名為 `kiosk_token`，避免與 Line Login 的 `token` 衝突。
  2. **iHub 前端 (Hubie)**：同步更新 QR 碼生成 URL 中的參數名為 `kiosk_token`。

---

### 🔴 【Bug 2】資料庫與路由不同步 (Database & Route Desync)
- **受影響模組**：`Alliance` (Allie), `tg25-infra` (Ina)
- **問題現象**：
  1. Alliance 的設備綁定 `bindDevice()` 邏輯要求訂單狀態必須是 `processing`，但設計規格已簡化為僅有 `draft` 與 `completed`，導致出廠綁定流程阻塞（狀態機斷裂）。
  2. FastAPI 路由 `/by-node/{node_id}` 在 `/{chip_id}` 之後定義，導致 `/by-node/xxx` 永遠被攔截成 `chip_id`，造成 HTTP 404/500。
- **修復方案**：
  1. **Alliance (Allie)**：修改 `bindDevice()` 中檢查，使之與最新的 `draft/completed` 狀態機一致，綁定前用 PHP 確認當前 item_id，移除過時的 `processing` 判斷。
  2. **Infra (Ina)**：在 FastAPI `routers/device.py` 中，將 `/{chip_id}` 路由移到 `/by-node/{node_id}` 之後，確保 FastAPI 優先匹配精準的 `/by-node` 前綴路由。

---

### 🔴 【Bug 3】架構越權 (Architectural Privilege Overwrite)
- **受影響模組**：`tg25-infra` (Ina), `wawOwner` (Sophie)
- **問題現象**：
  1. `tg25-infra/mqtt/scripts/listener.py` 中，設備 LWT 斷線觸發的 `update_device_status()` 仍會執行 Raw SQL `UPDATE devices SET status = 'maintenance' ...` 強制覆寫設備狀態。這導致 Owner 後台設定為 `active` 的設備，一旦短暫斷線就會被強制覆寫成 `maintenance`。
  2. `wawOwner` 的 `UserManagementController::store()` 允許寫入 `sub_agent` 角色，但 `EnsureIotAccess.php` 中間件僅放行 `['admin', 'owner', 'staff']`，不含 `sub_agent`，導致新建立的子帳號登入後直接 403 癱瘓。
- **修復方案**：
  1. **Infra (Ina)**：修改 `listener.py` 中的 `update_device_status()` SQL，使其僅更新 `last_seen_at = NOW()`，不再越權變更 `status` 欄位。
  2. **Owner (Sophie)**：修改 `EnsureIotAccess.php`，將 `sub_agent` 納入放行名單中，與實際代碼權限完全對齊。

---

### 🔴 【Bug 4】DB Schema 幽靈查詢 (Ghost Queries on Dropped/Missing Fields)
- **受影響模組**：`tg25-infra` (Ina), `wawOwner` (Sophie)
- **問題現象**：
  1. `tg25-infra` 的 `database.py` 中執行了 `SELECT pulse_ratio FROM devices`，但在最新的資料庫規格中，`devices` 表並無 `pulse_ratio` 欄位（正確的是 `pulse_to_token`、`pulse_to_display` 等）。這會導致高頻 SQL 崩潰。
  2. `wawOwner` 設備參數 V2 Migration 002 執行時受 Table Lock 影響，導致四個新欄位（`ticket_mode`、`out_pulse_to_ticket`、`ticket_value`、`direct_prize_cost`）未能成功寫入資料庫，但 Laravel 代碼卻已經開始查閱這些欄位，形成幽靈查詢 SQL Error。
- **修復方案**：
  1. **Infra (Ina)**：修改 `database.py` 的 SQL 查詢，將不合規格的 `pulse_ratio` 欄位替換為規格內的 `pulse_to_token` 等正確欄位，與 `DB_MANIFEST.md` 保持完全一致。
  2. **Owner (Sophie)**：透過 Migration 或手動補上受 table lock 未能成功寫入的四個新欄位，並驗證生產環境 DB 結構是否與 codebase 對齊。

---

### 🔴 【Bug 5】Python 直譯式語言盲區 (Runtime NameError / Unbound Variable)
- **受影響模組**：`tg25-infra` (Ina)
- **問題現象**：
  `tg25-infra/mqtt/scripts/listener.py` 中，呼叫了 `trigger_member_bill_detected`，其內部使用了 `MEMBER_BILL_API_URL` 變數。然而此變數並未在環境變數加載區定義，`.env.example` 中也缺少此配置，導致該路徑一旦被觸發就會發生 `NameError: name 'MEMBER_BILL_API_URL' is not defined` 崩潰。
- **修復方案**：
  - **Infra (Ina)**：在 `listener.py` 環境變數加載段（約行 37–90）補上對 `MEMBER_BILL_API_URL` 的載入與 Fallback 邏輯，並在 `.env.example` 中宣告該環境變數。

---

## 📅 可行性回報要求
各 Agent (hIna, hSophie, hMina, hAlie, hHubie) 請在接收到諮詢工單後：
1. 確認已詳細閱讀本修復計劃與對應模組的設計文件。
2. 指出該修復方案在自己模組中的具體實作程式碼檔案與行號。
3. 評估是否有潛在的 Side Effect 或回溯相容性風險。
4. 於 `_agent/` 下回報可行性報告。
