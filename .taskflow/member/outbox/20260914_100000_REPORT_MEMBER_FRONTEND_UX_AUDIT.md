# Member 專案前端 UX 玩家視角動線審查報告

**執行時間**：2026-09-14 10:00
**負責人**：Mina (Member)
**審查方法**：以玩家視角從頭到尾走完每一條操作動線，逐動作推敲 UI/UX 合理性
**審查範圍**：`welcome.blade.php`（首頁 + Dashboard + 掃碼 + 交易明細 + Kiosk 兌幣流程）、`play.blade.php`（遊戲機頁面）、`privacy.blade.php`、`terms.blade.php`、`venue/*.blade.php`

---

## 一、玩家完整動線圖

### 動線 A：遊戲機流程（主流程）
```
打開 win.tg25.win → LINE 登入 → Dashboard → 點掃碼 FAB → 掃遊戲機 QR
→ 跳轉 /m/play?t=xxx → 服務協議彈窗 → 點「同意並開始」→ 遊戲面板
→ 選開分數量 → 確認開分（扣代幣）→ 玩遊戲 → 點「立即洗分」
→ 等待 WebSocket 回推 → 彩票入帳 → 點「離開」→ 返回首頁
```

### 動線 B：Kiosk 儲值機流程
```
打開 win.tg25.win → LINE 登入 → Dashboard → 點掃碼 FAB → 掃 Kiosk QR
→ 綁定 API → Exchange 視圖 → 等待投幣 → 投入鈔票 → 代幣入帳
→ 60 秒倒數 → 自動結束或手動結束 → 結算頁 → 返回 Dashboard
```

### 動線 C：未登入直接掃碼
```
掃遊戲機 QR → 跳轉 /m/play?t=xxx → 偵測無 token → 顯示 LINE 登入按鈕
→ LINE 登入 → 回到 /m/play → 自動帶入 sessionStorage 參數 → 服務協議 → 遊戲面板
```

---

## 二、逐動動線推敲

### 📱 動作 1：打開首頁 `win.tg25.win`

**玩家看到**：暗色賽博龐克風格頁面，WAW Logo + 「玩家登入」標題 + LINE 綠色登入按鈕 + 三個特色圖標（即時上分、錢包管理、交易明細）

#### 🔴 問題 1.1：登入前無任何預覽

玩家第一次到訪，立刻被登入牆擋住。沒有「關於 WAW」、沒有「如何使用」、沒有任何預覽內容。玩家不知道這是什麼服務就被要求 LINE 授權。

**建議**：登入頁加入「快速導覽」或「什麼是 WAW？」的展開區塊，或至少在登入按鈕下方加一行說明文字。

#### 🟡 問題 1.2：外部背景紋理 CDN 依賴

```html
class="bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]"
```

背景紋理從 `transparenttextures.com` 載入。CDN 不穩定或被牆時，登入頁背景變成純黑色，視覺體驗降級。

**建議**：下載紋理圖片到 `public/images/` 本地引用。

#### 🟡 問題 1.3：隱私權 Modal 內容不完整

隱私權彈窗的內容被截斷，多個 `<section>` 段落的文字不完整：

```html
<section>🛡️ LINE ... LINE (LINE LINE (LINE </section>
<section>💬 LINE LINE LINE </section>
<section>🔒 </section>
```

看起來是模板渲染或編輯時的錯誤，內容流失或被誤刪。玩家點開隱私說明看到的卻是一堆亂碼文字。

**建議**：重新填寫完整的隱私權說明文字。

---

### 📱 動作 2：點擊「LINE 快速登入」

**玩家操作**：點擊綠色 LINE 按鈕 → 按鈕顯示轉圈 → 跳轉到 LINE 授權頁面 → 授權後跳回 `win.tg25.win?token=xxx&profile=xxx`

#### 🔴 問題 2.1：LINE 回調後 URL 帶有明文 Token

```javascript
const tokenQuery = urlParams.get('token');
const profileQuery = urlParams.get('profile');
// ...
localStorage.setItem('waw_token', token.value);
localStorage.setItem('waw_profile', profile.value);
```

