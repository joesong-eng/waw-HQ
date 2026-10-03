# 任務回報：TASK_20260921_ALLIE_CLEAN_TAILWIND_CUSTOMERS_SETTLEMENTS

**完成時間**：2026-09-21 00:50
**執行者**：allie

## 執行結果

依工單要求，移除 `customers/index.blade.php` 與 `settlements/index.blade.php` 中所有 Tailwind CSS class 依賴，改為專案原生手寫 CSS（暗色深藍科技風、玻璃擬態、大字高對比）。

### 1. customers/index.blade.php（完全重寫）

原檔 235 行全部使用 Tailwind class（`flex`、`px-4`、`text-slate-400`、`bg-slate-900/60`、`rounded-2xl` 等），因 Layout 未載入 Tailwind CDN 導致樣式全失效。

重寫為 100% 手寫 CSS，包含：
- **頂部動作列**：左右分欄，角色提示 + 快速新增按鈕
- **三格指標卡**：客戶總數、累計訂單、持有設備，漸屬邊框（白/藍/橙）
- **搜尋列**：關鍵字搜尋 + 結果計數
- **客戶表格**：頭像、聯絡方式、訂單數、採購額、設備數、狀態、日期、操作
- **設備折疊明細**：點擊展開，含晶片序號、設備類型、來源訂單、Node ID、綁定狀態、出貨日期
- **分頁**、**空狀態**、**響應式**

所有 CSS class 使用語意化前綴 `cust-`，與專案既有命名風格一致。

### 2. settlements/index.blade.php（局部替換）

原檔已有大量手寫 CSS（`<style>` 區塊），但 Tab 導航與月份篩選器仍用 Tailwind class。

替換部分：
- **Tab 導航**：`flex flex-col\|px-4\|rounded-xl\|bg-gradient-to-r\|text-slate-950\|shadow-lg` → `settlement-nav-row`、`settlement-tab active/inactive`
- **月份篩選器**：`px-3\|bg-slate-950\|border-slate-700\|text-slate-200\|focus:border-amber-500` → `settlement-month-form`、`settlement-month-select`、`settlement-month-btn`
- **「📍 本月」按鈕**：Tailwind 條件 class → `settlement-month-btn active/inactive`

### 3. 驗證

- 本地 + 遠端 grep 確認兩檔案 **0 個** Tailwind class 殘留（`text-slate`、`bg-slate`、`rounded-xl`、`px-4`、`py-2` 全為 0）。
- Layout 仍未載入 Tailwind CDN，兩頁面完全自足。

### Git 與部署

- **Commit**：`960fc92`（`refactor(ui): 移除 customers 與 settlements 頁 Tailwind 依賴，改為手寫 CSS`）已推送 `origin/main`。
- **遠端**：`yd16`（`ali.tg25.win`）同步至 `960fc92`，`view:clear`、`cache:clear`、`view:cache` 全數成功。

未動 `burning.blade.php`，未執行任何資料庫遷移。

## 結論
✅ 完成

---
**回報者**：allie
**回報時間**：2026-09-21 00:50

