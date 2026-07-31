# 兌幣機介面 UI 與多螢幕顯示規格書 (Kiosk UI & Screen Design Specification)

> **版本**：v2.0.0 (合併版)  
> **最後更新**：2026-06-05  
> **狀態**：Active / Authoritative  
> **適用角色**：Mina (Member), Hubie (iHub), Fio (Firmware)

---

# 兌幣機 UX 設計規範

> ⚠️ **此文件已過時（Superseded）**
> 
> 本文件版本 1.0.0（2026-05-04）的設計方向已被推翻，以下內容**不得作為實作依據**：
> - §一「手機是操作介面，平板是狀態顯示器」→ **已推翻**，現行設計為 iHub 平板是唯一裁決方
> - §二「投幣不需要確認步驟，系統自動入帳」→ **已推翻**，現行設計為人工確認（HQ 決策 2026-05-08）
> - §三「2 分鐘無投幣自動結束」→ **已推翻**，現行為 60 秒
> - §六 QR Code 靜態格式 → **已過時**，現行格式為 `KIOSK:{kiosk_id}:TOKEN:{token}`
> 
> **請以以下文件為準：**
> - UX 流程：`05_product_and_business_flows/kiosk_v0_exchange/KIOSK_UX_AND_SCREEN_DESIGN.md`（v3.0.0，2026-05-11）
> - 業務流程：`05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md`（v2.2.0）
> - API 規格：`.kiro/specs/kiosk-exchange-v2-implementation/design.md`（v1.0.0）

---

> **版本**: 1.0.0
> **日期**: 2026-05-04
> **狀態**: ~~✅ 定案~~ ⚠️ 已廢棄
> **設計者**: HQ
> **適用系統**: Member (`win.tg25.win`)、iHub (`ihub.tg25.win`)

---

## 一、核心設計原則

> **手機是操作介面，平板是狀態顯示器。**

| 裝置 | 職責 | 說明 |
|------|------|------|
| 手機（win.tg25.win） | 所有操作 | 掃碼、查看餘額、結束兌換 |
| iHub 平板 | 純狀態顯示 | 不需要用戶操作，只顯示目前狀態 |

---

## 二、投幣不需要確認步驟

投幣本身就是確認動作。系統自動入帳，不需要用戶再點「確認」。

**理由：**
- 鈔票已進機器 = 用戶意圖明確
- 韌體已驗鈔確認為真鈔
- Fail-Safe 保護：5 秒內無裁決自動退鈔

---

## 三、Session 結束觸發規則（定案）

| 優先順序 | 觸發條件 | 動作 |
|---------|---------|------|
| 1 | 用戶按「結束兌換」 | 立即結束，機器立即轉紅 |
| 2 | 用戶掃了其他 QR Code（遊戲機、另一台兌幣機） | 立即結束舊 session |
| 3 | 最後一次入帳後 **2 分鐘**無新投幣 | 自動結束 |

**不做的事：**
- ❌ 不做心跳判斷離場（小明可能留著頁面去掃遊戲機）
- ❌ 不做 session 保留讓小明回來（排隊就好，重掃 3 秒）
- ❌ 不做 venue_session（統計從機台記錄分析即可）

---

## 四、阿財情境處理

小明離開兌幣機但 session 還 active 時，iHub 平板顯示：

```
┌─────────────────────────────────┐
│  ⚠ 此機台使用中                  │
│  請稍候或選擇其他操作             │
│                                 │
│  [繼續兌幣]    [回到步驟一]       │
└─────────────────────────────────┘
```

- 資訊已給，決策是用戶責任
- 阿財看到「使用中」還按「繼續兌幣」再投幣，是用戶行為問題，不是系統問題

---

## 五、手機會員頁面狀態機

### 狀態 A：掃碼前
- 顯示錢包餘額
- 「掃描兌幣機」按鈕
- 麵包屑：首頁 › 兌換代幣

### 狀態 B：等待投幣
- 頁面標題：「等待投幣」
- 機台狀態卡片：綠色背景，明顯顯示「就緒」
- 「請送入紙鈔」大字
- 支援面額：100 / 500 / 1000 元
- 「投入後自動入帳，無需確認」
- ⚠️ 請勿關閉此頁面（橘色警告）
- 「結束兌換」按鈕：紅色，明顯可見

### 狀態 C：入帳成功（每次投幣後）
- 頁面標題：「兌換中」
- `+100 代幣` 大字動畫（綠色）
- 本次累計 / 目前餘額 兩欄
- 倒數計時：大字顯示 + 橘色進度條（2 分鐘）
- 「結束兌換」按鈕：紅色

### 狀態 D：結算確認
- 頁面標題：「兌換完成」
- ✓ 圓圈動畫
- 結算表格：本次兌換、目前餘額、兌幣機、時間
- 「確認」按鈕（白色，主要按鈕）
- 10 秒後自動關閉

---

## 六、iHub 平板狀態機

### 狀態 1：待機
- QR Code（靜態）+ 掃描線動畫
- 「掃描開始兌換」
- 步驟提示：① 掃碼（亮）② 投幣（暗）③ 完成（暗）
- 說明：使用 win.tg25.win 掃描

### 狀態 2：綁定中（掃碼成功）
- 「會員已連線」綠色標籤
- 「歡迎，[姓名]」大字
- 紙鈔槽動畫
- 「請送入紙鈔」
- 面額提示：100 / 500 / 1000

### 狀態 3：入帳完成
- 「已入帳 XX 代幣 ✅」
- 「可繼續投幣」

### 狀態 4：使用中（有人走過來）
- ⚠ 「此機台使用中」
- 兩個按鈕：「繼續兌幣」（白色主要）/ 「回到步驟一」（次要）

### 狀態 5：結束
- 「感謝使用 👋」
- 3 秒後自動回到待機 QR Code

---

## 七、視覺規範

對齊現有 iHub 設計稿風格：

| 項目 | 規格 |
|------|------|
| 字體 | Space Grotesk（內文）、Barlow Condensed Italic（標題） |
| 主色 | `#7c3aed`（紫）|
| 成功色 | `#10b981`（綠）|
| 警告色 | `#f59e0b`（橘）|
| 危險色 | `#ef4444`（紅）|
| 背景 | `#080808` |
| 邊框 | `rgba(255,255,255,0.07)` |

