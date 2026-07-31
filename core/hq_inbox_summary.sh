#!/bin/bash
# 查看收件匣摘要
# 使用方式：./hq_inbox_summary.sh

INBOX_DIR="_agent/inbox"

if [ ! -d "${INBOX_DIR}" ]; then
    echo "📭 收件匣為空"
    exit 0
fi

TOTAL=$(ls -1 "${INBOX_DIR}"/*.json 2>/dev/null | wc -l | xargs)

if [ "${TOTAL}" -eq 0 ]; then
    echo "📭 收件匣為空"
    exit 0
fi

echo "📬 收件匣摘要 (共 ${TOTAL} 則訊息)"
echo ""
echo "最近 10 則訊息:"
echo "─────────────────────────────────────────────────────────"

ls -lt "${INBOX_DIR}"/*.json 2>/dev/null | head -10 | while read line; do
    FILE=$(echo "$line" | awk '{print $9}')
    if [ -f "${FILE}" ]; then
        BASENAME=$(basename "${FILE}")
        AGENT=$(cat "${FILE}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('from_agent','unknown'))" 2>/dev/null)
        TIMESTAMP=$(cat "${FILE}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('timestamp','N/A'))" 2>/dev/null)
        echo "📨 ${BASENAME}"
        echo "   Agent: ${AGENT} | Time: ${TIMESTAMP}"
        echo ""
    fi
done

echo "─────────────────────────────────────────────────────────"
echo ""
echo "查看完整訊息: cat ${INBOX_DIR}/<filename>.json | jq ."