LINE OAuth 回調後，Sanctum Token 和會員資料直接寫在 URL Query String 裡。這意味著：
- 瀏覽器歷史記錄可見 Token
- Referer Header 可能洩漏 Token 給第三方
- 伺服器 Access Log 記錄了 Token

**建議**：改用 LINE OAuth Code Exchange 模式，後端透過 Session 或 HttpOnly Cookie 傳遞 Token，不在 URL 暴露。

#### 🟡 問題 2.2：登入成功後顯示 Debug Toast

```javascript
showToast('token: ' + (token.value ? token.value.substring(0,10) : 'NULL'), 'info');
```

玩家登入成功後，畫面頂部彈出 `token: e6cff92abc...` 的 debug 訊息。這是開發遺留，不應出現在正式環境。

#### 🟡 問題 2.3：登入按鈕中的 Dev Phone 登入殘留

```javascript
const loginPhone = ref('+886****2333');
const doLogin = async () => {
    loading.value = true;
    const data = await apiFetch(`/api/dev/token?phone=${loginPhone.value}`);
    // ...
};
```

雖然 UI 上沒有顯示 phone 登入入口，但 `doLogin` 和 `loginPhone` 仍在 JS 中且被 return。在 production 環境 `/api/dev/token` 會回 403，但如果有人從 Console 呼叫 `doLogin()` 會看到錯誤。

**建議**：移除 dev login 相關代碼，或用環境判斷包裹。

---

### 📱 動作 3：登入成功，進入 Dashboard

**玩家看到**：頭像/名稱 + ONLINE 徽章 + 餘額卡（代幣 + 彩票）+ 近期活動列表 + 底部巨大的紫色掃碼 FAB 按鈕

#### 🟠 問題 3.1：餘額顯示邏輯不一致

```javascript
const wallet = data.data.find(w => w.currency_type === 'COIN')
    || data.data.find(w => w.currency_type === 'TOKEN')
    || data.data.find(w => w.currency_type === 'POINT');
```

前端用 OR 鏈查找多種幣別字串，但後端常數只有 `COIN` 和 `TICKET`。如果後端只回傳 `COIN` 錢包但名稱跟前端不匹配，餘額顯示 0。

#### 🟡 問題 3.2：掃碼 FAB 按鈕遮擋內容

```html
<div class="fixed bottom-8 left-1/2 -translate-x-1/2 z-40">
```

FAB 按鈕使用 `fixed` 定位，在捲動瀏覽交易紀錄時會遮擋最後幾筆紀錄。雖然有 `pb-8` 留白但不足。

**建議**：改為 `sticky` 或增加底部 padding。

#### 🟡 問題 3.3：無下拉刷新

手機用戶最自然的刷新操作是下拉刷新，目前完全沒有實作。玩家想看最新餘額必須關閉重開頁面。

#### 🟡 問題 3.4：版本標記可見

```html
<div class="version-tag">v1.1.7</div>
```

右下角顯示版本號，這是開發用標記，正式環境不需要對玩家展示。

---

### 📱 動作 4：點擊掃碼 FAB → 掃碼視圖

**玩家操作**：點 FAB → 跳轉到全黑掃碼頁面 → 相機開啟 → 掃描 QR Code

#### 🔴 問題 4.1：手動輸入框預填了真實 chip_id

```javascript
const manualChipId = ref('sr9adyxpdyt1tuf7');
```

掃碼視圖底部的「手動 chip_id」輸入框預填了一個真實的 chip_id（`sr9adyxpdyt1tuf7`）。這是開發遺留。玩家如果直接點「確認」就會嘗試綁定這台機器。

**建議**：預設值改為空字串 `''`。

#### 🟡 問題 4.2：無手電筒/閃光燈開關

光線不足時無法開啟手電筒輔助掃碼，這在場館昏暗環境中是常見需求。

#### 🟡 問題 4.3：無前後鏡頭切換

部分手機默認使用前置鏡頭，沒有切換按鈕。

