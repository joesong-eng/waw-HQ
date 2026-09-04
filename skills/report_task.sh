#!/bin/bash
# 技能：report_task — Agent 回報給 HQ
# 用法（從 Agent workdir 執行）：
#   bash ../../skills/report_task.sh <agent_name> <task_id> <done|blocked|info> "<內容>"

AGENT_NAME="$1"
TASK_ID="$2"
STATUS="$3"
CONTENT="$4"

[ -n "${AGENT_NAME}" ] && [ -n "${TASK_ID}" ] || {
    echo "用法: report_task.sh <agent> <task_id> <status> \"<內容>\""
    exit 1
}

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="_agent/REPORT_${TIMESTAMP}_${TASK_ID}.md"
mkdir -p _agent

cat > "${REPORT_FILE}" <<EOF
# 任務回報：${TASK_ID}
- Agent: ${AGENT_NAME}
- 狀態: ${STATUS}
- 時間: $(date '+%Y-%m-%d %H:%M:%S')

${CONTENT}
EOF

# 找回報腳本（往上找兩層）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPORT_SCRIPT="${SCRIPT_DIR}/../scripts/agent_report_to_hq_v2.sh"

[ -f "${REPORT_SCRIPT}" ] || { echo "❌ 找不到 agent_report_to_hq_v2.sh"; exit 1; }
bash "${REPORT_SCRIPT}" "${AGENT_NAME}" "${REPORT_FILE}"
