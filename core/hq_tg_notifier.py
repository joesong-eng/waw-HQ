#!/usr/bin/env python3
"""HQ Telegram Notifier — reads secrets from config/secrets.py"""
import os
import sys
from pathlib import Path

import requests

HQ_PATH = Path(os.environ.get('HQ_PATH', Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(HQ_PATH / 'config'))

try:
    from secrets import BOT_TOKEN, CHAT_ID
except ImportError:
    BOT_TOKEN = os.environ.get('TG_BOT_TOKEN', '')
    CHAT_ID = os.environ.get('TG_CHAT_ID', '')
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️  Telegram credentials not found in config/secrets.py or env vars")


def send_telegram(title, message):
    """Send a notification to the configured Telegram chat."""
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️  Telegram not configured — skipping notification")
        return
    try:
        text = f"🛡️ HQ {title}: {message}"
        requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            data={'chat_id': CHAT_ID, 'text': text},
            timeout=10,
        )
    except Exception as e:
        print(f"Telegram Failed: {e}")


if __name__ == '__main__':
    if len(sys.argv) >= 3:
        send_telegram(sys.argv[1], sys.argv[2])
    else:
        print("Usage: hq_tg_notifier.py <title> <message>")
