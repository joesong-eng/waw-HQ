#!/usr/bin/env python3
"""
簡單的 Telegram 消息通知監聽器
監聽觸發文件變化，立即通知當前 session
"""

import os
import time
import json
from datetime import datetime

# 配置
TRIGGER_FILE = os.path.expanduser("~/.hermes/telegram_trigger.txt")
NOTIFICATION_FILE = os.path.expanduser("~/.hermes/telegram_notification.json")

def notify_current_session(message_info):
    """通知當前 session 有新的 Telegram 消息"""
    notification = {
        "timestamp": datetime.now().isoformat(),
        "message": f"📱 Telegram 新消息: {message_info}",
        "source": "telegram_listener"
    }
    
    # 寫入通知文件
    with open(NOTIFICATION_FILE, "w", encoding="utf-8") as f:
        json.dump(notification, f, ensure_ascii=False, indent=2)
    
    print(f"📱 通知已發送: {message_info}")

def monitor_trigger_file():
    """監聽觸發文件變化"""
    print(f"🔍 開始監聽: {TRIGGER_FILE}")
    
    last_mtime = 0
    if os.path.exists(TRIGGER_FILE):
        last_mtime = os.path.getmtime(TRIGGER_FILE)
    
    while True:
        try:
            if os.path.exists(TRIGGER_FILE):
                current_mtime = os.path.getmtime(TRIGGER_FILE)
                
                if current_mtime > last_mtime:
                    # 文件被更新了
                    with open(TRIGGER_FILE, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    
                    if content:
                        notify_current_session(content)
                        last_mtime = current_mtime
            
            time.sleep(1)  # 每秒檢查一次
            
        except KeyboardInterrupt:
            print("\n👋 監聽器停止")
            break
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # 確保目錄存在
    os.makedirs(os.path.dirname(TRIGGER_FILE), exist_ok=True)
    monitor_trigger_file()