---

## 八、設計稿參考

| 檔案 | 說明 |
|------|------|
| `HQ/ztemp/member-kiosk-mockup.html` | 手機 + iHub 完整視覺稿（7 個畫面） |
| `HQ/ztemp/kiosk_ux_flow.html` | 流程圖（狀態機 + session 結束規則） |
| `HQ/ztemp/ihub-kiosk.html` | iHub 現有稿件（風格參考） |
| Figma | https://www.figma.com/design/gLpPTuIL0OlW1NMDhfi4Xu |

---

## 九、實作任務

| # | 任務 | 負責 | 狀態 |
|---|------|------|------|
| 1 | Member 兌幣頁面按新 UX 設計更新 | Mina | ⏳ |
| 2 | iHub 平板畫面按新 UX 設計更新 | Hubie | ⏳ |

---

*設計者: HQ | 日期: 2026-05-04 | 版本: 1.0.0*

# 兌幣機 UX 設計規範

> **版本**: 1.0.0
> **日期**: 2026-05-04
> **狀態**: ✅ 定案
> **設計者**: HQ
> **適用系統**: Member (`win.tg25.win`)、iHub (`ihub.tg25.win`)

---

## 一、核心設計原則

> **手機是操作介面，平板是狀態顯示器。**

| 裝置 | 職責 | 說明 |
|------|------|------|
| 手機（win.tg25.win） | 所有操作 | 掃碼、查看餘額、結束兌換 |
| iHub 平板 | 純狀態顯示 | 不需要用戶操作，只顯示目前狀態 |

---

## 二、投幣不需要確認步驟

投幣本身就是確認動作。系統自動入帳，不需要用戶再點「確認」。

**理由：**
- 鈔票已進機器 = 用戶意圖明確
- 韌體已驗鈔確認為真鈔
- Fail-Safe 保護：5 秒內無裁決自動退鈔

---

## 三、Session 結束觸發規則（定案）

| 優先順序 | 觸發條件 | 動作 |
|---------|---------|------|
| 1 | 用戶按「結束兌換」 | 立即結束，機器立即轉紅 |
| 2 | 用戶掃了其他 QR Code（遊戲機、另一台兌幣機） | 立即結束舊 session |
| 3 | 最後一次入帳後 **2 分鐘**無新投幣 | 自動結束 |

**不做的事：**
- ❌ 不做心跳判斷離場（小明可能留著頁面去掃遊戲機）
- ❌ 不做 session 保留讓小明回來（排隊就好，重掃 3 秒）
- ❌ 不做 venue_session（統計從機台記錄分析即可）

---

## 四、阿財情境處理

小明離開兌幣機但 session 還 active 時，iHub 平板顯示：

```
┌─────────────────────────────────┐
│  ⚠ 此機台使用中                  │
│  請稍候或選擇其他操作             │
│                                 │
│  [繼續兌幣]    [回到步驟一]       │
└─────────────────────────────────┘
```

- 資訊已給，決策是用戶責任
- 阿財看到「使用中」還按「繼續兌幣」再投幣，是用戶行為問題，不是系統問題

---

## 五、手機會員頁面狀態機

### 狀態 A：掃碼前
- 顯示錢包餘額
- 「掃描兌幣機」按鈕
- 麵包屑：首頁 › 兌換代幣

### 狀態 B：等待投幣
- 頁面標題：「等待投幣」
- 機台狀態卡片：綠色背景，明顯顯示「就緒」
- 「請送入紙鈔」大字
- 支援面額：100 / 500 / 1000 元
- 「投入後自動入帳，無需確認」
- ⚠️ 請勿關閉此頁面（橘色警告）
- 「結束兌換」按鈕：紅色，明顯可見

### 狀態 C：入帳成功（每次投幣後）
- 頁面標題：「兌換中」
- `+100 代幣` 大字動畫（綠色）
- 本次累計 / 目前餘額 兩欄
- 倒數計時：大字顯示 + 橘色進度條（2 分鐘）
- 「結束兌換」按鈕：紅色

### 狀態 D：結算確認
- 頁面標題：「兌換完成」
- ✓ 圓圈動畫
- 結算表格：本次兌換、目前餘額、兌幣機、時間
- 「確認」按鈕（白色，主要按鈕）
- 10 秒後自動關閉

---

## 六、iHub 平板狀態機

### 狀態 1：待機
- QR Code（靜態）+ 掃描線動畫
- 「掃描開始兌換」
- 步驟提示：① 掃碼（亮）② 投幣（暗）③ 完成（暗）
- 說明：使用 win.tg25.win 掃描

### 狀態 2：綁定中（掃碼成功）
- 「會員已連線」綠色標籤
- 「歡迎，[姓名]」大字
- 紙鈔槽動畫
- 「請送入紙鈔」
- 面額提示：100 / 500 / 1000

### 狀態 3：入帳完成
- 「已入帳 XX 代幣 ✅」
- 「可繼續投幣」

### 狀態 4：使用中（有人走過來）
- ⚠ 「此機台使用中」
- 兩個按鈕：「繼續兌幣」（白色主要）/ 「回到步驟一」（次要）

### 狀態 5：結束
- 「感謝使用 👋」
- 3 秒後自動回到待機 QR Code

---

## 七、視覺規範

對齊現有 iHub 設計稿風格：

| 項目 | 規格 |
|------|------|
| 字體 | Space Grotesk（內文）、Barlow Condensed Italic（標題） |
| 主色 | `#7c3aed`（紫）|
| 成功色 | `#10b981`（綠）|
| 警告色 | `#f59e0b`（橘）|
| 危險色 | `#ef4444`（紅）|
| 背景 | `#080808` |
| 邊框 | `rgba(255,255,255,0.07)` |

---

## 八、設計稿參考

| 檔案 | 說明 |
|------|------|
| `HQ/ztemp/member-kiosk-mockup.html` | 手機 + iHub 完整視覺稿（7 個畫面） |
| `HQ/ztemp/kiosk_ux_flow.html` | 流程圖（狀態機 + session 結束規則） |
| `HQ/ztemp/ihub-kiosk.html` | iHub 現有稿件（風格參考） |
| Figma | https://www.figma.com/design/gLpPTuIL0OlW1NMDhfi4Xu |

