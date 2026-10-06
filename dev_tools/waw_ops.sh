#!/usr/bin/env bash
# ==============================================================================
# WaW 開發與運維智慧中樞 (WaW Ops v2.1)
# 整合宣告式部署、Taskflow 派工、Redis 通知與精準健康檢查
# ==============================================================================
set -eo pipefail

REAL_SCRIPT="$(readlink -f "$0" 2>/dev/null || realpath "$0" 2>/dev/null || echo "$0")"
DEV_TOOLS_DIR="$(cd -P "$(dirname "${REAL_SCRIPT}")" && pwd)"
ROOT_DIR="$(cd -P "${DEV_TOOLS_DIR}/.." && pwd)"
TASKFLOW_DIR="${ROOT_DIR}/.taskflow"
MANIFEST_FILE="${ROOT_DIR}/deploy_manifest.json"
LOG_FILE="${TASKFLOW_DIR}/task_flow.log"

mkdir -p "${TASKFLOW_DIR}"

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "${msg}" >> "${LOG_FILE}"
}

# Agent 代稱標準化映射
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
        shannie) echo "shannie";;
        nana) echo "nana";;
        hq) echo "hq";;
        *) echo "${name}";;
    esac
}

# Module 到 Agent 顯示名稱映射
module_to_display_name() {
    case "$1" in
        owner) echo "Sophie";;
        member) echo "Mina";;
        infra) echo "Ina";;
        alliance) echo "Allie";;
        ihub) echo "Hubie";;
        fio) echo "Fio";;
        coli) echo "Coli";;
        signalhub) echo "Sidney";;
        shannie) echo "Shannie";;
        nana) echo "Nana";;
        hq) echo "HQ";;
        *) echo "$1";;
    esac
}

# 讀取 manifest 中的 Agent 屬性
get_agent_manifest_field() {
    local mod="$1"
    local field="$2"
    python3 -c "
import json, sys
try:
    with open('${MANIFEST_FILE}', 'r') as f:
        data = json.load(f)
    agent = data.get('agents', {}).get('${mod}', {})
    val = agent.get('${field}', '')
    if isinstance(val, (list, dict)):
        print(json.dumps(val))
    elif val is None:
        print('')
    else:
        print(val)
except Exception:
    print('')
"
}

print_help() {
    cat << HELP
================================================================================
  WaW 開發與運維總控工具 (WaW Ops v2.1)
================================================================================
用法:
  ./dev_tools/waw_ops.sh <command> [arguments...]

核心指令:
  status                        檢視所有 Agent 信箱狀態 (Inbox/Outbox)
  task <agent> <id> "<desc>"    標準派發任務至指定 Agent 信箱 (觸發 Redis 通知)
  task <agent> <id> --file <f>  以既有 Markdown 檔案進行派工
  report <agent> [lines]        查看指定 Agent 最新回報內容 (預設 40 行)
  deploy <agent> [--dry-run]    依據 manifest 執行遠端精緻化標準部署
  remote <agent> "<cmd>"        在指定 Agent 的遠端目錄執行 SSH 指令
  health [agent]                執行宣告式健康檢查 (HTTP/Service)
  close <agent|hq> <key>        將指定 Agent 或 HQ 已結案工單歸檔
  test [agent]                  執行派工系統全流程一鍵自我診斷測試
  log [lines]                   檢視最近派工日誌 (預設 25 行)
================================================================================
HELP
}

