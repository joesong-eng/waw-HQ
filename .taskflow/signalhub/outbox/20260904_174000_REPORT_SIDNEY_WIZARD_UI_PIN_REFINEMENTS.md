# 任務追加回報：SignalHub 設置精靈 UI 互動修復、8大實體標準通道完整展開與介面精簡

- **任務 ID**：`TASK_20260904_SIDNEY_WIZARD_UI_PIN_REFINEMENTS`
- **執行 Agent**：Sidney (SignalHub Lead)
- **回報對象**：HQ
- **日期時間**：2026-09-04 17:40:00 (UTC+8)
- **專案路徑**：`/Users/ilawusong/Documents/WaW/PROJECT/SignalHub`
- **遠端站點**：`https://signal.tg25.win`
- **狀態**：✅ 已完成並遠端部署上線

---

## 📋 本次追加優化與修復重點

1. **模板腳本載入修復 (Alpine.js @stack('scripts'))**：
   - 修復 `resources/views/layouts/app.blade.php` 遺漏 `@stack('scripts')` 導致 Alpine.js 點擊事件未掛載之問題，確保 3 步精靈彈窗正常喚起。

2. **廢除死板倍率輸入，以小猴 Webhook 回傳為準**：
   - 精靈 Step 2 移除手動倍率輸入框，改由開分/洗分觸發固定上報 `delta: 1`，實際開洗分點數由小猴 Webhook 回覆之 `actual_points` / `cleared_points` 入庫做精準營運統計。

3. **8 大固定實體通道完整展開 (4 入 4 出：UI1~UI4, UO1~UO4)**：
   - 移除過渡期僅展示 2 個卡片的設計，Step 2 預設完整列出 8 組硬體標準通道。
   - **預設標籤與分組**：
     - `UI1 (GPIO13)`：預設名稱標籤「**開分**」、統計分組 `revenue`。
     - `UI2 (GPIO14)`：預設名稱標籤「**洗分**」、統計分組 `payout`。
     - `UI3 ~ UI4` (輸入)：預設名稱「備用輸入3/4」、分組 `auxiliary`。
     - `UO1 ~ UO4` (輸出)：預設名稱「控制輸出1~4」、分組 `status`。

4. **介面操作精簡（符合硬體物理規格）**：
   - 採集卡物理引腳固定為 8 組，移除多餘且不符合硬體規格的「+ 新增通道」及「刪除」按鈕，避免混淆操作員。

5. **快速帶入邏輯修復**：
   - 修復 `quickStartDevice` 點擊機台卡片（如 `M001`）未初始化 `pins` 陣列導致畫面空白之 Bug，點擊卡片與點擊精靈按鈕均能 100% 正常帶入 8 個標準通道。

---

## 🚀 提交與部署清單 (Git Commits)

- `b2ab663` refactor(SignalHub): Remove redundant add/delete pin buttons since 8 channels are fixed standard hardware pins
- `acf6bc2` fix(SignalHub): Include all 8 standard pins (UI1-UI4, UO1-UO4) by default in wizard
- `de0745f` fix(SignalHub): Ensure quickStartDevice properly initializes default pins list and fix addCustomPin action
- `9327728` feat(SignalHub): Support full 8 standard pins configuration in 3-step wizard with default 开分/洗分 and custom channels
- `f2c403e` feat(SignalHub): Allow selecting arbitrary UI1-UI4 pins for credit in and credit out in setup wizard
- `cedbe68` refactor(SignalHub): Remove manual pulse_ratio input, rely on webhook response cleared_points for accurate accounting
- `6aa60b3` fix: Add missing @stack(scripts) in layout template

---

## 🔍 遠端驗證狀態 (Source of Truth)
- **遠端站點**：`https://signal.tg25.win/signal-hub/profiles`
- **視圖快取**：已在 VPS 執行 `php artisan view:clear`。
- **功能驗證**：3 步設置精靈流暢運作，8 大通道預設展示正常。

**簽署**：Sidney (SignalHub)
