#!/bin/bash
# Shannie Outbox 輕量檢查腳本
# 用法：./dev_tools/shannie_watch.sh

SHANNIE_DIR="/Users/ilawusong/Documents/WaW/.taskflow/shannie"
OUTBOX="$SHANNIE_DIR/outbox"

echo "=== 檢查 Shannie Outbox ==="
PENDING_COUNT=0

for f in "$OUTBOX"/*.md; do
    [ -e "$f" ] || continue
    # 檢查是否有 status: pending
    if grep -q "status: pending" "$f" 2>/dev/null; then
        echo "[待處理任務] $(basename "$f")"
        echo "標題: $(grep -m 1 "^# " "$f")"
        echo "類型: $(grep "^type:" "$f" | cut -d: -f2 | tr -d ' ')"
        echo "優先級: $(grep "^priority:" "$f" | cut -d: -f2 | tr -d ' ')"
        echo "----------------------------------------"
        PENDING_COUNT=$((PENDING_COUNT + 1))
    fi
done

if [ "$PENDING_COUNT" -eq 0 ]; then
    echo "目前無待處理任務。"
else
    echo "共 $PENDING_COUNT 筆待處理任務。"
fi
