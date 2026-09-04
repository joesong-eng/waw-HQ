#!/usr/bin/env python3
"""
Redis Keeper - 確保 Redis 持續運行
由 launchd 啟動，定期檢查 Redis 狀態
"""
import subprocess
import time
import redis
from pathlib import Path

REDIS_BIN = "/opt/homebrew/opt/redis/bin/redis-server"
REDIS_CONF = "/opt/homebrew/etc/redis.conf"
CHECK_INTERVAL = 30  # 每30秒檢查一次

def is_redis_running():
    """檢查 Redis 是否運行"""
    try:
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
        r.ping()
        return True
    except:
        return False

def start_redis():
    """啟動 Redis"""
    try:
        print("🚀 啟動 Redis...")
        subprocess.run([REDIS_BIN, REDIS_CONF, '--daemonize', 'yes'], check=True)
        time.sleep(2)
        
        if is_redis_running():
            print("✅ Redis 啟動成功")
            return True
        else:
            print("❌ Redis 啟動後無法連接")
            return False
    except Exception as e:
        print(f"❌ 啟動 Redis 失敗: {e}")
        return False

def main():
    print("🔧 Redis Keeper 啟動")
    print(f"   檢查間隔: {CHECK_INTERVAL} 秒")
    print()
    
    # 初始檢查
    if not is_redis_running():
        print("⚠️  Redis 未運行，嘗試啟動...")
        start_redis()
    else:
        print("✅ Redis 已在運行")
    
    # 持續監控
    while True:
        time.sleep(CHECK_INTERVAL)
        
        if not is_redis_running():
            print(f"⚠️  [{time.strftime('%H:%M:%S')}] Redis 停止運行，重新啟動...")
            start_redis()

if __name__ == '__main__':
    main()
