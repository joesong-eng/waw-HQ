# 任務工單：TASK_20260930_SOPHIE_RESOLVE_M4_VENUE_ENTRY_PAGE

**派發時間**：2026-09-30 03:00 (台北時間)  
**優先級**：P1 (場地管理入口架構收斂與佔位頁清理)  
**指派對象**：Sophie (Owner Agent)  
**驗收人**：HQ / Joe

---

## 🎯 任務背景與目標

在 2026-09-30 模組盤點中，Sophie 標註 `m4/index.blade.php` 為佔位頁 (顯示「模組建置中」)。  
經 HQ 進一步稽核發現：
1. 實際完整具備 CRUD、分潤設定、員工指派之場地管理介面早已實作於 `resources/views/iot/modules/m4/venues.blade.php` (高達 52KB，功能完整)。
2. 主側邊欄連結 (`layouts/app.blade.php`) 指向 `route('venues')` ➔ 正確載入 `m4.venues`。
3. 舊有的 `m4/index.blade.php` 及其路由 `GET /venues/index` 實屬早期開發遺留之孤立佔位頁，造成「模組建置中」之誤判與混淆。

**本次任務目標**：
清理並收斂 M4 路由與視圖結構，廢除孤立佔位頁，並強化 `venues.blade.php` 作為 M4 唯一入口之完整度。

---

## 📋 具體實作要求

### 一、路由收斂 (`routes/web.php`)
1. 將 `Route::get('venues/index', ...)` 改為 301 重定向至 `route('venues')`，或統一別名指向 `iot.modules.m4.venues`。
2. 確保任何訪問 `/venues` 或 `/venues/index` 皆呈現功能完整之 `venues.blade.php`。
3. 刪除或重構 `m4/index.blade.php` 佔位頁（禁止在生產環境向用戶展示「模組建置中」）。

### 二、M4 子導航列 (Tab Navigation) 檢查與補齊
檢視 `venues.blade.php`、`stats.blade.php`、`profit-sharing-proposals.blade.php`：
1. 確認是否有頂部 Tab/切換按鈕讓業主在「場地列表 (`/venues`)」、「營運統計 (`/venues/stats`)」與「分潤協議 (`/profit-sharing/proposals`)」之間無縫切換。
2. 若無頂部切換列，請在 `venues.blade.php` 頂部加上乾淨高對比之 Tab 導航列，讓 M4 內的三大核心功能互通。

---

## 📦 驗收標準 (Acceptance Criteria)

1. **瀏覽器/HTTP 測試**：
   - `GET https://iot.tg25.win/venues` ➔ 200，正常渲染完整場地列表（非建置中）。
   - `GET https://iot.tg25.win/venues/index` ➔ 正確轉址或渲染場地列表，不再出現「模組建置中」。
2. **Git 與遠端部署**：
   - Commit message 格式：`refactor(m4): consolidate venue entry page and remove placeholder stub`
   - Push 至遠端 main 分支並完成 `waw_ops.sh deploy owner`。
3. **回報格式**：
   - 依據 `SIMPLE_FILE_DISPATCH_PROTOCOL.md` 將回報送達 `.taskflow/owner/outbox/`。
   - 附上遠端 curl 或瀏覽器確認之實測證據。

---
**派發者**：HQ  

