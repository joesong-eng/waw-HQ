# 任務工單：驗證 Owner 訂閱機制可涵蓋 SignalHub owner（架構對齊確認）

- **工單編號**：TASK_20261003_SOPHIE_VERIFY_SIGNALHUB_SUBSCRIPTION_SCOPE
- **派發時間**：2026-10-03
- **負責人**：Sophie (Owner)
- **優先級**：P2
- **架構依據**：`brains/knowledge/03_system_architecture/ADR-001_SIGNALHUB_SUBSCRIPTION.md`

---

## 一、背景

HQ 已裁定：SignalHub 訂閱機制**複用 Owner 基礎設施**（兩者共用 `iotv9` DB 與
`owner_subscriptions` 表）。此決策成立的前提是：**Owner 的 `users` 表與訂閱資料
能正確涵蓋 SignalHub 的 owner 帳號**。請你驗證此前提。

---

## 二、驗證項目

### 1. users 表是否為兩站共用

- 確認 SignalHub 登入的 owner 帳號，其 `id` 是否即 `iotv9.users.id`。
- 方式：遠端 Tinker 比對 SignalHub 登入 user 與 `users` 表記錄。

### 2. owner_subscriptions 表涵蓋性

- `owner_subscriptions.owner_id` FK → `users.id`。
- 確認 SignalHub owner（例如 user_id=11 ttest）是否有對應訂閱記錄。
- 若無記錄，確認 SignalHub 端應如何處理（ADR 定義：回 `status: none`）。

### 3. Owner 端訂閱管理是否可涵蓋 SignalHub owner

- Owner 後台「訂閱管理」是否能列出/管理將在 SignalHub 使用的 owner？
- 若 owner 概念不同（例如 SignalHub 有自己的 owner 定義），請立即回報 HQ 修正 ADR。

### 4. config/subscription.php 一致性

- 確認兩邊 config 在部署後仍一致（`diff`）。

---

## 三、產出

| # | 產出 | 方式 |
|:--|:---|:---|
| 1 | users 表共用性結論 | Tinker 實測 + 截圖/輸出 |
| 2 | owner_subscriptions 涵蓋性結論 | SQL 查詢結果 |
| 3 | 是否需要修正 ADR 的建議 | 文字說明 |

---

## 四、回報要求

寫入 `.taskflow/owner/outbox/`，附 Tinker/SQL 實際輸出。

---

## 五、注意

- **本工單僅做驗證，不改程式碼。**
- 若發現 SignalHub owner 與 Owner users 非同一套，**立即停止並回報 HQ**，
  因為這會推翻 ADR-001 的核心前提。
