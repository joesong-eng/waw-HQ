#!/bin/bash
# 清除指定 Agent 的待辦任務
# 使用方式：./hq_clear_tasks.sh <agent_name>
# 範例：./hq_clear_tasks.sh sophie

AGENT_NAME="${1}"

if [ -z "${AGENT_NAME}" ]; then
    echo "❌ 請提供 Agent 名稱"
    echo "使用方式: $0 <agent_name>"
    echo "範例: $0 sophie"
    exit 1
fi

OUTBOX_FILE="_agent/outbox/to_${AGENT_NAME}.json"

if [ -f "${OUTBOX_FILE}" ]; then
    rm "${OUTBOX_FILE}"
    echo "✅ 已清除 ${AGENT_NAME} 的待辦任務"
else
    echo "⚠️  ${AGENT_NAME} 沒有待辦任務"
fi
