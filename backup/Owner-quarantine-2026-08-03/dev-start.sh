#!/bin/bash
# WAW Core 本地開發啟動腳本

echo "🚀 啟動 WAW Core 開發環境..."

# 殺掉舊的 process
pkill -f "artisan serve" 2>/dev/null
pkill -f "ssh.*3308" 2>/dev/null
sleep 1

# 開 DB tunnel
echo "📡 連接 DB tunnel (port 3308)..."
ssh -f -N -L 3308:127.0.0.1:3306 infra -o StrictHostKeyChecking=no -o ExitOnForwardFailure=yes
sleep 2

# 確認 tunnel
if lsof -i :3308 | grep -q LISTEN; then
    echo "✅ DB tunnel OK"
else
    echo "❌ DB tunnel 失敗，請確認 SSH 白名單"
    exit 1
fi

# 清除 Laravel cache
cd /Users/ilawusong/Documents/sysWawIot/waw-core
php artisan config:clear 2>/dev/null

# 啟動 Laravel
echo "🌐 啟動 Laravel server (http://127.0.0.1:8080)..."
php artisan serve --port=8080 --host=127.0.0.1
