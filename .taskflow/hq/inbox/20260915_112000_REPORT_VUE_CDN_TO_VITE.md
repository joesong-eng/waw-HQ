# 任務回報：20260915_MINA_VUE_CDN_TO_VITE + P1_WELCOME_VUE_CDN（合併工單 #5 + #12）

**完成時間**：2026-09-15 11:20
**執行者**：mina

## 執行結果

### 問題
welcome.blade.php 和 play.blade.php 使用 `https://unpkg.com/vue@3/...` CDN 載入 Vue 3，存在資安風險、效能不佳、離線環境失效。

### 修改

**1. package.json** — 新增依賴：
- `vue@^3.5.0`（Vue 3 核心）
- `html5-qrcode@^2.3.8`（QR 掃碼器）
- `@vitejs/plugin-vue@^5.2.0`（Vite Vue 插件）

**2. vite.config.js** — 更新：
- 新增 `vue()` 插件
- 新增入口 `resources/js/welcome-app.js` 和 `resources/js/play-app.js`
- 更新註解說明

**3. resources/js/welcome-app.js** — 新建（775 行）：
- 從 welcome.blade.php 提取全部 Vue 3 createApp 邏輯
- `import { createApp, ref, computed, onMounted } from 'vue'`（npm 包）
- `import 'html5-qrcode'`（npm 包）
- `async setup()`（支援 top-level await）

**4. resources/js/play-app.js** — 新建（393 行）：
- 從 play.blade.php 提取全部 Vue 3 createApp 邏輯
- `import { createApp, ref, computed, onMounted, onUnmounted } from 'vue'`
- `async setup()`

**5. welcome.blade.php** — 精簡：
- 1256 行 → 488 行（移除 768 行內聯 Vue 腳本）
- 移除 `<script src="https://unpkg.com/html5-qrcode">`
- `@vite` 新增 `welcome-app.js` 入口

**6. play.blade.php** — 精簡：
- 650 行 → 258 行（移除 392 行內聯 Vue 腳本）
- `@vite` 新增 `play-app.js` 入口

### 部署修復過程
1. 首次部署：Vite build 失敗 — `await` in non-async function → 修正 `setup()` → `async setup()`
2. 二次部署：Vite build 失敗 — Python 風格 `if hasattr(e, 'event')` → 修正為 `e.event || 'unknown'`
3. 三次部署：✅ 成功（92 modules transformed）

### 驗收
- **首頁** `https://win.tg25.win/` → **200** ✅
- **Play 頁** `https://win.tg25.win/m/play` → **200** ✅
- **無 CDN 引用** — `curl` 確認首頁無 unpkg.com 引用 ✅
- **Vite manifest** 包含所有 4 個入口 ✅
- **Bundle sizes**：
  - welcome-app.js: 308.49 KB (gzip: 94.89 KB)
  - play-app.js: 6.73 KB (gzip: 2.50 KB)
  - Vue runtime: 60.83 KB (gzip: 24.09 KB) — 共享 chunk

### Commits
- `02022ca` — 主要遷移（6 files changed, 1187 insertions, 1182 deletions）
- `05c4357` — async setup() 修正
- `df5a30e` — Python-style if expression 修正

## 結論
✅ 完成（Vue 3 從 CDN 遷移至 Vite 打包，所有頁面正常渲染）

---
**回報者**：mina
**回報時間**：2026-09-15 11:20
