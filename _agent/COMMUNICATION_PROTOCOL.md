# HQ 溝通與任務協定 (Communication & Task Protocol)

本文件定義所有 Agent 與 HQ 的溝通與任務接收規則。

## 1. 任務接收來源 (Task Sources)
Agent 必須優先檢查以下目錄與機制以獲取 HQ 指派的任務：
1. **Outbox**: 檢查 `_agent/outbox/to_AgentName.json`。
2. **Dispatch Board**: 檢查 `_agent/DISPATCH_BOARD.md` (這是彙整狀態的核心文件)。
3. **Redis**: 監聽 `agent/Allie/task` 等專屬頻道 (若已建立連線)。

## 2. 留言與回報方式 (Messaging Protocol)
當 Agent 需要留言給 HQ 時，請依下列順序執行：

### A. 透過檔案系統 (推薦)
1. 在 `_agent/inbox/` 建立檔案。
2. 命名格式：`from_<AgentName>_<Topic>_<YYYYMMDD_HHMM>.md`。
3. 內容：必須包含 `Task_ID` (若有)、`Status`、`Details` (Log 或執行結果路徑)。

### B. 透過 Dispatch Board 回報
若任務涉及專案進度，請在 `_agent/DISPATCH_BOARD.md` 相關欄位更新執行狀態。

### C. 緊急通訊 (Redis)
若需 HQ 即時處理，請將訊息推送到 Redis 頻道 `agent/hq/message`。

---
## 3. 若找不到任務內容怎麼辦？
1. 若 `DISPATCH_BOARD.md` 未更新，請檢查 `_agent/task_flow.log` 確認 HQ 是否有發送動作。
2. 若確認有紀錄但無檔案，請直接向 HQ 報告：「無法在指定路徑讀取任務詳情，請補發或確認儲存路徑。」
3. **嚴禁**：不要隨意猜測，務必向 HQ 核實。
