任務回報：TASK_20261001_SOPHIE_OPTIMIZE_DASHBOARD_PERF（追加：前端 CDN 本地化）

**完成時間**：2026-10-01 08:59 (Asia/Taipei)
**執行者**：Sophie (Owner)
**關聯 commit**：`b9e56c6`（SQL/字型）、`20bac58`（CDN 本地化）
**觸發**：JOE 反映「首屏速度感覺還是不行」→ 重新量測定位真因

---

## 一、根因重新定位（實測數據）

JOE 反映首屏仍慢，經 CDP（cache-disabled）精確量測，發現**後端不是瓶頸**：

| 資源 | 優化前 | 來源 |
|:---|:---|:---|
| Document（Laravel SSR） | 443ms（TTFB 380ms） | 自家（**正常**） |
| **chart.js** | **351ms** | cdn.jsdelivr.net ❌ |
| **alpinejs** | **276ms** | cdn.jsdelivr.net ❌ |
| **@alpinejs/collapse** | **264ms** | cdn.jsdelivr.net ❌ |
| fonts.googleapis.com | 37ms | Google ❌ |
| app.css / app.js | 54ms / 45ms | 自家 |

**後端實測**：`getDashboardData()` COLD 46ms / WARM 8ms → 確認瓶頸在**前端外部 CDN**。

---

## 二、修復內容

### 前端外部 CDN 本地化（Vite bundle）

**新增**
- `resources/js/alpine.js` — Alpine + collapse 本地 bundle（`window.Alpine`）
- `resources/js/chartjs.js` — Chart.js 本地 bundle（`window.Chart`）

**修改**
- `package.json` — 新增 `alpinejs` / `@alpinejs/collapse` 依賴
- `vite.config.js` — 新增 `chartjs.js` entry（獨立 chunk，僅看板載入）
- `resources/js/app.js` — `import './alpine'`（全站生效）
- `layouts/app.blade.php` — 移除 Alpine CDN ×2
- `layouts/auth.blade.php` — 移除 Alpine CDN ×2
- `iot/auth/portal-login.blade.php` — 移除 Alpine CDN
- `m6/dashboard.blade.php` — chart.js CDN → `@vite`，並加入**載入順序防護**
  （module 可能晚於 Alpine 初始化，若 `window.Chart` 未就緒則輪詢重試）

---

## 三、驗收指標（CDP cache-disabled 實測）

| 資源 | 優化前 | 優化後 | 改善 |
|:---|:---|:---|:---|
| chart.js | 351ms（外部） | **61ms（本地）** | **-290ms** |
| alpinejs | 276ms（外部） | **43ms（本地，含於 app.js）** | **-233ms** |
| @alpinejs/collapse | 264ms（外部） | **0ms（已 bundle）** | **-264ms** |
| **外部 CDN 請求總數** | **3 個** | **0 個** ✅ | — |

**外部依賴現況**：僅剩 `fonts.googleapis.com`（全域 Outfit，未在本次範圍）。

---

## 四、瀏覽器實測（iot.tg25.win）

**營運看板**（owner@tg25.win）
- ✅ 頁首「今日交易 **5,089** 次」（Alpine 綁定正常）
- ✅ KPI 卡：今日營收 $1,235 / 交易次數 5,089
- ✅ 本週 $2,405、本月 $1,235
- ✅ 場地對比（西門旗艦店 $988 / 台中一中店 $247）
- ✅ **7 日趨勢圖正常渲染**（canvas width 1718）
- ✅ Console 無錯誤

**登入頁**（layouts/auth）
- ✅ 正常渲染、無錯誤
- ✅ `x-cloak` 正確運作（證明 Alpine 已載入並執行）
- ✅ 僅載入本地 app.js，無 CDN

**部署**
```
git push b9e56c6..20bac58
waw_ops.sh deploy owner → ✅ 部署完成
bundle: app-C36l7Pak.js (175KB) / chartjs-EtFAQelh.js (207KB)
```

---

## 五、結論

✅ 首屏慢真因確認為**外部 CDN 阻塞**（非後端、非資料庫）
✅ Alpine + Chart.js 已本地化，**外部 CDN 請求 3 → 0**
✅ 看板與登入頁功能完整、無 console 錯誤
✅ 遠端部署 + 瀏覽器實測通過

**殘留（未在本次範圍）**
- `fonts.googleapis.com`（全域 Outfit 字型，約 35ms）— 需另開工單
- `m3/devices.blade.php`（jsQR、qrcode）、`m9/settings.blade.php`（qrcodejs）
  仍有 CDN，屬其他模組，未動

---

✅ 完成

