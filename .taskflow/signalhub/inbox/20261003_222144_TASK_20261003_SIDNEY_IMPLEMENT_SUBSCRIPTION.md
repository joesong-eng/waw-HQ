# 任務工單：SignalHub 訂閱機制落地（複用 Owner 基礎設施）

- **工單編號**：TASK_20261003_SIDNEY_IMPLEMENT_SUBSCRIPTION
- **派發時間**：2026-10-03
- **負責人**：Sidney (SignalHub)
- **優先級**：P1
- **架構依據**：`brains/knowledge/03_system_architecture/ADR-001_SIGNALHUB_SUBSCRIPTION.md`
- **原始提案**：`.taskflow/archive/signalhub/202610/20260915_103000_PROPOSAL_SIDNEY_TO_HQ_SIGNALHUB_SUBSCRIPTION_DESIGN.md`

---

## 一、HQ 架構裁定摘要（已定案，直接執行）

| 決策 | 內容 |
|:---|:---|
| **複用不重造** | SignalHub 與 Owner **共用 iotv9 DB** + 相同 `config/subscription.php` + 既有 `owner_subscriptions` 表。**只補讀取與攔截層，不建帳務流程** |
| **不建** | 完整 SubscriptionController CRUD、繳費審核、帳務流程（屬 Owner 職責） |
| **定價** | 沿用 config（device 1200/台/月；venue tier_20~500），**不自訂** |
| **寬限期** | 3 天；提醒 7/3/1 天（config 現值） |
| **上線策略** | 程式碼可先落地，但**攔截 middleware 預設停用**（config flag），待 HQ 宣布上線才啟用 |

---

## 二、工作項目

### 項目 1：建立 OwnerSubscription Model（修復幽靈引用）

**檔案**：`app/Models/OwnerSubscription.php`（新增）

- 對應既有表 `owner_subscriptions`（**勿重建表**）：
  - `id, owner_id (unique), plan_tier (basic|pro|enterprise), start_date, end_date, status (active|expired|suspended), last_payment_ref, timestamps`
- `$fillable` / `$casts`（start_date、end_date → date）
- 關聯：`belongsTo(User::class, 'owner_id')`
- 修復 `User.php:127` 的 `hasOne(OwnerSubscription::class, 'owner_id')`

**驗收**：Tinker `new App\Models\OwnerSubscription()` 可載入；`User::find(1)->subscription` 可查。

### 項目 2：訂閱狀態 API

**端點**：`GET /api/v9/subscription/status`

- 回傳當前登入 owner 的訂閱狀態：`{status, plan_tier, start_date, end_date, days_remaining, is_expired, in_grace}`
- 若無訂閱記錄，回 `status: none`

**驗收**：帶有效 token 呼叫回 200 且 JSON 正確。

### 項目 3：EnsureSubscriptionActive Middleware（**預設停用**）

**檔案**：`app/Http/Middleware/EnsureSubscriptionActive.php`

- 依 ADR 攔截點策略：
  - 建立/編輯 profile、webhook、模擬器 GPIO、inbound 上報、webhook 派送 → **封鎖（403）**
  - 查看 deliveries/stats → **允許唯讀**
- 新增 config flag：`config('subscription.enforce', false)`，**預設 false**
- flag=false 時 middleware 直接放行（不影響現行技術測試）

**驗收**：flag=false 時站點功能不受影響；flag=true 時寫入端點回 403、唯讀端點正常。

### 項目 4：前端過期橫幅

- signal-hub 頁面顯示「訂閱已過期，請續費」橫幅（不阻擋瀏覽）
- 資料來源：項目 2 的 status API

**驗收**：過期狀態下可見橫幅，頁面仍可瀏覽。

---

## 三、注意事項

1. **勿重建 `owner_subscriptions` 表**，它由 Owner 管理。
2. **勿建立完整訂閱 CRUD Controller**，超出本工單範圍。
3. 攔截 middleware **務必預設停用**，避免影響小猴團隊現行 webhook 測試。
4. 所有變更需 commit + push，並於遠端部署驗證。

---

## 四、回報要求

寫入 `.taskflow/signalhub/outbox/`，附：
- Commit SHA
- Tinker 實測輸出（Model 可載入）
- status API 的 curl 回傳（含 HTTP code + JSON）
- `curl -sI https://signal.tg25.win/` 狀態碼
- 攔截 flag 預設值證明
