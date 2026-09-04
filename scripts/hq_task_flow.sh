#!/bin/bash
# HQ 派工腳本 — .taskflow 版本
# 用法：./scripts/hq_task_flow.sh task <agent> <task_id> "<描述>" [priority] 
# 寫入到 .taskflow/<agent>/inbox/，使用 Markdown 格式

set -e

HQ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TASK_LOG="${HQ_DIR}/.taskflow/task_flow.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${TASK_LOG}"
}

agent_to_lower() {
    local agent="$1"
    local agent_lower="$(echo "${agent}" | tr '[:upper:]' '[:lower:]')"
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

send_task() {
    local agent="$1"
    local task_id="$2"
    local description="$3"
    local priority="${4:-normal}"
    local agent_lower=$(agent_to_lower "${agent}")

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local inbox_dir="${HQ_DIR}/.taskflow/${agent_lower}/inbox"
    mkdir -p "${inbox_dir}"

    local task_file="${inbox_dir}/${timestamp}_${task_id}.md"
    
    cat > "${task_file}" <<MARKDOWN
# 任務：${task_id}

**派發時間**：$(date '+%Y-%m-%d %H:%M')  
**優先級**：${priority}  
**負責人**：${agent}

---

## 📋 任務內容

${description}

---

## 📝 回報格式

\`\`\`markdown
# 任務回報：${task_id}

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：${agent}

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：${agent}  
**回報時間**：YYYY-MM-DD HH:MM
\`\`\`

---

**派發者**：HQ  
**派發時間**：$(date '+%Y-%m-%d %H:%M')
MARKDOWN

    log "✅ 任務已派發：${agent} (${agent_lower}) → ${task_file}"
}

case "$1" in
    task)
        if [ $# -lt 4 ]; then
            echo "用法：$0 task <agent> <task_id> <描述> [priority]"
            exit 1
        fi
        send_task "$2" "$3" "$4" "$5"
        ;;
    *)
        echo "未知命令：$1"
        echo "用法：$0 task <agent> <task_id> <描述> [priority]"
        exit 1
        ;;
esac