#### 🟡 問題 4.4：掃碼器關閉時相機可能未正確釋放

```javascript
if (html5QrcodeScanner.isScanning) {
    html5QrcodeScanner.stop();
}
```

如果 `stop()` 失敗（網路問題、設備忙碌），相機可能不會被釋放，導致下次打開掃碼器時黑屏。

---

### 📱 動作 5：掃碼成功 → 跳轉到 /m/play

**玩家操作**：掃到 `https://win.tg25.win/m/play?t=xxx` → 瀏覽器跳轉 → play.blade.php 載入

#### 🟠 問題 5.1：跳轉過程無過渡動畫

從掃碼成功到跳轉頁面，玩家體驗是「突然白屏 → 新頁面載入」。沒有 loading 動畫或過渡。

#### 🟡 問題 5.2：URL 參數清理時機不精確

```javascript
// 清理 URL 中的 token 參數（如果誤帶的話）
if (urlParams.has('token')) {
    const searchPart = publicToken ? `?t=${publicToken}` : ...;
    window.history.replaceState({}, document.title, cleanUrl);
}
```

只在 URL 有 `token` 參數時才清理，但其他參數（`t`, `node_id`, `chip_id`）在 init() 成功後才清理。如果 init() 失敗，URL 中的參數會一直留著，玩家重新整理時會帶著舊參數。

---

### 📱 動作 6：服務協議彈窗

**玩家看到**：全屏遮罩 + 玻璃面板彈窗，標題「使用服務協議與確認開分」+ 規則文字 + 「拒絕並離開」「同意並開始」按鈕

#### 🟡 問題 6.1：協議文字硬編碼在前端

```javascript
agreementText.value = "遊戲規則：\n1. 請保持手機連線以接收洗分金額\n2. 機台斷線時無法洗分，分數將無法找回\n3. 120 秒無遊戲活動將自動結束遊戲\n4. 結束遊戲前請先洗分";
```

協議文字寫死在 JS 裡，不能從後台動態調整。如果要修改規則必須改代碼重新部署。

**建議**：由後端 API 動態返回，或存入資料庫。

#### 🟡 問題 6.2：協議文字用 \n 換行但 CSS 用 whitespace-pre-line

```html
<p class="... whitespace-pre-line ...">@{{ agreementText }}</p>
```

`whitespace-pre-line` 可以正確渲染 `\n` 為換行，但文字間距過密，無段落分隔。4 條規則擠在一起，閱讀體驗差。

#### 🟠 問題 6.3：「拒絕並離開」直接踢回首頁

玩家如果不小心點了拒絕，直接 `window.location.href = '/'` 回首頁。沒有二次確認。玩家必須重新掃碼。

---

### 📱 動作 7：進入遊戲面板

**玩家看到**：機台名稱 + 代幣/彩票餘額卡 + 開分選項按鈕（3 格）+ 確認開分按鈕 + 洗分按鈕 + 交易記錄

#### 🟠 問題 7.1：開分無二次確認

```javascript
const doCredit = async () => {
    if (!canCredit.value) return;
    // 直接扣款，無 confirm
    const data = await apiFetch('/api/device/credit', {...});
};
```

選好開分數量後點按鈕，**直接扣代幣送出開分指令**，沒有任何二次確認。這是涉及金錢的操作，玩家可能誤觸。相比之下，洗分反而有 `confirm()` 對話框。

**建議**：開分操作加二次確認（可以是滑動確認或點擊兩次）。

#### 🟠 問題 7.2：洗分用瀏覽器原生 confirm() — 嚴重破壞 UI 一致性

```javascript
if (!confirm('確定要執行洗分嗎？機台分數將會結算為彩票。')) return;
```

整個應用是賽博龐克玻璃擬態風格，突然彈出一個白色系統原生 `confirm()` 對話框，視覺嚴重割裂。且在 iOS Safari 中，原生 confirm 會阻塞主線程。

**建議**：用自訂 Modal 替換，與服務協議彈窗風格一致。

#### 🟠 問題 7.3：洗分後無進度反饋

