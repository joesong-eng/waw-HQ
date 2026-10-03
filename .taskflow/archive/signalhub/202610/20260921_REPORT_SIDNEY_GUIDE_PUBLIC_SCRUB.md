# 回報：公開指南安全 scrub

**回報者**：Sidney（SignalHub）
**日期**：2026-09-21
**狀態**：✅ 完成並上線

---

## 一、處理範圍

公開頁面：`https://signal.tg25.win/signal-hub/guide`

本次只處理對外文件顯示內容，不修改 API 行為、路由、權限、資料庫、Webhook payload 生成邏輯。

---

## 二、Scrub 項目

| 類別 | 原內容 | 新內容 |
|---|---|---|
| 範例簽名 | `sha256=a1b2c3d4...` | `sha256={hmac_sha256_signature}` |
| 範例 reply token | `token=4f8a9e2c1b7d` | `token={signed_callback_token}` |
| 內部 DB 名稱 | `iotv9.users` | `平台帳號` |
| 內部權限術語 | `effective owner` | `所屬機台主` |

---

## 三、驗證

**Commit**：`7dc7a08 docs(guide): scrub public placeholders and internal terminology`

**部署**：`../../dev_tools/waw_ops.sh deploy sidney` → ✅ 完成

**HTTP 驗證**：
- `GET https://signal.tg25.win/signal-hub/guide` → HTTP 200

**內容驗證**：
- `a1b2c3` → 0
- `4f8a9e2c1b7d` → 0
- `iotv9.users` → 0
- `effective owner` → 0
- `hmac_sha256_signature` → 1
- `signed_callback_token` → 1
- `所屬機台主` → 1

**瀏覽器驗證**：Codex In-app Browser reload 後確認新版內容已顯示。

---

## 四、備註

公開指南保留 API 規格、Header、HMAC、reply_url、session-end endpoint 等必要對接資訊。這些屬遊戲商整合文件必要內容，安全性依賴 secret key / HMAC / timestamp / delivery_id / signed token，而非隱藏規格。
