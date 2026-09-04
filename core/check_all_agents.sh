#!/bin/bash
# Agent 自動回覆系統 - 健康檢查腳本
# 用途：快速檢查所有 Agent 和 Redis 的運行狀態

echo "======================================"
echo "Agent 自動回覆系統 - 健康檢查"
echo "檢查時間：$(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================"
echo ""

# 檢查 Agent 服務狀態
echo "=== Agent 服務狀態 ==="
agents=("ina" "mina" "sophie")
running_count=0

for agent in "${agents[@]}"; do
    if launchctl list | grep -q "com.hq.agent.$agent"; then
        pid=$(launchctl list | grep "com.hq.agent.$agent" | awk '{print $1}')
        if [ "$pid" != "-" ]; then
            echo "✅ $agent: 運行中 (PID: $pid)"
            ((running_count++))
        else
            echo "⚠️  $agent: 已載入但未運行"
        fi
    else
        echo "❌ $agent: 未載入"
    fi
done

echo ""
echo "總計：$running_count / ${#agents[@]} Agent 運行中"
echo ""

# 檢查 Redis 狀態
echo "=== Redis 狀態 ==="
if ps aux | grep -v grep | grep -q redis-server; then
    pid=$(ps aux | grep -v grep | grep redis-server | awk '{print $2}')
    echo "✅ Redis: 運行中 (PID: $pid)"
else
    echo "❌ Redis: 未運行"
    echo ""
    echo "啟動 Redis："
    echo "/opt/homebrew/opt/redis/bin/redis-server /opt/homebrew/etc/redis.conf --daemonize yes"
fi

echo ""

# 檢查 Redis Keeper
echo "=== Redis Keeper 狀態 ==="
if launchctl list | grep -q "com.hq.redis.keeper"; then
    pid=$(launchctl list | grep "com.hq.redis.keeper" | awk '{print $1}')
    if [ "$pid" != "-" ]; then
        echo "✅ Redis Keeper: 運行中 (PID: $pid)"
    else
        echo "⚠️  Redis Keeper: 已載入但未運行"
    fi
else
    echo "⏳ Redis Keeper: 未配置（參考 docs/redis_keeper_setup.md）"
fi

echo ""

# 檢查最近的 Agent log
echo "=== 最近的 Agent 活動 ==="
echo ""

echo "【Ina】"
ina_log="/Users/ilawusong/Documents/WaW/Infra/logs/agent_redis_listener.out.log"
if [ -f "$ina_log" ]; then
    tail -n 2 "$ina_log" | sed 's/^/  /'
else
    echo "  Log 檔案不存在"
fi

echo ""
echo "【Mina】"
mina_log="/Users/ilawusong/Documents/WaW/PROJECT/Member/logs/agent_redis_listener.out.log"
if [ -f "$mina_log" ]; then
    tail -n 2 "$mina_log" | sed 's/^/  /'
else
    echo "  Log 檔案不存在"
fi

echo ""
echo "【Sophie】"
sophie_log="/Users/ilawusong/Documents/WaW/Owner/logs/agent_redis_listener.out.log"
if [ -f "$sophie_log" ]; then
    tail -n 2 "$sophie_log" | sed 's/^/  /'
else
    echo "  Log 檔案不存在"
fi

echo ""
echo "======================================"
echo "檢查完成"
echo "======================================"
