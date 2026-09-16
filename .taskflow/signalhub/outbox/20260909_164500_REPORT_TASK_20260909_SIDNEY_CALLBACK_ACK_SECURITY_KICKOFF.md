# 任務啟動與方案回報：TASK_20260909_SIDNEY_CALLBACK_ACK_SECURITY

- **任務 ID**：`TASK_20260909_SIDNEY_CALLBACK_ACK_SECURITY`
- **執行 Agent**：Sidney (SignalHub Lead)
- **回報對象**：HQ (Taskflow 總指揮)、Boss Joe
- **啟動時間**：2026-09-09 16:45:00 (UTC+8)
- **優先級**：P1 (High)
- **狀態**：🚀 啟動開發中 (IN PROGRESS)

---

## 📋 背景與安全問題診斷

在 WAW-USS 信號採集開放標準中，SignalHub 支援合作端（小猴/遊戲伺服器）的「雙軌返回模式」：
1. **模式一：同步原路返回 (Sync)**：單次 HTTP 200 回覆金額，零懸置狀態。
2. **模式二：異步 reply_url (Async)**：當合作端系統響應慢時，合作端秒回 200 簽收，並於 10 秒內向 `reply_url` (`https://signal.tg25.win/api/v9/signal-hub/callback-ack`) 主動 POST 回傳實際開洗分金額 (`actual_points`)。

### 現存重大安全隱患：
1. **未授權公開存取**：該端點無身分驗證，外網任何人皆可呼叫。
2. **IDOR 水平越權與偽造點數**：只要猜測 `delivery_id`（如 `del_10284`），即可惡意注入自訂金額、破壞營業對帳。
3. **無時效窗口**：已過期甚至數天前的記錄仍能被非法打入狀態。
4. **無數據一致性審核**：未驗證回傳之 `chip_id`、`pin_code` 是否與原推送匹配。

---

## 🛡️ 實作方案：動態時效簽名 URL（合作方零代碼負擔）

### 1. 發送端動態簽名 (`ProcessWebhookDelivery`)
推送給合作端時，`reply_url` 動態附加時效與 HMAC 憑證：
```
https://signal.tg25.win/api/v9/signal-hub/callback-ack?delivery_id=del_10284&token={HMAC_SHA256}&expires={TIMESTAMP}
```
- Token 計算：`hash_hmac('sha256', "del_{id}:{expires}", secret_key)`
- 合作方工程師無需額外計算簽名，原樣 POST 回傳該 URL 即可自動通過驗證。

### 2. 接收端專用控制器 (`CallbackAckController`) 四重防線
- **時效驗證**：檢查 `expires >= now()->timestamp`（預設 15 分鐘窗口），逾期回傳 401。
- **HMAC 常數時間比對**：利用 `hash_equals()` 防止時序攻擊；同時相容 Header `X-WAW-Signature` 簽名。
- **數據一致性校驗**：核對 `chip_id`、`pin_code` 是否與資料庫單號吻合。
- **等冪性與金額格式防禦**：
  - 嚴格要求 `actual_points >= 0`（整數）。
  - 若該單已結算完成，相同數據返回已記錄（等冪），不同數據拒絕竄改 (409 Conflict)。

---

## 📝 執行步驟與驗收標準
1. ✅ 本機完成代碼修改與重構（新增 `CallbackAckController`、升級 `ProcessWebhookDelivery`）。
2. ✅ 確保 `MockCallbackController` 與指令對帶參數 `reply_url` 100% 相容。
3. ✅ 本機 Git commit 並 push 至 GitHub。
4. ✅ 執行 `waw_ops.sh deploy sidney` 部署至遠端 VPS。
5. ✅ 遠端真實驗證：
   - 正常簽名 Token 回調成功 (200 OK)
   - 偽造 Token 阻擋 (401 Unauthorized)
   - 過期 Token 阻擋 (401 Unauthorized)
   - 重複請求等冪性 (200 OK，無重複寫入)
6. ✅ 同步規範文檔並產出最終結案回報。

