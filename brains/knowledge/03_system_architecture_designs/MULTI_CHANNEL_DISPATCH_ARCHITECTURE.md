# 多管道派工架構設計


**[On-Demand]** — 上下文注入策略

> **版本**: 1.0  
> **建立日期**: 2026-06-21  
> **狀態**: ✅ 設計定案，待實作  
> **維護者**: HQ

---

## 一、兩種工作模式定義

### 模式 A：Hermes（遠端自動化指揮中心）

**使用場景**：Joe 人在外面，不在桌面

- ✅ 可以發任務給 Agent
- ✅ 可以收到 Agent 完成回報
- ✅ 同一個 Hermes session 繼續對話、繼續派工
- ✅ 全程 Telegram 閉環，不需要回桌面
- ✅ 多輪派工（Sophie 做完 → Ina 接著做）

### 模式 B：Codex CLI / Kiro IDE（桌面精密作業台）

**使用場景**：Joe 在桌面工作

- ✅ 審查 code、看 diff
- ✅ 複雜設計討論
- ✅ 看 log 除錯
- ✅ 需要 IDE 能力的工作
- ❌ **不會因為收到訊息而自動啟動回覆**
- ❌ 需要 Joe 手動提示才會有下一個動作

> **關鍵差異**：Hermes 是 session 常駐，收到回報可以繼續對話。
> Codex / Kiro 不是常駐服務，Joe 不在桌面時沒有動作。

---

## 二、完整系統架構

```
【場景 A：Joe 在外面】

Joe（手機 Telegram）
  ↓
bessie202 Hermes（常駐服務）
  ↓ hq_task_flow.sh --source hermes
bessie202 Redis
  ↓
bessie202 hq_gateway.py（常駐）
  ↓ SSH → 各 Agent 伺服器，觸發 codex exec
Agent 伺服器（yd174 / yd47 / yd16）
  ↓ 完成後 agent_report_to_hq_v2.sh
  ↓ redis-cli -h bessie202 PUBLISH agent/<name>/report
bessie202 hq_gateway.py
  ↓ 讀 source=hermes
Telegram Bot 通知 Joe + Hermes session 繼續對話
  ↓ Joe 可以繼續在 Telegram 派下一個任務


【場景 B：Joe 在桌面】

Joe（Kiro IDE 或 Codex CLI）
  ↓ hq_task_flow.sh --source kiro（本機）
本機 Redis
  ↓
本機 hq_gateway.py（launchd 常駐）
  ↓ 觸發本機 codex exec（Agent 專案在本機）
  ↓ 完成後寫入 _agent/inbox/
  ↓ Telegram Bot 通知 Joe（知道結果）
Joe 回到桌面後手動提示 Kiro → 審查結果 → 決策
```

---

## 三、source 欄位設計

### hq_task_flow.sh payload

```json
{
  "type": "task",
  "task_id": "TASK_20260621_001",
  "to_agent": "Sophie",
  "priority": "high",
  "source": "hermes",
  "description": "..."
}
```

**source 可能值**：

| 值 | 說明 |
|---|---|
| `hermes` | 從 Telegram / Hermes 發出 |
| `kiro` | 從 Kiro IDE 發出（預設） |
| `codex` | 從 Codex CLI 桌面發出 |

### context store 新增欄位

```
hq:thread:<task_id>:source  → "hermes" / "kiro" / "codex"
```

### hq_gateway.py 回報路徑邏輯

```python
source = context_store.get(task_id, "source") or "kiro"

if source == "hermes":
    # 通知 Telegram，Hermes session 可繼續對話
    self._telegram_notify("✅ 任務完成", summary)
else:
    # source = kiro / codex
    # 寫 inbox，Telegram 通知（但不啟動 session）
    write_inbox(report)
    self._telegram_notify("✅ 任務完成，回桌面後查看", summary)
```

---

## 四、基礎設施需求（待實作）

### bessie202 需要

| 項目 | 現況 | 需要做 |
|---|---|---|
| Redis | ❌ 沒有 | `apt install redis-server` |
| `hq_task_flow.sh` | ❌ 沒有 | 同步到 `/www/wwwroot/HQ/scripts/` |
| `agent_report_to_hq_v2.sh` | ❌ 沒有 | 同步到 `/www/wwwroot/HQ/scripts/` |
| SSH 到 yd174/yd47/yd16 | ❌ 沒有 | 建立 SSH 憑證 |
| hq_gateway.py | ✅ 有 | 改接 VPS Redis，補環境變數 |

### 各 Agent 伺服器需要

| 伺服器 | Agent | 需要做 |
|---|---|---|
| `yd174` | Sophie, Ina | 裝 Codex CLI，設定 config，`agent_report_to_hq_v2.sh` 改連 bessie202 Redis |
| `yd47` | Mina, Hubie | 同上 |
| `yd16` | Allie | 同上 |

### hq_task_flow.sh 修改

加入 `--source` 參數：
```bash
./scripts/hq_task_flow.sh task sophie TASK_001 "..." --source hermes
./scripts/hq_task_flow.sh task sophie TASK_001 "..."  # 預設 source=kiro
```

---

## 五、實作順序（建議）

1. bessie202 裝 Redis
2. bessie202 建 SSH 憑證連到 yd174
3. `hq_task_flow.sh` 加 `--source` 參數
4. `hq_gateway.py` 加回報路徑邏輯
5. yd174 裝 Codex CLI + 設定
6. 測試 Telegram → Sophie 單條鏈路
7. 確認後再擴展到 yd47、yd16

---

## 🔗 相關文件

- `brains/knowledge/01_agent_governance/MESSAGE_HUB_PROTOCOL.md` - 現行通訊協定
- `brains/knowledge/01_agent_governance/HQ_AUTOFLOW.md` - HQ Gateway 架構
- `scripts/hq_task_flow.sh` - 發令腳本（待加 --source）
- `scripts/hq_gateway.py` - Gateway（待加回報路徑邏輯）

---

*制定者：HQ | 建立日期：2026-06-21*