---

## 九、實作任務

| # | 任務 | 負責 | 狀態 |
|---|------|------|------|
| 1 | Member 兌幣頁面按新 UX 設計更新 | Mina | ⏳ |
| 2 | iHub 平板畫面按新 UX 設計更新 | Hubie | ⏳ |

---

*設計者: HQ | 日期: 2026-05-04 | 版本: 1.0.0*


---

## 區塊二：Kiosk 三螢幕交互架構與顯示流程

# Kiosk 三端畫面 UX 流程（用戶體驗視角）

> **版本**: 5.1.0
> **日期**: 2026-05-11 (UTC+8)
> **來源**: 實際代碼查證（iHub/src/main.js、Member/resources/views/welcome.blade.php）
> **狀態**: ✅ 設計定稿

---

## 畫面清單總覽

### iHub 畫面

| 畫面 | stage | 說明 |
|------|-------|------|
| A | `stage-idle` | 待機 |
| B | `stage-qr_ready` | QR Code 顯示中 |
| C | `stage-active` | 等待投幣（會員已綁定） |
| D | escrow-modal（浮層） | Escrow 確認框（疊在 C 上） |
| C' | `stage-active`（escrow 消失後） | 處理中 |
| C'' | `stage-active`（toast 顯示中） | 入帳成功 toast |
| E | next-step-modal（浮層） | 選擇繼續或離開（疊在 C'' 上） |
| F | `stage-completed` | 結算 |

### Member 畫面

| 畫面 | currentView | 說明 |
|------|-------------|------|
| 1 | `dashboard` | 首頁 |
| 2 | `scanner` | 掃碼器 |
| 3a | `exchange` / waiting | 兌換中 — 等待投幣 |
| 3b | `exchange` / depositing | 兌換中 — 已入帳 |
| 3c | `exchange` / settling | 兌換完成結算 |
| 3d | escrow overlay（浮層） | 交易進行中（疊在 3a 或 3b 上） |
| 4 | `history` | 交易明細 |

### sim-bill 畫面

| 狀態 | ba_state | 燈號 |
|------|----------|------|
| R | `DISABLED` | 🔴 紅燈 |
| G | `IDLE` | 🟢 綠燈 |
| Y | `ESCROW` | 🟡 黃燈閃爍 |
| B | `STACKING` | 🔵 藍燈閃爍 |
| Y2 | `REJECTING` | 🟡 黃燈閃爍 |

---

## 按鈕清單與決策狀態

### iHub 按鈕

| 按鈕 | 所在畫面 | 功能 |
|------|---------|------|
| [取消並返回] | B | `resetToIdle()` 回畫面 A |
| [結束兌換] | C | `completeSession('ihub_force_ended')` → 畫面 F |
| [確認入鈔] | D | `confirmEscrow()` |
| [取消退鈔] | D | `rejectEscrow()` |
| [↩ 繼續兌換] | E | `continueExchange()` 回畫面 C |
| [離開] | E | `completeSession('ihub_manual')` → 畫面 F |
| [點擊提前返回] | F | `resetToIdle()` 回畫面 A |

### Member 按鈕

| 按鈕 | 所在畫面 | 功能 |
|------|---------|------|
| [掃碼 Scan to Play] | 1 | `openScanner()` → 畫面 2 |
| [✕ 關閉] | 2 | `closeScanner()` 回畫面 1 |
| [確認]（手動輸入） | 2 | `onScanSuccess()`（測試用） |
| [立即返回主頁] | 3c | `exitExchangeFlow()` 回畫面 1 |

---

## 核心設計原則

**所有金流裁決動作必須在 iHub 平板上操作，不可在手機上。**

理由：手機不在機台旁邊。若允許手機確認，會發生：
1. 上一個客人沒按結束就離開
2. 下一個客人走到機台前投幣
3. 上一個客人的手機收到確認請求
4. 上一個客人在遠端確認 → 錢入帳給上一個人

因此：
- ✅ **iHub 平板**：確認入鈔、取消入鈔、繼續兌換、離開（唯一裁決方）
- ✅ **Member 手機**：純顯示狀態，無裁決按鈕
- ✅ **sim-bill**：模擬紙鈔機物理動作

---

## 三端角色定義

| 端 | 位置 | 操作者 | 職責 |
|----|------|--------|------|
| **iHub** | 固定在機台旁 | 在場的人（客人或工作人員） | 所有裁決動作 |
| **sim-bill** | 固定在機台旁 | 模擬紙鈔機 | 顯示燈號、模擬投幣 |
| **Member 手機** | 客人手上 | 客人 | 掃碼綁定、查看狀態、查看餘額 |

---

## st1. 機台空閒待機

| 端 | 畫面 |
|----|------|
| **iHub** | 「點擊開始兌幣」待機畫面 |
| **Member** | 首頁，掃碼器入口 / 兌換紀錄 |
| **sim-bill** | 🔴 紅燈（DISABLED），投幣按鈕禁用 |

---

## st1.1. iHub 點擊「開始兌幣」

| 端 | 畫面 |
|----|------|
| **iHub** | 顯示 QR Code + 5 分鐘倒數 |
| **Member** | 不變（首頁，等待掃碼） |
| **sim-bill** | 不變（🔴 紅燈） |

> 5 分鐘內未掃碼 → iHub 自動回 st1

---

## st2. 手機掃碼綁定成功

> 會員用手機掃描 iHub 上的 QR Code。

| 端 | 畫面 | 觸發 |
|----|------|------|
| **iHub** | 切換畫面 C：顯示會員卡（姓名、餘額）、「請投入鈔票」、Awaiting Deposit...；底部 [結束兌換] enabled；5 分鐘 idle timer 啟動 | `.MemberBoundToKiosk` |
| **Member** | 切換畫面 3a（waiting）：「等待投幣」、面額標籤 100/500/1000、頂部警告條 | 掃碼 API 成功後 |
| **sim-bill** | 🟢 綠燈（IDLE），[100] [500] [1000] 按鈕 enabled | MQTT `enable` → SSE |

---

## st3. 送入紙鈔（sim-bill 點擊 [100]）

