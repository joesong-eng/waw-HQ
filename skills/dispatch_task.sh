#!/bin/bash
# 技能：dispatch_task — 從 HQ 派工給 Agent (.taskflow)
# 用法：./skills/dispatch_task.sh <agent> <task_id> "<描述>" [priority]
HQ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="${HQ_DIR}/dev_tools/waw_ops.sh"
if [ ! -f "${SCRIPT}" ]; then
  echo "❌ 找不到 waw_ops.sh"
  exit 1
fi
bash "${SCRIPT}" task "$@"
