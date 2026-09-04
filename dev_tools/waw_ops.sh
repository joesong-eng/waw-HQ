#!/usr/bin/env bash
set -eo pipefail

DEV_TOOLS_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "${DEV_TOOLS_DIR}/.." && pwd)"
TASKFLOW_DIR="${ROOT_DIR}/.taskflow"
LOG_FILE="${TASKFLOW_DIR}/task_flow.log"

agent_to_module() {
    local name="$(echo "$1" | tr '[:upper:]' '[:lower:]')"
    case "${name}" in
        sophie|owner) echo "owner";;
        mina|member) echo "member";;
        ina|infra) echo "infra";;
        allie|alliance) echo "alliance";;
        hubie|ihub) echo "ihub";;
        fio|kiosk|iotkiosk_v0) echo "fio";;
        coli|waws3|iotwaws3) echo "coli";;
         sidney|signalhub|signal) echo "signalhub";;
        *) echo "${name}";;
    esac
}

get_agent_server_info() {
    local module="$1"
    case "${module}" in
        member)
            echo "129.146.103.177 39022 /www/wwwroot/win.tg25.win laravel reverb"
            ;;
        owner)
            echo "129.153.116.174 39022 /www/wwwroot/iot.tg25.win laravel none"
            ;;
        alliance)
            echo "137.131.50.16 39022 /www/wwwroot/ali.tg25.win laravel none"
            ;;
        infra)
            echo "141.148.165.50 39022 /home/ubuntu/tg25-infra python mqtt-listener"
            ;;
        ihub)
            echo "129.146.103.177 39022 /www/wwwroot/ihub.tg25.win node none"
            ;;
         signalhub)
             echo "129.153.116.174 39022 /www/wwwroot/signal.tg25.win laravel none"
             ;;
        *)
            echo "none"
            ;;
    esac
}

print_help() {
    echo "WaW 開發與協作總控工具 (WaW Ops)"
    echo ""
    echo "用法:"
    echo "  ./dev_tools/waw_ops.sh <command> [arguments...]"
    echo ""
    echo "指令:"
    echo "  status                檢視所有 Agent 的 Inbox 與 Outbox 即時狀態"
    echo "  report <agent>        讀取指定 Agent 的最新回報內容"
    echo "  log                   檢視派工系統最近日誌"
    echo "  task <agent> <task_id> \"<desc>\" [prio]  派發標準任務到指定 Agent 的 Inbox"
    echo "  deploy <agent>        執行指定 Agent 的遠端 VPS 標準部署"
    echo "  remote <agent> \"<cmd>\"在指定 Agent 的遠端 VPS 執行指令"
    echo ""
}