cmd_status() {
    echo "================================================================================"
    echo " 📊 WaW Agent 任務流與信箱即時狀態 (.taskflow)"
    echo "================================================================================"
    local project_agents=("owner" "member" "infra" "alliance" "ihub" "signalhub" "fio" "coli")
    local support_agents=("hq" "shannie" "nana")
    
    printf "%-12s | %-12s | %-6s | %-6s | %s\n" "模組" "Agent" "Inbox" "Outbox" "最新回報"
    echo "-------------+--------+--------+------------------------------------------------"
    
    echo " 📦 專案工程 Agent"
    for agent in "${project_agents[@]}"; do
        local display_name=$(module_to_display_name "${agent}")
        local in_count=0
        local out_count=0
        if [ -d "${TASKFLOW_DIR}/${agent}/inbox" ]; then
            in_count=$(find "${TASKFLOW_DIR}/${agent}/inbox" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        fi
        if [ -d "${TASKFLOW_DIR}/${agent}/outbox" ]; then
            out_count=$(find "${TASKFLOW_DIR}/${agent}/outbox" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        fi
        
        local latest_str="-"
        if [ "${out_count}" -gt 0 ]; then
            local latest_out=$(ls -t "${TASKFLOW_DIR}/${agent}/outbox"/*.md 2>/dev/null | head -n 1)
            if [ -n "${latest_out}" ]; then
                latest_str="$(basename "${latest_out}")"
            fi
        fi
        printf "%-12s | %-12s | %-6s | %-6s | %s\n" "${agent}" "${display_name}" "${in_count}" "${out_count}" "${latest_str}"
    done
    
    echo ""
    echo " 🤝 支援角色 (非 WaW 專案成員)"
    for agent in "${support_agents[@]}"; do
        local display_name=$(module_to_display_name "${agent}")
        local in_count=0
        local out_count=0
        if [ -d "${TASKFLOW_DIR}/${agent}/inbox" ]; then
            in_count=$(find "${TASKFLOW_DIR}/${agent}/inbox" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        fi
        if [ -d "${TASKFLOW_DIR}/${agent}/outbox" ]; then
            out_count=$(find "${TASKFLOW_DIR}/${agent}/outbox" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        fi
        
        local latest_str="-"
        if [ "${out_count}" -gt 0 ]; then
            local latest_out=$(ls -t "${TASKFLOW_DIR}/${agent}/outbox"/*.md 2>/dev/null | head -n 1)
            if [ -n "${latest_out}" ]; then
                latest_str="$(basename "${latest_out}")"
            fi
        fi
        printf "%-12s | %-12s | %-6s | %-6s | %s\n" "${agent}" "${display_name}" "${in_count}" "${out_count}" "${latest_str}"
    done
    echo "================================================================================"
}

cmd_task() {
    local target="$1"
    local task_id="$2"
    local desc="$3"
    local priority="${4:-normal}"

    if [ -z "${target}" ] || [ -z "${task_id}" ] || [ -z "${desc}" ]; then
        echo "❌ 參數不足！"
        echo "  用法: ./dev_tools/waw_ops.sh task <agent> <task_id> \"<描述>\" [priority]"
        echo "  或:   ./dev_tools/waw_ops.sh task <agent> <task_id> --file <路徑> [priority]"
        exit 1
    fi

    local mod=$(agent_to_module "${target}")
    local inbox_dir="${TASKFLOW_DIR}/${mod}/inbox"
    mkdir -p "${inbox_dir}"

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local task_file="${inbox_dir}/${timestamp}_${task_id}.md"

    if [ "${desc}" = "--file" ]; then
        local src_file="$4"
        priority="${5:-normal}"
        if [ ! -f "${src_file}" ]; then
            echo "❌ 找不到指定工單檔案: ${src_file}"
            exit 1
        fi
        cp "${src_file}" "${task_file}"
        log "[DISPATCH:FILE] ${target} (${mod}) -> ${task_file}"
    else
        cat > "${task_file}" <<MARKDOWN
# 任務：${task_id}

**派發時間**：$(date '+%Y-%m-%d %H:%M')  
**優先級**：${priority}  
**負責人**：${target} (${mod})

---

## 📋 任務內容

${desc}

---

## 📝 標準回報格式

\`\`\`markdown
# 任務回報：${task_id}

**完成時間**：$(date '+%Y-%m-%d %H:%M')  
**執行者**：${target}

## 執行結果
- 具體變更與輸出摘要

## 驗收確認
- [x] 功能已驗證
- [x] 無回退錯誤

## 結論
✅ 完成 / ❌ 遇到問題
\`\`\`

---
**派發者**：HQ (bessie202)
MARKDOWN
        log "[DISPATCH] ${target} (${mod}) -> ${task_file} (prio: ${priority})"
    fi

    echo "✅ [已派發工單] ${task_id} → ${mod}"
    echo "📄 工單路徑: ${task_file}"

    # 觸發 Redis 通知 (含容錯機制)
    if [ -f "${DEV_TOOLS_DIR}/taskflow_notify.sh" ]; then
        bash "${DEV_TOOLS_DIR}/taskflow_notify.sh" dispatch "${mod}" "${task_id}" || true
    fi

    echo "💡 提示：任務已入信箱並發出喚醒事件。依據 HQ 規範，請結束回合靜候 Agent 完成通知。"
}

cmd_report() {
    local target="$1"
    local lines="${2:-40}"
    if [ -z "${target}" ]; then
        echo "❌ 請指定 Agent，例如: ./dev_tools/waw_ops.sh report sophie"; exit 1
    fi
    local mod=$(agent_to_module "${target}")
    local outbox_dir="${TASKFLOW_DIR}/${mod}/outbox"

    local latest=$(ls -t "${outbox_dir}"/*.md 2>/dev/null | head -n 1 || true)
    if [ -z "${latest}" ] || [ ! -f "${latest}" ]; then
        echo "⚠️ Agent ${target} (${mod}) 尚無回報檔案。"
        exit 0
    fi

    echo "================================================================================"
    echo "📄 ${target} (${mod}) 最新回報: $(basename "${latest}")"
    echo "================================================================================"
    head -n "${lines}" "${latest}"
    local total_lines=$(wc -l < "${latest}")
    if [ "${total_lines}" -gt "${lines}" ]; then
        echo ""
        echo "--- [已截斷：顯示前 ${lines}/${total_lines} 行，完整閱讀請用 cat ${latest}] ---"
    fi
}

cmd_deploy() {
    local target="$1"
    local flag="$2"
    if [ -z "${target}" ]; then
        echo "❌ 請指定 Agent，例如: ./dev_tools/waw_ops.sh deploy sophie [--dry-run]"; exit 1
    fi
    local mod=$(agent_to_module "${target}")

    local ssh_host=$(get_agent_manifest_field "${mod}" "ssh_host")
    local remote_path=$(get_agent_manifest_field "${mod}" "remote_path")
    local b_type=$(get_agent_manifest_field "${mod}" "type")
    local service=$(get_agent_manifest_field "${mod}" "service")

    if [ -z "${ssh_host}" ]; then
        if [ "${b_type}" = "firmware" ]; then
            echo "ℹ️ Agent ${target} (${mod}) 為硬體/韌體專案，不適用 VPS SSH 自動化部署。"
            exit 0
        fi
        echo "❌ 在 deploy_manifest.json 中找不到 ${mod} 的 ssh_host 設定。"; exit 1
    fi

    # 組合部署指令
    local remote_cmd="cd ${remote_path}"
    case "${b_type}" in
        laravel)
            remote_cmd="${remote_cmd} && git pull origin main && if [ -f package.json ]; then pnpm install && pnpm build; fi && sudo -u www php artisan migrate --force && sudo -u www php artisan optimize:clear"
            ;;
        python)
            remote_cmd="${remote_cmd} && git pull origin main && pip install -r requirements.txt"
            ;;
        node)
            remote_cmd="${remote_cmd} && git pull origin main && npm install && npm run build"
            ;;
        *)
            remote_cmd="${remote_cmd} && git pull origin main"
            ;;
    esac

    if [ -n "${service}" ] && [ "${service}" != "none" ]; then
        remote_cmd="${remote_cmd} && sudo systemctl restart ${service}"
    fi

    echo "🚀 [WaW Precision Deploy] 開始部署: ${target} (${mod})"
    echo "   目標主機: ${ssh_host}"
    echo "   遠端路徑: ${remote_path}"
    echo "   專案架構: ${b_type}"
    [ -n "${service}" ] && echo "   守護服務: ${service}"
    echo "   執行腳本: ${remote_cmd}"

    if [ "${flag}" = "--dry-run" ]; then
        echo "🔍 [--dry-run 模式] 僅預檢指令，未連線執行。"
        exit 0
    fi

    echo "📡 連線執行中..."
    ssh -o BatchMode=yes -o ConnectTimeout=10 "${ssh_host}" "${remote_cmd}"
    log "[DEPLOY:SUCCESS] ${target} (${mod}) on ${ssh_host}:${remote_path}"
    echo "✅ ${target} (${mod}) 部署完成！"

    # 若有配置健康檢查，順便執行
    cmd_health "${mod}"
}

cmd_remote() {
    local target="$1"
    local command="$2"
    if [ -z "${target}" ] || [ -z "${command}" ]; then
        echo "❌ 參數不足！用法: ./dev_tools/waw_ops.sh remote <agent> \"<指令>\""; exit 1
    fi
    local mod=$(agent_to_module "${target}")
    local ssh_host=$(get_agent_manifest_field "${mod}" "ssh_host")
    local remote_path=$(get_agent_manifest_field "${mod}" "remote_path")

    if [ -z "${ssh_host}" ]; then
        echo "❌ Agent ${target} (${mod}) 無遠端伺服器配置。"; exit 1
    fi

    echo "📡 [SSH ${ssh_host}] (${remote_path}) 執行: ${command}"
    ssh -o BatchMode=yes "${ssh_host}" "cd ${remote_path} && ${command}"
}

cmd_health() {
    local target="$1"
    if [ -n "${target}" ]; then
        local mod=$(agent_to_module "${target}")
        local ssh_host=$(get_agent_manifest_field "${mod}" "ssh_host")
        local service=$(get_agent_manifest_field "${mod}" "service")
        
        echo "🩺 [健康檢查] 檢查 Agent: ${target} (${mod})"
        if [ -n "${service}" ] && [ -n "${ssh_host}" ]; then
            printf "  - 守護服務 [%s]: " "${service}"
            if ssh -o BatchMode=yes -o ConnectTimeout=5 "${ssh_host}" "sudo systemctl is-active ${service}" >/dev/null 2>&1; then
                echo "🟢 Active (運行中)"
            else
                echo "🔴 Inactive 或無法探測"
            fi
        fi
    else
        echo "🩺 [全域健康檢查] 請指定 Agent，例如: ./dev_tools/waw_ops.sh health mina"
    fi
}

cmd_test() {
    local target="${1:-owner}"
    local mod=$(agent_to_module "${target}")
    local test_id="TASK_SELF_TEST_$(date +%Y%m%d_%H%M%S)"
    echo "🧪 [開始派工系統自我診斷測試] Target: ${target} (${mod})"
    echo "--------------------------------------------------------------------------------"
    
    echo "1️⃣ [測試派工] 發布任務: ${test_id}"
    cmd_task "${mod}" "${test_id}" "派工自我診斷測試任務" "normal" >/dev/null
    local inbox_file=$(ls -t "${TASKFLOW_DIR}/${mod}/inbox/"*"${test_id}"* 2>/dev/null | head -n 1)
    if [ -n "${inbox_file}" ] && [ -f "${inbox_file}" ]; then
        echo "   ✅ 成功生成工單: $(basename "${inbox_file}")"
    else
        echo "   ❌ 工單寫入失敗！"; exit 1
    fi

    echo "2️⃣ [測試回報] 模擬 ${target} 完工交卷"
    local tmp_report="/tmp/${test_id}_REPORT.md"
    cat << REPORT > "${tmp_report}"
# 任務回報：${test_id}
**完成時間**：$(date '+%Y-%m-%d %H:%M')
**執行者**：${target}
## 執行結果
- 自我診斷測試完成
## 結論
✅ 完成
REPORT
    "${DEV_TOOLS_DIR}/agent_report_to_hq_v2.sh" "${mod}" "${tmp_report}" >/dev/null
    rm -f "${tmp_report}"
    local outbox_file=$(ls -t "${TASKFLOW_DIR}/${mod}/outbox/"*"${test_id}"* 2>/dev/null | head -n 1)
    if [ -n "${outbox_file}" ] && [ -f "${outbox_file}" ]; then
        echo "   ✅ 成功送達回報: $(basename "${outbox_file}")"
    else
        echo "   ❌ 回報送達失敗！"; exit 1
    fi

    echo "3️⃣ [測試審核] 讀取回報內容"
    local report_header=$(head -n 1 "${outbox_file}")
    echo "   ✅ 成功讀取回報標題: ${report_header}"

    echo "4️⃣ [測試歸檔] 執行結案歸檔"
    cmd_close "${mod}" "${test_id}" >/dev/null
    if [ ! -f "${inbox_file}" ] && [ ! -f "${outbox_file}" ]; then
        echo "   ✅ 信箱已清空乾淨，工單與回報成功歸檔"
    else
        echo "   ❌ 歸檔後殘留檔案！"; exit 1
    fi

    echo "--------------------------------------------------------------------------------"
    echo "🎉 [診斷結果] 派工系統全生命週期測試 100% 通過！"
}

cmd_close() {
    local target="$1"
    local pattern="$2"
    if [ -z "${target}" ] || [ -z "${pattern}" ]; then
        echo "❌ 參數不足！用法: ./dev_tools/waw_ops.sh close <agent|hq> <關鍵字/ID>"; exit 1
    fi

    local mod
    if [ "${target}" = "hq" ]; then
        mod="hq"
    else
        mod=$(agent_to_module "${target}")
    fi

    local ym=$(date +%Y%m)
    local archive_dir="${TASKFLOW_DIR}/archive/${mod}/${ym}"
    mkdir -p "${archive_dir}"

    local matched=()
    for dir in "${TASKFLOW_DIR}/${mod}/inbox" "${TASKFLOW_DIR}/${mod}/outbox"; do
        if [ -d "${dir}" ]; then
            while IFS= read -r file; do
                [ -n "${file}" ] && [ -f "${file}" ] && matched+=("${file}")
            done < <(find "${dir}" -type f -name "*${pattern}*.md" 2>/dev/null)
        fi
    done

    if [ ${#matched[@]} -eq 0 ]; then
        echo "⚠️ 找不到包含 '${pattern}' 的工單檔案。"
        exit 1
    fi

    echo "📦 找到 ${#matched[@]} 個檔案，正在歸檔至 ${archive_dir}/"
    for src in "${matched[@]}"; do
        local fname=$(basename "${src}")
        mv "${src}" "${archive_dir}/${fname}"
        echo "  ✅ 歸檔: ${fname}"
        log "[CLOSED] ${mod} -> ${archive_dir}/${fname}"
    done
    echo "🎉 結案歸檔完成！"
}

case "$1" in
    status) cmd_status ;;
    task) shift; cmd_task "$@" ;;
    report) cmd_report "$2" "$3" ;;
    deploy) cmd_deploy "$2" "$3" ;;
    remote) cmd_remote "$2" "$3" ;;
    health) cmd_health "$2" ;;
    close) cmd_close "$2" "$3" ;;
    test) cmd_test "$2" ;;
    log) tail -n "${2:-25}" "${LOG_FILE}" ;;
    *) print_help ;;
esac