```javascript
const data = await apiFetch('/api/device/settle', {...});
showToast(data.message || '洗分指令已送出', 'success');
```

API 回 `queued` 後，只顯示一個 toast「洗分指令已送出」。玩家不知道接下來要等多久、是否成功。實際結果靠 WebSocket `DeviceCreditOut` 事件回推，但如果 WS 斷線，玩家永遠等不到結果。

**建議**：
1. 洗分後顯示進度條或等待動畫
2. 加超時處理：若 30 秒內無 WS 回推，顯示「洗分超時，請聯繫服務台」
3. 允許手動查詢洗分狀態

#### 🟡 問題 7.4：交易記錄不持久化

```javascript
const logs = ref([]);
```

本次交易記錄存在 Vue ref 記憶體中，頁面刷新即消失。玩家如果在上分後刷新頁面，看不到之前開了幾分。

#### 🟡 問題 7.5：離開按鈕太小且不明顯

```html
<button v-if="sessionId" @click="doUnbind"
    class="mt-2 px-4 py-2 rounded-xl bg-neutral-800 text-neutral-400 text-sm font-bold">
    ✕ 離開
</button>
```

「離開」按鈕在右上角，灰底灰字，很容易被忽略。玩家可能找不到如何結束遊戲。

#### 🟡 問題 7.6：無 WebSocket 斷線提示

如果 WebSocket 斷線（網路不穩、Reverb 重啟），玩家完全不知道。開分/洗分結果無法即時更新，但 UI 不會告訴玩家「連線中斷」。

**建議**：加 WS 連線狀態指示器，斷線時顯示「連線中斷，請檢查網路」。

#### 🟡 問題 7.7：超時踢人邏輯可能誤殺

```
120 秒無遊戲活動 → 自動結束 session
```

玩家在機台上玩遊戲時，API 活動（開分/洗分）之間可能超過 120 秒。玩家正在玩，但手機端被判超時踢出。"遊戲活動"應指機台端的活動，不應只看手機端 API 呼叫。

#### 🟡 問題 7.8：無餘額手動刷新

WebSocket 斷線時餘額卡死，沒有刷新按鈕或下拉刷新。

---

### 📱 動作 8：點擊「離開」返回首頁

**玩家操作**：點離開 → 呼叫 `/api/device/unbind` → 跳回首頁 → Dashboard

#### 🟡 問題 8.1：離開時無交易摘要

玩家離開遊戲時直接跳回首頁，沒有「本次遊戲摘要」：開了幾次分、洗了幾次分、總花費多少代幣、獲得多少彩票。

**建議**：離開前顯示一個摘要卡片。

#### 🟡 問題 8.2：unbind API 失敗靜默處理

```javascript
} catch (e) { /* 靜默失敗 */ }
window.location.href = '/';
```

即使 unbind API 失敗，仍然跳回首頁。如果 session 沒有正確結束，玩家下次掃其他機台時會被「一人一台」規則擋住（409）。

---

### 📱 動作 9：Kiosk 儲值機流程

**玩家操作**：掃碼 Kiosk QR → 綁定成功 → Exchange 視圖 → 投入鈔票 → 代幣入帳 → 倒數結束

#### 🔴 問題 9.1：大量 Debug Toast 洩露給玩家

```javascript
showToast('Ping heartbeat: SID=' + exchangeSessionId.value, 'info');
showToast(`Flow: SID:${data.session_id} | CID:${data.kiosk_id} | View:${currentView.value}`, 'info');
showToast('token: ' + (token.value ? token.value.substring(0,10) : 'NULL'), 'info');
```

玩家在 Kiosk 儲值流程中會看到一堆 session ID、kiosk ID、view 狀態的 debug 訊息。這些是完全的開發遺留。

#### 🟠 問題 9.2：60 秒初始倒數太短

```javascript
startExchangeCountdown(60);
```

玩家綁定 Kiosk 後只有 60 秒可以投幣。如果玩家需要從口袋掏錢、整理鈔票，60 秒可能不夠。每次投幣成功會重置為 60 秒，但第一段時間太緊張。

