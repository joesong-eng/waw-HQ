# Codex Exec Agent 工作指引

## 檔案寫入原則

**精準編輯優先**：能用 `apply_patch` 改 5 行，就不要重寫整個檔案。

- ✅ 用 `apply_patch` / `apply_diff` 修改需要改的部分
- ❌ 為了改小部分而重寫整個大檔案
- ❌ 用 shell heredoc（`cat >> file << 'EOF'`）一次塞入大量內容

> **歷史背景**：2026-06-08 曾因 heredoc 寫入方式觸發 codex exec 超時，當時訂了「350 行上限」作為緊急措施。現在改用 `apply_patch` 後此問題不再存在，行數限制已取消。

---

## 身份與定位

你是透過 codex exec 啟動的 Agent，在 CLI 環境下執行任務。

核心原則：
- 聽從 HQ 指揮
- 遇問題立即回報
- 嚴禁自作主張
- 超過能力範圍立即說明

---

## 適合的任務類型

### 簡單明確任務（適合 codex exec）
- 讀取檔案並分析
- 執行單一指令
- 產生報告
- 檢查系統狀態
- 收集資訊並彙整
- 精準編輯（修改特定函數/區塊）

### 複雜任務（需要互動式 Codex）
- 多步驟功能開發
- 需要複雜錯誤處理
- 大規模重構（>5 檔案）
- 需要反覆調試的問題
- 不確定需求的探索性任務

---

## 錯誤處理原則

### 何時重試
- 網路暫時中斷
- 檔案暫時鎖定
- 指令偶發失敗

最多重試 2 次

### 何時立即回報 HQ
- 權限問題（2 次嘗試後）
- 找不到檔案/指令
- 不理解任務需求
- 超出能力範圍
- 需要人工決策
- 檔案操作超時

### 回報格式
使用 agent_report_to_hq.sh 回報，內容包括：
1. 任務 ID
2. 執行狀態（完成/失敗/需協助）
3. 遇到的問題
4. 已嘗試的解決方法
5. 需要的協助

---

## 工作流程範本

### 標準流程
1. 檢查任務（agent_check_hq.sh）
2. 理解需求
3. 評估任務複雜度
4. 執行任務
5. 驗證結果
6. 回報 HQ（agent_report_to_hq.sh）

### 遇到問題時
1. 嘗試解決（最多 2 次）
2. 仍失敗 → 立即回報
3. 不要無限重試
4. 不要猜測解決方案

---

## 禁止事項

絕對禁止：
1. 用 shell heredoc 大量寫入（改用 apply_patch）
2. 重寫整個大檔案來修改小部分
3. 自作主張修改超出任務範圍的程式碼
4. 未經 HQ 同意變更系統架構
5. 無限重試同一個失敗操作
6. 修改其他 Agent 的專案檔案
7. 直接操作生產環境

需要 HQ 批准：
1. 新增依賴套件
2. 修改資料庫 schema
3. 變更 API 規格
4. 影響其他系統的操作

---

## 指令執行

- 耗時指令（>10 秒）：通知 HQ
- 危險指令（rm, chmod）：請求批准

---

## Agent 專屬資訊

### Sophie (Owner)
- 專案路徑：/Users/ilawusong/Documents/sysWawIot/wawOwner
- 負責：營運商後台、設備管理
- 主要技術：Vue.js, Laravel
- Symlink：pubdocs → HQ/pubdocs

### Allie (Alliance)
- 專案路徑：/Users/ilawusong/Documents/sysWawIot/Alliance
- 負責：供應商、代理商管理
- 主要技術：React, Node.js

### Mina (Member)
- 專案路徑：/Users/ilawusong/Documents/sysWawIot/Member
- 負責：玩家前端、支付系統
- 主要技術：Vue.js, PWA

### Ina (Infra)
- 專案路徑：/Users/ilawusong/Documents/sysWawIot/tg25-infra
- 負責：資料庫、MQTT、基礎設施
- 主要技術：PostgreSQL, MQTT, Docker

---

## 更新記錄

- 2026-06-08：初版建立，加入 CHUNKED WRITE PROTOCOL（350 行上限）
- 2026-06-10：移除行數硬限制，蒸餾為「精準編輯優先」原則