| 端 | 畫面 | 觸發 |
|----|------|------|
| **iHub** | 彈出 escrow modal：「入帳確認中」、會員姓名、手機末4碼、投入金額 $100、獲得代幣 100 Tokens、[確認入鈔] [取消退鈔]、底部計時條 15s | `.KioskEscrowPending` |
| **Member** | escrow overlay 蓋上：⏳ 旋轉動畫、「交易進行中...」、倒數 15s（無確認/拒絕按鈕） | `.KioskEscrowPending` |
| **sim-bill** | 🟡 黃燈閃爍（ESCROW），投幣按鈕 disabled | iHub Server 自動發 |

---

## st3.1. 確認入鈔（按下「確認入鈔」瞬間）

| 端 | 畫面 |
|----|------|
| **iHub** | escrow modal 消失；「請投入鈔票」和「Awaiting Deposit...」隱藏；顯示「⏳ 處理中，請稍候...」（黃色）；底部 [結束兌換] disabled |
| **Member** | escrow overlay 消失；底層畫面不變（waiting 或 depositing） |
| **sim-bill** | 不變（🟡 黃燈閃爍 ESCROW） |

---

## st3.1.1. 收到入帳成功通知（`.KioskSessionUpdated`，約 1-3 秒後）

| 端 | 畫面 | 觸發 |
|----|------|------|
| **iHub** | 「處理中」切換為「✅ +100 代幣，餘額 XXX」（綠色 toast）；會員卡餘額更新；粒子噴發動畫 | `.KioskSessionUpdated` |
| **Member** | 飛入動畫「+100」；切換畫面 3b（depositing）：「本次累計 100 代幣」、60 秒倒數重置、餘額更新 | `.KioskSessionUpdated` |
| **sim-bill** | 🔵 藍燈（STACKING）→ 500ms → 🟢 綠燈（STACKED）→ 1.5s → **� 紅燈（DISABLED）**，錢盒 +100。**STACKED 完成後必須進入 DISABLED，投幣按鈕 disabled，等待 iHub 操作** | SSE `stack` |

> **設計原則**：每張鈔票 STACKED 後，sim-bill 必須先回到 🔴 紅燈（DISABLED），讓用戶在 iHub 選擇「繼續兌換」或「離開」。按下 [↩ 繼續兌換] 後，iHub 發送 MQTT `enable` 指令，sim-bill 才變回 🟢 綠燈（IDLE）。

---

## st3.1.2. 3 秒後 toast 消失，彈出選擇 modal

| 端 | 畫面 |
|----|------|
| **iHub** | toast 隱藏；「請投入鈔票」和「Awaiting...」繼續隱藏（不恢復）；彈出 next-step-modal：✓ 綠圈、「入帳成功！」、「已獲得 100 代幣，帳戶餘額 XXX 代幣」、[↩ 繼續兌換] [離開] |
| **Member** | 不變（depositing 狀態，60 秒倒數繼續跑） |
| **sim-bill** | � 紅燈（DISABLED），投幣按鈕 disabled，等待 iHub 操作 |

---

## st3.1.2a. 繼續兌換（按「繼續兌換」）

| 端 | 畫面 |
|----|------|
| **iHub** | modal 消失；「請投入鈔票」和「Awaiting Deposit...」恢復顯示；[結束兌換] 按鈕 enabled；idle timer 重置；發送 MQTT `enable` 指令 |
| **Member** | 不變（depositing 狀態，60 秒倒數繼續跑） |
| **sim-bill** | 收到 MQTT `enable` → 🟢 綠燈（IDLE），投幣按鈕 enabled，等待下一張 |

> 回到 st3（等待下一張投幣）

---

## st3.1.2b. 離開（按「離開」）

> iHub 呼叫 `completeSession('ihub_manual')`，等待 `.KioskSessionEnded`

| 端 | 畫面 | 觸發 |
|----|------|------|
| **iHub** | modal 直接消失；等待 `.KioskSessionEnded`；切換畫面 F（stage-completed）：「兌換完成」、「本次成功兌換 N 枚代幣」、「系統將於 8 秒後自動返回」 | `.KioskSessionEnded` |
| **Member** | 切換畫面 3c（settling）：「兌換完成」、「本次兌換 N 代幣」、「目前餘額 N 代幣」、「X 秒後自動返回」、[立即返回主頁] | `.KioskSessionEnded` |
| **sim-bill** | 收到 MQTT `disable` → 🔴 紅燈（DISABLED），投幣按鈕 disabled | SSE `disable` |

> 8 秒後回 st1

---

## st3.1.x. 入帳失敗（後端錯誤）

| 端 | 畫面 |
|----|------|
| **iHub** | 「處理中」切換為「❌ 交易失敗，請洽客服櫃檯」（紅色） |
| **Member** | 顯示「交易失敗，請洽客服櫃檯」 |
| **sim-bill** | 維持 🟢 綠燈（IDLE）（鈔票已入盒，需人工對帳） |

---

## st3.2. 取消入鈔（按「取消退鈔」）

> 取消入鈔只是「這張不要」，session 繼續有效，可繼續投幣。

| 端 | 畫面 | 觸發 |
|----|------|------|
| **iHub** | escrow modal 消失；顯示「↩ 退鈔中...」（灰色，1 秒後隱藏）；「請投入鈔票」和「Awaiting...」維持顯示；底部按鈕 enabled | 按下後立即 |
| **Member** | escrow overlay 消失；底層畫面不變（waiting 或 depositing） | overlay 關閉 |
| **sim-bill** | 🟡 黃燈閃爍（REJECTING）→ 🟢 綠燈（IDLE），退鈔動畫，投幣按鈕 enabled | SSE `reject` |

> 回到 st3（session 保留，可繼續投幣）

---

## st3.x. Escrow 15 秒超時（無人確認）

> 超時只是「這張來不及確認」，session 繼續有效，可繼續投幣。

| 端 | 畫面 |
|----|------|
| **iHub** | escrow modal 消失（倒數到 0）；顯示「⏱ 確認超時，鈔票已自動退回」（橘色，3 秒後隱藏）；「請投入鈔票」和「Awaiting...」維持顯示；[結束兌換] 按鈕 enabled |
| **Member** | escrow overlay 消失（倒數到 0 自動關閉）；底層畫面不變（waiting 或 depositing） |
| **sim-bill** | 韌體 Fail-Safe 自動退鈔：ESCROW → 🟡 REJECTING → 🟢 IDLE，投幣按鈕 enabled |

