# Alliance 系統快速診斷修復 SOP


**[On-Demand]** — 上下文注入策略

> **文檔版本**：1.0  
> **最後更新**：2026-06-18  
> **編寫角色**：HQ (協調者)  
> **執行時間**：緊急故障 < 15 分鐘診斷

---

## 🚨 緊急診斷流程 (5 分鐘內)

### 第一步：系統狀態快檢
```bash
# 1. 服務運行狀態
systemctl status alliance-api
systemctl status mysql
systemctl status redis
systemctl status mosquitto

# 2. 網路連通性
ping 141.148.165.50
telnet 141.148.165.50 3306  # MySQL
telnet 141.148.165.50 6379  # Redis
```

### 第二步：關鍵配置驗證
```bash
# 1. 環境配置檢查
cat /home/ubuntu/alliance/.env | grep -E "(DB_|REDIS_|MQTT_)"

# 2. 認證金鑰確認
grep "CALLBACK_INTERNAL_KEY" /home/ubuntu/alliance/.env

# 3. 日誌檔案檢查
tail -20 /var/log/alliance/app.log
tail -20 /var/log/alliance/error.log
```

### 第三步：資料庫連接測試
```bash
# 1. MySQL 連接測試
mysql -h localhost -u alliance_user -p alliance_db -e "SELECT 1;"

# 2. Redis 連接測試
redis-cli ping

# 3. 關鍵表存在性檢查
mysql -u root -p -e "USE alliance_db; SHOW TABLES;"
```

---

## 🔍 問題分類診斷

### A. HTTP 401/403 錯誤
**症狀**：API 呼叫返回認證失敗
```bash
# 診斷步驟
1. 確認金鑰：cat /home/ubuntu/alliance/.env | grep CALLBACK_INTERNAL_KEY
2. 測試呼叫：curl -H "X-Internal-Key: v9-internal-key-2026" http://localhost:8080/api/health
3. 檢查日誌：tail -50 /var/log/alliance/access.log
```

### B. HTTP 500 錯誤
**症狀**：服務器內部錯誤
```bash
# 診斷步驟
1. 檢查應用日誌：tail -100 /var/log/alliance/error.log
2. 資料庫連接：mysql -u alliance_user -p alliance_db -e "SELECT 1;"
3. 磁碟空間：df -h
4. 記憶體使用：free -h
```

### C. 資料庫錯誤
**症狀**：SQL 執行失敗、表不存在
```bash
# 診斷步驟
1. 檢查資料庫服務：systemctl status mysql
2. 驗證資料庫存在：mysql -u root -p -e "SHOW DATABASES LIKE 'alliance%';"
3. 檢查表結構：mysql -u root -p alliance_db -e "SHOW TABLES;"
4. 權限檢查：mysql -u root -p -e "SHOW GRANTS FOR 'alliance_user'@'localhost';"
```

### D. 網路連接問題
**症狀**：外部 API 呼叫失敗、超時
```bash
# 診斷步驟
1. 防火牆檢查：ufw status
2. 埠占用檢查：netstat -tulpn | grep :8080
3. DNS 解析：nslookup alliance.domain.com
4. 外部連接：curl -I http://alliance.domain.com/api/health
```

---

## ⚡ 標準修復程序

### 程序 A：服務重啟修復
```bash
#!/bin/bash
# 標準服務重啟順序

echo "=== Alliance 系統重啟程序 ==="

# 1. 停止應用服務
systemctl stop alliance-api
sleep 5

# 2. 檢查依賴服務
systemctl restart mysql
systemctl restart redis
systemctl restart mosquitto
sleep 10

# 3. 重啟應用服務
systemctl start alliance-api
sleep 5

# 4. 驗證服務狀態
systemctl status alliance-api
curl -f http://localhost:8080/api/health || echo "服務啟動失敗"
```

