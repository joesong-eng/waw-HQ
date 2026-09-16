# 任務：TASK_20260913_ALLIE_PUBLIC_TOKEN_QR_REFACTOR

**派發時間**：2026-09-13 22:49  
**優先級**：High  
**負責人**：Allie (Alliance ali.tg25.win)
**指導規範**：`brains/knowledge/02_technical_standards/QRCODE_FORMAT_STANDARD.md` (v2.0.0)
**HQ 裁決依據**：`.taskflow/hq/outbox/ANSWER_20260913_HQ_ALLIE_CHIP_ID_QR_SECURITY_DECISION.md`

---

## 📋 任務目標與職責邊界

依據 HQ 架構治理邊界：**資料庫實體表變更由 Ina 統一負責，Allie 專注 Alliance 業務邏輯與介面。**

### 1. 燒錄綁定流程自動生成 Token
- 檢查 `DeviceController.php` 燒錄配對與寫入 `ali_device_bindings` 處：
- 當老邱完成設備燒錄建立綁定記錄時，若無 `public_token`，由程式自動產生 32 字元無符號隨機代號（例如 `bin2hex(random_bytes(16))`）。
- 儲存至該設備的 `public_token` 欄位（DB 欄位已由 Ina 擴充就緒）。

### 2. 出廠標籤生成重構（徹底移除 Raw JSON）
重構 `resources/views/devices/burning.blade.php` 與 `DeviceController.php@generateQrPdf`：
- **單張標籤預覽 / 列印 (`showQrPreview`)**：
  - 若有 `node_id`：`https://win.tg25.win/m/play?node_id=${nodeId}`
  - 若無 `node_id`（出廠標準狀態）：`https://win.tg25.win/m/play?t=${publicToken}`
  - **徹底刪除** `JSON.stringify({ type, chip_id, mac })` 邏輯！
- **批次 PDF 輸出 (`generateQrPdf`)**：
  - 遍歷 `$bindings` 時，無 `node_id` 一律取用 `$b->public_token` 產出 `https://win.tg25.win/m/play?t={$b->public_token}`，廢除原本的 `json_encode` 邏輯。

### 3. 前後端介面與 API 回傳對齊
- `DeviceController@burningProgress` 與 `pairDevice` 等 API 回傳欄位需包含 `public_token`。
- 標籤列印樣式上，MAC 與 Chip ID 僅作為老邱品檢辨識用小字印在底部，大 QR Code 核心編碼必須為 `https://win.tg25.win/m/play?t=...`。

---

## 📝 驗收標準

1. [ ] 燒錄新設備會自動帶出高熵 `public_token`。
2. [ ] 點擊「標籤預覽」與「批次列印 PDF」時，掃碼解析結果皆為標準 URL `https://win.tg25.win/m/play?t=...`，完全無任何 JSON 格式出現。
3. [ ] 執行回報至 `.taskflow/alliance/outbox/`，附上檔案 diff 或測試截圖/log 證明。
