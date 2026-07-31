# Alliance 系統故障排除指南


**[On-Demand]** — 上下文注入策略

> **文檔版本**：1.0  
> **最後更新**：2026-06-18  
> **編寫角色**：HQ (協調者)  
> **適用場景**：系統故障排除、問題診斷

---

## 🎯 故障排除總原則

### 診斷順序
1. **系統層**：檢查服務狀態、資源使用率
2. **網路層**：驗證連接性、埠可用性
3. **應用層**：檢查配置、日誌、API 回應
4. **資料層**：驗證資料庫連接、資料完整性

### 證據收集
- 所有診斷結果必須有**截圖或 log 輸出**
- 記錄**時間戳記**和**執行環境**
- 保存**錯誤訊息的完整文本**
- 記錄**已嘗試的修復步驟**

---

## 🚨 常見故障類型診斷

### 故障類型 1：API 完全無回應

**症狀描述**
- curl 請求超時
- 瀏覽器無法訪問
- 健康檢查失敗

**診斷步驟**
```bash
# 1. 檢查服務狀態
systemctl status alliance-api
ps aux | grep alliance

# 2. 檢查埠占用
netstat -tulpn | grep :8080
ss -tulpn | grep :8080

# 3. 檢查防火牆
ufw status
iptables -L | grep 8080

# 4. 檢查應用日誌
tail -50 /var/log/alliance/error.log
journalctl -u alliance-api -f
```

**修復方案**
```bash
# 方案 A：重啟服務
systemctl restart alliance-api
sleep 10
curl http://localhost:8080/api/health

# 方案 B：重新啟動
pkill -f alliance
cd /home/ubuntu/alliance
./start.sh

# 方案 C：檢查配置
cd /home/ubuntu/alliance
source .env
echo $API_PORT  # 確認埠號正確
```

---

### 故障類型 2：間歇性 500 錯誤

**症狀描述**
- 部分 API 請求成功，部分失敗
- 錯誤率約 10-30%
- 回應時間不穩定

**診斷步驟**
```bash
# 1. 系統資源檢查
top -bn1 | head -20
free -h
df -h

# 2. 資料庫連接檢查
mysql -u alliance_user -p alliance_db -e "SHOW PROCESSLIST;"
mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';"

# 3. 連接池狀態
# 檢查應用程式連接池配置
grep -r "pool" /home/ubuntu/alliance/config/

# 4. 慢查詢分析
mysql -u root -p -e "SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;"
```

**修復方案**
```bash
# 方案 A：調整連接池
# 編輯 database.conf
max_connections=50
pool_size=20
timeout=30

# 方案 B：資料庫優化
mysql -u root -p alliance_db << 'SQLEOF'
OPTIMIZE TABLE users;
OPTIMIZE TABLE transactions;
ANALYZE TABLE users;
ANALYZE TABLE transactions;
SQLEOF

# 方案 C：重啟相關服務
systemctl restart mysql
systemctl restart alliance-api
```

---

### 故障類型 3：認證錯誤 (401)

**症狀描述**
- 所有 API 請求返回 401
- 正確的金鑰仍然被拒絕
- 認證日誌顯示失敗

**診斷步驟**
```bash
# 1. 檢查金鑰配置
cat /home/ubuntu/alliance/.env | grep CALLBACK_INTERNAL_KEY
echo "配置中的金鑰：$CALLBACK_INTERNAL_KEY"

# 2. 測試金鑰
curl -H "X-Internal-Key: v9-internal-key-2026" \
     -H "Content-Type: application/json" \
     http://localhost:8080/api/health -v

# 3. 檢查認證日誌
grep "authentication" /var/log/alliance/app.log | tail -10
grep "401" /var/log/alliance/access.log | tail -10

# 4. 檢查 Header 名稱
# 確認應用程式期待的 Header 名稱
grep -r "X-Internal-Key\|INTERNAL_KEY" /home/ubuntu/alliance/src/
```

**修復方案**
```bash
# 方案 A：重設金鑰
# 1. 備份舊配置
cp /home/ubuntu/alliance/.env /home/ubuntu/alliance/.env.backup

# 2. 更新金鑰
sed -i 's/CALLBACK_INTERNAL_KEY=.*/CALLBACK_INTERNAL_KEY=v9-internal-key-2026/' /home/ubuntu/alliance/.env

# 3. 重啟服務
systemctl restart alliance-api

# 方案 B：檢查 Header 處理
# 確認應用程式正確讀取 Header
grep -A 10 -B 5 "X-Internal-Key" /home/ubuntu/alliance/src/middleware/auth.py
```

---

### 故障類型 4：資料庫連接失敗

**症狀描述**
- "Connection refused" 錯誤
- "Access denied" 錯誤
- 資料庫操作超時

**診斷步驟**
```bash
# 1. MySQL 服務狀態
systemctl status mysql
mysqladmin ping

# 2. 連接測試
mysql -h localhost -u alliance_user -p alliance_db -e "SELECT 1;"

# 3. 權限檢查
mysql -u root -p << 'SQLEOF'
SELECT User, Host FROM mysql.user WHERE User='alliance_user';
SHOW GRANTS FOR 'alliance_user'@'localhost';
SQLEOF

# 4. 連接數檢查
mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';"
mysql -u root -p -e "SHOW VARIABLES LIKE 'max_connections';"
```

