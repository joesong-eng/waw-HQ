# Alliance 系統維護最佳實踐


**[On-Demand]** — 上下文注入策略

> **文檔版本**：1.0  
> **最後更新**：2026-06-18  
> **編寫角色**：HQ (協調者)  
> **適用對象**：Allie Agent、系統維護人員

---

## 🎯 維護核心原則

### 1. 預防勝於治療
- **定期備份**：每日自動備份資料庫和配置
- **監控預警**：設置關鍵指標告警閾值
- **版本控制**：所有配置變更必須記錄
- **測試驗證**：生產變更前必須在測試環境驗證

### 2. 變更管理紀律
- **變更窗口**：非緊急變更在維護時段執行
- **回滾準備**：每次變更前準備回滾方案
- **影響評估**：評估變更對其他系統的影響
- **文檔更新**：變更完成後立即更新文檔

### 3. 問題處理策略
- **快速隔離**：優先隔離故障影響範圍
- **根因分析**：修復後必須分析根本原因
- **知識沉澱**：每次故障處理後更新知識庫
- **改進措施**：制定預防類似問題的措施

---

## 📋 日常維護檢查清單

### 每日例行檢查 (5 分鐘)
```bash
#!/bin/bash
# Alliance 系統日檢腳本

echo "=== Alliance 日常健康檢查 $(date) ==="

# 1. 服務狀態
echo "1. 服務狀態檢查"
services=("alliance-api" "mysql" "redis" "mosquitto")
for service in "${services[@]}"; do
    status=$(systemctl is-active $service)
    echo "  $service: $status"
    if [ "$status" != "active" ]; then
        echo "  ⚠️  警告：$service 服務異常"
    fi
done

# 2. 磁碟空間
echo -e "\n2. 磁碟空間檢查"
df -h | awk '$5 > 85 {print "  ⚠️  " $6 " 使用率: " $5}'

# 3. API 健康檢查
echo -e "\n3. API 健康檢查"
response=$(curl -s -w "%{http_code}" http://localhost:8080/api/health -o /dev/null)
if [ "$response" = "200" ]; then
    echo "  ✅ API 正常"
else
    echo "  ❌ API 異常 (HTTP $response)"
fi

# 4. 錯誤日誌檢查
echo -e "\n4. 錯誤日誌檢查"
error_count=$(tail -100 /var/log/alliance/error.log | grep "$(date '+%Y-%m-%d')" | wc -l)
if [ "$error_count" -gt 10 ]; then
    echo "  ⚠️  今日錯誤日誌 $error_count 筆，需要關注"
else
    echo "  ✅ 錯誤日誌正常 ($error_count 筆)"
fi
```

### 每週深度檢查 (30 分鐘)
```bash
#!/bin/bash
# Alliance 系統週檢腳本

echo "=== Alliance 週度深度檢查 $(date) ==="

# 1. 資料庫效能分析
echo "1. 資料庫效能分析"
mysql -u root -p alliance_db << 'SQLEOF'
-- 慢查詢統計
SELECT 
    ROUND(AVG(query_time), 3) as avg_query_time,
    COUNT(*) as query_count,
    LEFT(sql_text, 50) as sample_query
FROM mysql.slow_log 
WHERE start_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY LEFT(sql_text, 50)
ORDER BY avg_query_time DESC
LIMIT 5;

-- 表大小統計
SELECT 
    TABLE_NAME,
    ROUND(DATA_LENGTH/1024/1024, 2) as data_mb,
    ROUND(INDEX_LENGTH/1024/1024, 2) as index_mb,
    TABLE_ROWS
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'alliance_db'
ORDER BY DATA_LENGTH DESC;
SQLEOF

# 2. 日誌輪轉和清理
echo -e "\n2. 日誌清理"
find /var/log/alliance/ -name "*.log.*" -mtime +30 -delete
logrotate -d /etc/logrotate.d/alliance

# 3. 系統資源使用分析
echo -e "\n3. 系統資源分析"
echo "過去一週平均負載："
sar -u 1 1 | tail -1

# 4. 安全檢查
echo -e "\n4. 安全檢查"
echo "失敗登入嘗試："
grep "Failed password" /var/log/auth.log | tail -10

# 5. 備份驗證
echo -e "\n5. 備份驗證"
ls -la /backup/alliance/ | tail -7
```

