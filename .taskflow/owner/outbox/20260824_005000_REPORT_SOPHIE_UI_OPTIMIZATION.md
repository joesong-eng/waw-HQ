# 服務訂閱中心 UI 調整回報

**時間**：2026-08-24 00:50  
**負責人**：Sophie (Owner Agent)

## 調整說明
針對「老一代營運商（土老闆）」在行動裝置及電腦上的視覺易讀性，本視圖 (`resources/views/iot/modules/m2/status.blade.php`) 已進行以下標準化 UI 比例與對比度調整：

1. **文字大小與字重全面放大 (Standard Readable Typography)**：
   - 標題由 `text-2xl` 提升為 `text-3xl sm:text-4xl`，加強視覺焦點。
   - 說明與副標題由 `text-xs` (12px) 提升為 `text-sm sm:text-base` (14-16px)。
   - 移除所有小於 `text-xs` 的字體 (如 `text-[11px]`)。
   - 店面明細、表格欄位、機台序號等關鍵字體全部加粗加黑 (`font-black`, `font-bold`, `text-slate-950`)，方便快速掃視。

2. **對比度升級，拒絕傷眼淺色/低對比字 (High Contrast Colors)**：
   - 白底配低對比灰字 (`text-slate-500`, `text-slate-400`) 全面替換為高對比深灰色/純黑色 (`text-slate-700`, `text-slate-900`, `text-slate-955`)。
   - 狀態 Badge 改為飽和色底（例如「營運中」改用深綠色底白字 `bg-emerald-600 text-white`；「已過期」改用深紅底白字 `bg-rose-600 text-white`），而非難以辨識的淺綠/淺粉。
   - 暗色模式 (`dark:`) 下的灰字提升為 `dark:text-slate-100` / `dark:text-white`，確保不會有「深灰背景配中灰字」的刺眼情況。

3. **按鈕與點擊範圍擴大 (Fat-Finger Friendly Controls)**：
   - 所有的功能按鈕、彈窗操作、勾選框（Checkbox）高度與內距全面增加（`py-2` -> `py-3`，並提升字重至 `font-black`）。
   - 「方案 Y 自選機台」彈出面板中的設備勾選框 (`w-6 h-6`) 與標籤間距放大，減少誤觸。

4. **將此作為標準樣式範本**：
   - 接下來 M2/M3/M8 所有相關頁面將統一參照此對比度與比例標準進行重構。

## 執行結果
- 變更已儲存於本地並 commit (`5ed3763`)，且順利推送到 `origin/main`，Governance 檢測通過。

---
*Sophie 呈報 | 2026-08-24 00:50 | iot.tg25.win*
