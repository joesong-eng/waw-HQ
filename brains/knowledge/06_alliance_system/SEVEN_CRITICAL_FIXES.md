# Alliance 系統七個主要問題解決方案


**[On-Demand]** — 上下文注入策略

> **文檔版本**：1.0  
> **最後更新**：2026-06-18  
> **編寫角色**：HQ (協調者)  
> **適用場景**：Alliance 系統故障診斷與修復

---

## 問題 1：資料庫交叉污染問題

### 症狀描述
- Alliance 資料庫出現異常
- waw2.0 系統疑似影響 Alliance 資料庫
- 資料庫連接配置混亂

### 根本原因
- waw2.0 migration 意外影響其他資料庫
- 資料庫隔離機制不完善
- 連接字串配置錯誤

### 解決方案
```bash
# 1. 檢查資料庫配置
cat /path/to/alliance/.env | grep DB_
cat /path/to/waw-core/.env | grep DB_

# 2. 確認連接隔離
mysql -u root -p -e "SHOW DATABASES;"

# 3. 修正配置檔案
# 確保 Alliance 和 waw2.0 使用不同的資料庫名稱
```

### 預防措施
- 嚴格的資料庫命名規範
- Migration 前必須備份
- 定期檢查資料庫隔離

---

## 問題 2：API 認證失敗 (401 錯誤)

### 症狀描述
- 自製 `test_webhook.sh` 全程拿到 401
- 誤判為 Member Webhook 路由問題
- 花費大量時間排查錯誤方向

### 根本原因
- **認證金鑰填寫錯誤**
- 混淆 401 (認證問題) 與 404/405 (路由問題)

### 解決方案
```bash
# 1. 最先檢查：確認真實 Key
cat /home/ubuntu/tg25-infra/api/credit-relay/.env

# 2. 正確金鑰配置
CALLBACK_INTERNAL_KEY=v9-internal-key-2026

# 3. 正確 Header 名稱
X-Internal-Key: v9-internal-key-2026
```

### 防坑規則
1. **401 = 認證問題，404/405 = 路由問題**
2. 第一步必須驗證金鑰正確性
3. 不要混淆錯誤類型進行排查

---

## 問題 3：系統部署架構混亂

### 症狀描述
- 部署路徑不一致
- 環境配置缺失
- 服務啟動失敗

### 根本原因
- 缺乏統一的部署標準
- 環境變數管理不當
- 服務依賴關係不明確

### 解決方案
```bash
# 1. 標準化部署路徑
/home/ubuntu/alliance/
├── .env
├── api/
├── database/
└── logs/

# 2. 環境配置檢查清單
- DB_HOST, DB_PORT, DB_NAME
- CALLBACK_INTERNAL_KEY
- LOG_LEVEL, LOG_PATH
- REDIS_HOST, REDIS_PORT
```

---

## 問題 4：資料庫 Schema 不一致

### 症狀描述
- 欄位名稱不匹配
- 資料類型錯誤
- Migration 執行失敗

### 根本原因
- 缺乏統一的 Schema 管理
- Migration 版本控制不當

### 解決方案
```sql
-- 1. 檢查當前 Schema
DESCRIBE table_name;

-- 2. 比對標準 Schema
-- 參考：brains/knowledge/02_technical_standards/DB_SCHEMA_WAW2_DELTA.md

-- 3. 執行修復 Migration
ALTER TABLE table_name ADD COLUMN column_name TYPE;
```

---

## 問題 5：MQTT 通訊中斷

### 症狀描述
- 設備無法連線
- 訊息傳遞失敗
- 即時事件中斷

### 根本原因
- MQTT Broker 配置錯誤
- Topic 命名不符合標準

### 解決方案
```bash
# 1. 檢查 MQTT Broker 狀態
systemctl status mosquitto

# 2. 驗證 Topic 標準
# 參考：brains/knowledge/02_technical_standards/MQTT_TOPIC_STANDARD.md

# 3. 重啟服務
systemctl restart mosquitto
```

---

## 問題 6：WebSocket 事件遺漏

### 症狀描述
- 前端無法收到即時事件
- 用戶體驗中斷
- 事件通知延遲

### 根本原因
- WebSocket 頻道配置錯誤
- 事件類型不符合標準

### 解決方案
```javascript
// 1. 檢查頻道配置
// 參考：brains/knowledge/02_technical_standards/WEBSOCKET_CHANNEL_STANDARD.md

// 2. 驗證事件格式
{
  "type": "event_type",
  "data": {},
  "timestamp": "2026-06-18T06:38:42.595Z"
}
```

---

## 問題 7：日誌系統失效

### 症狀描述
- 日誌檔案無法產生
- 錯誤資訊遺失
- 除錯困難

### 根本原因
- 日誌路徑權限不足
- 日誌配置錯誤

### 解決方案
```bash
# 1. 檢查日誌目錄權限
ls -la /var/log/
chmod 755 /var/log/alliance/

# 2. 驗證日誌配置
tail -f /var/log/alliance/app.log

# 3. 重啟日誌服務
systemctl restart rsyslog
```

---

## 🎯 修復優先順序

1. **高優先**：資料庫交叉污染 (影響資料完整性)
2. **高優先**：API 認證失敗 (影響基本功能)
3. **中優先**：系統部署架構 (影響維護效率)
4. **中優先**：資料庫 Schema (影響資料一致性)
5. **低優先**：MQTT 通訊 (影響即時性)
6. **低優先**：WebSocket 事件 (影響用戶體驗)
7. **低優先**：日誌系統 (影響除錯效率)

---

## 🔗 文件神經連結

- 上級文件：`06_alliance_system/README.md`
- 關聯文件：`06_alliance_system/QUICK_DIAGNOSIS_SOP.md`
- 技術標準：`02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md`
