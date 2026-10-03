# 任務回報：營運看板 UI 標準化 + 手機版導航欄麵包屑

**完成時間**：2026-10-01 10:30 (Asia/Taipei)
**執行者**：Sophie (Owner)
**關聯 commit**：5f5bc6b、a265486（waw-business: main）
**部署**：waw_ops.sh deploy owner 成功

---

## 一、需求

1. /statistics/dashboard（營運看板）UI 依 resources/docs/UI_STANDARDS.md 標準規範整理。
2. 導航欄麵包屑（PLATFORM › 營運看板）在手機版**不要隱藏**。

---

## 二、執行內容

### 1. 導航欄麵包屑（layouts/app.blade.php）

| 項目 | 修改前 | 修改後 |
|:---|:---|:---|
| 顯示斷點 | hidden sm:flex（<640px 隱藏） | flex（全寬度顯示） |
| 防擠壓 | 無 | 加 min-w-0 + 標題 truncate，圖示 flex-shrink-0 |

### 2. 營運看板標準化（m6/dashboard.blade.php，997 → 472 行）

| 規範 | 修正內容 |
|:---|:---|
| §1 頁面骨架 | 移除 .dash-scroll 的 height:100dvh，**消除雙層捲動**；改為 flex flex-col h-full min-h-0 + 唯一 flex-1 overflow-y-auto |
| §2 Action Bar | 場地選擇／即時狀態／狀態說明 收斂為 flex-shrink-0 Action Bar；移除重複頁面標題 |
| §3 字級 | 移除自訂 .page-title／.kpi-amount 等，改用 text-xl font-black／text-base font-black／text-xs font-bold |
| §6 狀態色 | 趨勢徽章改用標準 emerald／rose／slate（新增 trendClass() helper） |
| §7 卡片 | bg-white dark:bg-slate-900 + rounded-xl + border-slate-200 dark:border-slate-800 |
| §10 禁止 | 移除 min-h-screen、重複 h1、假 class |
| 色票 | 移除本頁專屬 --c-* 自訂色票（**全專案唯一使用**），回歸 Tailwind 標準，與其餘 27 個模組頁一致 |

### 3. 附帶修復（部署驗證時發現）

x-data 已含 init()，Alpine 會自動呼叫；額外 x-init="init()" 導致 init 執行**兩次** →
建立兩個 Chart 實例 → 舊實例 destroy 後殘留動畫幀重繪 → TypeError: Cannot read properties of null (reading save)。
已加 _initialized 旗標確保 init 僅執行一次。

---

## 三、瀏覽器實測驗收（iot.tg25.win）

| 項目 | 桌面（750px） | 手機（390px） | iPhone（375px） |
|:---|:---|:---|:---|
| 麵包屑「PLATFORM › 營運看板」 | ✅ 顯示 | ✅ 顯示 | ✅ 顯示（右緣 245/375，不裁切） |
| 導航欄水平溢出 | ✅ 無 | ✅ 無 | ✅ 無（scrollWidth == clientWidth） |
| 頁面水平捲動 | ✅ 無 | ✅ 無 | ✅ 無 |
| 捲動層數量 | ✅ 1 層 | ✅ 1 層 | — |
| 雙層捲動 | ✅ 無 | ✅ 無 | — |
| Chart.js 錯誤 | ✅ 0 | ✅ 0 | — |
| init() 呼叫次數 | ✅ 1 | — | — |
| 手機漢堡側邊欄 | — | ✅ 正常滑出 280px | — |

**回歸測試**（改動共用 layout，實測 390px）：/subscriptions/status、/devices、/realtime、/settings、/portal
→ 麵包屑全部正確顯示（服務訂閱中心／設備管理／即時數據／全局設定／V9 系統門戶），無水平溢出。

---

## 四、結論

✅ 完成。看板已符合 UI_STANDARDS，手機版導航欄麵包屑不再隱藏，且無 Console 錯誤、無版面回歸。