> 回到 st3（session 保留，可繼續投幣）

---

## st4. 結束兌換

### st4.0. iHub 按「結束兌換」（畫面 C 底部按鈕）

> iHub 呼叫 `completeSession('ihub_force_ended')`，等待 `.KioskSessionEnded`

| 端 | 畫面 | 觸發 |
|----|------|------|
| **iHub** | 切換畫面 F（stage-completed）：「兌換完成」、「本次成功兌換 N 枚代幣」、「系統將於 8 秒後自動返回」 | `.KioskSessionEnded` |
| **Member** | 切換畫面 3c（settling）：「兌換完成」、「本次兌換 N 代幣」、「目前餘額 N 代幣」、「X 秒後自動返回」、[立即返回主頁] | `.KioskSessionEnded` |
| **sim-bill** | 🔴 紅燈（DISABLED），投幣按鈕 disabled | SSE `disable` |

> 8 秒後回 st1

### st4.1. iHub 5 分鐘 idle timer 到期

> iHub 自動呼叫 `completeSession('ihub_timeout')`

| 端 | 畫面 | 觸發 |
|----|------|------|
| **iHub** | 切換 stage-completed：「兌換完成」、「本次成功兌換 N 枚代幣」、「系統將於 8 秒後自動返回」 | `.KioskSessionEnded` |
| **Member** | exchangeState → settling：「兌換完成」、「本次兌換 N 代幣」、「X 秒後自動返回」 | `.KioskSessionEnded` |
| **sim-bill** | 🔴 紅燈（DISABLED），投幣按鈕 disabled | SSE `disable` |

> 8 秒後回 st1

### st4.2. Member 60 秒倒數到 0 自動結算

> Member 前端倒數到 0，自動呼叫 `finishExchange('timeout')`，後端結束 session，廣播 `.KioskSessionEnded`

| 端 | 畫面 | 觸發 |
|----|------|------|
| **iHub** | 切換畫面 F（stage-completed）：「兌換完成」、「本次成功兌換 N 枚代幣」、「系統將於 8 秒後自動返回」 | `.KioskSessionEnded` |
| **Member** | 倒數到 0 → 自動切換畫面 3c（settling）：「兌換完成」、「本次兌換 N 代幣」、「X 秒後自動返回」 | 倒數到 0 |
| **sim-bill** | 🔴 紅燈（DISABLED），投幣按鈕 disabled | SSE `disable` |

> 8 秒後回 st1

### st4.x. MQTT 斷線

| 端 | 畫面 |
|----|------|
| **iHub** | 顯示連線錯誤提示 |
| **Member** | 維持當前畫面，等待重連 |
| **sim-bill** | 🔴 紅燈（DISABLED，斷線 Fail-Safe） |

---

## 狀態轉換總覽

```
st1（待機）
  │ iHub 點擊「開始兌幣」
  ▼
st1.1（QR Code 顯示中，5 分鐘倒數）
  │ Member 掃碼成功
  ▼
st2（綁定完成，等待投幣）
  iHub: 畫面 C | sim-bill: 🟢 | Member: 畫面 3a
  │
  ├─ iHub 按「結束兌換」（st4.0）──▶ st4 → st1
  │
  │ sim-bill 點擊金額
  ▼
st3（Escrow 暫存，15 秒倒數）
  iHub: 畫面 D | sim-bill: 🟡 | Member: 畫面 3d
  │
  ├─ 確認入鈔 ──▶ st3.1（畫面 C'，處理中）
  │                 ▼ .KioskSessionUpdated
  │              st3.1.1（畫面 C''，入帳成功 toast）
  │                 ▼ 3 秒後
  │              st3.1.2（畫面 E，next-step-modal；sim-bill 🔴 紅燈）
  │                 ├─ 繼續兌換（st3.1.2a）──▶ iHub 發 MQTT enable → sim-bill 🟢 → 回到 st2
  │                 └─ 離開（st3.1.2b）──▶ st4 → st1
  │
  ├─ 取消退鈔（st3.2）──▶ 回到 st2（session 保留）
  │
  └─ 15s 超時（st3.x）──▶ 回到 st2（session 保留）

st4（結束）
  st4.0 iHub 按「結束兌換」──▶ 畫面 F → st1
  st4.1 iHub idle timer 到期 ──▶ 畫面 F → st1
  st4.2 Member 60s 倒數到 0 ──▶ 畫面 F → st1
  st4.x MQTT 斷線
```

---

## 關鍵技術對照

| 動作 | 訊號 | 發送方 |
|------|------|--------|
| 掃碼成功 → 綠燈 | MQTT `kiosk/{chip_id}/cmd {"action":"enable"}` | Member |
| 投幣 → Escrow | MQTT `kiosk/{chip_id}/event {"event_type":"escrow","amount":100}` | sim-bill（透過 iHub Server proxy） |
| **確認入鈔** | `POST api.tg25.win/api/kiosk/escrow/confirm {"kiosk_id":"..."}` | **iHub（唯一裁決方）** |
| **取消入鈔** | `POST api.tg25.win/api/kiosk/escrow/reject {"kiosk_id":"..."}` | **iHub（唯一裁決方）** |
| **繼續兌換 → 綠燈** | `POST ihub.tg25.win/api/simulator/command {"action":"enable"}` → MQTT enable | **iHub `continueExchange()`** |
| **結束 session** | `POST api.tg25.win/api/kiosk/session/{session_id}/end {"reason":"ihub_manual"\|"ihub_force_ended"\|"ihub_timeout"}` → Infra bridge → `win.tg25.win/api/kiosk/session/{id}/end` | **iHub `completeSession()`** |
| 入帳完成通知 | WebSocket `.KioskSessionUpdated` on `kiosk.{node_id}` | Member |
| Session 結束通知 | WebSocket `.KioskSessionEnded` on `kiosk.{node_id}` | Member |
| 結束 → 紅燈 | MQTT `kiosk/{chip_id}/cmd {"action":"disable"}` | Member |

---

## 待實作項目（Hubie）

> 代碼位置：`iHub/src/main.js`

