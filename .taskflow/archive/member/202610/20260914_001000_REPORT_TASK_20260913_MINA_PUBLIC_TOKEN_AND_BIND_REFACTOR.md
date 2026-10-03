# 任務執行報告：TASK_20260913_MINA_PUBLIC_TOKEN_AND_BIND_REFACTOR

**執行時間**：2026-09-14 00:10  
**負責人**：Mina (Member)  
**狀態**：✅ COMPLETED  
**依據標準**：`brains/knowledge/02_technical_standards/QRCODE_FORMAT_STANDARD.md` (v2.0.0)  
**提交 Commit**：`e6cff92` (origin/main)

---

## 一、修改摘要

依據出廠標籤安全性防枚舉重構方案（Public Token），完成 Member 前後端重構：

### 1. 前端掃碼與 URL 解析
- **`resources/views/welcome.blade.php`**：
  - 掃描解析新增支援 `t` 參數 (`urlObj.searchParams.get('t')`)，優先導向 `/m/play?t=${publicToken}`。
  - 登入返回後支援 `sessionStorage.getItem('play_token')` 續玩導向。
- **`resources/views/play.blade.php`**：
  - 同時提取 URL 中的 `node_id`、`t`（以及相容的 `chip_id`）。
  - 修正 `init()`：將 `t` 參數帶入 `GET /api/device/check-session?t=${publicToken}`。
  - 修正 `isNewScan` 判定：只要有 `node_id`、`publicToken` 或 `chipIdQuery`，即視為掃碼新進入，不再誤判為超時秒退。
  - 修正 `acceptAgreement()`：調用 `POST /api/device/bind` 時傳遞 `{ token: publicToken, node_id: nodeId }`。
  - 清除邏輯同步維護 `play_token`。

### 2. 後端 API 與防暴力枚舉
- **`app/Http/Controllers/Api/DeviceController.php`**：
  - 新增 `fetchDeviceByToken($token)`，呼叫 Infra `GET /api/device/by-token/{token}`。
  - `checkSession()` 支援接收 `token` / `t`，依優先級 `token > node_id > chip_id` 反查機台參數。
  - `bind()` 支援接收 `token` 完成機台會話建立。
- **`routes/api.php`**：
  - 對 `/api/device/check-session` 與 `/api/device/bind` 加上 `throttle:60,1` 中間件，防範腳本高頻暴力撞庫與枚舉。

---

## 二、部署與驗收

1. **Git 提交與推送**：
   - Commit: `e6cff92` (`feat(member): support public_token for qr scan and device binding with rate limiting`)
   - Push 至 `github.com:joesong-eng/Member.git` main 分支。
2. **遠端部署**：
   - 部署目標：`yd177` (`win.tg25.win`)。
   - 執行 `git pull`、`view:clear`、`config:cache`、`route:cache`、`cache:clear` 與 `reverb` 重啟成功。
3. **驗證結果**：
   - 首頁：`https://win.tg25.win` -> HTTP 200。
   - 帶 Token 頁面：`https://win.tg25.win/m/play?t=c8f3b610a2d54e19b84a912e73f84c01` -> HTTP 200，前端正確載入且未誤判超時秒退。
   - API 防護：未授權調用回傳 401，未提供參數回傳 422，帶 Token 正確轉發 Infra 端點且包含 Rate Limit 標頭 (`x-ratelimit-limit: 60`)。
   - 瀏覽器真實驗證：Chrome 訪問 `/m/play?t=c8f3b610a2d54e19b84a912e73f84c01` 正常渲染。
