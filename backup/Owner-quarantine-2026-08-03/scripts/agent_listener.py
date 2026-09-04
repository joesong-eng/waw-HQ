# 設置 Redis 配置\nREDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')\nREDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
import redis
import json
import os
from datetime import datetime

AGENT_NAME = "Owner"
REDIS_CHANNEL = f"agent/{AGENT_NAME.lower()}/task"
BASE_DIR = os.getcwd()
INBOX_DIR = os.path.join(BASE_DIR, "_agent")

def main():
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    pubsub = r.pubsub()
    pubsub.subscribe(REDIS_CHANNEL)
    print(f"🕵️ Agent {AGENT_NAME} 監聽啟動...")
    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            print(f"📥 收到任務: {data.get('task_id')}")