| # | 類型 | 位置 | 要改什麼 |
|---|------|------|---------|
| 1 | 移除 HTML | `stage-active` | 移除 `id="complete-btn"` 和 `id="force-end-btn"`，新增 `id="end-btn"`（[結束兌換]） |
| 2 | 改 JS | `bindEvents()` | 移除 `complete-btn` 和 `force-end-btn` 的 click listener，改為 `end-btn` → `completeSession('ihub_force_ended')` |
| 3 | 改 JS | `setCompleteBtnsLoading()` | 改為操作 `end-btn`，移除對 `complete-btn` 和 `force-end-btn` 的引用 |
| 4 | 改 JS | `updateMemberUI()` | 移除 `force-end-btn` 的 textContent 更新（死代碼） |
| 5 | 改 JS | `confirmEscrow()` | `$('complete-btn')?.setAttribute('disabled', true)` 和 `$('force-end-btn')` 改為 `$('end-btn')` |
| 6 | 改 JS | `continueExchange()` | `$('complete-btn')?.removeAttribute('disabled')` 和 `$('force-end-btn')` 改為 `$('end-btn')` |
| 7 | 改 JS | `confirmEscrow()` 按下後 | 隱藏 `.deposit-title` 和 `.deposit-status` |
| 8 | 改 JS | `hideDepositFeedback()` 後 | 不恢復 `.deposit-title` 和 `.deposit-status`（繼續隱藏） |
| 9 | 改 JS | `continueExchange()` 按下後 | 恢復顯示 `.deposit-title` 和 `.deposit-status` |
| 10 | 改 JS | `resetToIdle()` | 完整重置 stage-active 的所有 UI 狀態（恢復 `.deposit-title`、`.deposit-status`、清空 feedback、重置按鈕、關閉 modal），確保第二輪掃碼後畫面正常 |

**不動的部分**：
- `.KioskSessionUpdated` 監聽邏輯
- `memberBalance`/`tokensThisRound` 更新
- `triggerBurst` 動畫
- `completeSession` 函數本體
- `rejectEscrow` 邏輯
- `next-step-modal` HTML 和樣式
- `stage-completed` 畫面
- `setupEngineeringWhisper` 邏輯
- `startIdleTimer` / `resetIdleTimer` 邏輯

---

## 待實作項目（Mina）

> 代碼位置：`Member/resources/views/welcome.blade.php`

| # | 類型 | 位置 | 要改什麼 |
|---|------|------|---------|
| 1 | 移除 HTML | 畫面 3a（waiting） | 移除 `[結束兌換]` 按鈕（`@click="finishExchange('manual')"`） |
| 2 | 移除 HTML | 畫面 3b（depositing） | 移除 `[繼續投幣（重置倒數）]` 按鈕（`@click="extendExchange"`）和 `[結束兌換]` 按鈕 |
| 3 | 清理 JS | `extendExchange()` | 函數可移除（按鈕移除後為死代碼，倒數已由 `.KioskSessionUpdated` 自動重置） |

**不動的部分**：
- `finishExchange()` 函數本體（仍被 60s 倒數到 0 的 `timeout` 路徑呼叫）
- `handleBeforeUnload`（瀏覽器關閉時的 best-effort 清理，合理保留）
- `startExchangeCountdown()` 邏輯
- `cleanupExchangeResources()` 邏輯
- `setupKioskEcho()` 邏輯
- `startEscrowCountdown()` 邏輯
- `showEscrowConfirm` overlay 顯示邏輯
- `exitExchangeFlow()` 邏輯

---

## 畫面詳細規格

### iHub 畫面

#### 畫面 A：待機（stage-idle）
- 文字：「點擊螢幕 開始兌幣」、「掃碼後投入鈔票，即可自動完成兌換」
- 操作：點擊畫面任意處 → 畫面 B

#### 畫面 B：QR Code（stage-qr_ready）
- 文字：「STEP 1 · 掃碼配對帳號」、QR Code、「有效時間 300s」、「請掃描上方 QR Code」、「使用 WAW APP 掃描，連結會員帳號」
- 按鈕：[取消並返回] → 畫面 A
- 計時：5 分鐘未掃碼 → 自動回畫面 A

#### 畫面 C：等待投幣（stage-active）
- 會員卡：頭像、姓名、#ID、末 4 碼、Account Balance N Tokens
- 投幣區：bill-slot 圖示、「請投入鈔票」（`.deposit-title`）、● Awaiting Deposit...（`.deposit-status`）
- 底部：[結束兌換] → 畫面 F（`completeSession('ihub_force_ended')`）
- 浮層：畫面 D（escrow modal）疊在上面

#### 畫面 D：Escrow 確認框（escrow-modal，浮在畫面 C 上）
- 文字：「入帳確認中」、會員姓名、手機末 4 碼、投入金額、獲得代幣、計時條 15s
- 按鈕：[確認入鈔] → 畫面 C'　｜　[取消退鈔] → 畫面 C（退鈔）

#### 畫面 C'：處理中（stage-active，escrow 消失後）
- 同畫面 C，但「請投入鈔票」和「Awaiting...」隱藏
- deposit-feedback 顯示：「⏳ 處理中，請稍候...」
- 底部兩個按鈕 disabled

#### 畫面 C''：入帳成功 toast（stage-active，3 秒）
- 同畫面 C'，但 deposit-feedback 切換為「✅ +100 代幣，餘額 XXX」
- 粒子噴發動畫
- 浮層：畫面 E（next-step-modal）疊在上面



#### 畫面 F：結算（stage-completed）
- 文字：✓ 圓圈、「兌換完成」、「本次成功兌換 N 枚代幣」、「系統將於 8 秒後自動返回」
- 按鈕：[點擊提前返回] → 畫面 A
- 計時：8 秒後自動回畫面 A

---

### Member 畫面

#### 畫面 1：首頁 Dashboard（currentView = 'dashboard'）
- 餘額卡、近期交易紀錄
- FAB 按鈕：[掃碼 Scan to Play] → 畫面 2
- 右上角：[登出]

#### 畫面 2：掃碼器（currentView = 'scanner'）
- 相機畫面、「掃描機台 QR Code」
- 按鈕：[✕ 關閉] → 畫面 1
- 手動輸入 chip_id + [確認]（測試用）

