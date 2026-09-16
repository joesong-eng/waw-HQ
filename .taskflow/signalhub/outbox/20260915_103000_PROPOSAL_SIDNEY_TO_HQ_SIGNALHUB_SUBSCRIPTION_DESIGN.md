# 提案：20260915_PROPOSAL_SIDNEY_TO_HQ_SIGNALHUB_SUBSCRIPTION_DESIGN

**提交時間**：2026-09-15 10:30  
**提交者**：Sidney (SignalHub Lead)  
**呈報對象**：HQ (Taskflow 總指揮)  
**主旨**：SignalHub 訂閱機制設計方案提案 — 從無到有建立完整訂閱生命週期  
**優先級**：high  
**觸發原因**：Joe 直接口頭指示「正式上線時要考慮訂閱問題」，經盤點確認 SignalHub 目前完全沒有訂閱機制  

---

## 1. 現狀盤點（已查證）

### 1.1 SignalHub 程式碼中訂閱相關 — 幾乎空白

| 項目 | 狀態 | 說明 |
| --- | --- | --- |
| `SubscriptionController` | ❌ 不存在 | 沒有訂閱管理 API |
| `OwnerSubscription` Model | ❌ 不存在 | `User.php` 有引用 `hasOne(OwnerSubscription::class)` 但 Model 檔案不存在，呼叫會報錯 |
| 訂閱路由（API） | ❌ 0 筆 | `routes/api.php` 中無任何 subscription 相關路由 |
| 訂閱路由（Web） | ❌ 0 筆 | `routes/web.php` 中無任何 subscription 相關路由 |
| `SignalHubController` 訂閱檢查 | ❌ 完全沒有 | 903 行中 0 筆訂閱邏輯（只有 `auth()->id()` owner 隔離） |
| `Authv9Controller` 訂閱檢查 | ❌ 完全沒有 | 登入時不檢查訂閱狀態 |
| 訂閱管理 UI（Blade） | ❌ 不存在 | 無任何訂閱方案、續期、帳務頁面 |
| Middleware 攔截 | ❌ 無 | signal-hub 路由只有 `['web', 'auth']`，無 subscription check |

### 1.2 殘留骨架（從 Owner 系統繼承的空殼）

| 項目 | 狀態 | 實際有用嗎 |
| --- | --- | --- |
| `config/subscription.php` | 有完整定價方案（device 1200/月、venue tier 20-500、grace_days=3、discount、bank_account） | ❌ 沒被任何代碼引用 |
| `User.php` `subscription()` 關聯 | 有 `hasOne(OwnerSubscription::class)` | ❌ Model 不存在，呼叫會報錯 |
| `EventServiceProvider` `SubscriptionExpired` 事件 | 有註冊 Listener | ❌ Event/Listener 檔案不存在，實際無法觸發 |

### 1.3 資料庫現況（signal.tg25.win / DB=iotv9）

- `devices` 表有 `subscription_status` / `subscription_expires_at` 欄位，但全是 `expired` 且 `subscription_expires_at = null`
- `owner_subscriptions` 表存在但 **ttest（user_id=11）0 筆紀錄**
- `subscription_audit_logs` 表存在但 9/14 全天 0 筆
- `billing_cycles` 表存在但未確認有無資料

### 1.4 對外測試現況

- 小猴團隊（使用 ttest 帳號）昨天 9/14 能正常登入、設定 webhook、用模擬器觸發 GPIO、測試 webhook 派送
- **因為完全沒有訂閱攔截，所以技術測試不受影響**
- 但正式上線時，若沒有訂閱機制 → **所有功能無條件開放，無法收費、無法管控**

---

## 2. 需要設計的範圍

### 2.1 訂閱生命週期

```
註冊 → 試用（？天） → 過期 → 續費 → 恢復
                ↓                    ↑
              寬限期（？天） → 恢復
```

需確認的問題：
- **訂閱標的**：是綁 device（採集卡）？還是綁 owner（帳號）？還是兩者都有？
- **試用期**：新註冊用戶是否給免費試用天數？多少天？
- **寬限期**：過期後功能保留幾天？（config 目前寫 3 天，但未被引用）
- **過期後行為**：完全封鎖？還是只封鎖 webhook 派送但保留查詢？

### 2.2 訂閱方案與定價

`config/subscription.php` 已有的方案（可沿用或調整）：

| 標的 | 方案 | 價格 | 限制 |
| --- | --- | --- | --- |
| Device（採集卡） | 逐台計費 | 1,200 元/台/月 | — |
| Venue（場館）tier_20 | 基礎版 20 | 2,500 元/月 | 最多 20 台 |
| Venue tier_50 | 進階版 50 | 5,000 元/月 | 最多 50 台 |
| Venue tier_100 | 專業版 100 | 10,000 元/月 | 最多 100 台 |
| Venue tier_200 | 企業版 200 | 15,000 元/月 | 最多 200 台 |
| Venue tier_500 | 尊榮版 500 | 25,000 元/月 | 最多 500 台 |