---

## 🔧 配置管理最佳實踐

### 環境配置標準化
```bash
# Alliance 標準環境配置範本
# 檔案：/home/ubuntu/alliance/.env.template

# === 資料庫配置 ===
DB_HOST=localhost
DB_PORT=3306
DB_NAME=alliance_db
DB_USER=alliance_user
DB_PASSWORD={{SECURE_PASSWORD}}  # 使用強密碼
DB_CHARSET=utf8mb4
DB_TIMEZONE=Asia/Taipei

# === Redis 配置 ===
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD={{REDIS_PASSWORD}}  # 生產環境必須設密碼
REDIS_DB=2  # 使用專用 DB 編號

# === MQTT 配置 ===
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USERNAME=alliance_mqtt
MQTT_PASSWORD={{MQTT_PASSWORD}}

# === API 配置 ===
API_PORT=8080
API_HOST=0.0.0.0
CALLBACK_INTERNAL_KEY=v9-internal-key-2026
API_RATE_LIMIT=1000  # 每分鐘請求限制

# === 日誌配置 ===
LOG_LEVEL=INFO  # DEBUG|INFO|WARN|ERROR
LOG_PATH=/var/log/alliance/
LOG_MAX_SIZE=100MB
LOG_MAX_FILES=30

# === 監控配置 ===
HEALTH_CHECK_INTERVAL=30  # 秒
METRICS_ENABLED=true
PROMETHEUS_PORT=9090
```

### 配置變更流程
1. **變更申請**：提交配置變更申請
2. **影響評估**：評估對系統的影響
3. **測試驗證**：在測試環境驗證
4. **備份原配置**：備份當前配置
5. **執行變更**：在維護窗口執行
6. **驗證結果**：確認系統正常運行
7. **文檔更新**：更新配置文檔

---

## 📊 效能調優指南

### 資料庫效能優化
```sql
-- 1. 索引優化建議

-- 用戶查詢優化
CREATE INDEX idx_users_status_created ON users(status, created_at);
CREATE INDEX idx_users_email ON users(email);

-- 交易查詢優化
CREATE INDEX idx_transactions_user_time ON transactions(user_id, created_at);
CREATE INDEX idx_transactions_status ON transactions(status);

-- 收益查詢優化
CREATE INDEX idx_revenue_agent_date ON revenue_facts(agent_id, date_created);

-- 2. 查詢優化
-- 使用 EXPLAIN 分析慢查詢
EXPLAIN SELECT * FROM transactions WHERE user_id = 123 AND created_at >= '2026-06-01';

-- 3. 定期維護
-- 每月執行表優化
OPTIMIZE TABLE users, transactions, revenue_facts;

-- 更新表統計資訊
ANALYZE TABLE users, transactions, revenue_facts;
```

### 應用程式效能優化
```python
# 1. 資料庫連接池配置
DATABASE_CONFIG = {
    'pool_size': 10,           # 連接池大小
    'max_overflow': 20,        # 最大溢出連接
    'pool_timeout': 30,        # 連接超時
    'pool_recycle': 3600,      # 連接回收時間（秒）
    'pool_pre_ping': True,     # 連接前測試
}

# 2. Redis 快取策略
CACHE_CONFIG = {
    'user_session': {'ttl': 1800},      # 用戶會話 30 分鐘
    'api_response': {'ttl': 300},       # API 回應 5 分鐘
    'static_data': {'ttl': 86400},      # 靜態資料 24 小時
}

# 3. API 回應優化
@app.middleware("http")
async def add_performance_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

---

## 🛡️ 安全維護規範

### 密碼和金鑰管理
```bash
# 1. 定期更換系統密碼（每 90 天）
# 資料庫密碼
ALTER USER 'alliance_user'@'localhost' IDENTIFIED BY 'new_secure_password';

# 2. API 金鑰輪替（每 180 天）
# 更新 .env 中的 CALLBACK_INTERNAL_KEY

# 3. SSH 金鑰管理
# 定期檢查授權金鑰
cat ~/.ssh/authorized_keys
# 移除不再需要的金鑰

