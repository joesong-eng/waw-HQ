# 任務回報：TASK_20260909_SIDNEY_CALLBACK_ACK_SECURITY

- **任務 ID**：`TASK_20260909_SIDNEY_CALLBACK_ACK_SECURITY`
- **執行 Agent**：Sidney (SignalHub Lead)
- **決策者 / 評審**：Joe (Boss / 最高決策者)
- **回報對象**：HQ (Taskflow 總指揮)
- **日期時間**：2026-09-09 16:30:00 (UTC+8)
- **狀態**：✅ 100% 達成並已部署生產驗證 (COMPLETED & VERIFIED)

---

## 📋 本次任務重點與落實成果

針對小猴（合作端/遊戲伺服器）在異步結算回調端點（`https://signal.tg25.win/api/v9/signal-hub/callback-ack`）缺乏安全驗證之重大漏洞，完成全面架構升級與四重安全防線實作：

### 1. 動態時效簽名 URL 機制 (`ProcessWebhookDelivery`)
- **零代碼負擔理念**：小猴等合作端無須在其異步回調客戶端編寫複雜的 HMAC 簽名演算法，SignalHub 在推送信號時，動態將專屬 HMAC-SHA256 Token 與時效窗口注入 `reply_url`：
  ```
  https://signal.tg25.win/api/v9/signal-hub/callback-ack?delivery_id=del_10284&token={HMAC_TOKEN}&expires={TIMESTAMP}
  ```
- **單筆單密雜湊**：以 Webhook 專屬 `secret_key` 針對 `del_{id}:{expires}` 進行雜湊，外網攻擊者無法憑空偽造。

### 2. 獨立結算回調控制器 (`CallbackAckController`) 四重防線
- **時效驗證 (Expiration Window)**：預設 15 分鐘（900 秒）時效窗口，超時請求直接返回 `401 Token Expired`。
- **HMAC 常數時間比對 (Constant-time Comparison)**：使用 `hash_equals()` 防止時序攻擊；雙軌相容 URL Token 與 Header `X-WAW-Signature` 簽名。
- **數據一致性校驗 (Data Integrity)**：核對回傳之 `chip_id` 與 `pin_code` 是否與原資料庫紀錄相符。
- **等冪性防禦與金額格式過濾 (Idempotency & Anti-Tamper)**：
  - 嚴格要求 `actual_points >= 0`（非負整數）。
  - 已結算成功之單號，重複提交相同金額視為合法冪等確認（返回 200 OK）。
  - 若已結算完成卻企圖以不同金額覆蓋竄改，系統直接阻斷並返回 `409 Conflict`。

### 3. Mock 伺服器與文檔全線對齊
- `MockCallbackController.php` 升級支援動態簽名 `reply_url`，並內建遺失 URL 時之自動簽名補救。
- 整合文檔 `docs/THIRD_PARTY_INTEGRATION_GUIDE.md` 與 `docs/SIGNALHUB_SYSTEM_DESIGN_v2.md` 同步更新至最新規範。
- `webhooks.blade.php` 範例代碼同步更新。

---

## 🚀 部署與遠端 VPS 真實驗證證據

- **Git 最新 Commit**：`bfb2219` (branch: `main`)
- **遠端主機**：`129.153.116.174:39022` (`signal.tg25.win`)
- **部署工具**：`waw_ops.sh deploy sidney` (零停機成功)

### 遠端真實測試數據矩陣：

| 測試情境 | 請求特徵 | 預期結果 | 遠端實測結果 |
|---|---|---|---|
| **1. 未授權存取** | 無 Token、無 Header 直接 POST | 401 Unauthorized | ✅ HTTP 401 `身分驗證失敗：無效或缺失安全簽名憑證` |
| **2. 偽造 Token 攻擊** | 隨意傳送 `token=fake_token_123456` | 401 Unauthorized | ✅ HTTP 401 `身分驗證失敗：無效或缺失安全簽名憑證` |
| **3. 過期 Token 攻擊** | 傳送已過期時間戳（如 `expires=1000000000`） | 401 Unauthorized | ✅ HTTP 401 `回調時效已過期 (Callback token has expired)` |
| **4. 正向簽名結算** | 持有效動態簽名 URL 回傳 `actual_points: 2500` | 200 OK | ✅ HTTP 200 OK `cleared_points: 2500` 入庫 |
| **5. 冪等性重複提交** | 相同單號以相同點數 1000 再次提交 | 200 OK | ✅ HTTP 200 OK `結算已確認 (Idempotent ACK already recorded)` |
| **6. 惡意覆蓋竄改** | 已結算成功之單號企圖竄改為 999999 點 | 409 Conflict | ✅ HTTP 409 `該推送已完成結算，禁止篡改已確定金額` |
| **7. 瀏覽器 GET 友善響應** | 瀏覽器直接點開 URL | 200 OK Info | ✅ HTTP 200 OK 提示使用 POST 提交並提供文檔連結 |

---

## 結論
✅ **已完成驗收並正式上線運作**。
SignalHub 回調安全機制已達到企業級防偽標準，杜絕外網盜刷、金額篡改與偽造點數之風險。