需確認：
- 這些定價是否仍然有效？還是要重新訂？
- SignalHub 是否需要「Venue tier」概念？還是只需 device 逐台計費？

### 2.3 功能攔截點

SignalHub 需要在哪些地方加訂閱檢查：

| 攔截點 | 路徑 | 過期後行為（建議） |
| --- | --- | --- |
| 登入後進入 signal-hub | `auth` middleware 後 | 顯示「訂閱已過期」橫幅但允許瀏覽 |
| 建立/編輯 profile | `POST/PATCH /profiles` | 封鎖，引導續費 |
| 建立/編輯 webhook | `POST/PATCH /webhooks` | 封鎖 |
| 模擬器觸發 GPIO | `POST /simulator/gpio` | 封鎖 |
| 真實設備信號上報 | inbound API | 封鎖（回 403） |
| Webhook 派送 | delivery job | 封鎖（不派送） |
| 查看 deliveries/stats | `GET /deliveries` | 允許唯讀（讓用戶看到歷史資料） |

### 2.4 帳務流程

- `billing_cycles` 表已存在，需確認 schema 是否夠用
- 續費流程：用戶選方案 → 上傳繳費證明 → 管理員審核 → 開通
- `config/subscription.php` 已有 `proof_upload` 設定（5MB、jpeg/png/pdf、storage_path=payment-proofs）
- `EventServiceProvider` 已有 `BillingRequestSubmitted` / `BillingRequestReviewed` 事件骨架

### 2.5 管理員後台

- `routes/api.php`（Owner 系統）已有 admin 路由骨架：
  - `GET /admin/subscription/list`
  - `PUT /admin/subscription/{id}/extend`
  - `GET /admin/subscription/audit/{id}`
- 但 SignalHub 沒有引入這些路由

---

## 3. 與 Owner 系統的關係

SignalHub 與 Owner（iot.tg25.win）共用同一個 DB（iotv9）和同一個 `users` 表。Owner 系統已有完整訂閱機制：

- `SubscriptionController`（在 Owner 專案）
- `SubscriptionService`
- `owner_subscriptions` / `subscriptions` / `billing_cycles` / `subscription_audit_logs` 表

**需確認的架構問題**：
- SignalHub 的訂閱是**獨立於 Owner**（SignalHub 自己一套）？還是**共用 Owner 的訂閱體系**？
- 如果共用 → SignalHub 只需加 middleware 檢查 Owner 的 `owner_subscriptions` 表
- 如果獨立 → 需要建新的 `signal_subscriptions` 表和獨立的 Controller

---

## 4. 請 HQ 裁示的問題清單

| # | 問題 | 選項 |
| --- | --- | --- |
| Q1 | 訂閱標的 | A) 綁 device（逐台） / B) 綁 owner（帳號全包） / C) 雙軌（device + venue tier） |
| Q2 | 與 Owner 系統的關係 | A) 共用 Owner 訂閱 / B) SignalHub 獨立一套 |
| Q3 | 試用期 | A) 不給試用 / B) 7 天 / C) 14 天 / D) 其他 |
| Q4 | 寬限期 | A) 0 天（立即封鎖） / B) 3 天（config 現值） / C) 7 天 |
| Q5 | 過期後行為 | A) 完全封鎖 / B) 封鎖寫入但允許唯讀 / C) 封鎖 webhook 派送但保留查詢 |
| Q6 | 定價 | A) 沿用 config/subscription.php 現有方案 / B) 重新訂價 |
| Q7 | 帳務流程 | A) 沿用 Owner 的「上傳繳費證明→管理員審核」 / B) 線上刷卡 / C) 其他 |
| Q8 | 優先級 | A) 等 SignalHub 核心功能穩定後再做 / B) 現在就排程 / C) 等其他 Agent 的關聯功能先完成 |

---

## 5. 建議方向（Sidney 個人意見，供 HQ 參考）

基於 SignalHub 目前仍是「技術測試階段」（小猴團隊仍在串接 webhook），建議：

1. **短期（現在）**：不做訂閱攔截，讓技術測試繼續順暢
2. **中期（核心功能穩定後）**：先做 Q2 決策（與 Owner 共用或獨立），再設計攔截點
3. **長期（正式上線前）**：完成帳務流程 + 管理員後台 + 過期告警

但最終時機和方向由 HQ 裁示。

---

**附件**：
- 盤點詳情參見 `outbox/20260915_100832_REPORT_TTEST_20260914_ACTIVITY_AUDIT.md`（ttest 9/14 活動稽核報告）
- `config/subscription.php` 全文
- `SignalHubController.php` 903 行（無訂閱邏輯）

---

> Sidney (SignalHub Lead)  
> 本提案僅為規劃建議，未修改任何代碼或資料。等待 HQ 裁示後再執行。
