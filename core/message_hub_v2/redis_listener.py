"""
Message Hub v2.0 - Redis 監聽模組
負責監聽 Redis Pub/Sub 並將事件放入佇列
"""
import json
import datetime
import queue
import time
from typing import Optional

# Redis 支援（可選）
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .config import REDIS_HOST, REDIS_PORT, REDIS_SUBSCRIBE_CHANNELS

class RedisListener:
    """Redis Pub/Sub 監聽器"""
    
    def __init__(self, event_queue: queue.Queue, host: str = None, port: int = None):
        """
        初始化 Redis 監聽器
        
        Args:
            event_queue: 事件佇列
            host: Redis 主機
            port: Redis 埠號
        """
        self.event_queue = event_queue
        self.host = host or REDIS_HOST
        self.port = port or REDIS_PORT
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.is_running = False
    
    def start(self):
        """啟動監聽"""
        if not REDIS_AVAILABLE:
            print("⚠️  Redis 套件未安裝，跳過 Redis 監聽")
            print("   安裝方式: pip install redis")
            return
        
        try:
            # 連接 Redis
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                decode_responses=True,
                socket_connect_timeout=5
            )
            
            # 測試連線
            self.redis_client.ping()
            print(f"✅ Redis 連線成功 ({self.host}:{self.port})")
            
            # 建立 Pub/Sub
            self.pubsub = self.redis_client.pubsub()
            
            # 訂閱頻道（使用 psubscribe 支援萬用字元）
            self.pubsub.psubscribe(*REDIS_SUBSCRIBE_CHANNELS)
            
            print(f"✅ Redis 監聽已啟動")
            print(f"   訂閱頻道: {len(REDIS_SUBSCRIBE_CHANNELS)} 個")
            for channel in REDIS_SUBSCRIBE_CHANNELS:
                print(f"   - {channel}")
            
            self.is_running = True
            
            # 開始監聽
            self._listen_loop()
            
        except redis.ConnectionError as e:
            print(f"⚠️  無法連接 Redis ({self.host}:{self.port})")
            print(f"   錯誤: {e}")
            print(f"   Redis 監聽功能已停用")
        except Exception as e:
            print(f"❌ Redis 監聽啟動失敗: {e}")
    
    def _listen_loop(self):
        """監聽迴圈"""
        for message in self.pubsub.listen():
            if not self.is_running:
                break
            
            # 只處理實際訊息（忽略訂閱確認）
            if message['type'] == 'pmessage':
                try:
                    self._process_message(message)
                except Exception as e:
                    print(f"❌ 處理 Redis 訊息失敗: {e}")
    
    def _process_message(self, message: dict):
        """
        處理 Redis 訊息
        
        Args:
            message: Redis 訊息 {'pattern': '...', 'channel': '...', 'data': '...'}
        """
        channel = message['channel']
        raw_data = message['data']
        
        # 解析 JSON（如果是 JSON 格式）
        try:
            if isinstance(raw_data, str):
                data = json.loads(raw_data)
            else:
                data = raw_data
        except json.JSONDecodeError:
            # 不是 JSON，當作純文字
            data = {'message': raw_data}
        
        # 建立事件物件
        event = {
            'source': 'redis',
            'channel': channel,
            'data': data,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        # 放入事件佇列
        try:
            self.event_queue.put(event, timeout=1)
            print(f"📡 Redis 事件: {channel}")
        except queue.Full:
            print(f"⚠️  事件佇列已滿，丟棄事件: {channel}")
    
    def stop(self):
        """停止監聽"""
        self.is_running = False
        
        if self.pubsub:
            try:
                self.pubsub.unsubscribe()
                self.pubsub.close()
            except:
                pass
        
        if self.redis_client:
            try:
                self.redis_client.close()
            except:
                pass
        
        print("👋 Redis 監聽已停止")
    
    def test_connection(self) -> bool:
        """測試 Redis 連線"""
        if not REDIS_AVAILABLE:
            return False
        
        try:
            test_client = redis.Redis(
                host=self.host,
                port=self.port,
                socket_connect_timeout=2
            )
            test_client.ping()
            test_client.close()
            return True
        except:
            return False

# 測試函數
def test_redis_listener():
    """測試 Redis 監聽器"""
    print("🧪 測試 Redis 監聽器...")
    
    test_queue = queue.Queue()
    listener = RedisListener(test_queue)
    
    # 測試連線
    if listener.test_connection():
        print("✅ Redis 連線測試通過")
    else:
        print("❌ Redis 連線測試失敗")
        return False
    
    return True

if __name__ == '__main__':
    test_redis_listener()
