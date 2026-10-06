#!/usr/bin/env bash
# ==============================================================================
# WaW Agent 完工標準回報工具 (waw-report v1.0)
# 自動上下文感測 Agent 身份、標準交卷、即時觸發 Redis 事件喚醒 HQ
# ==============================================================================
set -eo pipefail

REPORT_FILE="$1"
AGENT_OVERRIDE="$2"

print_help() {
    cat << HELP
================================================================================
  📬 WaW Agent 標準交卷工具 (waw-report)
================================================================================
用法:
  waw-report <report_file.md> [agent_name]

說明:
  當 Agent 完成工單任務後，執行此指令交卷。
  系統會自動感測你當前的目錄識別 Agent 身分，將報告投遞至 outbox，
  並透過 Redis 事件秒級喚醒 HQ 總指揮進行驗收！
================================================================================
HELP
}

if [ -z "${REPORT_FILE}" ] || [ "${REPORT_FILE}" = "-h" ] || [ "${REPORT_FILE}" = "--help" ]; then
    print_help
    exit 0
fi

if [ ! -f "${REPORT_FILE}" ]; then
    echo "❌ 找不到回報檔案: ${REPORT_FILE}"
    exit 1
fi

# 自動上下文感測 Agent 身份
detect_agent() {
    if [ -n "${AGENT_OVERRIDE}" ]; then
        echo "${AGENT_OVERRIDE}" | tr '[:upper:]' '[:lower:]'
        return
    fi

    local cwd="$(pwd)"
    case "${cwd}" in
        */PROJECT/Sophie*|*/PROJECT/Owner*|*/wawOwner*) echo "owner" ;;
        */PROJECT/Member*|*/PROJECT/Mina*|*/Member*) echo "member" ;;
        */PROJECT/Infra*|*/PROJECT/Ina*|*/tg25-infra*) echo "infra" ;;
        */PROJECT/Alliance*|*/PROJECT/Allie*|*/Alliance*) echo "alliance" ;;
        */PROJECT/iHub*|*/PROJECT/Hubie*|*/iHub*) echo "ihub" ;;
        */PROJECT/SignalHub*|*/PROJECT/Sidney*|*/SignalHub*) echo "signalhub" ;;
        */PROJECT/IOTkiosk_v0*|*/PROJECT/Fio*) echo "fio" ;;
        */PROJECT/IOTwawS3*|*/PROJECT/Coli*) echo "coli" ;;
        */WaW/shannie*|*/shannie*) echo "shannie" ;;
        /home/ubuntu) echo "nana" ;;
        */WaW*) echo "hq" ;;
        *) echo "nana" ;;
    esac
}

AGENT="$(detect_agent)"
DEV_TOOLS_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "${DEV_TOOLS_DIR}/.." && pwd)"
TASKFLOW_DIR="${ROOT_DIR}/.taskflow"
OUTBOX_DIR="${TASKFLOW_DIR}/${AGENT}/outbox"
INBOX_DIR="${TASKFLOW_DIR}/${AGENT}/inbox"

mkdir -p "${OUTBOX_DIR}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BASE_NAME=$(basename "${REPORT_FILE}")

# 若檔案名稱本身不帶時間戳，則補上前綴
if [[ "${BASE_NAME}" =~ ^[0-9]{8}_[0-9]{6}_ ]]; then
    FINAL_NAME="${BASE_NAME}"
else
    FINAL_NAME="${TIMESTAMP}_${BASE_NAME}"
fi

TARGET_PATH="${OUTBOX_DIR}/${FINAL_NAME}"
cp "${REPORT_FILE}" "${TARGET_PATH}"

echo "================================================================================"
echo " 📬 [WaW Taskflow 交卷回報] 執行者: ${AGENT}"
echo "================================================================================"
echo "✅ 回報檔案已交付: ${TARGET_PATH}"

# 檢查是否能關聯 inbox 工單並進行提示
TASK_ID=$(echo "${BASE_NAME}" | sed -E 's/^[0-9]{8}_[0-9]{6}_//; s/_REPORT\.md$//; s/\.md$//')
if [ -d "${INBOX_DIR}" ]; then
    INBOX_MATCH=$(find "${INBOX_DIR}" -name "*${TASK_ID}*.md" 2>/dev/null | head -n 1 || true)
    if [ -n "${INBOX_MATCH}" ]; then
        echo "📄 關聯 inbox 待辦工單: $(basename "${INBOX_MATCH}")"
    fi
fi

# 透過 Redis 發送即時通知喚醒 HQ
if [ -f "${ROOT_DIR}/dev_tools/taskflow_notify.sh" ]; then
    bash "${ROOT_DIR}/dev_tools/taskflow_notify.sh" response "${AGENT}" "${FINAL_NAME}"
fi

echo "🎉 [回報完成] 已成功送達並即時喚醒 HQ 總指揮進行驗收！"
echo "================================================================================"