**建議**：初始倒數改為 120 秒。

#### 🟠 問題 9.3：Escrow 確認倒數 15 秒太短

```javascript
escrowConfirmCountdown.value = 15;
```

Escrow（裁決入帳）確認只有 15 秒。玩家可能還在理解發生了什麼事，倒數就結束了。且 Escrow Modal 只顯示「交易進行中...」+ 金額，沒有解釋為什麼需要確認、確認什麼。

#### 🟡 問題 9.4：無紙鈔退回通知

KioskRejected 事件只在 Dashboard 的 Echo 監聽中處理：

```javascript
channel.listen('.KioskRejected', (e) => {
    showToast(`⚠️ ${e.message || '入金被拒...'}`, 'error');
});
```

但在 Exchange 視圖中，`setupKioskEcho` 沒有監聽 `KioskRejected` 事件。玩家在儲值機頁面投幣被退時，**不會收到任何通知**。

#### 🟡 問題 9.5：心跳間隔 10 秒可能耗電

```javascript
exchangeHeartbeatInterval = setInterval(pingHeartbeat, 10000);
```

每 10 秒發一次心跳，在長時間儲值場景下會持續喚醒手機無線模組，耗電。

#### 🟡 問題 9.6：結束後無收據

Exchange 完成後顯示簡短摘要（本次兌換 X 代幣），但返回 Dashboard 後沒有持久化的收據。玩家無法回顧「我在哪台 Kiosk 存了多少錢」。

#### 🟡 問題 9.7：beforeunload 心跳可能孤兒化

```javascript
fetch(`/api/kiosk/session/${exchangeSessionId.value}/end`, {
    keepalive: true
}).catch(err => console.error('beforeunload fetch error:', err));
```

如果 `keepalive` fetch 失敗（iOS Safari 對 keepalive 有限制），session 不會被正確關閉，成為殭屍 session。

---

### 📱 動作 10：交易明細頁面

**玩家操作**：Dashboard 點「View All Transactions →」→ 交易明細列表 + Tab 篩選

#### 🟡 問題 10.1：Tab 篩選邏輯不完整

```javascript
if (activeTab.value === 'coins') {
    return list.filter(tx => tx.currency_type === 'COIN' || tx.currency_type === 'TOKEN' || tx.currency_type === 'POINT');
}
if (activeTab.value === 'tickets') {
    return list.filter(tx => tx.currency_type === 'TICKET');
}
```

「代幣」Tab 篩選三種字串，但系統只有 `COIN`。如果未來加新幣別，這裡要手動改。

#### 🟡 問題 10.2：交易記錄時間格式不友善

```html
@{{ new Date(tx.created_at).toLocaleString() }}
```

顯示 `2026/9/14 上午 10:30:00` 格式，太長。應改為相對時間（「3 分鐘前」）或精簡格式（`09/14 10:30`）。

#### 🟡 問題 10.3：無分頁

只從 API 取 20 筆，超過的看不到。無限滾動或「載入更多」按鈕都沒有。

---

### 📱 動作 11：Venue 場館管理頁面

**玩家操作**：不會主動到達，但 URL 可直接訪問 `/devices`, `/billing`, `/subscriptions`

#### 🔴 問題 11.1：Venue 頁面無任何認證保護

```php
Route::get('/subscriptions', view('venue.subscriptions'));
Route::get('/devices', view('venue.devices'));
Route::get('/billing', view('venue.billing'));
```

場館管理頁面（設備管理、帳單繳費、訂閱方案）完全沒有 auth middleware。任何人都能訪問並看到場館的設備清單、帳單金額、繳費帳號。

#### 🔴 問題 11.2：Venue 頁面用 Tailwind CDN 而非 Vite

```html
<script src="https://cdn.tailwindcss.com"></script>
```

Venue 頁面用 Tailwind CDN，與主站的 Vite 打包流程完全不同。CDN 版會在 production 顯示警告，且效能差。

