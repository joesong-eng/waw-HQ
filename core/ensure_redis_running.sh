#!/bin/bash
# 確保 Redis 正在運行
# 可用於手動檢查或作為其他服務的前置條件

REDIS_BIN="/opt/homebrew/opt/redis/bin/redis-server"
REDIS_CONF="/opt/homebrew/etc/redis.conf"
REDIS_CLI="/opt/homebrew/bin/redis-cli"

# 檢查 Redis 是否運行
if $REDIS_CLI ping > /dev/null 2>&1; then
    echo "✅ Redis 已在運行"
    $REDIS_CLI info server | grep "redis_version\|process_id" | head -2
    exit 0
fi

# 檢查是否有 Redis 進程
if pgrep -x redis-server > /dev/null 2>&1; then
    echo "⚠️  Redis 進程存在但無法連接"
    exit 1
fi

# 啟動 Redis
echo "🚀 啟動 Redis..."
$REDIS_BIN $REDIS_CONF --daemonize yes

# 等待啟動
sleep 1

# 驗證
if $REDIS_CLI ping > /dev/null 2>&1; then
    echo "✅ Redis 啟動成功"
    $REDIS_CLI info server | grep "redis_version\|process_id" | head -2
    exit 0
else
    echo "❌ Redis 啟動失敗"
    exit 1
fi