# 4. 憑證管理
# 檢查 SSL 憑證到期時間
openssl x509 -in /etc/ssl/certs/alliance.crt -noout -dates
```

### 系統安全檢查
```bash
# 1. 埠掃描檢查
nmap -sS localhost

# 2. 檔案權限檢查
find /home/ubuntu/alliance -type f -perm 777 -ls

# 3. 系統更新檢查
apt list --upgradable | grep security

# 4. 防火牆規則檢查
ufw status verbose

# 5. 登入日誌檢查
last -n 20
grep "Failed password" /var/log/auth.log | tail -20
```

---

## 📈 監控和告警設置

### 關鍵監控指標
```yaml
# Prometheus 監控配置
monitoring_rules:
  # 系統資源
  - alert: HighCPUUsage
    expr: cpu_usage > 85
    for: 5m
    
  - alert: HighMemoryUsage
    expr: memory_usage > 90
    for: 3m
    
  - alert: DiskSpaceLow
    expr: disk_usage > 95
    for: 1m

  # 應用指標
  - alert: HighAPIResponseTime
    expr: api_response_time > 1000
    for: 2m
    
  - alert: HighErrorRate
    expr: error_rate > 5
    for: 1m
    
  # 資料庫指標
  - alert: DatabaseConnectionHigh
    expr: db_connections > 80
    for: 5m
    
  - alert: SlowQueryDetected
    expr: slow_query_count > 10
    for: 3m
```

### 告警通知設置
```bash
# 1. 系統監控腳本
#!/bin/bash
# 檔案：/home/ubuntu/scripts/alliance_monitor.sh

# CPU 使用率檢查
cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d% -f1)
if (( $(echo "$cpu_usage > 85" | bc -l) )); then
    echo "警告：CPU 使用率 ${cpu_usage}% 過高" | \
    mail -s "Alliance CPU 警告" admin@example.com
fi

# 磁碟空間檢查
disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d% -f1)
if [ "$disk_usage" -gt 90 ]; then
    echo "警告：磁碟使用率 ${disk_usage}% 過高" | \
    mail -s "Alliance 磁碟警告" admin@example.com
fi
```

---

## 🔄 災難恢復計劃

### 備份策略
```bash
#!/bin/bash
# Alliance 系統完整備份腳本

BACKUP_DIR="/backup/alliance/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# 1. 資料庫備份
mysqldump -u root -p alliance_db > $BACKUP_DIR/alliance_db.sql

# 2. 配置檔案備份
cp -r /home/ubuntu/alliance/.env* $BACKUP_DIR/
cp -r /etc/alliance/ $BACKUP_DIR/configs/

# 3. 日誌備份
tar -czf $BACKUP_DIR/logs.tar.gz /var/log/alliance/

# 4. 應用程式備份
tar -czf $BACKUP_DIR/application.tar.gz /home/ubuntu/alliance/

# 5. 備份驗證
echo "備份完成：$BACKUP_DIR"
ls -la $BACKUP_DIR
```

### 恢復程序
```bash
#!/bin/bash
# Alliance 系統恢復腳本

BACKUP_DIR=$1
if [ -z "$BACKUP_DIR" ]; then
    echo "使用方法: $0 <backup_directory>"
    exit 1
fi

echo "開始恢復 Alliance 系統從 $BACKUP_DIR"

# 1. 停止服務
systemctl stop alliance-api

# 2. 恢復資料庫
mysql -u root -p alliance_db < $BACKUP_DIR/alliance_db.sql

# 3. 恢復配置
cp $BACKUP_DIR/.env* /home/ubuntu/alliance/
cp -r $BACKUP_DIR/configs/* /etc/alliance/

# 4. 重啟服務
systemctl start alliance-api

# 5. 驗證恢復
curl -f http://localhost:8080/api/health && echo "恢復成功"
```

---

## 🔗 文件神經連結

- 上級文件：`06_alliance_system/README.md`
- 診斷指南：`06_alliance_system/QUICK_DIAGNOSIS_SOP.md`
- 問題解決：`06_alliance_system/SEVEN_CRITICAL_FIXES.md`
- 部署指南：`04_deployment_operations/DEPLOYMENT_GUIDE.md`
- 基礎架構：`04_deployment_operations/INFRASTRUCTURE_REFERENCE.md`