#### 畫面 3a：兌換中 — 等待投幣（currentView = 'exchange'，waiting）
- 頂部警告條：「⚠️ 請勿離開頁面」
- 機台狀態卡：kiosk_id、「就緒」、「1:1」
- 掃描線動畫、「等待投幣」、面額標籤 100/500/1000
- 無操作按鈕（純顯示，等待 iHub 操作）
- 浮層：畫面 3d（escrow overlay）

#### 畫面 3b：兌換中 — 已入帳（currentView = 'exchange'，depositing）
- 頂部警告條：「⚠️ 請勿離開頁面」
- 飛入動畫「+N」、「本次累計 N 代幣」、60 秒倒數（自動重置，無需按鈕）、目前餘額
- 無操作按鈕（純顯示，等待 iHub 操作或倒數到 0 自動結算）
- 浮層：畫面 3d（escrow overlay）

#### 畫面 3c：兌換完成結算（currentView = 'exchange'，settling）
- ✓ 綠圈、「兌換完成」、「本次兌換 N 代幣」、「目前餘額 N 代幣」、「X 秒後自動返回」
- 按鈕：[立即返回主頁] → 畫面 1

#### 畫面 3d：Escrow overlay（浮在 3a 或 3b 上）
- ⏳ 旋轉動畫、「交易進行中...」、倒數 15s
- 無按鈕（純顯示，iHub 才是裁決方）

#### 畫面 4：交易明細（currentView = 'history'）
- 交易列表
- 按鈕：[← 返回] → 畫面 1

---

### sim-bill 畫面

#### 狀態 R：DISABLED（🔴 紅燈）
- 投幣按鈕 disabled

#### 狀態 G：IDLE（🟢 綠燈）
- [100] [500] [1000] 按鈕 enabled

#### 狀態 Y：ESCROW（🟡 黃燈閃爍）
- 投幣按鈕 disabled、倒數計時

#### 狀態 B：STACKING（🔵 藍燈閃爍）
- 投幣按鈕 disabled

#### 狀態 Y2：REJECTING（🟡 黃燈閃爍）
- 投幣按鈕 disabled、退鈔動畫

---

*設計者：HQ | 日期：2026-05-11 (UTC+8) | 版本：5.0.0*
*來源：iHub/src/main.js、Member/resources/views/welcome.blade.php 實際代碼查證*


---

## 區塊三：Kiosk 顯示界面 UI 細節規範

# Kiosk 三端 UI 完整規格

> **版本**: 1.0.0
> **日期**: 2026-05-11 (UTC+8)
> **用途**: 發任務給 Hubie / Mina 的完整 UI 規格，每一動三端都交代清楚
> **原則**: 不變的說「不變」，要變的說清楚變成什麼

---

## st1. 掃碼成功，等待投幣

```
[iHub]
  會員卡：頭像 | 姓名 | #ID | 末4碼 | Account Balance: N Tokens
  投幣區：
    [bill-slot 圖示]
    「請投入鈔票」（h3）
    ● Awaiting Deposit...（綠點閃爍）
  底部：[確認完成兌換] [✕ 結束]（enabled）
  進度條：5 分鐘 idle timer 跑動

[Member]
  exchangeState = 'waiting'
  畫面：綠色掃描線動畫
  標題：「等待投幣」
  面額標籤：100 / 500 / 1000（灰色）
  按鈕：[結束兌換]（紅色）

[sim-bill]
  🟢 綠燈（IDLE）
  投幣按鈕：[100] [500] [1000]（enabled）
```

---

## st2. 投幣後 Escrow（sim-bill 點擊 [100]）

```
[iHub]
  背景：stage-active 不變（會員卡 + 投幣區）
  彈出 escrow-modal（黑色遮罩）：
    ! 圖示
    「入帳確認中」
    會員姓名：XXX
    手機號碼：末4碼
    投入金額：$100
    獲得代幣：100 Tokens
    [確認入帳] [取消退鈔]（enabled）
    底部計時條：15 秒倒數

[Member]
  showEscrowConfirm = true → overlay 蓋上
  overlay 內容：
    ⏳ 旋轉動畫
    「交易進行中...」
    倒數：15s
  底層畫面：不變（waiting 或 depositing 狀態）
  ⚠️ 無確認/拒絕按鈕（已移除）

[sim-bill]
  🟡 黃燈閃爍（ESCROW）
  投幣按鈕：disabled
  顯示：「暫存中 15s 倒數」
```

---

## st3.1. 按下「確認入鈔」（0ms）

```
[iHub]
  escrow-modal 消失
  stage-active 畫面：
    會員卡：不變
    投幣區：
      「請投入鈔票」 → ❌ 隱藏
      ● Awaiting Deposit... → ❌ 隱藏
      deposit-feedback 顯示：「⏳ 處理中，請稍候...」（黃色）
  底部：[確認完成兌換] [✕ 結束] → disabled

[Member]
  showEscrowConfirm = false → overlay 消失
  exchangeState 不變（waiting 或 depositing）
  畫面：不變

[sim-bill]
  不變（ESCROW 黃燈閃爍）
```

---

## st3.1. 收到 `.KioskSessionUpdated`（入帳成功，約 1-3 秒後）

```
[iHub]
  投幣區：
    「請投入鈔票」 → 繼續隱藏
    ● Awaiting... → 繼續隱藏
    deposit-feedback 切換：「✅ +100 代幣，餘額 XXX」（綠色）
  會員卡：balance 數字更新為新餘額
  粒子噴發動畫（triggerBurst）觸發
  底部按鈕：繼續 disabled（等 modal 出現）

[Member]
  exchangeState → 'depositing'（若原本是 waiting）
  飛入動畫：「+100」
  畫面切換為 depositing 狀態：
    「+100 代幣」（本次累計）
    60 秒倒數重置
    目前餘額更新
  按鈕：[繼續投幣（重置倒數）] [結束兌換]

[sim-bill]
  🔵 藍燈閃爍（STACKING）→ 🟢 綠燈（IDLE）
  投幣按鈕：enabled
```

---

## st3.1. 3 秒後 toast 消失，next-step-modal 彈出

