"""
HQ Message Hub v2.0 - 主程式入口
啟動方式：
  python -m scripts.message_hub_v2
  或
  python scripts/message_hub_v2/__main__.py
"""
import queue
import threading
import signal
import sys
from pathlib import Path

# 修正導入路徑
if __name__ == '__main__':
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from message_hub_v2.config import HTTP_HOST, HTTP_PORT
    from message_hub_v2.router import route_event_to_agent
    from message_hub_v2.task_manager import TaskManager
    from message_hub_v2.redis_listener import RedisListener
    from message_hub_v2.http_server import create_http_server
except ImportError:
    # 如果還是失敗，嘗試相對導入
    from .config import HTTP_HOST, HTTP_PORT
    from .router import route_event_to_agent
    from .task_manager import TaskManager
    from .redis_listener import RedisListener
    from .http_server import create_http_server

# 全域變數
event_queue = queue.Queue(maxsize=1000)
task_manager = None
redis_listener = None
http_server = None
running = True

def event_processor():
    """背景執行緒：處理事件佇列"""
    global running, task_manager
    
    print("✅ 事件處理器已啟動")
    
    while running:
        try:
            event = event_queue.get(timeout=5)
            
            # 路由到對應 Agent
            agents = route_event_to_agent(event)
            
            if agents:
                print(f"🎯 事件路由到: {', '.join(agents)}")
                
                for agent in agents:
                    task_id = task_manager.create_task(agent, event)
                    print(f"   → {agent}: {task_id}")
            else:
                print(f"⚠️  事件無匹配 Agent，已記錄")
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"❌ 事件處理失敗: {e}")

def signal_handler(sig, frame):
    """處理中斷信號"""
    global running, redis_listener, http_server
    
    print('\n\n👋 正在停止 HQ Message Hub v2.0...')
    running = False
    
    # 停止 Redis 監聽
    if redis_listener:
        redis_listener.stop()
    
    # 停止 HTTP 伺服器
    if http_server:
        http_server.shutdown()
    
    sys.exit(0)

def main():
    """主程式"""
    global task_manager, redis_listener, http_server, running
    
    # 標題
    print('=' * 70)
    print('🚀 HQ Message Hub v2.0 啟動 (事件驅動版)')
    print('=' * 70)
    print(f'📡 HTTP 服務：http://{HTTP_HOST}:{HTTP_PORT}')
    print(f'📥 收件匣：.taskbox/inbox/')
    print(f'📤 發件匣：.taskbox/outbox/')
    print(f'📊 事件日誌：_agent/event_logs/')
    print('=' * 70)
    print()
    
    # 註冊信號處理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 初始化任務管理器
    task_manager = TaskManager()
    print("✅ 任務管理器已初始化")
    
    # 啟動事件處理執行緒
    processor_thread = threading.Thread(target=event_processor, daemon=True)
    processor_thread.start()
    
    # 啟動 Redis 監聽執行緒
    redis_listener = RedisListener(event_queue)
    redis_thread = threading.Thread(target=redis_listener.start, daemon=True)
    redis_thread.start()
    
    # 啟動 HTTP 伺服器
    try:
        http_server = create_http_server(
            HTTP_HOST,
            HTTP_PORT,
            task_manager=task_manager,
            event_queue=event_queue
        )
        
        print(f"✅ HTTP 伺服器已就緒")
        print()
        print("📋 可用的 API 端點：")
        print(f"   GET  /status           - 系統狀態")
        print(f"   GET  /tasks/<agent>    - Agent 查詢任務")
        print(f"   GET  /agents           - Agent 列表")
        print(f"   POST /report           - Agent 回報")
        print()
        print("🎧 開始監聽...")
        print("   按 Ctrl+C 停止服務")
        print()
        
        http_server.serve_forever()
        
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f'\n❌ 服務啟動失敗: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
