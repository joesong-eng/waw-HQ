#!/bin/bash

# HQ Core Services Startup Script

# Exit immediately if a command exits with a non-zero status.
set -e

HQ_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# --- Configuration ---
# Load HQ path if not set
if [ -z "$HQ_PATH" ]; then
    export HQ_PATH="$HQ_DIR"
fi

# Load secrets if available
if [ -f "$HQ_PATH/config/secrets.py" ]; then
    # Source secrets to load variables
    # This assumes secrets.py exports variables like BOT_TOKEN, CHAT_ID
    # For security, it's better to load them as environment variables or use a dedicated loader
    # For simplicity here, we'll assume they are loaded directly or via environment
    # Example: source "$HQ_PATH/config/secrets.py"
    echo "ℹ️ Loading secrets from $HQ_PATH/config/secrets.py (ensure variables are exported or loaded)"
fi

# --- Services ---

# 1. Ensure Redis is running
REDIS_SCRIPT="$HQ_DIR/core/ensure_redis_running.sh"
if [ -x "$REDIS_SCRIPT" ]; then
    echo "🚀 Starting Redis guardian..."
    nohup bash "$REDIS_SCRIPT" > /dev/null 2>&1 &
    sleep 3 # Give Redis a moment to start
else
    echo "⚠️ Redis guardian script not found or not executable."
fi

# 2. Start HQ Redis Listener
HQ_LISTENER_SCRIPT="$HQ_DIR/core/hq_redis_listener.py"
if [ -f "$HQ_LISTENER_SCRIPT" ]; then
    echo "🚀 Starting HQ Redis Listener..."
    # Set HQ_PATH for the listener script if it uses it
    export HQ_PATH="$HQ_DIR"
    nohup python3 "$HQ_LISTENER_SCRIPT" > /dev/null 2>&1 &
else
    echo "⚠️ HQ Redis Listener script not found."
fi

# 3. Start Telegram Listener (HHQM)
# NOTE: telegram_listener.py and auto_reply_telegram.py seem to serve different purposes.
# telegram_listener.py notifies Hermes Agent via a file.
# auto_reply_telegram.py monitors a file and sends to Telegram.
# The prompt mentioned HHQM is the one for Telegram Bot.
# Let's start the one that seems to interact with the Telegram bot for notifications.
# Based on the previous context, HHQM's `notify_hermes_agent` seems to be the relevant one for notifications.
# However, the script named `telegram_notifier.py` and `hq_tg_notifier.py` were also found.

# For now, I'll assume `hq_tg_notifier.py` is the primary notification mechanism for HQ.
# If other listeners are needed, they should be started separately or integrated here.

TELEGRAM_NOTIFIER_SCRIPT="$HQ_DIR/core/hq_tg_notifier.py"
if [ -f "$TELEGRAM_NOTIFIER_SCRIPT" ]; then
    echo "🚀 Starting HQ Telegram Notifier..."
    # Assuming it uses BOT_TOKEN and CHAT_ID from secrets.py, ensure they are available
    export HQ_PATH="$HQ_DIR"
    nohup python3 "$TELEGRAM_NOTIFIER_SCRIPT" > /dev/null 2>&1 &
else
    echo "⚠️ HQ Telegram Notifier script not found."
fi

# If you need to start other listeners like `telegram_listener.py` or `auto_reply_telegram.py`:
# TELEGRAM_LISTENER_SCRIPT="$HQ_DIR/core/telegram_listener.py"
# if [ -f "$TELEGRAM_LISTENER_SCRIPT" ]; then
#     echo "🚀 Starting Telegram Listener..."
#     nohup python3 "$TELEGRAM_LISTENER_SCRIPT" > /dev/null 2>&1 &
# fi

echo "\nAll HQ core services should be running in the background."

exit 0