```
[iHub]
  deposit-feedback 隱藏
  「請投入鈔票」 → 繼續隱藏（不恢復）
  ● Awaiting... → 繼續隱藏（不恢復）
  彈出 next-step-modal（黑色遮罩）：
    ✓ 綠色圓圈
    「入帳成功！」（綠色標題）
    「已獲得 100 代幣，帳戶餘額 XXX 代幣」（灰色副標）
    [↩ 繼續兌換]（綠色）[離開]（灰色）

[Member]
  不變（depositing 狀態，60 秒倒數繼續跑）

[sim-bill]
  不變（🟢 綠燈 IDLE，等待下一張）
```

---

## st3.1.1. 按「繼續兌換」

```
[iHub]
  next-step-modal 消失
  投幣區恢復：
    「請投入鈔票」 → ✅ 恢復顯示
    ● Awaiting Deposit... → ✅ 恢復顯示
    deposit-feedback → 隱藏
  底部按鈕：[確認完成兌換] [✕ 結束] → enabled
  idle timer 重置（5 分鐘重新計算）

[Member]
  不變（depositing 狀態，60 秒倒數繼續跑）

[sim-bill]
  不變（🟢 綠燈 IDLE，等待下一張）
```

> 回到 st2（等待下一張投幣）

---

## st3.1.2. 按「離開」

```
[iHub]
  next-step-modal 消失
  呼叫 completeSession('ihub_manual')
  等待 .KioskSessionEnded 事件
  → setState('completed')：
    ✓ 圓圈動畫
    「兌換完成」
    「本次成功兌換 N 枚代幣」
    「系統將於 8 秒後自動返回」
    [點擊提前返回]

[Member]
  收到 .KioskSessionEnded
  exchangeState → 'settling'
  畫面：
    ✓ 綠色圓圈
    「兌換完成」
    「本次兌換 N 代幣」
    「目前餘額 N 代幣」
    「X 秒後自動返回」
    [立即返回主頁]

[sim-bill]
  收到 SSE disable
  🔴 紅燈（DISABLED）
  投幣按鈕：disabled
```

> 8 秒後回 st1（iHub 回待機，Member 回首頁）

---

## st3.2. 按「取消退鈔」

```
[iHub]
  escrow-modal 消失
  投幣區：
    「請投入鈔票」 → ✅ 恢復顯示（或維持顯示，未被隱藏）
    ● Awaiting Deposit... → ✅ 恢復顯示
    deposit-feedback 顯示：「↩ 退鈔中...」（灰色，1 秒後隱藏）
  底部按鈕：enabled

[Member]
  showEscrowConfirm = false → overlay 消失
  exchangeState 不變
  畫面：回到 waiting 或 depositing 狀態（不變）

[sim-bill]
  🟡 黃燈閃爍（REJECTING）→ 🟢 綠燈（IDLE）
  退鈔動畫
  投幣按鈕：enabled
```

> 回到 st2（session 保留，可繼續投幣）

---

## st3.x. Escrow 15 秒超時（無人確認）

```
[iHub]
  escrow-modal 消失（倒數到 0）
  投幣區：
    「請投入鈔票」 → ✅ 顯示
    ● Awaiting Deposit... → ✅ 顯示
    deposit-feedback 顯示：「⏱ 確認超時，鈔票將自動退回」（橘色，3 秒後隱藏）
  底部按鈕：enabled

[Member]
  showEscrowConfirm = false（倒數到 0 自動關閉）
  exchangeState 不變
  畫面：不變

[sim-bill]
  韌體 Fail-Safe 自動退鈔
  ESCROW → REJECTING（🟡 黃燈閃爍）→ IDLE（🟢 綠燈）
  投幣按鈕：enabled
```

> 回到 st2（session 保留，可繼續投幣）

---

## st4.1. iHub 5 分鐘 idle timer 到期

```
[iHub]
  自動呼叫 completeSession('ihub_timeout')
  → setState('completed')：
    「兌換完成」
    「本次成功兌換 N 枚代幣」
    「系統將於 8 秒後自動返回」

[Member]
  收到 .KioskSessionEnded
  exchangeState → 'settling'
  「兌換完成」「本次兌換 N 代幣」「X 秒後自動返回」

[sim-bill]
  收到 SSE disable
  🔴 紅燈（DISABLED）
  投幣按鈕：disabled
```

---

## st4.2. Member 60 秒無操作自動結算

```
[iHub]
  收到 .KioskSessionEnded
  → setState('completed')：
    「兌換完成」「本次成功兌換 N 枚代幣」「系統將於 8 秒後自動返回」

[Member]
  60 秒倒數到 0 → 自動呼叫 finishExchange('timeout')
  exchangeState → 'settling'
  「兌換完成」「本次兌換 N 代幣」「X 秒後自動返回」

[sim-bill]
  收到 SSE disable
  🔴 紅燈（DISABLED）
  投幣按鈕：disabled
```

---

## 需要修改的清單

### Hubie（iHub）需改的地方

| # | 時機 | 要改什麼 |
|---|------|---------|
| 1 | `confirmEscrow()` 按下後 | 隱藏 `.deposit-title`（「請投入鈔票」）和 `.deposit-status`（Awaiting...） |
| 2 | `confirmEscrow()` 按下後 | 底部 `complete-btn` 和 `force-end-btn` → disabled |
| 3 | `hideDepositFeedback()` 後 | 不要恢復 `.deposit-title` 和 `.deposit-status`（讓它們繼續隱藏） |
| 4 | `continueExchange()` 按下後 | 恢復顯示 `.deposit-title` 和 `.deposit-status` |
| 5 | `continueExchange()` 按下後 | 底部兩個按鈕 → enabled |

### 不動的地方（確認不要碰）

- `.KioskSessionUpdated` 監聽邏輯
- `memberBalance`、`tokensThisRound` 更新
- `triggerBurst` 動畫
- `completeSession` 函數
- `rejectEscrow` 邏輯（取消退鈔流程已正常）
- `next-step-modal` 的 HTML 和樣式
- `stage-completed` 的畫面

### Mina（Member）

✅ 已完成（Escrow 確認/拒絕按鈕已移除，commit 8487d2b）
無需再改。

---

*制定者：HQ | 日期：2026-05-11 (UTC+8) | 版本：1.0.0*


---

## 🔗 文件神經連結

### 強關聯（必讀）
- `brains/knowledge/05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` - 兌幣機物理與金流交互流程。
- `brains/knowledge/02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - 技術命名與 Payload 數據負載標準規範。
