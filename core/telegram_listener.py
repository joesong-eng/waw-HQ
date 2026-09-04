#!/usr/bin/env python3
"""
HHQM Telegram Listener
監聽 Telegram 訊息並通知 Hermes Agent 回應
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime

# ==========================================
# ⚙️ 配置區
# ==========================================

HQ_DIR = "/Users/ilawusong/Documents/WaW"
AGENT_NAME = "HHQM"
PROJECT_NAME = "sysWawIot"

# Telegram 監聽配置
TELEGRAM_MESSAGES_FILE = os.path.expanduser("~/.kiro/telegram/messages.json")
HERMES_NOTIFY_FILE = os.path.join(HQ_DIR, "telegram_queries.json")
POLL_INTERVAL = 3  # 每 3 秒檢查一次

# ==========================================
# 🛠️ 核心函式
# ==========================================

def log_message(message):
    """記錄日誌"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def read_telegram_messages(since_id=0):
    """讀取 Telegram 訊息"""
    try:
        if not os.path.exists(TELEGRAM_MESSAGES_FILE):
            return []
        
        with open(TELEGRAM_MESSAGES_FILE, "r", encoding="utf-8") as f:
            messages = json.load(f)
        
        # 返回 since_id 之後的訊息
        return [m for m in messages if m.get("id", 0) > since_id]
    except Exception as e:
        log_message(f"❌ 讀取 Telegram 訊息失敗: {e}")
        return []

def notify_hermes_agent(query_content, sender="User"):
    """通知 Hermes Agent 有新查詢"""
    try:
        # 建立查詢記錄
        query = {
            "id": int(time.time() * 1000),  # 使用時間戳作為 ID
            "sender": sender,
            "content": query_content,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        
        # 讀取現有查詢
        queries = []
        if os.path.exists(HERMES_NOTIFY_FILE):
            with open(HERMES_NOTIFY_FILE, "r", encoding="utf-8") as f:
                queries = json.load(f)
        
        # 添加新查詢
        queries.append(query)
        
        # 寫入文件
        with open(HERMES_NOTIFY_FILE, "w", encoding="utf-8") as f:
            json.dump(queries, f, ensure_ascii=False, indent=2)
        
        log_message(f"📨 已通知 Hermes Agent: {query_content[:50]}...")
        
        # 觸發 Hermes cronjob 立即執行
        trigger_hermes_response()
        
        return True
    except Exception as e:
        log_message(f"❌ 通知 Hermes Agent 失敗: {e}")
        return False

def trigger_hermes_response():
    """觸發 Hermes Agent 立即回應"""
    try:
        # 建立一個 cronjob 來處理查詢
        subprocess.run([
            "hermes", "cronjob", "create",
            "--name", "telegram-query-response",
            "--schedule", "now",
            "--repeat", "1",
            "--deliver", "telegram",
            "--prompt", f"""處理來自 Telegram 的查詢。

工作目錄: {HQ_DIR}

任務:
1. 讀取 telegram_queries.json 中的 pending 查詢
2. 根據查詢內容提供回應:
   - 如果問進度/狀態 → 讀取 DISPATCH_BOARD.md 提供最新狀態
   - 如果問 game_v0 → 提供 game_v0 相關進度
   - 如果問問題/錯誤 → 檢查相關日誌
   - 其他問題 → 根據專案情況回應

3. 將查詢狀態更新為 completed
4. 發送回應到 Telegram

回應格式:
📱 **回應您的查詢**: [查詢內容]

[具體回應內容]

⏰ 回應時間: [時間]"""
        ], capture_output=True, text=True)
        
        log_message("🚀 已觸發 Hermes Agent 回應")
    except Exception as e:
        log_message(f"⚠️ 觸發 Hermes 回應失敗: {e}")

def is_query_message(content):
    """判斷是否為查詢訊息"""
    query_keywords = [
        "進度", "狀態", "status", "如何", "怎麼", "什麼",
        "game_v0", "測試", "完成", "問題", "錯誤", "error",
        "下一步", "next", "現在", "目前", "最新"
    ]
    
    content_lower = content.lower()
    return any(keyword in content_lower for keyword in query_keywords)

def main_loop():
    """主循環 - 持續監聽 Telegram"""
    log_message(f"🚀 {AGENT_NAME} Telegram Listener 啟動")
    log_message(f"📁 專案路徑: {HQ_DIR}")
    log_message(f"📱 Telegram 訊息文件: {TELEGRAM_MESSAGES_FILE}")
    log_message(f"⏱️ 輪詢間隔: {POLL_INTERVAL} 秒")
    
    # 初始化：讀取現有訊息的最大 ID
    try:
        existing_messages = read_telegram_messages(since_id=0)
        last_message_id = max((m.get("id", 0) for m in existing_messages), default=0)
        log_message(f"📊 初始化：last_message_id = {last_message_id}")
    except:
        last_message_id = 0
    
    while True:
        try:
            # 讀取新訊息
            messages = read_telegram_messages(since_id=last_message_id)
            
            for msg in messages:
                msg_id = msg.get("id", 0)
                sender = msg.get("sender", "User")
                content = msg.get("content", "")
                
                # 更新最後讀取的訊息 ID
                if msg_id > last_message_id:
                    last_message_id = msg_id
                
                # 檢查是否為查詢訊息（且不是 Agent 發的）
                if is_query_message(content) and sender != AGENT_NAME:
                    log_message(f"📨 收到來自 {sender} 的查詢 (ID: {msg_id})")
                    log_message(f"📝 查詢內容: {content}")
                    
                    # 通知 Hermes Agent
                    notify_hermes_agent(content, sender)
            
            # 等待下一次輪詢
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            log_message(f"👋 {AGENT_NAME} Telegram Listener 停止")
            break
        except Exception as e:
            log_message(f"❌ 主循環錯誤: {e}")
            time.sleep(POLL_INTERVAL)

# ==========================================
# 🚀 程式入口
# ==========================================

if __name__ == "__main__":
    main_loop()