#### 🟡 問題 11.3：Venue 頁面用 Alpine.js 而非 Vue

```html
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.3/dist/cdn.min.js"></script>
```

主站用 Vue 3，Venue 用 Alpine.js，兩套前端框架並存，維護成本高。

#### 🟡 問題 11.4：Venue 頁面資料全是假資料

設備列表、帳單金額、訂閱方案全部是寫死的假資料（`M-001`, `V-0012`, 玉山銀行帳號 `0123-456-789012` 等）。不是從 API 拉取的真實資料。

---

### 📱 通用問題

#### 🟡 問題 G.1：console.log 遍布正式代碼

整個前端 JS 充滿 `console.log()`：
- `console.log('Detected Kiosk QR...')`
- `console.log('Bind API success:', ...)`
- `console.log('Heartbeat sent')`
- `console.log('Kiosk event received:', e)`

在 production 環境這些都會輸出到瀏覽器 Console，影響效能且洩露內部邏輯。

#### 🟡 問題 G.2：中英文混用不統一

- 標題："RECENT ACTIVITY"（英）、"交易明細"（中）
- 按鈕："Scan to Play"（英）、"確認開分"（中）
- 狀態："ONLINE"（英）、"已連線"（中）
- 幣別："Tokens"（英）、"彩票"（中）

視覺層次混亂，不專業。

#### 🟡 問題 G.3：Vue 從 CDN 載入導致載入順序問題

```javascript
import { createApp } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js'
```

Vue 從 CDN 載入，如果 CDN 慢或被牆，頁面會白屏。且 `echo.js` 依賴 `window.Echo`，載入順序不正確時 `Echo` 可能未定義。

#### 🟡 問題 G.4：無 PWA 安裝引導

有 `site.webmanifest` 但無安裝引導邏輯。玩家不知道可以「加到主畫面」當 App 用。

#### 🟡 問題 G.5：無離線/斷網處理

完全沒有離線處理。如果手機斷網，所有 API 呼叫直接報錯，沒有「網路已斷線」的友善提示或重試邏輯。

#### 🟡 啈題 G.6：無頁面切換動畫

Dashboard → Scanner、Dashboard → History 等視圖切換沒有過渡動畫，畫面突然切換，體驗生硬。

---

## 三、問題優先級匯總

### 🔴 P0 嚴重問題（安全/功能破壞）

| # | 問題 | 影響 |
|:---|:---|:---|
| 2.1 | LINE 回調 URL 帶明文 Token | Token 洩漏風險 |
| 4.1 | 手動輸入框預填真實 chip_id | 玩家誤觸綁定隨機機台 |
| 9.1 | Kiosk 流程大量 Debug Toast | 洩露內部資訊，破壞體驗 |
| 11.1 | Venue 頁面無認證 | 場館敏感資訊全暴露 |

### 🟠 P1 邏輯/體驗問題

| # | 問題 | 影響 |
|:---|:---|:---|
| 1.1 | 登入前無預覽 | 新用戶困惑 |
| 1.3 | 隱私權 Modal 內容損壞 | 法律合規風險 |
| 7.1 | 開分無二次確認 | 誤觸扣款 |
| 7.2 | 洗分用原生 confirm() | 視覺割裂 |
| 7.3 | 洗分後無進度反饋 | 玩家焦慮等待 |
| 7.7 | 超時踢人邏輯可能誤殺 | 玩家正玩到一半被踢 |
| 9.2 | Kiosk 初始 60 秒太短 | 來不及掏錢 |
| 9.3 | Escrow 確認 15 秒太短 | 來不及理解 |
| 9.4 | Exchange 視圖無退鈔通知 | 玩家不知道鈔票被退 |

### 🟡 P2 優化建議

