# 檢查待辦任務技能

## 使用時機
Agent 被 `hq_gateway.py` 觸發後，或 HQ 手動查看回報時使用。

## Agent 端：任務自動送達
Agent 不需要主動輪詢。`hq_gateway.py`（launchd 常駐）收到 Redis 訊號後，
會自動觸發 `codex exec` 並傳入任務內容。

任務檔案位置：`_agent/REDIS_<timestamp>_<task_id>.json`

## HQ 端：查看回報

### 列出最新回報
```bash
ls -lht /Users/ilawusong/Documents/sysWawIot/HQ/_agent/inbox/ | head -10
```

### 查看 context store 狀態
```bash
TASK_ID="TASK_20260610_001"
redis-cli GET hq:thread:${TASK_ID}:status   # pending/consulting/resolved/escalated
redis-cli GET hq:thread:${TASK_ID}:round
redis-cli LRANGE hq:thread:${TASK_ID}:history 0 -1
```

### 查看 gateway 即時 log
```bash
tail -f /Users/ilawusong/Documents/sysWawIot/HQ/logs/hq_gateway.out.log
```

## 標準回報格式（Agent 執行完後產生）

```markdown
# <AgentName> 任務回報

> 任務 ID: <task_id>
> 狀態: completed / blocked / needs_review
> 回報時間: <timestamp>

## 執行摘要
<說明做了什麼>

## 證明
<log、API 回傳、grep 結果等>

## 後續風險
<如有>
```

## 注意事項
- ~~Chat Bridge~~ 已於 2026-06-06 廢棄，禁止使用
- Agent 不可自行呼叫 `codex exec`，只能被 `hq_gateway.py` 觸發
