#!/bin/bash
# HQ 系統狀態查看

HQ_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "🔍 HQ 系統狀態"
echo ""

# Redis
echo "── Redis ──"
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis 在線"
else
    echo "❌ Redis 未啟動 → 執行: redis-server --daemonize yes"
fi

# agents_supervisor
echo ""
echo "── agents_supervisor ──"
if launchctl list | grep -q "com.hq.agents.supervisor"; then
    PID=$(launchctl list | grep "com.hq.agents.supervisor" | awk '{print $1}')
    echo "✅ agents_supervisor 運行中 (PID: ${PID})"
else
    echo "❌ agents_supervisor 未運行"
    echo "   → 執行: launchctl load ~/Library/LaunchAgents/com.hq.agents.supervisor.plist"
fi

# Message Hub HTTP（可選）
echo ""
echo "── Message Hub HTTP (可選) ──"
if curl -s "http://localhost:8899/status" > /dev/null 2>&1; then
    echo "✅ Message Hub HTTP 運行中 (localhost:8899)"
else
    echo "⚠️  Message Hub HTTP 未啟動（非必要，Redis 為主要通道）"
fi

# 收件匣
echo ""
echo "── 收件匣 (.taskbox/inbox/) ──"
INBOX_COUNT=$(ls -1 "${HQ_DIR}/.taskbox/inbox/"*.json 2>/dev/null | wc -l | xargs)
echo "📥 共 ${INBOX_COUNT} 則回報"
if [ "${INBOX_COUNT}" -gt 0 ]; then
    echo "最近 5 則："
    ls -lt "${HQ_DIR}/.taskbox/inbox/"*.json 2>/dev/null | head -5 | awk '{print "  -", $NF}' | xargs -I{} basename {}
fi

# 發件匣
echo ""
echo "── 發件匣 (.taskbox/outbox/) ──"
OUTBOX_COUNT=$(ls -1 "${HQ_DIR}/.taskbox/outbox/"*.json 2>/dev/null | wc -l | xargs)
echo "📤 共 ${OUTBOX_COUNT} 個待辦"
if [ "${OUTBOX_COUNT}" -gt 0 ]; then
    for f in "${HQ_DIR}/.taskbox/outbox/"*.json; do
        AGENT=$(basename "$f" | sed 's/to_//;s/.json//')
        TASK_ID=$(python3 -c "import sys,json; print(json.load(open('$f')).get('task_id','N/A'))" 2>/dev/null)
        echo "  - ${AGENT}: ${TASK_ID}"
    done
fi

echo ""
