#!/bin/bash

# Agent 專案初始化腳本
# 作用：為新 Agent 創建標準化專案結構與基礎能力

set -e

HQ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES_DIR="${HQ_DIR}/core/templates"

# --- 參數與預設值 ---
NEW_AGENT_NAME=""

# Redis 配置
DEFAULT_REDIS_HOST="localhost"
DEFAULT_REDIS_PORT="6379"

# --- 函數定義 ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

usage() {
    echo "用法: $0 <new_agent_name> [--redis-host <host>] [--redis-port <port>]"
    echo "  <new_agent_name>: 要創建的新 Agent 名稱 (例如: mina, sophie)"
    echo "  --redis-host: (可選) Redis 主機位址，預設為 localhost"
    echo "  --redis-port: (可選) Redis 連接埠，預設為 6379"
    exit 1
}

# 檢查必備工具
check_dependencies() {
    if ! command -v git >/dev/null 2>&1; then log "❌ Git 未安裝，請先安裝 Git"; exit 1; fi
    if ! command -v redis-cli >/dev/null 2>&1; then log "⚠️ Redis CLI 未找到，某些功能可能受限 (例如：測試連線)"; fi
    if ! command -v python3 >/dev/null 2>&1; then log "❌ Python 3 未安裝，請先安裝 Python 3"; exit 1; fi
}

# 建立目錄結構
create_directories() {
    local agent_path="$1"
    log "Creating directories for $agent_path..."
    mkdir -p "${agent_path}"
    mkdir -p "${agent_path}/.taskbox/inbox"
    mkdir -p "${agent_path}/.taskbox/outbox"
    mkdir -p "${agent_path}/.taskbox/archive"
    mkdir -p "${agent_path}/scripts"
    mkdir -p "${agent_path}/core"
    mkdir -p "${agent_path}/config"
    mkdir -p "${agent_path}/deploy"
    mkdir -p "${agent_path}/exports"
    mkdir -p "${agent_path}/tests"
}

# 複製範本檔案
copy_templates() {
    local agent_path="$1"
    local redis_host="$2"
    local redis_port="$3"

    log "Copying template files to $agent_path..."

    # AGENTS.md
    cp "${TEMPLATES_DIR}/AGENTS.md.template" "${agent_path}/AGENTS.md"
    sed -i "" "s/REPLACE_AGENT_NAME/${NEW_AGENT_NAME}/g" "${agent_path}/AGENTS.md"

    # .gitignore
    cp "${TEMPLATES_DIR}/gitignore.template" "${agent_path}/.gitignore"

    # README.md
    cp "${TEMPLATES_DIR}/README.md.template" "${agent_path}/README.md"
    sed -i "" "s/REPLACE_AGENT_NAME/${NEW_AGENT_NAME}/g" "${agent_path}/README.md"

    # Agent Listener (Redis Subscriber)
    cp "${TEMPLATES_DIR}/agent_listener.py" "${agent_path}/core/agent_listener.py"
    sed -i "" "s/AGENT_NAME = \"AGENT_NAME\"/AGENT_NAME = \"${NEW_AGENT_NAME}\"/g" "${agent_path}/core/agent_listener.py"
    # 設置 Redis 主機與埠號 (使用環境變數或預設值)
    # 這裡不直接寫死，讓 listener 讀取環境變數
    echo "# 設置 Redis 配置\nREDIS_HOST = os.environ.get('REDIS_HOST', '${redis_host}')\nREDIS_PORT = int(os.environ.get('REDIS_PORT', '${redis_port}'))" | cat - "${agent_path}/core/agent_listener.py" > temp && mv temp "${agent_path}/core/agent_listener.py"

    # Agent Reporter
    cp "${TEMPLATES_DIR}/agent_reporter.py" "${agent_path}/core/agent_reporter.py"
    sed -i "" "s/REPLACE_AGENT_NAME/${NEW_AGENT_NAME}/g" "${agent_path}/core/agent_reporter.py"

    # 通用工具 (從 Infra 專案複製)
    # MQTT Util
    cp "${TEMPLATES_DIR}/mqtt_util.py" "${agent_path}/exports/mqtt_util.py"
    # DB Connector
    cp "${TEMPLATES_DIR}/db_connector.py" "${agent_path}/exports/db_connector.py"

    # 部署腳本範本
    cp "${TEMPLATES_DIR}/deploy.sh.template" "${agent_path}/deploy/deploy.sh"
    sed -i "" "s/REPLACE_AGENT_NAME/${NEW_AGENT_NAME}/g" "${agent_path}/deploy/deploy.sh"
    chmod +x "${agent_path}/deploy/deploy.sh"

    log "Template files copied."
}

# 設置 Git 儲存庫
setup_git_repo() {
    local agent_path="$1"
    log "Initializing Git repository in $agent_path..."
    cd "$agent_path"
    git init
    # 創建初始 commit
    git add .
    git commit -m "feat: Initial agent scaffold for ${NEW_AGENT_NAME}"
    log "Git repository initialized."
}

# --- 主程式邏輯 ---

# 檢查依賴
check_dependencies

# 解析參數
if [ "$#" -eq 0 ]; then
    usage
fi

NEW_AGENT_NAME="$1"
shift

REDIS_HOST="${DEFAULT_REDIS_HOST}"
REDIS_PORT="${DEFAULT_REDIS_PORT}"

while [[ "$#" -gt 0 ]]; do
    key="$1"
    case $key in
        --redis-host)
        REDIS_HOST="$2"
        shift # past argument
        shift # past value
        ;;
        --redis-port)
        REDIS_PORT="$2"
        shift # past argument
        shift # past value
        ;;
        *)
        log "未知參數: $1"
        usage
        ;;
    esac
done

log "=== Agent Scaffold 啟動 ==="
log "Agent 名稱: ${NEW_AGENT_NAME}"
log "Redis 主機: ${REDIS_HOST}:${REDIS_PORT}"

# 設置 Agent 的工作目錄
AGENT_DIR="/Users/ilawusong/Documents/WaW/${NEW_AGENT_NAME}"

# 檢查目標目錄是否存在
if [ -d "${AGENT_DIR}" ]; then
    log "❌ 目錄 ${AGENT_DIR} 已存在。請選擇其他名稱或手動處理。"
    exit 1
fi

# 創建目錄結構
create_directories "${AGENT_DIR}"

# 複製範本檔案
copy_templates "${AGENT_DIR}" "${REDIS_HOST}" "${REDIS_PORT}"

# 設置 Git 儲存庫
setup_git_repo "${AGENT_DIR}"

log "✅ Agent '${NEW_AGENT_NAME}' 專案結構已成功建立在 ${AGENT_DIR}"
log "後續步驟:"
log "1. 進入 ${AGENT_DIR}"
log "2. 編輯 AGENTS.md 以定義角色與規範."
log "3. 根據需求修改 deploy/deploy.sh."
log "4. 執行 'python3 core/agent_listener.py ${NEW_AGENT_NAME}' 來啟動 Redis 監聽."
log "   (也可設定 REDIS_HOST 和 REDIS_PORT 環境變數來更改連線)"
log "5. 測試任務派發與接收."

log "=== Agent Scaffold 完成 ==="
exit 0