### 程序 B：資料庫修復
```sql
-- 資料庫緊急修復腳本

-- 1. 檢查資料庫完整性
CHECK TABLE users;
CHECK TABLE transactions;
CHECK TABLE revenue_facts;

-- 2. 修復損壞的表
REPAIR TABLE users;
REPAIR TABLE transactions;

-- 3. 重建索引
ALTER TABLE users DROP INDEX idx_user_id;
ALTER TABLE users ADD INDEX idx_user_id (user_id);

-- 4. 更新統計資訊
ANALYZE TABLE users;
ANALYZE TABLE transactions;
```

### 程序 C：配置復原
```bash
#!/bin/bash
# 配置檔案復原程序

# 1. 備份當前配置
cp /home/ubuntu/alliance/.env /home/ubuntu/alliance/.env.backup.$(date +%Y%m%d_%H%M%S)

# 2. 復原標準配置
cat > /home/ubuntu/alliance/.env << 'ENVEOF'
# Alliance 系統標準配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=alliance_db
DB_USER=alliance_user
DB_PASSWORD=alliance_secure_password

REDIS_HOST=localhost
REDIS_PORT=6379

MQTT_HOST=localhost
MQTT_PORT=1883

CALLBACK_INTERNAL_KEY=v9-internal-key-2026
LOG_LEVEL=INFO
LOG_PATH=/var/log/alliance/
ENVEOF

# 3. 重啟服務
systemctl restart alliance-api
```

---

## 📊 效能監控指標

### 關鍵指標閾值
| 指標 | 正常值 | 警告值 | 危險值 |
|------|--------|--------|--------|
| CPU 使用率 | < 70% | 70-85% | > 85% |
| 記憶體使用率 | < 80% | 80-90% | > 90% |
| 磁碟使用率 | < 85% | 85-95% | > 95% |
| API 回應時間 | < 200ms | 200-500ms | > 500ms |
| 資料庫連接數 | < 50 | 50-80 | > 80 |

### 監控命令
```bash
# 即時監控腳本
#!/bin/bash

echo "=== Alliance 系統健康檢查 ==="
echo "時間：$(date)"
echo ""

# CPU 和記憶體
echo "CPU 使用率：$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d% -f1)%"
echo "記憶體使用率：$(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"

# 磁碟空間
echo "磁碟使用率："
df -h | grep -E "(/$|/var|/home)"

# 服務狀態
echo ""
echo "服務狀態："
systemctl is-active alliance-api mysql redis mosquitto

# API 健康檢查
echo ""
echo "API 健康狀態："
curl -s -o /dev/null -w "回應時間: %{time_total}s, HTTP 狀態: %{http_code}" http://localhost:8080/api/health
echo ""
```

---

## 🔄 預防性維護

### 每日檢查清單
- [ ] 檢查系統日誌錯誤
- [ ] 監控磁碟空間使用率
- [ ] 驗證資料庫備份完成
- [ ] 檢查 API 回應時間

### 每週檢查清單
- [ ] 清理過期日誌檔案
- [ ] 檢查資料庫效能統計
- [ ] 更新系統安全補丁
- [ ] 驗證監控告警正常

### 每月檢查清單
- [ ] 完整系統備份
- [ ] 檢查資料庫索引效能
- [ ] 審查系統配置變更
- [ ] 更新文檔和 SOP

---

## 🚨 緊急聯絡程序

### 故障升級機制
1. **Level 1**：自動修復 (< 5 分鐘)
2. **Level 2**：Allie Agent 處理 (< 15 分鐘)
3. **Level 3**：HQ 協調其他 Agent (< 30 分鐘)
4. **Level 4**：人工介入 (通知 Joe)

### 通報格式
```
緊急故障通報
時間：2026-06-18 14:39:18
系統：Alliance
嚴重度：[Critical/High/Medium/Low]
影響範圍：[具體描述]
已執行步驟：[列出已嘗試的修復步驟]
當前狀態：[系統當前狀態]
需要協助：[需要什麼支援]
```

---

## 🔗 文件神經連結

- 上級文件：`06_alliance_system/README.md`
- 問題解決：`06_alliance_system/SEVEN_CRITICAL_FIXES.md`
- 維護指南：`06_alliance_system/MAINTENANCE_BEST_PRACTICES.md`
- 基礎設施：`04_deployment_operations/INFRASTRUCTURE_REFERENCE.md`
