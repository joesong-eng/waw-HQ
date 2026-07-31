# Trae 回報：hq_gateway.py 重構完成

> **執行者**：Trae
> **日期**：2026-06-10

---

## 修改一：`on_consultation()` 補上 `execute_task()`

已完成。`on_consultation()` 現在和 `on_task()` 一樣，會：
1. 查 AGENTS 確認 agent 存在
2. 建立 `_agent` 目錄並寫入 task file
3. 以 threading 觸發 `execute_task()`
4. 寫入 context store 記錄已 dispatch

**修改後邏輯（lines 313-325）：**
```python
def on_consultation(self, agent: str, payload: dict):
    cfg = AGENTS.get(agent)
    if not cfg:
        log('gateway', f"⚠️ 未知 Agent: {agent}"); return
    work_dir = Path(cfg['work_dir'])
    task_file = save_task_file(agent, payload, work_dir)
    threading.Thread(target=execute_task, args=(agent, cfg['label'], work_dir, payload, task_file), daemon=True).start()
    cid = payload.get('consult_id') or 'UNKNOWN'
    self.cs.append_history(cid, {'round': 0, 'from': 'Gateway', 'action': 'consultation_dispatched',
                                 'summary': f"諮詢已觸發 {agent} 執行", 'ts': now_iso()})
    log(agent, f"📨 收到諮詢: {cid}")
```

---

## 修改二：`hq_gateway.py` 移除 import 耦合

已完成。原本：
```python
from agents_supervisor import AGENTS, save_task_file, execute_task, log, HQ_PATH
```

已替換為直接內嵌所有常數與函式（lines 19-145）：
- `HQ_PATH`、`CODEX_BIN`、`EXEC_TIMEOUT`、`REDIS_HOST/PORT`、`SKILL_FILE`
- `AGENTS` dict（8 agents）
- `log()`
- `save_task_file()`
- `read_context_store()`
- `build_prompt()`
- `execute_task()`

`agents_supervisor.py` 保留原樣作為備份參考，現在只是純函式庫，不再被 `hq_gateway.py` import。

---

## 修改三：`com.hq.agents.supervisor.plist` 改指向 `hq_gateway.py`

已完成。兩處變更：
1. `ProgramArguments` 從 `agents_supervisor.py` → `hq_gateway.py`
2. Log 檔名從 `agents_supervisor.{out,err}.log` → `hq_gateway.{out,err}.log`

---

## 驗證結果

```bash
✅ 語法正確
✅ 無 import 耦合
✅ plist 已更新（指向 hq_gateway.py）
✅ AGENTS、HQ_PATH、log、execute_task 皆在 hq_gateway.py 內定義
✅ 行數：414 行（未超過 600 行限制）
```

---

## Launchd 切換提醒

**目前尚未重啟 launchd**，確認成果後由 Joe/HQ 手動執行：

```bash
launchctl unload ~/Library/LaunchAgents/com.hq.agents.supervisor.plist
launchctl load ~/Library/LaunchAgents/com.hq.agents.supervisor.plist
```

或重啟 `bessie202` 上的 `com.hq.agents.supervisor` service。

---

*Trae | 2026-06-10*
