#!/bin/bash
# 技能：dispatch_task — 從 HQ 派工給 Agent
# 用法：./skills/dispatch_task.sh <agent> <task_id> "<描述>" [priority]

HQ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="${HQ_DIR}/scripts/hq_task_flow.sh"

[ -f "${SCRIPT}" ] || { echo "❌ 找不到 hq_task_flow.sh"; exit 1; }
bash "${SCRIPT}" task "$@"
