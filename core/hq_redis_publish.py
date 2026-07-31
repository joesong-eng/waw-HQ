#!/usr/bin/env python3
"""HQ 透過 Redis 發布任務給 Agent"""
import sys
import json
from datetime import datetime, timedelta

try:
    import redis
except ImportError:
    print("❌ Redis 套件未安裝")
    print("   安裝方式: pip install redis")
    sys.exit(1)

def publish_task(agent_name, task_id, description, priority="normal"):
    """發布任務到 Redis"""
    
    task = {
        "type": "task",
        "task_id": task_id,
        "to_agent": agent_name,
        "priority": priority,
        "description": description,
        "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "deadline": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d") + " EOD"
    }
    
    channel = f"agent/{agent_name}/task"
    
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        result = r.publish(channel, json.dumps(task))
        
        print(f"✅ 任務已發布到 Redis")
        print(f"📡 頻道: {channel}")
        print(f"📊 訂閱者數量: {result}")
        print()
        print(json.dumps(task, indent=2, ensure_ascii=False))
        
        return True
        
    except redis.ConnectionError as e:
        print(f"❌ Redis 連線失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 發布失敗: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("使用方式: python hq_redis_publish.py <agent_name> <task_id> <description> [priority]")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    task_id = sys.argv[2]
    description = sys.argv[3]
    priority = sys.argv[4] if len(sys.argv) > 4 else "normal"
    
    success = publish_task(agent_name, task_id, description, priority)
    sys.exit(0 if success else 1)