cmd_status() {
    echo "============================================================"
    echo " 📊 WaW Agent 任務流與信箱即時狀態 (.taskflow)"
    echo "============================================================"
    local agents=("owner" "member" "infra" "alliance" "ihub" "fio" "coli" "signalhub")
    for agent in "${agents[@]}"; do
        local in_count=$(find "${TASKFLOW_DIR}/${agent}/inbox" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        local out_count=$(find "${TASKFLOW_DIR}/${agent}/outbox" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        
        printf "🔹 %-10s | Inbox (待處理): %-3s | Outbox (已回報): %-3s" "${agent}" "${in_count}" "${out_count}"
        
        if [ "${out_count}" -gt 0 ]; then
            local latest_out=$(ls -t "${TASKFLOW_DIR}/${agent}/outbox"/*.md 2>/dev/null | head -n 1)
            local filename=$(basename "${latest_out}")
            printf " [最新: %s]" "${filename}"
        fi
        echo ""
    done
    echo "============================================================"
}

cmd_report() {
    local target="$1"
    if [ -z "${target}" ]; then
        echo "❌ 請指定 Agent 名稱，例如: ./dev_tools/waw_ops.sh report mina"; exit 1
    fi
    local mod=$(agent_to_module "${target}")
    local latest=$(ls -t "${TASKFLOW_DIR}/${mod}/outbox"/*.md 2>/dev/null | head -n 1)
    if [ -z "${latest}" ] || [ ! -f "${latest}" ]; then
        echo "⚠️ ${target} (${mod}) 目前沒有回報檔案。"
        exit 0
    fi
    echo "============================================================"
    echo "📄 ${target} (${mod}) 最新回報: $(basename "${latest}")"
    echo "============================================================"
    cat "${latest}"
}

cmd_task() {
    local target="$1"
    local task_id="$2"
    local desc="$3"
    local prio="${4:-normal}"
    
    if [ -z "${target}" ] || [ -z "${task_id}" ] || [ -z "${desc}" ]; then
        echo "❌ 參數不足！用法: ./dev_tools/waw_ops.sh task <agent> <task_id> \"<描述>\" [priority]"
        exit 1
    fi
    "${DEV_TOOLS_DIR}/hq_task_flow.sh" task "${target}" "${task_id}" "${desc}" "${prio}"
}

cmd_deploy() {
    local target="$1"
    if [ -z "${target}" ]; then
        echo "❌ 請指定 Agent 名稱，例如: ./dev_tools/waw_ops.sh deploy mina"; exit 1
    fi
    local mod=$(agent_to_module "${target}")
    local info=$(get_agent_server_info "${mod}")
    
    if [ "${info}" = "none" ]; then
        echo "❌ Agent ${target} (${mod}) 無遠端部署伺服器配置（或屬於純韌體/硬體專案）。"
        exit 1
    fi

    read -r host port path type service <<< "${info}"

    echo "🚀 開始執行 ${target} (${mod}) 遠端部署..."
    echo "   目標伺服器: ${host}:${port}"
    echo "   目標路徑:   ${path}"
    echo "   專案架構:   ${type}"

    case "${type}" in
        laravel)
            local deploy_cmd="cd ${path} && git pull origin main && pnpm install && pnpm build && php artisan migrate --force && php artisan view:clear && php artisan config:cache && php artisan cache:clear"
            if [ "${service}" != "none" ]; then
                deploy_cmd="${deploy_cmd} && sudo systemctl restart ${service}"
            fi
            echo "📡 執行 SSH 指令..."
            ssh -o RequestTTY=no -p "${port}" "ubuntu@${host}" "${deploy_cmd}"
            ;;
        python)
            local deploy_cmd="cd ${path} && git pull origin main && pip install -r requirements.txt"
            if [ "${service}" != "none" ]; then
                deploy_cmd="${deploy_cmd} && sudo systemctl restart ${service}"
            fi
            echo "📡 執行 SSH 指令..."
            ssh -o RequestTTY=no -p "${port}" "ubuntu@${host}" "${deploy_cmd}"
            ;;
        node)
            local deploy_cmd="cd ${path} && git pull origin main && npm install && npm run build"
            echo "📡 執行 SSH 指令..."
            ssh -o RequestTTY=no -p "${port}" "ubuntu@${host}" "${deploy_cmd}"
            ;;
    esac

    echo "✅ ${target} (${mod}) 部署完成！"
}

cmd_remote() {
    local target="$1"
    local command="$2"
    if [ -z "${target}" ] || [ -z "${command}" ]; then
        echo "❌ 參數不足！用法: ./dev_tools/waw_ops.sh remote <agent> \"<指令>\""
        exit 1
    fi
    local mod=$(agent_to_module "${target}")
    local info=$(get_agent_server_info "${mod}")
    if [ "${info}" = "none" ]; then
        echo "❌ Agent ${target} (${mod}) 無遠端伺服器配置。"; exit 1
    fi
    read -r host port path type service <<< "${info}"
    echo "📡 在 ${host} (${path}) 執行: ${command}"
    ssh -o RequestTTY=no -p "${port}" "ubuntu@${host}" "cd ${path} && ${command}"
}

case "$1" in
    status) cmd_status ;;
    report) cmd_report "$2" ;;
    task) cmd_task "$2" "$3" "$4" "$5" ;;
    deploy) cmd_deploy "$2" ;;
    remote) cmd_remote "$2" "$3" ;;
    log) tail -n 30 "${LOG_FILE}" ;;
    *) print_help ;;
esac

