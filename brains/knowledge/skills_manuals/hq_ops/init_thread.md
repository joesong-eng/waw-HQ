# Skill: init_thread

## 描述
HQ 發任務給 Agent 時，同步在 Redis 初始化 context store thread。
確保後續所有分身都能讀到任務的完整脈絡。

## 觸發時機
- `hq_task_flow.sh` 發任務後立即執行

## 執行步驟

### 1. 初始化 context store
```bash
TASK_ID="<task_id>"
AGENT="<agent>"
DESC="<任務描述>"

redis-cli SET hq:thread:${TASK_ID}:status "pending"
redis-cli SET hq:thread:${TASK_ID}:round "0"
redis-cli SET hq:thread:${TASK_ID}:agent "${AGENT}"
redis-cli SET hq:thread:${TASK_ID}:issue "${DESC}"
redis-cli DEL hq:thread:${TASK_ID}:history

# 寫入第一筆歷史
redis-cli RPUSH hq:thread:${TASK_ID}:history \
  "{\"round\":0,\"from\":\"HQ\",\"action\":\"task_issued\",\"desc\":\"${DESC}\"}"
```

### 2. 設定 TTL（避免 Redis 堆積）
```bash
redis-cli EXPIRE hq:thread:${TASK_ID}:status 604800    # 7天
redis-cli EXPIRE hq:thread:${TASK_ID}:round 604800
redis-cli EXPIRE hq:thread:${TASK_ID}:history 604800
redis-cli EXPIRE hq:thread:${TASK_ID}:issue 604800
```

## 相關文件
- `skills/hq_ops/analyse_agent_report.md` — 收到回報後的處理
- `scripts/hq_task_flow.sh` — 發任務腳本
