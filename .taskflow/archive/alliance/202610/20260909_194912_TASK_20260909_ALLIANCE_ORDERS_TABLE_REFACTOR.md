# 任務派工：TASK_20260909_ALLIANCE_ORDERS_TABLE_REFACTOR

**派工時間**：2026-09-09 22:00  
**派工者**：HQ (Taskflow 總指揮)  
**執行者**：Allie (Alliance Lead)  
**優先級**：P0 (High)  
**決策來源**：Joe (Boss) 訂單列表頁面深度整改裁示  

---

## 📋 任務目標

Joe 在驗收 `https://ali.tg25.win/orders` 時指出多項嚴重版面與排版問題，請 Allie 立即針對 **`resources/views/orders/index.blade.php`** 進行徹底重構升級：

### 1. 移除冗餘表頭，「建立新訂單」按鈕靠右貼頂
- 移除原表格上方的卡片式表頭：`<h3>📊 訂單列表</h3>`。
- 將「➕ 建立新訂單」按鈕移至 `@section('page-header-extra')`，使其緊貼在頂部導航欄下方、直接靠右對齊（樣式：緊湊、高對比橘金按鈕，padding: 0.35rem 0.85rem, font-size: 0.85rem, font-weight: 700）。

### 2. 搜尋與篩選區塊改為「預設折疊」
- 搜尋表單包裝於可折疊容器 (`.filter-collapsible`)。
- 頂部設置一條高度極低（約 36px）、微透深色質感的觸發展開條：
  `🔍 搜尋與篩選條件 (點擊展開)`，右側放置指示箭頭。
- **預設為收合折疊 (Collapsed)**，不佔用任何預設視窗高度。點擊標題條平滑展開/收合。

### 3. 合併「合作夥伴」與「介紹人」欄位
- Joe 指示：「合作夥伴？？介紹人？？ 就是同一個吧」。
- 將原先分散的兩欄合併為單一欄位：**「夥伴 / 介紹人」**。
  - 若有夥伴：顯示夥伴名稱。
  - 若有介紹人：以醒目標籤顯示 `🤝 介紹人: {name}`。
  - 若無：顯示 `— 直客 —`。
  - 釋放出大量水平寬度，徹底消除冗餘！

### 4. 徹底重構表格文字大小與間距（落實 WAW 大字清晰、高密度規範）
- 現狀被嚴厲指出：「字小 間距大 超級爛的版頁設計」。
- **表頭 (th)**：字體加大至 `0.9rem` (約 14.5px)，加粗 (`font-weight: 700`)，高對比色 `#e2e8f0`，上下 padding 大幅縮緊至 `0.45rem 0.75rem`。
- **內容列 (td)**：
  - 字體加大至 `0.95rem` (15px)，消除小字看不清問題。
  - 上下 padding 大幅縮減至 `0.45rem 0.75rem`，資訊密度大幅提升。
  - 訂單編號加大加粗 (`font-weight: 700; color: #f8fafc;`)。
  - 客戶名稱與電話大字清晰。
  - 總金額以高對比金黃色加粗標示 (`color: #fbbf24; font-weight: 800; font-size: 1.05rem;`)。
  - 狀態標籤緊湊精美。

### 5. 表格內部滾動（禁止整頁無限長滾動）& 全裝置適配
- 表格容器使用 `.table-scroll-container`：
  - 設定 `max-height: calc(100vh - 170px);` (行動端 `calc(100vh - 150px)`)。
  - `overflow-y: auto; overflow-x: auto;`。
  - 頁面整體不隨訂單筆數長滾動，只有表格主體在容器內上下滾動！
  - 表頭 `th` 必須設置 `position: sticky; top: 0; z-index: 10; background: #1e293b;`（確保凍結在最頂部，且背景不透視下方內容）。
  - 設定表格 `min-width: 840px`，手機與平板寬度下可在容器內流暢橫向拖曳滑動，絕對不擠壓破版。

---

## 🏗️ 交付流程
1. 本機修改 `PROJECT/Alliance/resources/views/orders/index.blade.php`。
2. Git commit & push 至 origin/main。
3. 執行 `../../dev_tools/waw_ops.sh deploy alliance` 遠端更新。
4. 遠端渲染與 HTTP 驗證。
5. 寫入標準回報至 `.taskflow/alliance/outbox/`。
