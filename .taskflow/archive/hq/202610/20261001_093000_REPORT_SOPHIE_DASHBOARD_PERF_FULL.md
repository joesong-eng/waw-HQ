# 任務回報：TASK_20261001_SOPHIE_OPTIMIZE_DASHBOARD_PERF（完整結案報告）

**回報時間**：2026-10-01 09:30 (Asia/Taipei)
**執行者**：Sophie (Owner)
**上級**：HQ
**優先級**：P1 / high
**狀態**：✅ 全部完成
**關聯 commit**：`b9e56c6` / `20bac58` / `bf652d4`（waw-business: main）

---

## 一、任務來源與演進

本任務歷經**三次範圍擴張**，皆由 JOE 實測回饋驅動：

| 階段 | 觸發 | 範圍 |
|:---|:---|:---|
| 原始工單 | HQ 派發（銜接 Ina 索引成果） | SQL 收斂 + 字型移除 + 骨架屏 |
| 擴張一 | JOE：「首屏速度感覺還是不行」 | 重新量測 → 發現外部 CDN 才是真瓶頸 |
| 擴張二 | JOE：「外部依賴要下載到 server 嗎？」 | 全站外部依賴清零 |

**關鍵教訓**：原始工單假設「後端慢查詢」為主因，但實測後**後端僅 46ms**，
真因是**前端外部 CDN 阻塞**。若未經實測直接做骨架屏，將無法解決問題。

---

## 二、根因分析（實測數據）

### 2.1 後端（非瓶頸）

以 Tinker 實測 `DashboardDataService::getDashboardData()`：

| 情境 | 耗時 |
|:---|:---|
| COLD（快取失效） | **46ms** |
| WARM（快取命中） | **8ms** |

### 2.2 前端外部 CDN（真瓶頸）

以 Chrome DevTools Protocol（cache-disabled）精確量測：

| 資源 | 優化前 | 來源 |
|:---|:---|:---|
| Document（Laravel SSR） | 443ms | 自家（正常） |
| **chart.js** | **351ms** | cdn.jsdelivr.net ❌ |
| **alpinejs** | **276ms** | cdn.jsdelivr.net ❌ |
| **@alpinejs/collapse** | **264ms** | cdn.jsdelivr.net ❌ |
| fonts.googleapis.com | 37ms | Google ❌ |

---

## 三、執行內容（三階段）

### 階段 1：SQL 收斂與快取優化（`b9e56c6`）

**問題**：`StatisticsController::dashboard()` 額外呼叫 `countTodayTransactions()`，
該方法位於 `getDashboardData()` 快取閉包**之外**，每次請求都觸發一次
`revenue_facts` 全表掃描。

**修復**：
1. 完全移除 `countTodayTransactions()` 與其呼叫（含未用 import）
2. 改直接複用 `DashboardDataService` 快取閉包內已算好的 `transaction_count`
3. `buildKPIs()` 補上 `transactions` / `avg_price` / `daily_avg` 欄位
   （原本只有 `value/trend/percent`，導致前端只能顯示硬編碼 0）
4. `dashboard.blade.php` 移除 Google Fonts `@import` 外部阻塞

**快取 TTL 檢視**：

| 快取 | TTL | 評估 |
|:---|:---|:---|
| `dashboard_data_<venueIds+tz>` | 300s | 合理 |
| `rev_month_<venueIds+start>` | 600s | 合理（月營收獨立防爆表） |
| `dash_summary_<venueIds>` | 60s | 合理（骨架頁輕量摘要） |

### 階段 2：Alpine + Chart.js 本地化（`20bac58`）

**新增**
- `resources/js/alpine.js` — Alpine + collapse bundle（`window.Alpine`）
- `resources/js/chartjs.js` — Chart.js bundle（`window.Chart`）

**修改**
- `package.json` 新增 `alpinejs` / `@alpinejs/collapse`
- `vite.config.js` 新增 `chartjs.js` entry（獨立 chunk，僅看板載入）
- `resources/js/app.js` → `import './alpine'`（全站生效）
- `layouts/app.blade.php`、`layouts/auth.blade.php`、
  `iot/auth/portal-login.blade.php` 移除 Alpine CDN
- `m6/dashboard.blade.php` chart.js CDN → `@vite`，並加入**載入順序防護**
  （module 可能晚於 Alpine 初始化，若 `window.Chart` 未就緒則輪詢重試）

### 階段 3：QR 本地化 + 字型清除（`bf652d4`）

**依賴處置原則**（回應 JOE 提問）：

| 類型 | 處置 | 原因 |
|:---|:---|:---|
| 功能庫（QR 掃描/產生） | 下載到 server（npm 打包） | 無法用系統內建替代 |
| 純視覺字型（未被使用） | 直接刪除 | 無功能價值 |
| 純視覺字型（有被使用） | 改系統字型 | 零下載、視覺可接受 |

**新增**
- `resources/js/qr-scan.js` — jsQR@1.4.0（`window.jsQR`）
- `resources/js/qr-code.js` — qrcode@1.5.4（`window.QRCode`）

**修改**
- `m3/devices.blade.php` — 2 個 CDN script → `@vite`
- `m9/settings.blade.php` — CDN → `@vite`，並**改寫 API**
  （`qrcodejs` 的 `new QRCode(container,{...})` → `qrcode` 的 `QRCode.toCanvas()`）

