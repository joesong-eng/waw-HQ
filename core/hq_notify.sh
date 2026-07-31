#!/bin/bash
# HQ 雙重通知工具 (macOS + Telegram)

TITLE=$1
MESSAGE=$2
BOT_TOKEN="8669253700:AAGzsPKlawjhDSnamtHLUKAoblJ2Mg7R0G4"
CHAT_ID="1367155154"

# 1. macOS 桌面通知
osascript -e "display notification \"$MESSAGE\" with title \"🛡️ HQ: $TITLE\""

# 2. Telegram 手機通知
curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
     -d "chat_id=${CHAT_ID}&text=🛡️ HQ $TITLE: $MESSAGE" > /dev/null
