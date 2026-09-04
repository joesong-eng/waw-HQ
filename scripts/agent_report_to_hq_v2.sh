#!/bin/bash
# Agent 回報給 HQ — .taskflow 版本
# 用法：bash ../../scripts/agent_report_to_hq_v2.sh <agent_name> <report_file.md>
# 寫入到 .taskflow/<agent>/outbox/

AGENT_NAME="${1}"
REPORT_FILE="${2}"

if [ -z "${AGENT_NAME}" ]; then
    echo "❌ 請提供 Agent 名稱"; exit 1
fi
if [ -z "${REPORT_FILE}" ] || [ ! -f "${REPORT_FILE}" ]; then
    echo "❌ 找不到回報檔案: ${REPORT_FILE}"; exit 1
fi

# Agent 名稱轉小寫路徑
agent_to_lower() {
    local agent_lower="$(echo "${1}" | tr '[:upper:]' '[:lower:]')"
    case "${agent_lower}" in
        sophie) echo "owner";;
        mina) echo "member";;
        ina) echo "infra";;
        allie) echo "alliance";;
        hubie) echo "ihub";;
        fio) echo "fio";;
        coli) echo "coli";;
        *) echo "${agent_lower}";;
    esac
}

# 自動找 HQ .taskflow 目錄
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HQ_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
AGENT_LOWER=$(agent_to_lower "${AGENT_NAME}")
OUTBOX_DIR="${HQ_DIR}/.taskflow/${AGENT_LOWER}/outbox"

mkdir -p "${OUTBOX_DIR}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEST="${OUTBOX_DIR}/${TIMESTAMP}_${AGENT_NAME}.md"

cp "${REPORT_FILE}" "${DEST}"
echo "✅ ${AGENT_NAME} 回報已送達 HQ"
echo "   → ${DEST}"
