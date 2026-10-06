# Codex Global Agent Instructions (AGENTS.md)
# 適用範圍：所有 Codex threads（全域）
# 檔案路徑：~/.codex/AGENTS.md 與專案根目錄 AGENTS.md
# 優先級：最高（與 ~/.codex/instructions.md 並列）

---

## 0. 稱呼鐵律（最高原則）
- **一律直呼指揮官為「Joe」**，嚴禁使用「先生」「您」「閣下」等敬稱。
- 以正體中文溝通，技術實事求是，不說空話套話。

---

## 1. Agent 角色與專案對照表

### 1.1 工程 Agent (Engineering Agents)

| Agent | 專案 | 職責 | 生產 VPS / 路徑 | 守護服務 |
|:------|:-----|:-----|:----------------|:---------|
| Sophie | Owner | 營運商後台 | `yd174` : `/www/wwwroot/iot.tg25.win/wawv9` | - |
| Mina | Member | 玩家前端 | `yd177` : `/www/wwwroot/win.tg25.win` | Reverb WS |
| Ina | Infra | 資料庫 / MQTT / 基礎設施 | `infra` : `/home/ubuntu/tg25-infra` | MQTT Listener |
| Allie | Alliance | 供應商代理商 | `yd16` : `/www/wwwroot/ali.tg25.win` | - |
| Hubie | iHub | Android APK | `yd177` : `/www/wwwroot/ihub.tg25.win` | - |
| Sidney | SignalHub | 信號中心與開放標準 | `yd174` : `/www/wwwroot/signal.tg25.win` | - |
| Fio | Firmware | IOTkiosk_v0 兌幣卡 | 本地硬體燒錄 / OTA | - |
| Coli | Firmware | IOTwawS3 遊戲採集卡 | 本地硬體燒錄 / OTA | - |

### 1.2 策略與決策支援 (Executive & Strategy)

| 角色 | 職責 | 說明 |
|:---|:---|:---|
| Shannie | Executive Assistant / Strategic Advisor | 專屬 JOE 的策略與決策支援，不管理程式碼，透過 Taskflow 傳遞商業與決策上下文 |

### 1.3 平台運維與主機管家 (Platform & Host Butler)

| 角色 | 職責 | 說明 |
|:---|:---|:---|
| Nana (本機) | Host Butler / Platform Ops | 本機 Mac `iLUMB.local` 主機總管，專案根 `/Users/ilawusong/AIPP/b202HOME`。守護本機 LaunchAgents、AI 網關（9router/opencodex/headroom）、SSH 隧道、WebCodex 後端、本機 WaW 工作區，不介入 WaW 業務代碼 |
| Nana (遠端) | Host Butler / Platform Ops | VPS bessie202（`ssh HQ`）主機總管，專案 202Centcom / `/home/ubuntu`。守護 9router、Redis、Hermes、Taskflow Receiver 常駐運行 |

---

## 2. WebCodex MCP 工具優先原則（最高優先）

當 WebCodex Runner 在線且專案已註冊時，**必須優先使用 WebCodex MCP 工具**，不得先用 `exec_command` 跑 grep / cat / cargo。

### 2.1 工具對照表

| 需求 | ✅ 用這個 | ❌ 不要用 |
|------|----------|-----------|
| 搜尋專案文字 | `mcp__webcodex__search_project_texts` | `grep -r` / `rg` |
| 搜尋 + 讀上下文 | `mcp__webcodex__search_and_read` | `grep` + `cat` |
| 讀取檔案 | `mcp__webcodex__work_on_project` → `read_files` | `cat` / `head` / `tail` |
| Rust 驗證 | `mcp__webcodex__cargo_check` | `cargo check` |
| Rust 測試 | `mcp__webcodex__cargo_test` | `cargo test` |
| 執行 runtime 工具 | `mcp__webcodex__call_runtime_tool` | `exec_command`（能用 WebCodex 時） |

### 2.2 容錯降級機制（Fallback 原則 - 避免死鎖與 Token 浪費）
- **單次失敗即降級**：WebCodex 工具調用回傳錯誤、逾時或斷線（Runner 離線 / 專案未註冊 / 報錯）**滿 1 次，必須立即降級改用 `exec_command`**（`rg`、`grep`、`cat`、`sed` 等）。
- **嚴禁連續重試**：禁止對同一操作連續呼叫失敗的 WebCodex 工具 2 次以上。
- **恢復時機**：當前小任務已用 `exec_command` 滿足後，在後續獨立新操作時才可再次嘗試 WebCodex。