**修復方案**
```bash
# 方案 A：重建用戶權限
mysql -u root -p << 'SQLEOF'
DROP USER IF EXISTS 'alliance_user'@'localhost';
CREATE USER 'alliance_user'@'localhost' IDENTIFIED BY 'alliance_secure_password';
GRANT ALL PRIVILEGES ON alliance_db.* TO 'alliance_user'@'localhost';
FLUSH PRIVILEGES;
SQLEOF

# 方案 B：增加連接數限制
mysql -u root -p -e "SET GLOBAL max_connections = 200;"
# 永久設定：編輯 /etc/mysql/mysql.conf.d/mysqld.cnf
echo "max_connections = 200" >> /etc/mysql/mysql.conf.d/mysqld.cnf

# 方案 C：重啟 MySQL
systemctl restart mysql
```

---

### 故障類型 5：MQTT 通訊中斷

**症狀描述**
- 設備無法發送資料
- MQTT 訊息遺失
- 連接頻繁斷開

**診斷步驟**
```bash
# 1. MQTT Broker 狀態
systemctl status mosquitto
netstat -tulpn | grep :1883

# 2. 連接測試
mosquitto_pub -h localhost -t "test/topic" -m "test message"
mosquitto_sub -h localhost -t "test/topic" -C 1

# 3. 檢查 MQTT 日誌
tail -50 /var/log/mosquitto/mosquitto.log

# 4. 檢查配置
cat /etc/mosquitto/mosquitto.conf
ls -la /etc/mosquitto/conf.d/
```

**修復方案**
```bash
# 方案 A：重啟 MQTT Broker
systemctl restart mosquitto
sleep 5
mosquitto_sub -h localhost -t '$SYS/broker/uptime' -C 1

# 方案 B：檢查配置檔案
# 確認 mosquitto.conf 正確
cat > /etc/mosquitto/conf.d/alliance.conf << 'CONFEOF'
# Alliance MQTT 配置
listener 1883 localhost
allow_anonymous true
max_connections 1000
CONFEOF

systemctl reload mosquitto

# 方案 C：清理持久會話
# 停止服務並清理資料
systemctl stop mosquitto
rm -rf /var/lib/mosquitto/mosquitto.db
systemctl start mosquitto
```

---

### 故障類型 6：效能降級

**症狀描述**
- API 回應時間超過 1 秒
- 資料庫查詢緩慢
- 系統負載過高

**診斷步驟**
```bash
# 1. 系統效能檢查
top -bn1
iostat -x 1 5
sar -u 1 5

# 2. 資料庫效能分析
mysql -u root -p alliance_db << 'SQLEOF'
-- 檢查慢查詢
SHOW VARIABLES LIKE 'slow_query_log';
SELECT COUNT(*) FROM mysql.slow_log WHERE start_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR);

-- 檢查鎖等待
SHOW ENGINE INNODB STATUS\G

-- 檢查表大小
SELECT 
    TABLE_NAME,
    ROUND(DATA_LENGTH/1024/1024, 2) as data_mb,
    TABLE_ROWS
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'alliance_db'
ORDER BY DATA_LENGTH DESC;
SQLEOF

# 3. 應用程式效能
# 檢查連接池使用率
grep "pool" /var/log/alliance/app.log | tail -20

# 4. 網路延遲
ping -c 10 localhost
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8080/api/health
```

**修復方案**
```bash
# 方案 A：資料庫調優
mysql -u root -p alliance_db << 'SQLEOF'
-- 建立缺失的索引
CREATE INDEX idx_users_email ON users(email) IF NOT EXISTS;
CREATE INDEX idx_transactions_user_time ON transactions(user_id, created_at) IF NOT EXISTS;

-- 更新統計資訊
ANALYZE TABLE users, transactions, revenue_facts;

-- 清理過期資料
DELETE FROM log_entries WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
SQLEOF

# 方案 B：調整系統參數
# 增加檔案描述符限制
echo "alliance soft nofile 65536" >> /etc/security/limits.conf
echo "alliance hard nofile 65536" >> /etc/security/limits.conf

# 調整 MySQL 參數
cat >> /etc/mysql/mysql.conf.d/mysqld.cnf << 'CONFEOF'
innodb_buffer_pool_size = 2G
innodb_log_file_size = 512M
query_cache_size = 256M
tmp_table_size = 256M
max_heap_table_size = 256M
CONFEOF

systemctl restart mysql

# 方案 C：應用程式調優
# 調整連接池設定
sed -i 's/pool_size=10/pool_size=20/' /home/ubuntu/alliance/config/database.conf
sed -i 's/timeout=30/timeout=60/' /home/ubuntu/alliance/config/database.conf
systemctl restart alliance-api
```

---

## 🔧 診斷工具和指令

