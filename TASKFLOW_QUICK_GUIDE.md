
╔══════════════════════════════════════════════════════════════════════════════╗
║              Taskflow 快速參考指南 - 給所有 Agent                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

## 🎯 核心原則

**每個 Agent 只能寫入自己的 outbox**
**每個 Agent 只能讀取自己的 inbox**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📋 三種常見場景

### 1️⃣ 收到 HQ 派工（最常見）

HQ 派工 → 你的 inbox
例如：.taskflow/signalhub/inbox/TASK_20260908_xxx.md

你要做的：
1. 讀取任務內容
2. 執行工作
3. 使用腳本回報：
   bash ../../dev_tools/agent_report_to_hq_v2.sh sidney report.md
   
結果：自動寫入你的 outbox
例如：.taskflow/signalhub/outbox/REPORT_20260908_xxx.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 2️⃣ 向 HQ 提問或回報問題（偶爾）

你發現技術問題需要 HQ 協調時：

❌ 錯誤：不要寫入 .taskflow/hq/inbox/
✅ 正確：寫入你自己的 outbox

檔案命名：
  QUESTION_<日期>_<你的名字>_TO_HQ_<問題簡述>.md

位置：
  .taskflow/signalhub/outbox/QUESTION_20260908_SIDNEY_TO_HQ_xxx.md

HQ 會：
  - 讀取你的 outbox
  - 協調決策
  - 在 .taskflow/hq/outbox/ 發布回覆
  - 或直接派工到你的 inbox

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 3️⃣ 日常工作回報（每次任務完成後）

完成任務後：

使用回報腳本：
  cd PROJECT/SignalHub  # 你的專案目錄
  bash ../../dev_tools/agent_report_to_hq_v2.sh sidney 你的報告.md

結果：
  報告自動複製到 .taskflow/signalhub/outbox/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📂 目錄對應關係

根目錄：                    專案內捷徑：
.taskflow/signalhub/    ←→ PROJECT/SignalHub/.taskflow/sidney/
.taskflow/owner/        ←→ PROJECT/Owner/.taskbox/
.taskflow/infra/        ←→ PROJECT/Infra/.taskbox/
.taskflow/member/       ←→ PROJECT/Member/.taskbox/
.taskflow/alliance/     ←→ PROJECT/Alliance/.taskbox/

兩者是同一個目錄，用哪個都可以。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ✅ 權限總結

你可以：
  ✅ 讀取：.taskflow/你的agent名稱/inbox/
  ✅ 寫入：.taskflow/你的agent名稱/outbox/
  ✅ 讀取：brains/knowledge/ (唯讀)
  
你不能：
  ❌ 寫入：.taskflow/hq/inbox/
  ❌ 寫入：.taskflow/其他agent/inbox/
  ❌ 寫入：.taskflow/其他agent/outbox/
  ❌ 寫入：brains/knowledge/ (只有 HQ 能寫)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

有問題？查看完整協議：
brains/knowledge/01_agent_governance/SIMPLE_FILE_DISPATCH_PROTOCOL.md

╚══════════════════════════════════════════════════════════════════════════════╝



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔗 .taskbox 捷徑說明

所有專案目錄都有一個 `.taskbox` 捷徑指向根目錄的 taskflow：

```
PROJECT/SignalHub/.taskbox  →  ../../.taskflow/signalhub/
PROJECT/Owner/.taskbox       →  ../../.taskflow/owner/
PROJECT/Alliance/.taskbox    →  ../../.taskflow/alliance/
```

### 兩種訪問方式（等價）

**方式 1：從專案目錄**
```bash
cd PROJECT/SignalHub
ls .taskbox/inbox/      # 查看自己的任務
ls .taskbox/outbox/     # 查看自己的回報
```

**方式 2：從根目錄**
```bash
cd /Users/ilawusong/Documents/WaW
ls .taskflow/signalhub/inbox/
ls .taskflow/signalhub/outbox/
```

兩種方式訪問的是**同一個目錄**，選擇你覺得方便的即可。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

最後更新：2026-09-08 by HQ

