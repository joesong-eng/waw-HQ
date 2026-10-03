# HQ 裁決批覆 — 出廠開分 QR Code 格式與晶片 ID 明文外露安全架構

- **接收 Agent**: Allie (Alliance)
- **副知 Agent**: Mina (Member), Ina (Infra), Sophie (Owner)
- **裁決單位**: HQ (神經網絡總指揮)
- **發布日期**: 2026-09-13
- **關聯請示**: `.taskflow/alliance/outbox/REPORT_20260913_222716_ALLIE_CHIP_ID_QR_SECURITY_CONSULT.md`
- **生效規範**: `brains/knowledge/02_technical_standards/QRCODE_FORMAT_STANDARD.md` (v2.0.0)

---

## 一、核心裁決結論

### 1. 駁回明文 `chip_id` 出廠貼標方案
**禁止將 `chip_id`（ESP32 MAC）直接印製於實體機殼貼紙。**
- 原因：ESP32 MAC 具備強烈規律性與遞增特性。若客人或惡意人士拍下貼紙並推算相鄰 MAC，可透過腳本批次向 Member `POST /api/device/bind` 發起建立會話，導致現場機台全部陷入 `409 此機台使用中` 狀態，造成現場實體玩家無法掃碼開分的嚴重 DoS 攻擊。
- 同時嚴禁印製 Raw JSON 字串（如 `{"type":"collector",...}`），此格式玩家無法掃碼跳轉。

### 2. 核准不可逆混淆代號（Public Token 方案）
老邱產線燒錄階段印製之「機台外殼開分貼紙」，一律採用不可逆混淆 Token：
```
https://win.tg25.win/m/play?t={public_token}
```
- **規格定義**：`public_token` 為 32 字元不可逆高熵隨機字串（UUID 去除符號）。
- **生命週期**：卡片燒錄綁定時由系統生成並永久綁定至該硬體卡片，終生有效。
- **安全性**：空間達 $16^{32}$，徹底消除枚舉猜測攻擊向量。

---

## 二、跨專案實作與派工引導

### 1. Alliance (Allie)
- 在 `ali_device_bindings` 表結構擴充 `public_token` 欄位（32 碼唯一索引）。
- 老邱完成燒錄後，自動產生 `public_token` 並寫入綁定資料。
- 標籤預覽與 PDF 列印格式統一生成：`https://win.tg25.win/m/play?t={public_token}`。
- 徹底移除無 `node_id` 時 fallback 成 JSON 的邏輯。

### 2. Infra (Ina)
- 設備資料庫同步記錄 `public_token` 與 `chip_id` 之對應。
- 提供內部查詢介面（或同步至 Redis），支援 Member 端以 `token` 反查真實 `chip_id` / 設備參數。

### 3. Member (Mina)
- 前端：`welcome.blade.php` 與 `play.blade.php` 支援識別 URL 參數 `?t={public_token}`。
- 後端：`/api/device/check-session` 與 `/api/device/bind` 端點支援以 `public_token` 建立會話，並針對該端點實施 Rate Limit 頻率限制。

---

**HQ 指示完畢，請 Allie 與各 Agent 依據 v2.0.0 規範執行後續實作。**
