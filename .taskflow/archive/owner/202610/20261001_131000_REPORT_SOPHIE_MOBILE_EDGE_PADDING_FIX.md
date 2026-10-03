# 任務回報：手機版左右邊界（頁面層 padding 疊加）徹底修正

**完成時間**：2026-10-01 13:10 (Asia/Taipei)
**執行者**：Sophie (Owner)
**關聯 commit**：`e72e05d`、`2a5fe5f`（waw-business: main）
**部署**：`waw_ops.sh deploy owner` 成功（vite build + cache clear）

---

## 一、需求

1. 手機版左右邊界留白過大，內容被擠壓（要寫進規則）。
2. 手機版頂部（瀏覽器網址列 + 導航欄）佔用過多。
3. 使用者選項 **A**：改成「文件層捲動」，讓手機瀏覽器**網址列可自動收合**。

---

## 二、真正根因（本次才找到）

上一版（`ca2a200`）只改了 **13 個頁面的最外層**，但**頁面內的 Action Bar 與主捲動區仍各自帶 `px-3`**，與 layout 的 `12.75px` **疊加**：

| 層 | 手機左右 padding |
|:---|:---|
| `.v9-content-area`（layout） | 12.75px |
| 頁面 Action Bar `px-3` | 12.75px |
| 頁面主捲動區 `px-3` | 12.75px |
| **實際單側合計** | **25.5px（390px 螢幕吃掉 51px）** |

實測（390px viewport）：`/statistics/dashboard` 卡片左緣 = **25.49px**。

---

## 三、修正方式

**原則：手機的左右留白，唯一來源是 `.v9-content-area`；頁面層手機一律為 0，只在 ≥768px 用 `sm:px-5` 放大。**

- 移除 28 個檔案中，頁面層（Action Bar／主捲動區／頁首／卡片外層）的**手機**左右 padding（`px-1`～`px-6`、`px-2 sm:px-4 lg:px-6` 等），保留 `sm:` / `lg:` 變體。
- 內層卡片、表格、按鈕的 padding **不動**（避免內容貼邊）。
- 頂部空間（`--v9-header-h` 56px、PWA meta、safe-area）於 `ca2a200` 已處理，本次維持。
- **文件層捲動**（`5c82eac`）：`html/body` 改 `min-height` 不再鎖高，`.v9-header-area` 改 `sticky`，`.v9-content-area` 不再自行捲動 → 手機下滑時瀏覽器**自動收合網址列**。

### 修改檔案（28）

`m1/users`、`m2/list`、`m2/plans`、`m2/status`、`m3/devices`、`m3/groups`、`m3/parameter-templates`、`m4/profit-sharing-proposals(-batch)`、`m4/stats`、`m4/venues`、`m5/bot`、`m5/logs`、`m5/notifications`、`m6/dashboard`、`m6/reports`、`m6/report-detail`、`m7/bank`、`m7/statements`、`m7/settlement-detail`、`m8/admin-approval`、`m8/invoices`、`m8/renewals`、`m9/alerts`、`m9/settings`、`m10/pins`、`m10/profiles`、`m10/stats`

---

## 四、瀏覽器實測（iot.tg25.win）

### 手機 390px（viewport 覆寫）

| 頁面 | layout 左右 | 頁面層左右 | 水平溢出 |
|:---|:---|:---|:---|
| /statistics/dashboard | 12.75px | **0**（卡片左緣 12.74px） | 無 |
| /users | 12.75px | 0 | 無 |
| /devices | 12.75px | 0 | 無 |
| /venues | 12.75px | 0 | 無 |
| /settings | 12.75px | 0 | 無 |
| /subscriptions/status | 12.75px | 0 | 無 |
| /billing/invoices | 12.75px | 0 | 無 |
| /billing/renewals | 12.75px | 0 | 無 |
| /settlements/statements | 12.75px | 0 | 無 |
| /statistics/reports | 12.75px | 0 | 無 |
| /portal | 12.75px | 0 | 無 |

**改善：單側 25.5px → 12.75px（-50%）**，內容明顯變寬。

### 桌面版（1910px）回歸

- `.v9-content-area` padding 40px、Action Bar `sm:px-5` 25px ✅
- 側邊欄 `fixed`、導航欄 `sticky`、無水平捲動 ✅

### 已知既有問題（非本次造成）

- `/settlements/statements`：載入時 alert「載入結算單失敗：Server Error」（後端既有）。
- `/realtime`、`/signal-hub/profiles`：含 `min-w-[760px]` 寬表格，於 390px 需橫向捲動（設計如此，本次未動這些檔案）。

---

## 五、規則入庫（`resources/docs/UI_STANDARDS.md`）

| 節 | 更新 |
|:---|:---|
| §1 頁面結構骨架 | 新增**捲動模型**說明：全站採文件層捲動，頁面 root 不可鎖固定高度 |
| §1 範例 | Action Bar／捲動區範例改為 `sm:px-5`（手機 0） |
| §9 間距密度 | 「頁面層左右 padding：手機 **0**（交給 layout）、桌機 sm:px-5」 |
| §10.1 左右邊界 | 明文：**layout 是手機唯一左右留白來源**；頁面層手機 0，只寫 `sm:px-5` |
| §11 禁止事項 | 新增「頁面層手機寫任何 px-*（會與 layout 疊加）」 |

---

## 六、結論

✅ 完成。手機版左右邊界由 **25.5px 降為 12.75px**，且手機瀏覽器**網址列可自動收合**（文件層捲動）。
規則已入庫，後續新頁面不得再於頁面層寫手機 `px-*`。
