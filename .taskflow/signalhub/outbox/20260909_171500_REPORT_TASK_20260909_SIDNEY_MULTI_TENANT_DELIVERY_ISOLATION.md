# 任務回報：TASK_20260909_SIDNEY_MULTI_TENANT_DELIVERY_ISOLATION

- **任務 ID**：`TASK_20260909_SIDNEY_MULTI_TENANT_DELIVERY_ISOLATION`
- **執行 Agent**：Sidney (SignalHub Lead)
- **決策者 / 評審**：Joe (Boss / 最高決策者)
- **回報對象**：HQ (Taskflow 總指揮)
- **日期時間**：2026-09-09 16:40:00 (UTC+8)
- **狀態**：✅ 100% 達成並已部署生產驗證 (COMPLETED & VERIFIED)

---

## 📋 業務問題與多租戶資料隔離

### 核心問題定位：
當有多家店主（如店主 A 串接小猴，店主 B 購買自訂採集卡並串接其他系統）同時使用 SignalHub 時，必須確保**資料絕對隔離，絕不可互相窺探或跨租戶洩漏信號**。

經全面審查，系統在以下四道防線完成徹底加固：

1. **信號觸發與推送分發隔離 (`HandleWebhookDelivery`)**：
   - **原潛在隱患**：若店主 B 設定 `profile_id: NULL`（代表該店主名下全部設備），先前的推送匹配邏輯未對 `owner_id` 進行強制約束，導致店主 A 的設備信號會被誤廣播至店主 B 的 Webhook 端點。
   - **加固修正**：在 `getMatchingWebhooks` 中加入嚴格多租戶條件：`$query->where('owner_id', $ownerId)`。店主 B 即使設定「全部設備」，也**僅能且絕對只能**接收店主 B 自己設備的信號。

2. **Webhook 設定越權防護 (`SignalHubController`)**：
   - 在 `storeWebhook` 與 `updateWebhook` 中，增加 `Rule::exists('signal_profiles', 'id')->where('owner_id', auth()->id())` 驗證，禁止任何用戶將 Webhook 綁定至他人機台。

3. **後台「派送記錄」頁面隔離 (`indexDeliveries` & `showDelivery`)**：
   - 列表查詢 API 嚴格約束 `whereHas('webhook', fn($q) => $q->where('owner_id', auth()->id()))`。
   - 店主 A 登入後**只能看到店主 A 的派送記錄**。
   - 店主 B 登入後**只能看到店主 B 的派送記錄**。
   - 單筆查詢 (`showDelivery`) 具備防越權檢查，跨帳號直接查詢他人物件返回 `404 Not Found`。

4. **異步回調密鑰簽名隔離 (`CallbackAckController`)**：
   - 每筆推送記錄的動態 Token 均使用該 Webhook 的專屬 `secret_key` 加密。
   - 合作端（小猴）即便持有 Token，也無法簽收或操作其他廠商的推送單號。

---

## 🚀 遠端多租戶模擬驗證結果

在生產主機（`signal.tg25.win`）建立模擬租戶 A（Owner: 8881）與租戶 B（Owner: 8882）：
- **租戶 A 機台觸發脈衝** ➔ 租戶 A Webhook 收到派送 (1 筆)，租戶 B Webhook 收到 0 筆。
- **租戶 B 登入 `/signal-hub/deliveries` 派送記錄頁面** ➔ 總筆數為 0，完全看不到租戶 A 的任何記錄。
- **租戶 B 嘗試透過 API 查詢租戶 A 單號** ➔ 系統直接回傳 404 ModelNotFoundException，徹底杜絕 IDOR 越權存取。

