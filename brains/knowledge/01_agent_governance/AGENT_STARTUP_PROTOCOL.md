# Agent 啟動協議 (Agent Startup Protocol)

> **版本**: 2.0.0  
> **建立日期**: 2026-08-16  
> **最後更新**: 2026-08-22  
> **狀態**: Active / Authoritative (權威標準)  
> **維護者**: HQ  
> **適用範圍**: 所有 Agent (Sophie, Mina, Ina, Allie, Hubie, Fio, Coli)

---

## 📋 核心概念

Codex CLI Agent 是**對話驅動、按需啟動 (On-Demand)** 的一次性執行個體，不是常駐守護行程 (Daemon)。

---

## 🔄 Agent 啟動與執行標準流程

### 步驟 1：環境識別與讀取職責
Agent 被啟動於對應專案目錄（例如 `PROJECT/Member`）時：
1. 讀取專案內的 `AGENTS.md` 與全局知識庫規則。
2. 認知自身專案邊界與本機限制（嚴守 `LOCAL_DEVELOPMENT_CONSTRAINTS.md`）。

### 步驟 2：檢查信箱
1. 查看 `.taskflow/<agent>/inbox/` 獲取分配到的任務。
2. 確認任務目標、邊界與驗收條件。

### 步驟 3：執行工作
1. 編輯代碼或文檔。
2. 保持本機純淨（不在本機執行 `php artisan`、不啟動本地 Web 服務）。
3. 提交 Git 變更。

### 步驟 4：遠端部署與驗證（如涉及）
1. 依照 `DEPLOYMENT_GUIDE.md` 規範，透過 SSH 遠端拉取並驗證。
2. 遠端執行必要之 migrate、cache:clear、restart 等指令。

### 步驟 5：撰寫報告並回傳
1. 撰寫 Markdown 格式的回報。
2. 執行 `bash ../../scripts/agent_report_to_hq_v2.sh <Agent名稱> <報告檔案>`。
3. 任務結束，Agent session 自行終止。

