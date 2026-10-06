#!/bin/bash
# ==============================================================================
# Agent 回報給 HQ (Taskflow v5.1)
# 用法：./dev_tools/agent_report_to_hq_v2.sh <agent_name> <report_file.md>
# ==============================================================================
set -e

AGENT_NAME="${1}"
REPORT_FILE="${2}"

if [ -z "${AGENT_NAME}" ]; then
    echo "❌ 請提供 Agent 名稱，例如: sophie"; exit 1
fi
if [ -z "${REPORT_FILE}" ] || [ ! -f "${REPORT_FILE}" ]; then
    echo "❌ 找不到回報檔案: ${REPORT_FILE}"; exit 1
fi

agent_to_lower() {
    local agent_lower="$(echo "${1}" | tr '[:upper:]' '[:lower:]')"
    case "${agent_lower}" in
        sophie|owner) echo "owner";;
        mina|member) echo "member";;
        ina|infra) echo "infra";;
        allie|alliance) echo "alliance";;
        hubie|ihub) echo "ihub";;
        fio|kiosk) echo "fio";;
        coli|waws3) echo "coli";;
        sidney|signalhub) echo "signalhub";;
        *) echo "${agent_lower}";;
    esac
}

REAL_SCRIPT="$(readlink -f "$0" 2>/dev/null || realpath "$0" 2>/dev/null || echo "$0")"
SCRIPT_DIR="$(cd -P "$(dirname "${REAL_SCRIPT}")" && pwd)"
HQ_DIR="$(cd -P "${SCRIPT_DIR}/.." && pwd)"
AGENT_LOWER=$(agent_to_lower "${AGENT_NAME}")
OUTBOX_DIR="${HQ_DIR}/.taskflow/${AGENT_LOWER}/outbox"

mkdir -p "${OUTBOX_DIR}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BASE_REPORT_NAME=$(basename "${REPORT_FILE}")

# 若檔案名稱本身不帶時間戳，則補上前綴，並保留原報告檔名（包含 TASK_ID）
if [[ "${BASE_REPORT_NAME}" =~ ^[0-9]{8}_[0-9]{6}_ ]]; then
    DEST="${OUTBOX_DIR}/${BASE_REPORT_NAME}"
else
    DEST="${OUTBOX_DIR}/${TIMESTAMP}_${BASE_REPORT_NAME}"
fi

cp "${REPORT_FILE}" "${DEST}"
echo "✅ ${AGENT_NAME} (${AGENT_LOWER}) 回報已送達 HQ"
echo "   → ${DEST}"

# Redis notify hook (含容錯降級機制)
if [ -f "${HQ_DIR}/dev_tools/taskflow_notify.sh" ]; then
    bash "${HQ_DIR}/dev_tools/taskflow_notify.sh" response "${AGENT_LOWER}" "${BASE_REPORT_NAME}" || true
fi
