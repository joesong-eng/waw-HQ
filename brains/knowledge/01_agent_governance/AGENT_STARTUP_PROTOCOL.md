# Agent 啟動協議 (Agent Startup Protocol)

> **版本**: 2.2.0  
> **建立日期**: 2026-08-16  
> **最後更新**: 2026-09-06  
> **狀態**: Active / Authoritative (權威標準)  
> **維護者**: HQ  
> **適用範圍**: 所有 Agent (Sophie, Mina, Ina, Allie, Hubie, Fio, Coli, Sidney)

---

## 📋 核心概念

Codex CLI Agent 是**對話驅動、按需啟動 (On-Demand)** 的一次性執行個體，不是常駐守護行程 (Daemon)。
啟動後的第一要務，是**確認自身身分、專案邊界、與環境拓撲常識**，嚴禁憑空猜測環境參數或預設網路配置。

---

## 🔄 Agent 啟動與執行標準流程

### 步驟 1：環境識別與載入系統常識
Agent 被啟動於對應專案目錄（例如 `PROJECT/SignalHub`、`PROJECT/Owner` 等）時：
1. **讀取專案內的 `AGENTS.md`**：確認自身身份鎖定口令、專案邊界與所屬遠端主機配置。
2. **載入環境與連線常識**：嚴格遵守 `../../brains/knowledge/04_deployment_operations/VPS_TOPOLOGY_CARD.md`：
   - 嚴禁使用 raw IP、嚴禁使用預設 Port 22、嚴禁用 root 帳號直連。
   - 必須使用本機 `~/.ssh/config` 定義之別名（如 `yd174`, `mina`, `alliance`, `infra`）。
   - 認知資料庫實體位於 `infra`（141.148.165.50），Web 主機禁止直連 `mysql -u root`，嚴禁在 CLI 打上明文密碼。
3. **認知本機限制**：嚴守 `LOCAL_DEVELOPMENT_CONSTRAINTS.md`，本機僅供 Code/Git，不跑本地伺服器、Artisan 或本地 DB 測試。

### 步驟 2：檢查信箱與任務目標
1. 查看 `.taskflow/<agent>/inbox/` 獲取分配到的任務工作單。
2. 確認任務目標、邊界、先決條件與驗收標準。

### 步驟 3：執行代碼與文檔工作
1. 僅修改所屬專案範圍內的代碼或文檔。
2. 保持本機純淨，不啟動本地 Web 服務。
3. 提交 Git 變更（保持乾淨的 Commit message）。

### 步驟 4：遠端部署與驗證（如涉及）
1. **首選總控工具**：
   - 部署：`../../dev_tools/waw_ops.sh deploy <agent>`
   - 遠端指令/驗證：`../../dev_tools/waw_ops.sh remote <agent> "<指令>"`
2. **手動 SSH 備援**：必須使用標準別名（例如 `ssh yd174 "..."`），Port 39022，User ubuntu。
3. **真實狀態驗收**：驗證真實 HTTP 狀態碼、API 回傳或遠端服務 log，拒絕口頭宣稱完成。

### 步驟 5：撰寫報告並回傳
1. 依標準模板撰寫 Markdown 格式的回報檔案至專案目錄或直接提交。
2. 執行 `bash ../../dev_tools/agent_report_to_hq_v2.sh <Agent名稱> <報告檔案>` 或放入 `../../.taskflow/<agent>/outbox/`。
3. 任務結束，Agent session 自行終止。
