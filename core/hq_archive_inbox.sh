#!/bin/bash
# 歸檔收件匣訊息
# 使用方式：./hq_archive_inbox.sh [days]
# 範例：./hq_archive_inbox.sh 7  # 歸檔 7 天前的訊息

DAYS="${1:-7}"
INBOX_DIR=".taskbox/inbox"
ARCHIVE_DIR=".taskbox/archive/$(date +%Y%m)"

if [ ! -d "${INBOX_DIR}" ]; then
    echo "📭 收件匣為空"
    exit 0
fi

echo "📦 歸檔 ${DAYS} 天前的訊息..."

mkdir -p "${ARCHIVE_DIR}"

COUNT=0
for FILE in "${INBOX_DIR}"/*.json; do
    if [ -f "${FILE}" ]; then
        # 檢查檔案修改時間
        if [ "$(uname)" == "Darwin" ]; then
            # macOS
            FILE_TIME=$(stat -f %m "${FILE}")
        else
            # Linux
            FILE_TIME=$(stat -c %Y "${FILE}")
        fi
        
        CUTOFF_TIME=$(($(date +%s) - (DAYS * 86400)))
        
        if [ "${FILE_TIME}" -lt "${CUTOFF_TIME}" ]; then
            mv "${FILE}" "${ARCHIVE_DIR}/"
            COUNT=$((COUNT + 1))
            echo "  ✅ $(basename ${FILE})"
        fi
    fi
done

if [ "${COUNT}" -eq 0 ]; then
    echo "  無符合條件的訊息"
else
    echo ""
    echo "✅ 已歸檔 ${COUNT} 則訊息至 ${ARCHIVE_DIR}/"
fi
