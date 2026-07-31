#!/usr/bin/env python3
"""
自動回覆 Telegram 機制
監聽文件變化 → 讀取內容 → 回覆到 Telegram
"""

import os
import time
import subprocess
from datetime import datetime

TRIGGER_FILE = os.path.expanduser("~/.hermes/telegram_trigger.txt")

def send_to_telegram(message):
    """發送訊息到 Telegram"""
    try:
        # 使用 Hermes send_message 功能
        result = subprocess.run([
            "hermes", "send", "telegram", message
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ 已發送到 Telegram: {message[:50]}...")
        else:
            print(f"❌ 發送失敗: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 發送錯誤: {e}")

def monitor_and_reply():
    """監聽文件變化並自動回覆"""
    print("🔍 開始監聽文件變化...")
    
    last_mtime = 0
    if os.path.exists(TRIGGER_FILE):
        last_mtime = os.path.getmtime(TRIGGER_FILE)
    
    while True:
        try:
            if os.path.exists(TRIGGER_FILE):
                current_mtime = os.path.getmtime(TRIGGER_FILE)
                
                if current_mtime > last_mtime:
                    # 讀取文件內容
                    with open(TRIGGER_FILE, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    
                    if content:
                        # 自動回覆到 Telegram
                        reply = f"📱 收到: {content}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
                        send_to_telegram(reply)
                        
                        last_mtime = current_mtime
            
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n👋 停止監聽")
            break
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_and_reply()