### 2.3 什麼時候直接用 exec_command
- WebCodex 工具剛發生過錯誤（已進入降級狀態）
- WebCodex Runner 離線或專案未註冊
- 需要操作系統層級指令（git、chmod、mkdir、ps、kill 等）
- 需要存取專案目錄以外的檔案
- WebCodex 工具不支援的操作（如 pip install、npm install、composer 等）

---

## 3. Token 節約原則與對話主動引導規範

### 3.1 WebCodex 工具操作規範
- **搜尋先用 `files_with_matches` 或 `count` 模式**，確認範圍後再用 `matches` 看內容。
- **`search_and_read` 設定合理的 `read_before` / `read_after`**，預設 3~5 行，不超過 20 行。
- **批次查詢用 `queries` 陣列**，一次 1~8 個獨立 query，不要逐個搜。
- **`limit` 設定合理上限**，預設 20，視情況調整。

### 3.2 對話互動主動節約機制（主動攔截與引導）
當用戶提出過於廣泛、未指定範圍的請求時，AI 必須主動攔截並引導精準操作，不得直接執行大範圍讀取：
1. **主動攔截泛查指令**：當用戶提出如「幫我看整個專案」「分析全部架構」「檢查登入流程為什麼錯（未附線索）」等廣泛指令時，**立即暫停全域掃描**，主動提醒用戶先指定子專案（如 Owner / Member / Infra）或核心關鍵字。
2. **先搜尋定位，後讀取內容**：嚴禁直接整檔讀取或多檔批次全讀。先列出 3~5 個候選檔案路徑供確認，僅針對確認後的檔案讀取核心區段（以 20~50 行為原則）。
3. **查進度優先讀 Taskflow Outbox，不讀原始碼**：查詢各模組進度或 Agent 狀態時，優先讀取 `.taskflow/<agent>/outbox/` 最新報告，避免重複逆向工程。

### 3.3 派工與回報文件特別規範（「工單豁免」最高優先）
- **全面豁免 Token 節約限制**：對 `.taskflow/**/inbox/*.md`（工單）與 `.taskflow/**/outbox/*.md`（回報），**必須整檔完整讀取（使用 `cat` 或完整讀取）**，嚴禁使用 `read_before`/`read_after` 切片或只讀 20~50 行，以防漏掉驗收指標、邊界條件與代碼細節。
- **長工單走實體檔案**：所有 Agent 任務一律以完整目標檔 `.taskflow/<agent>/inbox/` 交付，長工單一律以 `--file` 派發防 Shell 截斷。
- **雙軌容錯通知機制**：
  - **信箱持久化**：所有工單與回報以實體 Markdown 檔存於 `.taskflow/<agent>/inbox/` 與 `outbox/`，這是系統唯一的狀態真相來源（SSOT）。
  - **Redis 事件秒級喚醒**：在 VPS 環境中，交卷工具 `waw-report` 或派工工具 `waw task` 會自動發送 Redis 事件通知常駐的 `taskflow-receiver.service`，秒級喚醒目標 Session。若 Redis 離線，系統安全降級為信箱輪詢，絕不丟失任務。
- **標準交卷工具**：完工後一律執行 `waw-report <報告檔.md>`（或調用 Skill `waw-report`，Nana 可用 `nana report <檔案>`）標準交卷，禁止私自 cat 進 outbox 了事。

### 3.4 CLI 原生命令 Token 節約鐵律（exec_command 執行最高準則）
1. **先搜檔名，再切片讀核心（20~50 行），嚴禁對業務代碼全檔 cat**。
2. **編譯日誌只取 tail 與 error，嚴禁全量傾印**（如 `pnpm build 2>&1 | tail -n 25`）。
3. **版本比對先看統計，後審細節**（優先 `git status -s` 或 `git diff --stat`）。

---

## 4. Protected Path 規範

WebCodex 內建 protected-path policy，自動排除：
- `.env` / 環境變數檔
- secrets / 金鑰
- build artifacts（target/、dist/、node_modules/）

**不要嘗試繞過這些保護**。如果需要讀取設定檔，用 `exec_command` 並明確告知用戶。

---

## 5. 與 instructions.md 的關係

本檔案與 `~/.codex/instructions.md` 互補為全域指令。
- `instructions.md`：Agent 角色鎖定、工作目錄規範、WAW SOP
- `AGENTS.md`（本檔）：WebCodex 工具優先原則、Token 節約、派工操作規範

兩者衝突時，以 `instructions.md` 的角色鎖定定義為先，以本檔的授權工具規範為先。