### 系統診斷工具
```bash
#!/bin/bash
# Alliance 系統完整診斷腳本
# 檔案：/home/ubuntu/scripts/alliance_diagnosis.sh

echo "=== Alliance 系統完整診斷 $(date) ==="
echo ""

# 1. 基本系統資訊
echo "1. 系統基本資訊"
echo "  主機名稱：$(hostname)"
echo "  系統版本：$(lsb_release -d | cut -f2)"
echo "  核心版本：$(uname -r)"
echo "  系統負載：$(uptime | awk -F'load average:' '{print $2}')"
echo ""

# 2. 服務狀態
echo "2. 關鍵服務狀態"
services=("alliance-api" "mysql" "redis" "mosquitto" "nginx")
for service in "${services[@]}"; do
    status=$(systemctl is-active $service 2>/dev/null || echo "not-found")
    echo "  $service: $status"
done
echo ""

# 3. 資源使用率
echo "3. 系統資源使用率"
echo "  CPU 使用率：$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')"
echo "  記憶體使用：$(free -h | grep Mem | awk '{print $3"/"$2" ("int($3/$2*100)"%)"}')"
echo "  磁碟使用：$(df -h / | tail -1 | awk '{print $3"/"$2" ("$5")"}')"
echo ""

# 4. 網路連接
echo "4. 網路連接檢查"
ports=("3306" "6379" "1883" "8080")
for port in "${ports[@]}"; do
    if netstat -tulpn | grep ":$port " >/dev/null; then
        echo "  埠 $port：✅ 監聽中"
    else
        echo "  埠 $port：❌ 未監聽"
    fi
done
echo ""

# 5. API 健康檢查
echo "5. API 健康檢查"
response=$(curl -s -w "%{http_code}" http://localhost:8080/api/health -o /dev/null)
if [ "$response" = "200" ]; then
    echo "  API 健康狀態：✅ 正常 (HTTP $response)"
else
    echo "  API 健康狀態：❌ 異常 (HTTP $response)"
fi

# 測試認證
auth_response=$(curl -s -w "%{http_code}" \
    -H "X-Internal-Key: v9-internal-key-2026" \
    http://localhost:8080/api/test -o /dev/null)
echo "  認證測試：HTTP $auth_response"
echo ""

# 6. 資料庫連接
echo "6. 資料庫連接檢查"
if mysql -u alliance_user -p alliance_db -e "SELECT 1;" 2>/dev/null; then
    echo "  資料庫連接：✅ 正常"
else
    echo "  資料庫連接：❌ 失敗"
fi

# 檢查連接數
connections=$(mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';" 2>/dev/null | tail -1 | awk '{print $2}')
echo "  當前連接數：$connections"
echo ""

# 7. 最近錯誤
echo "7. 最近錯誤日誌 (最新 5 筆)"
if [ -f /var/log/alliance/error.log ]; then
    tail -5 /var/log/alliance/error.log | while read line; do
        echo "  $line"
    done
else
    echo "  錯誤日誌檔案不存在"
fi
echo ""

echo "=== 診斷完成 ==="
```

### 效能監控指令
```bash
# 即時效能監控
#!/bin/bash
# 檔案：/home/ubuntu/scripts/alliance_monitor.sh

while true; do
    clear
    echo "=== Alliance 即時監控 $(date) ==="
    echo ""
    
    # CPU 和記憶體
    echo "系統資源："
    top -bn1 | head -5
    echo ""
    
    # API 回應時間
    echo "API 效能："
    time_total=$(curl -w "%{time_total}" -o /dev/null -s http://localhost:8080/api/health)
    echo "  回應時間：${time_total}s"
    
    # 資料庫連接
    connections=$(mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';" 2>/dev/null | tail -1 | awk '{print $2}')
    echo "  DB 連接數：$connections"
    
    # 最新錯誤
    echo ""
    echo "最新錯誤："
    tail -3 /var/log/alliance/error.log 2>/dev/null | tail -1
    
    sleep 5
done
```

---

## 📋 故障處理記錄範本

### 故障報告範本
```
【Alliance 故障報告】

時間：2026-06-18 14:40:49
報告人：[Agent 名稱]
嚴重度：[Critical/High/Medium/Low]

=== 故障描述 ===
[詳細描述故障現象]

=== 影響範圍 ===
[說明受影響的功能和用戶]

=== 診斷過程 ===
1. [執行的診斷指令和結果]
2. [檢查的日誌和發現]
3. [測試的功能和狀態]

=== 根本原因 ===
[分析得出的根本原因]

=== 修復措施 ===
[執行的修復步驟和結果驗證]

=== 預防措施 ===
[避免類似問題的改進建議]

=== 附件 ===
- 錯誤日誌截圖
- 診斷指令輸出
- 系統狀態快照
```

---

## 🔗 文件神經連結

- 上級文件：`06_alliance_system/README.md`
- 快速診斷：`06_alliance_system/QUICK_DIAGNOSIS_SOP.md`
- 問題解決：`06_alliance_system/SEVEN_CRITICAL_FIXES.md`
- 維護指南：`06_alliance_system/MAINTENANCE_BEST_PRACTICES.md`
- 基礎設施：`04_deployment_operations/INFRASTRUCTURE_REFERENCE.md`
