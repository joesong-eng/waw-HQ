# 任務回報：手機版邊界與頂部空間壓縮（規範入庫）

**完成時間**：2026-10-01 11:00 (Asia/Taipei)
**執行者**：Sophie (Owner)
**關聯 commit**：ca2a200（waw-business: main）
**部署**：waw_ops.sh deploy owner 成功

---

## 一、需求

1. 手機版左右邊界留白過大，內容被擠壓 → **要寫進規則**。
2. 手機版上方（瀏覽器網址列 + 導航欄）佔用太多，主要內容被壓縮。

---

## 二、問題實測

| 項目 | 修改前 | 修改後 |
|:---|:---|:---|
| layout 左右 padding（手機） | 16px | **12.75px** |
| 頁面自身左右 padding | 額外 12~24px（疊加） | **0**（交給 layout） |
| 單側合計 | 最多 40px（390px 螢幕吃掉 80px） | **12.75px** |
| 頂部導航欄高度 | 64px | **56px**（≥1024px 才回 64px） |
| 瀏海／動態島 | 無處理（固定值硬墊） | `max(0.75rem, env(safe-area-inset-*))` |
| PWA | 未啟用 | manifest + apple meta 已接 |

---

## 三、變更內容

### 1. resources/css/app.css
- `.v9-content-area` 改為**手機優先**：`padding: 0.5rem 0.75rem`（原 `1rem`），
  `≥768px → 1.5rem`、`≥1024px → 2rem`。
- 左右改用 `max(0.75rem, env(safe-area-inset-left/right))`，支援瀏海／動態島。
- `--v9-header-h` 64px → **56px**（手機），`≥1024px` 還原 64px。

### 2. resources/views/layouts/app.blade.php
- 修正未定義的 `--core-header-h`（品牌區高度原本**完全失效**）→ `--v9-header-h`。
- 補 PWA meta：`theme-color`、`mobile-web-app-capable`、
  `apple-mobile-web-app-capable`、`apple-mobile-web-app-status-bar-style`、
  `manifest`、`apple-touch-icon`。

### 3. 13 個頁面移除最外層重複左右 padding

| 檔案 | 修改 |
|:---|:---|
| m10/deliveries, m10/test-webhook, m10/webhooks | `px-4` → 移除（layout 供給） |
| m6/quick-dashboard | `p-6` → `py-6` |
| m3/parameter-templates, m6/report-detail, m6/reports, m7/settlement-detail, m7/statements | `p-0 xl:p-6` → 移除 |
| portal | `px-6 py-8` → `py-8` |
| m2/plans | 捲動區 `px-4 sm:px-6` → `px-3 sm:px-5` |
| m3/devices | 捲動區 `p-6` → `p-4 sm:p-6` |
| realtime | `p-6` → `p-4 sm:p-6` |

### 4. resources/docs/UI_STANDARDS.md（規則入庫）
- **新增 §10「手機版邊界與頂部空間（強制）」**：
  - 10.1 左右邊界由 layout 統一供給，頁面最外層 padding 一律為 0，禁止疊加。
  - 10.2 頂部空間：導航欄手機 56px；**瀏覽器網址列無法由網頁關閉**，
    唯一正規做法是 PWA「加到主畫面」以 standalone 開啟；嚴禁 scrollTo 藏網址列等 hack。
- **§11 禁止事項新增 3 條**：頁面外層 padding 疊加、手機大留白（p-6/px-6）、卡片 mx- 二次內縮。
- §9 表格措辭精確化為「內層捲動區左右 padding」。

---

## 四、瀏覽器實測驗收（iot.tg25.win，390px）

| 頁面 | 頂部欄 | 左右 padding | 水平捲動 |
|:---|:---|:---|:---|
| /statistics/dashboard | 56px | 12.75px | 無 |
| /devices | 56px | 12.75px | 無 |
| /subscriptions/status | 56px | 12.75px | 無 |
| /realtime | 56px | 12.75px | 無 |
| /portal | 56px | 12.75px | 無 |
| /settings | 56px | 12.75px | 無 |
| /venues | 56px | 12.75px | 無 |

PWA meta 實測：manifest / theme-color / apple-mobile-web-app-capable /
apple-mobile-web-app-status-bar-style 全部正確輸出。

---

## 五、關於瀏覽器網址列（誠實說明）

手機瀏覽器網址列**無法由網頁 JavaScript 關閉**（瀏覽器安全限制）。
目前採取的兩項正規手段：
1. **縮減本站可控的頂部高度**（64 → 56px）。
2. **啟用 PWA**：使用者「加到主畫面」後以獨立 App 視窗開啟，網址列完全消失。

若希望進一步「開啟即無網址列」，建議在操作手冊中加註「加到主畫面」步驟；
或在 Safari 以「網頁 App」形式加入。此為瀏覽器層限制，非程式可繞過。

---

## 六、結論

✅ 完成。手機版單側邊界由最多 40px 降為 12.75px，頂部欄由 64px 降為 56px，
且規則已寫入 UI_STANDARDS.md §10/§11，後續新頁面不得再犯。
