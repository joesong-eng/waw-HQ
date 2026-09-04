# Skill: HQ 任務協調（兩階段派工）

> **版本**：1.0
> **建立**：2026-08-01
> **適用角色**：HQ（唯一使用者）
> **核心規則**：諮詢先行，核准後執行，不得越階

---

## 什麼時候用這個 Skill

每當 Joe 要求 HQ 對任何 Agent 下指令，且工作內容涉及：

- 修改程式碼、設定檔、migration
- 新建或刪除檔案、資料表、API
- 改變部署配置、基礎設施、MQTT 設定
- 跨 Agent 協作（影響超過一個專案）

**一律使用本 Skill 的兩階段流程，不得直接下執行任務。**

純查詢（例如：「目前 Owner 的 API 有哪些」）可跳過 Stage B，但 Stage A 仍需建立。

---

## Stage A：諮詢（Consultation）

### A1. HQ 建立諮詢任務

```bash
./core/hq_task_flow.sh consult <agent> <thread_id> "<諮詢問題>" high
```

**諮詢內容必須包含：**

1. 背景說明（為什麼要做這件事）
2. 預期目標（驗收條件）
3. 已知限制（不得觸碰的範圍）
4. 要求 Agent 回覆的問題（方案可行性、影響範圍、替代方案）

**諮詢內容禁止包含：**

- 具體的程式碼實作指令（「請在 XXX 加這段程式」）
- 要求直接修改任何檔案

---

### A2. Agent 執行諮詢

Agent 在其專案目錄內啟動，**只讀不寫**（業務程式碼），回覆 consultation report：

```json
{
  "thread_id": "<thread_id>",
  "agent": "<agent_name>",
  "status": "awaiting_approval",
  "understanding": "用 Agent 自己的話重述需求，確認理解正確",
  "current_state_evidence": [
    "實際讀取的檔案路徑與關鍵內容摘要",
    "指令輸出 log",
    "現有架構與需求的差距"
  ],
  "recommended_plan": [
    "Step 1: ...",
    "Step 2: ...",
    "Step N: ..."
  ],
  "alternatives": [
    { "option": "方案 B", "tradeoff": "..." }
  ],
  "affected_files": ["預計修改或新建的檔案列表"],
  "risks": ["風險描述與對應回滾方法"],
  "validation_plan": ["執行後用什麼指令或 log 來驗證成功"],
  "questions_for_hq": ["需要 Joe/HQ 決策的尚未明確事項"]
}
```

回報後：Telegram 通知 Joe，status 更新為 `awaiting_approval`。

---

### A3. HQ 審閱（Joe 開啟 HQ session）

收到 Telegram 通知後，Joe 回到 HQ session：

1. 閱讀 consultation report
2. 判斷：
   - ✅ 方案可行 → 進入 Stage B
   - 🔄 需要補充 → 補充後重新諮詢（REDO，同 thread_id）
   - ❌ 不做 → 關閉 thread，status = "rejected"
3. 若核准，明確告知 HQ 哪個方案被核准（或調整後核准）

---

## Stage B：執行（Execution）

### B1. HQ 建立執行任務

只有在 Stage A 完成且已獲核准後執行：

```bash
./core/hq_task_flow.sh task <agent> <thread_id>_EXEC "<執行任務說明>" high
```

**執行任務 payload 必須帶入：**

- 核准的方案摘要（approved_plan）
- consultation report 路徑（作為執行依據）
- 驗收條件（與 consultation report 的 validation_plan 一致）
- 明確的回報格式要求

---

### B2. Agent 執行任務

Agent 在其專案目錄內啟動，**只實作已核准的方案**：

- 遇到方案外的決策 → 立即停止，回報 `blocked: true`，等待 HQ 補充
- 不得自行擴大範圍
- 完成後寫入 `.taskbox/outbox/<thread_id>_EXEC_report.json`

**執行 report 最少須包含：**

```json
{
  "thread_id": "<thread_id>_EXEC",
  "agent": "<agent_name>",
  "status": "done | blocked | partial",
  "summary": "完成工作的一句話摘要",
  "evidence": [
    "git diff 摘要或修改檔案列表",
    "測試指令與實際輸出 log",
    "驗證指令輸出"
  ],
  "requires_review": false,
  "blocked": false,
  "blocked_reason": "",
  "sub_tasks": []
}
```

---

### B3. HQ 驗收

收到 Telegram 通知後，Joe 回到 HQ session：

1. 閱讀 execution report
2. 以 `evidence` 中的 log 和 diff 驗收，不以口頭聲明驗收
3. 若有問題：REDO，帶入具體問題描述

---

## 快速狀態速查

```bash
# 查所有任務 context store
redis-cli KEYS "hq:thread:*:status" | xargs -I{} sh -c 'echo "{}: $(redis-cli GET {})"'

# 查特定任務
redis-cli GET "hq:thread:<thread_id>:status"

# 查 HQ inbox 回報
ls -lt .taskbox/inbox/ | head -10

# 查 HQ outbox 發出的任務
ls .taskbox/outbox/
```

---

## 防呆清單（HQ 每次派工前自問）

- [ ] 我有沒有先做 consultation？
- [ ] Agent 有沒有回覆 `consultation_report`？
- [ ] 我有沒有明確告知哪個方案被核准？
- [ ] Execution payload 有沒有帶入 `approved_plan` 與驗收條件？
- [ ] Agent 在諮詢階段有沒有「questions_for_hq」未回答？

---

## 適用 Agent 與工作目錄

| Agent | 工作目錄 | 主要職責 |
|-------|---------|---------|
| Sophie | `/Users/ilawusong/Documents/WaW/Owner` | 營運商後台 |
| Mina | `/Users/ilawusong/Documents/WaW/Member` | 玩家前端 |
| Ina | `/Users/ilawusong/Documents/WaW/Infra` | 資料庫、MQTT、基礎設施 |
| Allie | `/Users/ilawusong/Documents/WaW/Alliance` | 供應商代理商 |
| Hubie | `/Users/ilawusong/Documents/WaW/iHub` | Android APK |
| Fio | `/Users/ilawusong/Documents/WaW/Firmware/IOTkiosk_v0` | 兌幣卡韌體 |
| Coli | `/Users/ilawusong/Documents/WaW/Firmware/IOTwawS3` | 遊戲採集卡韌體 |

---

## 🔗 文件神經連結

- **設計依據**：`CLI_AGENT_DISPATCH_DESIGN.md`
- **實作腳本**：`../../core/hq_task_flow.sh`、`../../core/hq_gateway.py`
- **治理規範**：`AGENT_EXECUTION_PROTOCOL.md`、`AGENT_RESPONSIBILITY_BOUNDARIES.md`
