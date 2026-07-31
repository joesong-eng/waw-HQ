#!/bin/bash
# HQ 主動任務流程管理腳本 (Fixed Version)
# 支援：諮詢 → 補充 → 任務 → 審核 → 重做
# 擴充：--watch 動態哨兵監控

set -e

HQ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTBOX="${HQ_DIR}/_agent/outbox"
INBOX="${HQ_DIR}/_agent/inbox"
TASK_LOG="${HQ_DIR}/_agent/task_flow.log"
WATCHDOG_SCRIPT="${HQ_DIR}/scripts/hq_watchdog.sh"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${TASK_LOG}"
}

start_watchdog() {
    local agent="$1"
    local id="$2"
    if [ -x "$WATCHDOG_SCRIPT" ]; then
        log "🛡️ 自動掛載哨兵監控任務 [$id]..."
        nohup "$WATCHDOG_SCRIPT" "$agent" "$id" 300 24 >/dev/null 2>&1 &
    fi
}

init_context_store() {
    local task_id="$1"; local agent="$2"; local description="$3"
    if ! command -v redis-cli >/dev/null 2>&1 || ! redis-cli ping >/dev/null 2>&1; then return; fi
    local key="hq:thread:${task_id}"
    redis-cli SET "${key}:status" "pending" >/dev/null
    redis-cli SET "${key}:agent" "${agent}" >/dev/null
    redis-cli SET "${key}:description" "${description}" >/dev/null
    log "🧠 context store 初始化: ${key}"
}

publish_redis() {
    local agent="$1"; local type="$2"; local file="$3"
    if command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1; then
        redis-cli PUBLISH "agent/${agent}/${type}" "$(cat "${file}")" >/dev/null
        log "📡 Redis 推送 ${agent}: ${type}"
    fi
}

send_task() {
    local agent="$1"; local task_id="$2"; local description="$3"; local priority="${4:-normal}"; local watch="$5"
    local agent_cap="$(echo "${agent:0:1}" | tr '[:lower:]' '[:upper:]')${agent:1}"
    local outbox_file="${OUTBOX}/to_${agent_cap}.json"
    cat > "${outbox_file}" << EOJSON
{"type": "task", "task_id": "${task_id}", "to_agent": "${agent_cap}", "priority": "${priority}", "description": "${description}"}
EOJSON
    log "📤 發送任務給 ${agent}: ${task_id}"
    init_context_store "${task_id}" "${agent}" "${description}"
    publish_redis "${agent}" "task" "${outbox_file}"
    if [ "$watch" = "--watch" ]; then start_watchdog "$agent" "$task_id"; fi
}

# 主程式簡化解析
COMMAND=$1; shift
case "$COMMAND" in
    task)
        # 參數: agent task_id description [priority] [--watch]
        AGENT=$1; TID=$2; DESC=$3; PRIO=${4:-normal}; WATCH=$5
        if [ "$PRIO" = "--watch" ]; then WATCH="--watch"; PRIO="normal"; fi
        send_task "$AGENT" "$TID" "$DESC" "$PRIO" "$WATCH"
        ;;
    *)
        echo "Usage: $0 {task} <args> [--watch]"
        exit 1
        ;;
esac
