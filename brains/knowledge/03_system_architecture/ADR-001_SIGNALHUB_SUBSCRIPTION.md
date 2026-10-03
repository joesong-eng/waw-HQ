# ADR-001：SignalHub 訂閱機制架構裁定

> **文件類型**：Architecture Decision Record
> **決策者**：HQ
> **建立日期**：2026-10-03
> **狀態**：Superseded（部分被 ADR-003 取代）
> **⚠️ 後續**：2026-10-04 Joe 裁定 ADR-003，將訂閱表統一為 `subscriptions`，廢除 `owner_subscriptions`。
> 本 ADR 的「複用 Owner 訂閱基礎設施」方向仍成立，但「以 `owner_subscriptions` 為 SSOT」的決策一已被取代。
> **現行權威**：`ADR-003_SUBSCRIPTION_TABLE_UNIFICATION.md`
> **關聯提案**：`20260915_103000_PROPOSAL_SIDNEY_TO_HQ_SIGNALHUB_SUBSCRIPTION_DESIGN.md`
> **關聯 SPEC**：`WAW_CLEANUP_AND_TASKS_SPEC_20261003.md` P1-1

---

## 1. 背景

Sidney 於 2026-09-15 提報 SignalHub 完全沒有訂閱機制，並列出 Q1–Q8 待 HQ 裁定。
經 HQ 盤點，確認以下**架構事實**：

| # | 事實 | 證據 |
|:--|:---|:---|
| 1 | SignalHub 與 Owner **共用同一個 DB**（`iotv9`） | 兩者 `.env` 皆指向 `iotv9` |
| 2 | 兩者 `config/subscription.php` **完全相同** | `diff` = SAME |
| 3 | `owner_subscriptions` 表**已存在於 iotv9** | Owner migration `2026_03_11_193419` |
| 4 | Owner 已有**完整訂閱堆疊** | Model / Controller / Service / Middleware / Event / Command |
| 5 | SignalHub 的 `User.php:127` 引用 `OwnerSubscription` 但**Model 不存在** | 幽靈引用 |
| 6 | SignalHub 無 `SubscriptionController`、無訂閱路由、無 Middleware | 盤點確認 |

### owner_subscriptions 表結構（既有）

```
id, owner_id (unique, FK→users), plan_tier (basic|pro|enterprise),
start_date, end_date, status (active|expired|suspended),
last_payment_ref, timestamps
```

---

## 2. 核心決策

### 決策一：SignalHub **複用** Owner 訂閱基礎設施，不另建平行系統

**理由**：共用 DB + 共用 config + 共用 `owner_subscriptions` 表，若另建一套會造成
資料分裂與雙寫問題。

**實作方式**：SignalHub 端只補「**讀取 + 攔截**」層，**不重複**建帳務流程。

```
┌─────────────────────────────────────────┐
│  iotv9 DB（共用）                        │
│  owner_subscriptions / subscription_audit_logs │
└─────────────────────────────────────────┘
        ↑ 讀寫                    ↑ 讀取
   ┌────────────┐          ┌──────────────┐
   │  Owner     │          │  SignalHub   │
   │ 帳務主控    │          │ 訂閱狀態檢查   │
   │ 審核/續費   │          │ + 功能攔截     │
   └────────────┘          └──────────────┘
```

### 決策二：SignalHub 端補齊項目（最小必要）

1. `app/Models/OwnerSubscription.php`（複用既有表，修復幽靈引用）
2. `app/Http/Middleware/EnsureSubscriptionActive.php`（SignalHub 版攔截）
3. 訂閱狀態 API：`GET /api/v9/subscription/status`
4. 前端過期橫幅（Blade）

**不建**：SubscriptionController（完整 CRUD）、帳務流程、繳費審核（這些屬 Owner）。

### 決策三：攔截點策略（依 Sidney 提案 2.3）

| 攔截點 | 過期後行為 |
|:---|:---|
| 登入後進入 signal-hub | 顯示「訂閱已過期」橫幅，**允許瀏覽** |
| 建立/編輯 profile | 封鎖（403），引導續費 |
| 建立/編輯 webhook | 封鎖 |
| 模擬器觸發 GPIO | 封鎖 |
| 真實設備信號上報（inbound API） | 封鎖（回 403） |
| Webhook 派送（delivery job） | 封鎖（不派送） |
| 查看 deliveries / stats | **允許唯讀** |

### 決策四：參數沿用（不自訂）

| 項目 | 決策 | 依據 |
|:---|:---|:---|
| 定價 | 沿用 `config/subscription.php`（device 1200/台/月；venue tier_20~500） | 兩邊已一致 |
| 寬限期 | 3 天 | config 現值 |
| 續費提醒 | 到期前 7 / 3 / 1 天 | config 現值 |
| 帳務流程 | 沿用 Owner「上傳繳費證明 → 管理員審核」 | 不重造 |

### 決策五：上線時機（依 Sidney 建議）

- **短期（現在）**：**不啟用**攔截（SignalHub 仍在技術測試，小猴團隊串接 webhook 中）
- **中期（核心功能穩定後）**：補 Model + status API + 橫幅
- **長期（正式上線前）**：啟用攔截 middleware + 帳務流程整合

> **實作原則**：程式碼可以先落地，但攔截 middleware **預設停用**（config flag），
> 待 HQ 宣布正式上線時再啟用。

---

## 3. 實作派工

| 任務 | 負責 | 內容 |
|:---|:---|:---|
| SH-1 | **Sidney** | 建 `OwnerSubscription` Model（複用既有表）|
| SH-2 | **Sidney** | 建 `EnsureSubscriptionActive` Middleware（預設停用）+ 訂閱狀態 API |
| SH-3 | **Sidney** | 前端過期橫幅 + 攔截點套用 |
| SH-4 | **Sophie** | 確認 Owner 端訂閱可涵蓋 SignalHub owner（users 表共用驗證）|

---

## 4. 驗收

| # | 驗收項 | 期望 |
|:--|:---|:---|
| 1 | `OwnerSubscription` Model 存在且可載入 | Tinker `new App\Models\OwnerSubscription` 成功 |
| 2 | 訂閱狀態 API 回 200 | `GET /api/v9/subscription/status` |
| 3 | 幽靈引用解除 | `User.php:127` 可正常解析 |
| 4 | 攔截預設停用 | config flag = false，站點功能不受影響 |
| 5 | 站點存活 | `curl -sI https://signal.tg25.win/` = 2xx |

---

**維護者**：HQ
**最後更新**：2026-10-03
