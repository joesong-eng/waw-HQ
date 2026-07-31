# 跨 Agent 任務廣播技能

## 使用時機
HQ 需要同時派發任務給多個 Agent 時使用。

## 執行步驟

### 廣播給多個 Agent
```bash
cd /Users/ilawusong/Documents/sysWawIot/HQ

# 依序對每個 Agent 發任務
./scripts/hq_task_flow.sh task sophie TASK_YYYYMMDD_001 "<描述>" high
./scripts/hq_task_flow.sh task ina    TASK_YYYYMMDD_002 "<描述>" high
./scripts/hq_task_flow.sh task mina   TASK_YYYYMMDD_003 "<描述>" normal
```

### 發送後確認
```bash
# 確認 Redis 有收到
redis-cli keys "hq:thread:TASK_*" | head -10

# 確認 gateway 有處理
tail -20 logs/hq_gateway.out.log
```

## 注意事項
- 每個任務都有獨立的 `task_id`，方便追蹤
- `hq_gateway.py` 會自動接收回報並決策下一步
- ~~Chat Bridge~~ 已於 2026-06-06 廢棄，禁止使用

## 相關文件
- `skills/hq_ops/message_hub_operations.md` — 完整操作指南
- `brains/knowledge/01_agent_governance/MESSAGE_HUB_PROTOCOL.md` — 協定規範
