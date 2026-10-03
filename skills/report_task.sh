#!/bin/bash
# 技能：report_task — Agent 回報給 HQ (.taskflow)
# 用法（從 Agent workdir 執行）：
#   bash ../../skills/report_task.sh <agent_name> <task_id> <done|blocked|info> "<內容>"
AGENT_NAME="$1"
TASK_ID="$2"
STATUS="$3"
CONTENT="$4"

if [ -z "${AGENT_NAME}" ] || [ -z "${TASK_ID}" ]; then
  echo '用法: report_task.sh <agent> <task_id> <status> "<內容>"'
  exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="/tmp/REPORT_${TIMESTAMP}_${TASK_ID}.md"
{
  echo "# 任務回報：${TASK_ID}"
  echo "- Agent: ${AGENT_NAME}"
  echo "- 狀態: ${STATUS}"
  echo "- 時間: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""
  echo "${CONTENT}"
} > "${REPORT_FILE}"

# 使用標準回報腳本（寫入 .taskflow/<agent>/outbox/）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPORT_SCRIPT="${SCRIPT_DIR}/../dev_tools/agent_report_to_hq_v2.sh"
if [ ! -f "${REPORT_SCRIPT}" ]; then
  echo "❌ 找不到 agent_report_to_hq_v2.sh"
  exit 1
fi
bash "${REPORT_SCRIPT}" "${AGENT_NAME}" "${REPORT_FILE}"
