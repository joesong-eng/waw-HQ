任務回報：TASK_20261001_SOPHIE_OPTIMIZE_DASHBOARD_PERF（追加二：外部依賴全數清零）

**完成時間**：2026-10-01 09:15 (Asia/Taipei)
**執行者**：Sophie (Owner)
**關聯 commit**：`bf652d4`（QR 本地化 + 字型清除）
**前置**：`b9e56c6`（SQL/字型）、`20bac58`（Alpine/Chart CDN 本地化）

---

## 一、決策依據：依賴 vs 取得方式

JOE 提問「外部依賴是不需要的嗎？還是要下載到 server？」
經分析，需區分**依賴本身**與**取得方式**：

| 類型 | 處置 | 原因 |
|:---|:---|:---|
| 功能庫（QR 掃描/產生） | **下載到 server（npm 打包）** | 無法用系統內建替代，必須保留功能 |
| 純視覺字型（未被使用） | **直接刪除** | 無功能價值，純浪費下載 |
| 純視覺字型（有被使用） | **改系統字型** | 零下載、視覺可接受 |

**「下載到 server」的正確流程**（非手動 wget）：
```
pnpm add 套件 → node_modules → vite build → public/build/assets/*.js
                                          ↑ waw_ops.sh deploy 自動執行
```

---

## 二、執行內容

### 1. QR 功能庫本地化（下載到 server）

**新增**
- `resources/js/qr-scan.js` — jsQR@1.4.0 bundle（`window.jsQR`）
- `resources/js/qr-code.js` — qrcode@1.5.4 bundle（`window.QRCode`）

**修改**
- `package.json` — 新增 `jsqr` / `qrcode` 依賴
- `vite.config.js` — 新增 2 個 entry
- `m3/devices.blade.php` — 2 個 CDN script → `@vite`
- `m9/settings.blade.php` — CDN script → `@vite`，並**改寫 API**
  （原用 `qrcodejs` 的 `new QRCode(container, {...})`，統一改用 `qrcode` 的
  `QRCode.toCanvas(canvas, text, {...})`，避免同站載入兩套 QR 函式庫）

**技術決策說明**：`qrcode` 與 `qrcodejs` 是兩套不同 API 但共用全域名稱 `QRCode`。
若同時載入會互相覆蓋，故統一為 `qrcode`（維護較活躍、支援 Promise API）。

### 2. 未使用字型清除

| 檔案 | 處置 | 依據 |
|:---|:---|:---|
| `layouts/app.blade.php` | **刪除 Outfit 載入** | 全站搜尋確認**無任何地方套用**，純浪費 |
| `layouts/auth.blade.php` | 改系統字型 | 有實際使用 `font-family: 'Outfit'` |
| `iot/auth/portal-login.blade.php` | 改系統字型 | 同上 |
| `welcome.blade.php` | 改系統字型 | 同上 |

系統字型堆疊：`system-ui, -apple-system, 'PingFang TC', 'Microsoft JhengHei', sans-serif`

---

## 三、驗收指標

### 外部依賴清零

```
rg 'cdn.jsdelivr|unpkg|cdnjs|googleapis|gstatic' resources/views/
→ NONE ✅
```

**CDP 實測（cache-disabled）m9 頁面**：
```
EXTERNAL(fonts/cdn): []   ← 外部請求歸零
```

### 功能實測（CDP Runtime.evaluate）

**m3 設備管理**
```json
{"jsQR":"function","QRCode":"object","toDataURL":"function","toCanvas":"function"}
```
- QR 產生實測：`{"ok":true,"isDataUrl":true,"len":1710}` ✅

**m9 全局設定**
```json
{"QRCode":"object","toCanvas":"function"}
```
- 改寫後 QR 產生實測：`{"ok":true,"canvasW":200,"hasPixels":true}` ✅
- Console 無錯誤 ✅

**部署**
```
git push 20bac58..bf652d4
waw_ops.sh deploy owner → ✅ 部署完成
新 bundle: qr-scan (130KB) / qr-code (25KB)
```

---

## 四、全工單累計成果（三階段）

| 階段 | commit | 內容 | 效益 |
|:---|:---|:---|:---|
| 1 | `b9e56c6` | 移除脫靶 SQL + 看板字型 | 少 1 次全表掃描 |
| 2 | `20bac58` | Alpine + Chart.js 本地化 | **-787ms** |
| 3 | `bf652d4` | QR 本地化 + 字型清除 | 外部依賴 **歸零** |

**最終狀態**：iot.tg25.win 全站 **零外部 CDN / 零外部字型依賴**，
所有第三方資源均於部署時打包至自站 `public/build/assets/`。

**後端效能**：`getDashboardData()` COLD 46ms / WARM 8ms
**資料庫**：Ina 索引 `idx_venue_valid_ts`，7 日查詢 47.9s → 0.20s

---

## 五、結論

✅ QR 功能庫已下載至 server（npm 打包），功能實測正常
✅ 未使用的 Outfit 字型已刪除，有使用的改系統字型
✅ 全站外部 CDN 與 Google Fonts 依賴 **= 0**
✅ m3 / m9 / 看板 / 登入頁 全部實測通過、無 console 錯誤

---

✅ 完成

