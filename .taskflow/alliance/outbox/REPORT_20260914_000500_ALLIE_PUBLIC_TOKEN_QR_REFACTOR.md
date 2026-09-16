# 任務回報：TASK_20260913_ALLIE_PUBLIC_TOKEN_QR_REFACTOR

- **負責 Agent**: Allie (Alliance ali.tg25.win)
- **提交時間**: 2026-09-14 00:05
- **任務目標**: 出廠標籤 QR Code 格式重構，徹底廢除 Raw JSON，全面改採高熵 public_token
- **狀態**: ✅ 完成 (Completed)

---

## 🛠️ 執行內容變更

1. **資料模型與表結構擴充**：
   - 在 `app/Models/AliDeviceBinding.php` 補齊 `public_token` 與 `qr_printed_at` 至 `$fillable` 與 `$casts`。
   - 新增 Migration `2026_09_13_230000_add_public_token_to_ali_device_bindings_table.php`。
   - 遠端 `ali_device_bindings` 表已具備 `public_token varchar(32)` 欄位並驗證為 true。

2. **燒錄後端控制器 (`app/Http/Controllers/DeviceController.php`)**：
   - `commitRegistration`: 燒錄成功寫入記錄時，自動生成 32 字元無符號隨機代號 `bin2hex(random_bytes(16))`，回傳包含 `public_token`。
   - `pendingPairing` / `burnedDevices` / `burningProgress`: 查詢欄位補上 `adb.public_token`。
   - `pair`: 配對成功回傳資料帶上 `public_token`。
   - `generateQrPdf`: 遍歷設備輸出 PDF 標籤時，若無 `node_id` 一律使用 `https://win.tg25.win/m/play?t={$public_token}`，徹底移除 `json_encode` 邏輯。

3. **燒錄前端視圖 (`resources/views/devices/burning.blade.php`)**：
   - `window.showQrPreview`: 接收 `publicToken` 參數。
   - QR 內容生成邏輯改為：
     - 若有 `node_id`：`https://win.tg25.win/m/play?node_id=${nodeId}`
     - 若無 `node_id`：`https://win.tg25.win/m/play?t=${publicToken}`
     - 徹底移除 `JSON.stringify({ type, chip_id, mac })`。
   - 單張標籤底部的 MAC / Chip ID 保留作為老邱品檢辨識小字。

---

## 📡 驗證結果

1. **Git Commit & Push**:
   - Commit: `d08c1d0` (`feat(qr): refactor device burning public_token and eliminate raw json qr codes`)
   - Branch: `main`
2. **遠端部署與快取清理**:
   - 遠端代碼已同動更新至 commit `d08c1d0`。
   - 執行 `php artisan view:clear && php artisan config:cache && php artisan cache:clear` 成功。
3. **實體驗證測試**:
   - 查詢遠端 `ali_device_bindings` 記錄，確認 `public_token` 正常存取。
   - 實測隨機 Token 生成為 32 字元，產出 QR 解析格式為 `https://win.tg25.win/m/play?t={public_token}`。
