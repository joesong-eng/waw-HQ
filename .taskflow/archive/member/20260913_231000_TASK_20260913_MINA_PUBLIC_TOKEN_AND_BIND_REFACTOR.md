# 任務：TASK_20260913_MINA_PUBLIC_TOKEN_AND_BIND_REFACTOR

**派發時間**：2026-09-13 23:10  
**優先級**：High  
**負責人**：Mina (Member)
**指導規範**：`brains/knowledge/02_technical_standards/QRCODE_FORMAT_STANDARD.md` (v2.0.0)
**協調依據**：出廠標籤安全性防枚舉重構（Public Token 方案）

---

## 📋 任務目標與具體執行細節

老邱出廠貼紙現已升級為 `https://win.tg25.win/m/play?t={public_token}`，不再使用連續明文 MAC。Mina 需修改 Member 玩家端，確保掃碼即玩流程順暢且無漏洞。

### 1. 前端掃碼與落腳點解析 (`welcome.blade.php` & `play.blade.php`)
- **`welcome.blade.php`**：
  - 掃描到 `win.tg25.win/m/play` 且帶 `t` 參數時，正確導向 `/m/play?t=${token}`。
- **`play.blade.php` (修復抓取與超時誤判 Bug)**：
  - 同時提取 URL 中的 `node_id` 與 `t`（以及向下相容的 `chip_id`）：
    ```javascript
    const params = new URLSearchParams(window.location.search);
    const nodeId = params.get('node_id') || '';
    const publicToken = params.get('t') || '';
    ```
  - 修正 `init()`：帶入 `t=${publicToken}` 呼叫 `/api/device/check-session`。
  - 修正 `isNewScan` 判斷：當有 `nodeId` 或 `publicToken` 時，皆視為新掃碼進入，彈出服務協議，不可誤判為超時秒退！
  - 修正 `acceptAgreement` 綁定：向 `/api/device/bind` 傳遞 `{ node_id: nodeId, token: publicToken }`。

### 2. 後端 API 支援 Token 解析與防暴力枚舉 (`DeviceController.php`)
- **`checkSession` & `bind`**：
  - 接收 `token`（即 `public_token`）。
  - 若有 `token`，呼叫 Infra `fetchDeviceByToken($token)`（或由 Ina 提供的 `GET /api/device/by-token/{token}`）取得設備參數與 `chip_id`。
- **防枚舉安全限制 (Rate Limiting)**：
  - 在 `routes/api.php` 對 `device/check-session` 與 `device/bind` 套用頻率限制（例如 `throttle:60,1`），防止腳本頻繁撞庫。

---

## 📝 驗收標準
1. [ ] 手機模擬掃描 `/m/play?t=32位Token` 能正確拉取機台資訊並彈出同意協議。
2. [ ] 點擊「同意協議」後能成功調用 `bind` 並進入開分頁面，不拋 422 錯誤。
3. [ ] 驗收報告寫入 `.taskflow/member/outbox/`。
