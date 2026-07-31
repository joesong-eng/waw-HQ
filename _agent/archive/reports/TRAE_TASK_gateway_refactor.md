# Trae 任務：hq_gateway.py 重構 — 脫離 agents_supervisor 依賴

> **發派者**：HQ
> **日期**：2026-06-10
> **優先級**：high

---

## 背景說明

原本 `hq_gateway.py` 是 Qoder 在「350 行限制」的前提下寫的，
為了湊行數，選擇從 `agents_supervisor.py` import 共用邏輯。
現在 350 行限制已取消，且架構決策是：

> **`hq_gateway.py` 全權接管所有監聽與觸發，`agents_supervisor.py` 只是純函式庫，不跑 main()。**

目前問題：
1. `hq_gateway.py` 還在 `from agents_supervisor import ...`（不必要的耦合）
2. `GatewayListener.on_task()` 只處理 task/consult，**沒有處理 Agent 執行任務的邏輯**（只存檔，不 codex exec）——這塊原本在 `AgentThread` 裡，現在沒人接
3. `on_consultation()` 收到諮詢後只存 context store，**沒有觸發 codex exec 讓 Agent 執行諮詢**
4. launchd `com.hq.agents.supervisor.plist` 還指向 `agents_supervisor.py`，需要改指向 `hq_gateway.py`

---

## 目前檔案現狀

### `scripts/hq_gateway.py`（291 行）
- ✅ `ContextStore`：正確，不動
- ✅ `DecisionEngine`：正確，不動
- ⚠️ `GatewayListener`：需修改
  - `on_task()`：缺少 `execute_task()` 呼叫（現在只存 context store，沒有真的觸發 codex exec）
  - `on_consultation()`：同上，沒有觸發 Agent 執行諮詢
- ⚠️ 頂部 import：需要把 `from agents_supervisor import ...` 改成直接內嵌常數與函式

### `scripts/agents_supervisor.py`（194 行，HQ 已整理好）
- ✅ 已移除 `AgentThread`、`HQReportThread`、`main()`
- ✅ 現在只有：`AGENTS`、`HQ_PATH`、`CODEX_BIN`、`EXEC_TIMEOUT`、`log()`、`save_task_file()`、`read_context_store()`、`build_prompt()`、`execute_task()`
- 這些函式的內容你可以直接複製進 `hq_gateway.py`，或繼續 import 都可以——**但如果繼續 import，agents_supervisor.py 就不能再有 `if __name__ == '__main__'`**（現在已經沒有了，沒問題）

### `~/Library/LaunchAgents/com.hq.agents.supervisor.plist`
- 現在指向 `agents_supervisor.py`，需要改成 `hq_gateway.py`

---

## 需要做的修改

### 修改一：`hq_gateway.py` — 修正 `on_task()` 補上 execute_task

**現在的 `on_task()`（錯誤）：**
```python
def on_task(self, agent: str, payload: dict):
    cfg = AGENTS.get(agent)
    if not cfg:
        log('gateway', f"⚠️ 未知 Agent: {agent}"); return
    work_dir = Path(cfg['work_dir'])
    task_file = save_task_file(agent, payload, work_dir)
    threading.Thread(target=execute_task, args=(agent, cfg['label'], work_dir, payload, task_file), daemon=True).start()
    ...
```

等等，這個其實**有呼叫 execute_task**——問題是 `on_consultation()` 沒有。

**修正 `on_consultation()`：**
```python
def on_consultation(self, agent: str, payload: dict):
    cfg = AGENTS.get(agent)
    if not cfg:
        log('gateway', f"⚠️ 未知 Agent: {agent}"); return
    work_dir = Path(cfg['work_dir'])
    task_file = save_task_file(agent, payload, work_dir)
    # 諮詢也要觸發 Agent 去回答
    threading.Thread(target=execute_task, args=(agent, cfg['label'], work_dir, payload, task_file), daemon=True).start()
    cid = payload.get('consult_id') or 'UNKNOWN'
    self.cs.append_history(cid, {'round': 0, 'from': 'Gateway', 'action': 'consultation_dispatched',
                                 'summary': f"諮詢已觸發 {agent} 執行", 'ts': now_iso()})
    log(agent, f"📨 收到諮詢: {cid}")
```

### 修改二：`hq_gateway.py` — 移除 import 耦合，改為自包含

把頂部的：
```python
from agents_supervisor import AGENTS, save_task_file, execute_task, log, HQ_PATH
```

改為直接在 `hq_gateway.py` 內定義這些常數與函式（從 `agents_supervisor.py` 複製過來即可）。
`agents_supervisor.py` 保留原樣作為備份參考，但 `hq_gateway.py` 不再依賴它。

需要複製進來的內容：
- `HQ_PATH`、`CODEX_BIN`、`EXEC_TIMEOUT`、`SKILL_FILE` 常數
- `AGENTS` dict
- `log()`
- `save_task_file()`
- `read_context_store()`（給 `build_prompt` 用）
- `build_prompt()`
- `execute_task()`

### 修改三：`com.hq.agents.supervisor.plist` — 改指向 gateway

把：
```xml
<string>/Users/ilawusong/Documents/sysWawIot/HQ/scripts/agents_supervisor.py</string>
```
改成：
```xml
<string>/Users/ilawusong/Documents/sysWawIot/HQ/scripts/hq_gateway.py</string>
```

---

## 完成後請驗證

```bash
# 1. 語法檢查
python3 -c "compile(open('scripts/hq_gateway.py').read(), 'hq_gateway.py', 'exec'); print('✅ 語法正確')"

# 2. 確認不再 import agents_supervisor
grep "from agents_supervisor" scripts/hq_gateway.py && echo "❌ 還有 import" || echo "✅ 無 import 耦合"

# 3. 確認 AGENTS、execute_task 在 gateway 內定義
grep -n "^AGENTS\|^def execute_task\|^def log\|^HQ_PATH" scripts/hq_gateway.py

# 4. 確認行數合理（不超過 600 行）
wc -l scripts/hq_gateway.py

# 5. 確認 plist 已更新
grep "hq_gateway" ~/Library/LaunchAgents/com.hq.agents.supervisor.plist && echo "✅ plist 已更新"
```

---

## 完成後回報

請將回報寫入 `/Users/ilawusong/Documents/sysWawIot/HQ/_agent/TRAE_REPORT_gateway_refactor.md`，包含：
1. 各項修改是否完成
2. 驗證指令的輸出結果（貼上截圖或文字）
3. 任何你覺得需要 HQ 注意的設計決策

**不需要重啟 launchd**，那個由 Joe/HQ 手動確認後再做。

---

*HQ | 2026-06-10*
