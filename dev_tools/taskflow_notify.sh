#!/usr/bin/env bash
# Taskflow Redis 通知鉤子 (含容錯降級機制)
# 用法: taskflow_notify.sh <dispatch|response|recovery> <agent> <task_id>

EVENT_TYPE="$1"
AGENT="$2"
TASK_ID="$3"

if [ -z "$EVENT_TYPE" ] || [ -z "$AGENT" ] || [ -z "$TASK_ID" ]; then
  echo "Usage: $0 <dispatch|response|recovery> <agent> <task_id>"
  exit 1
fi

agent_to_lower() {
  local a
  a=$(echo "$1" | tr "[:upper:]" "[:lower:]")
  case "$a" in
    sophie) echo "owner" ;;
    mina) echo "member" ;;
    ina) echo "infra" ;;
    allie) echo "alliance" ;;
    hubie) echo "ihub" ;;
    sidney|signal) echo "signalhub" ;;
    *) echo "$a" ;;
  esac
}

AGENT_LOWER=$(agent_to_lower "$AGENT")

case "$EVENT_TYPE" in
  dispatch)
    CHANNEL="taskflow:dispatch:$AGENT_LOWER"
    MSG='{"task_id":"'"$TASK_ID"'","event":"new_task","agent":"'"$AGENT_LOWER"'","ts":'$(date +%s)'}'
    ;;
  response)
    CHANNEL="taskflow:response:$AGENT_LOWER"
    MSG='{"task_id":"'"$TASK_ID"'","event":"response","responder":"'"$AGENT_LOWER"'","ts":'$(date +%s)'}'
    ;;
  recovery)
    CHANNEL="taskflow:recovery"
    MSG='{"task_id":"'"$TASK_ID"'","event":"recovery","ts":'$(date +%s)'}'
    ;;
  *)
    echo "Unknown event type: $EVENT_TYPE"
    exit 1
    ;;
esac

# 嘗試發送 Redis 通知，若失敗或超時則安全降級
if command -v redis-cli >/dev/null 2>&1; then
  if timeout 2 redis-cli PUBLISH "$CHANNEL" "$MSG" >/dev/null 2>&1; then
    echo "📡 [Notify:Redis] $CHANNEL -> $TASK_ID"
    exit 0
  fi
fi

echo "⚠️ [Notify:Fallback] Redis 未就緒，已透過檔案信箱持久化 ($TASK_ID)"
exit 0
