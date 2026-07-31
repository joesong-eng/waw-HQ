# Agent 啟動安全協議 (Startup Protocol)


**[On-Demand]** — 上下文注入策略

## 🚨 問題背景
當 Agent 在大型 Mono-repo 或多專案目錄結構中啟動時，若執行遞迴掃描 (如 `ls -R ..` 或 `find ..`)，會觸發 `vendor/`, `node_modules/`, `.git/` 等目錄，導致輸出超過 Token 限制 (如 36 萬 tokens) 而造成系統卡死或連線中斷。

## ✅ 執行規範

### 1. 禁止操作 (Strictly Forbidden)
- ❌ **禁止** 遞迴掃描父目錄：`ls -R ..`
- ❌ **禁止** 無差別全域搜尋：`find .. -name "*"`
- ❌ **禁止** 讀取其他專案的依賴庫：`cat ../*/vendor/*`
- ❌ **禁止** 掃描大型套件目錄：`ls node_modules/` (除非必要且限深度)

### 2. 啟動標準程序 (Standard Procedure)
Agent 啟動時僅能執行以下精準操作：
- `pwd` : 確認當前路徑。
- `cat AGENTS.md` : 讀取角色規範。
- `ls -l _agent/` : 檢查當前專案的任務文件。
- `ls -l ../HQ/_agent/outbox/` : 檢查是否有發送給自己的任務 (精準路徑)。
- `rg --max-depth 2` : 進行有深度限制的搜尋。

### 3. 異常處理
若發現環境輸出過大，Agent 應立即停止執行並回報 HQ，而非嘗試繼續讀取。

---
*由 HQ 頒布於 2026-06-21*
