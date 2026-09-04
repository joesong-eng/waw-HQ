# HQ 派工使用說明書

> **版本**: 2026-08-01 v1.0  
> **維護者**: HQ  
> **適用對象**: 所有 Agent（Sophie / Ina / Mina / Allie / Hubie / Fio / Coli）

---

## 1. 派工管道總覽

```
Joe（使用者）
  ↓ 指令 / 截圖 / 問題描述
HQ（協調者）
  ↓ ./core/hq_task_flow.sh task <agent> <task_id> "<描述>" [priority]
  ↓
  ├─ ① HQ outbox 寫入 JSON 檔
  │     路徑: WHQ/.taskbox/outbox/to_<Agent>.json
  │
  ├─ ② Redis context store 初始化
  │     key: hq:thread:<task_id>:status → "pending"
  │     key: hq:thread:<task_id>:agent → "<agent>"
  │     key: hq:thread:<task_id>:description → "<描述>"
  │
  └─ ③ Redis Pub/Sub 發布
        channel: agent/<agent>/task
        payload: JSON 內容
```

---

## 2. ⚠️ 重要：Agent 如何確認收到任務

### ❌ 錯誤做法
> 檢查 `.taskbox/inbox/` 是否有新檔案來判斷是否有派工

**原因**：目前 `hq_task_flow.sh` 只寫入 **HQ outbox**（`WHQ/.taskbox/outbox/to_<Agent>.json`），並透過 Redis Pub/Sub 發布。**不會** 直接寫入各 Agent 的 `.taskbox/inbox/`。

### ✅ 正確做法（依優先順序）

| 方法 | 說明 |
|------|------|
| **1. HQ 直接在對話中交代** | HQ 在 Codex chat 中直接貼上完整任務描述，Agent 直接執行 |
| **2. 讀取 HQ outbox** | `cat /Users/ilawusong/Documents/WaW/WHQ/.taskbox/outbox/to_<Agent>.json` |
| **3. 查 Redis context store** | `redis-cli GET hq:thread:<task_id>:status` |
| **4. Redis Pub/Sub 訂閱** | `redis-cli SUBSCRIBE agent/<agent>/task`（需常駐 daemon，Codex 環境不適用） |

> **結論**：在 Codex 環境下，Agent 是 conversation-driven，不是常駐 daemon。因此 **方法 1** 是最可靠的派工方式。

---

## 3. 任務優先級

| 優先級 | 說明 |
|--------|------|
| `critical` | 使用者正在等待、影響生產環境、需立即處理 |
| `high` | 重要但非緊急，當日需完成 |
| `normal` | 一般任務，合理排程即可 |

---

## 4. 任務回報規範

### 必須提供的回報內容
- **截圖** 或 **log** 或 **API 回傳結果**（禁止純口頭結案）
- 回報檔案放置路徑：`<專案>/_agent/REPORT_<timestamp>_<task_id>.md`

### 回報範例結構
```markdown
# 回報：<task_id>
- **狀態**: 完成 / 進行中 / 受阻
- **發現**:
  - ...
- **操作**:
  - ...
- **證據**:
  - (附截圖路徑 / log 片段 / curl 輸出)
- **後續建議**:
  - ...
```

---

## 5. 常見 FAQ

### Q: Redis Pub/Sub subscriber 數量為 0 怎麼辦？
**A**: 這是正常的。Codex Agent 不是常駐程式，不會持續訂閱 channel。Pub/Sub 訊息是 fire-and-forget，發完就消失。所以 **HQ 會在對話中直接交代任務內容**，不依賴 Pub/Sub 作為唯一傳遞管道。

### Q: 我在 `.taskbox/inbox/` 沒看到任務檔？
**A**: 見第 2 節。`hq_task_flow.sh` 不會寫入你的 inbox，請改讀 HQ outbox 或直接看 HQ 在對話中的指示。

### Q: 跨專案查詢需要什麼資料？
**A**: 不可自行全域掃描（見 AGENTS.md 安全協議）。向 HQ 回報需求，由 HQ 協調取得。

---

## 6. 派工腳本位置

```
/Users/ilawusong/Documents/WaW/WHQ/core/hq_task_flow.sh
```

### 使用語法
```bash
./core/hq_task_flow.sh task <agent> <task_id> "<描述>" [priority]
```

### 範例
```bash
./core/hq_task_flow.sh task sophie SOPHIE-API-241 "修復 /details endpoint 504 問題" critical
```