| # | 問題 | 影響 |
|:---|:---|:---|
| 1.2 | 外部背景紋理 CDN | 視覺降級 |
| 2.2 | 登入 debug toast | 不專業 |
| 2.3 | Dev login 殘留代碼 | 程式碼污染 |
| 3.1 | 餘額幣別查找不一致 | 顯示 0 |
| 3.2 | FAB 遮擋內容 | 可用性 |
| 3.3 | 無下拉刷新 | 操作不便 |
| 3.4 | 版本標記可見 | 不專業 |
| 4.2 | 無手電筒 | 昏暗環境不可用 |
| 4.3 | 無鏡頭切換 | 部分手機不可用 |
| 5.1 | 跳轉無過渡動畫 | 體驗生硬 |
| 6.1 | 協議文字硬編碼 | 不易維護 |
| 6.3 | 拒絕協議無二次確認 | 誤觸需重掃 |
| 7.4 | 交易記錄不持久 | 刷新遺失 |
| 7.5 | 離開按鈕不明顯 | 找不到出口 |
| 7.6 | 無 WS 斷線提示 | 不知連線中斷 |
| 7.8 | 無餘額手動刷新 | 餘額卡死 |
| 8.1 | 離開無交易摘要 | 缺乏回顧 |
| 9.5 | 心跳 10 秒耗電 | 電池續航 |
| 9.6 | 無 Kiosk 收據 | 無法追溯 |
| 10.1 | Tab 篩選邏輯不完整 | 分類不準 |
| 10.2 | 時間格式不友善 | 閱讀困難 |
| 10.3 | 無分頁 | 歷史看不到 |
| 11.2 | Venue 用 Tailwind CDN | 效能差 |
| 11.3 | Venue 用 Alpine.js | 維護成本 |
| 11.4 | Venue 假資料 | 無實際功能 |
| G.1 | console.log 遍布 | 效能/安全 |
| G.2 | 中英文混用 | 不專業 |
| G.3 | Vue CDN 依賴 | 可靠性 |
| G.4 | 無 PWA 引導 | 發現性 |
| G.5 | 無離線處理 | 斷網即崩 |
| G.6 | 無頁面切換動畫 | 體驗生硬 |

---

## 四、建議修復排程

### 第一階段：緊急（1-2 天）
1. P0-4.1：清除手動輸入框預填值 → 1min
2. P0-9.1：移除所有 debug toast → 15min
3. P0-11.1：Venue 頁面加 auth middleware → 10min
4. P0-2.1：LINE OAuth 改用 Code Exchange → 需後端配合，3-4h
5. P1-7.2：洗分 confirm() 改為自訂 Modal → 30min
6. P1-7.1：開分加二次確認 → 20min
7. P1-9.4：Exchange 加 KioskRejected 監聽 → 15min

### 第二階段：重要（1 週內）
8. P1-9.2：Kiosk 初始倒數改 120 秒 → 5min
9. P1-9.3：Escrow 倒數改 30 秒 → 5min
10. P1-7.3：洗分後加進度動畫 + 超時處理 → 1h
11. P1-7.7：超時邏輯改為看機台活動 → 需後端配合
12. P1-1.3：修復隱私權 Modal 內容 → 15min
13. P2-7.6：加 WS 斷線提示 → 30min
14. P2-7.8：加餘額刷新按鈕 → 15min
15. P2-6.1：協議文字改後端返回 → 1h

### 第三階段：優化（2 週內分批）
16. P2-G.1：移除所有 console.log → 30min
17. P2-G.2：統一語言 → 1h
18. P2-G.3：Vue 改 Vite 打包 → 2h（與代碼審查報告 P2-1 合併）
19. P2-3.2：FAB 改 sticky → 10min
20. P2-3.4：移除版本標記 → 1min
21. P2-4.2：加手電筒開關 → 30min
22. P2-7.5：離開按鈕加大 → 5min
23. P2-8.1：離開加交易摘要 → 1h
24. P2-9.6：Kiosk 完成後加收據 → 1h
25. P2-10.2：時間格式改相對時間 → 15min
26. P2-G.6：加頁面切換動畫 → 1h
27. P2-1.1：登入頁加預覽 → 30min

---

**回報人**：Mina (Member)
**回報時間**：2026-09-14 10:00
**等待指示**：HQ 裁決修復排程，是否與代碼安全審查報告合併處理