**技術決策**：`qrcode` 與 `qrcodejs` 是兩套不同 API 但**共用全域名稱 `QRCode`**。
同時載入會互相覆蓋，故統一為 `qrcode`（維護較活躍、支援 Promise API）。

**字型清除**：

| 檔案 | 處置 | 依據 |
|:---|:---|:---|
| `layouts/app.blade.php` | **刪除 Outfit** | 全站搜尋確認**無任何地方套用** |
| `layouts/auth.blade.php` | 改系統字型 | 有實際使用 |
| `iot/auth/portal-login.blade.php` | 改系統字型 | 有實際使用 |
| `welcome.blade.php` | 改系統字型 | 有實際使用 |

---

## 四、驗收指標

### 4.1 效能改善（CDP cache-disabled 實測）

| 資源 | 優化前 | 優化後 | 改善 |
|:---|:---|:---|:---|
| chart.js | 351ms（外部） | 61ms（本地） | **-290ms** |
| alpinejs | 276ms（外部） | 43ms（本地） | **-233ms** |
| @alpinejs/collapse | 264ms（外部） | 0ms（bundle） | **-264ms** |
| **外部 CDN 請求數** | **3 個** | **0 個** | ✅ |

### 4.2 外部依賴清零

```
rg 'cdn.jsdelivr|unpkg|cdnjs|googleapis|gstatic' resources/views/
→ NONE ✅

CDP 實測 m9 頁面 EXTERNAL(fonts/cdn): []   ← 歸零
```

### 4.3 功能實測（CDP Runtime.evaluate）

| 頁面 | 驗證項 | 結果 |
|:---|:---|:---|
| m3 設備管理 | `window.jsQR` | function ✅ |
| m3 設備管理 | `window.QRCode.toDataURL` | function ✅ |
| m3 設備管理 | QR 產生實測 | `{ok:true, isDataUrl:true}` ✅ |
| m9 全局設定 | `window.QRCode.toCanvas` | function ✅ |
| m9 全局設定 | QR 產生實測 | `{ok:true, canvasW:200, hasPixels:true}` ✅ |
| 營運看板 | 頁首「今日交易」 | 5,089 次 ✅ |
| 營運看板 | 7 日趨勢圖 | 正常渲染（canvas 1718） ✅ |
| 營運看板 | KPI 卡 | 交易次數 5,089 ✅ |
| 登入頁 | `x-cloak` 運作 | Alpine 已載入 ✅ |

**Console 錯誤**：全頁面 **0 錯誤**

### 4.4 部署驗證

```
waw_ops.sh deploy owner → ✅ 部署完成
bundle: app-TVCow97y.js (175KB)
        chartjs-EtFAQelh.js (207KB)
        qr-scan-BqHEuZRg.js (130KB)
        qr-code-CQDVsArr.js (25KB)
```

---

## 五、顯示語意修正（JOE 指示）

原本頁首「今日投幣」與 KPI 卡「投幣次數」語意不清。
經 JOE 確認，`transactionCount` 實為**動作筆數**（投幣 + 開分 + 退幣 + 洗分），
與金額無關。統一改為「**交易次數**」。

---

## 六、未完成 / 待決事項

### 6.1 Item 3「骨架屏 + Ajax 異步化」— 未執行

**原因**：經實測，SSR 首屏延遲主因（慢查詢 + 外部 CDN）已於階段 1-3 修復。
骨架屏屬「觀感優化」而非「效能瓶頸」，且需新增完整 dashboard JSON API
（目前僅有輕量 `/api/v9/dashboard/summary`，只回 device_count / today_revenue）。

**建議**：由 JOE 實測當前首屏表現後，再決定是否投入。

### 6.2 全域 layout 快取/查詢（次要）

`ArrearsComposer` 於每次 `layouts.app` 渲染時執行 3 次 DB 查詢
（devices arrears / venues arrears / outstanding_amount），未快取。
目前量測影響不大（Document 443ms 內），列為後續優化候選。

---

## 七、累計成果總表

| 階段 | commit | 內容 | 效益 |
|:---|:---|:---|:---|
| 1 | `b9e56c6` | 移除脫靶 SQL + 看板字型 | 少 1 次全表掃描 |
| 2 | `20bac58` | Alpine + Chart.js 本地化 | **-787ms** |
| 3 | `bf652d4` | QR 本地化 + 字型清除 | 外部依賴 **歸零** |

**最終狀態**：
- iot.tg25.win 全站 **零外部 CDN / 零外部字型依賴**
- 所有第三方資源均於部署時打包至自站 `public/build/assets/`
- 後端 `getDashboardData()` COLD 46ms / WARM 8ms
- 資料庫（Ina）`idx_venue_valid_ts`：7 日查詢 47.9s → 0.20s

---

## 八、結論

✅ 階段 1 完成：SQL 收斂 + 快取優化 + 資料流打通
✅ 階段 2 完成：Alpine + Chart.js 本地化（-787ms）
✅ 階段 3 完成：QR 本地化 + 字型清除（外部依賴歸零）
✅ 顯示語意修正（交易次數）
✅ 遠端部署 + 瀏覽器實測全數通過
⏸️ Item 3 骨架屏 — 建議待 JOE 實測後再決策

**請 HQ 審閱，並裁示 Item 3 是否投入。**

---

**Sophie (Owner) - 任務完成**

