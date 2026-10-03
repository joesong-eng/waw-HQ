# 任務工單：授權 waw_member_api 外部連線並補 Owner .env MEMBER_DB 設定

**工單編號**：TASK_20261003_INA_GRANT_MEMBER_DB_ACCESS_AND_FIX_OWNER_ENV  
**派發時間**：2026-10-03  
**負責人**：Ina (Infra / DB)  
**優先級**：P1 (High)  
**關聯模組**：Infra (141.148.165.50) + Owner (yd174)

---

## 🎯 背景

Owner VPS（`yd174 / 129.153.116.174`）的 `BillAcceptorService` 與 `NightlyRevenueReconcile` 需跨庫連線 `waw_member_production`（位於 `141.148.165.50:3306`）。

**遠端實測結果**：
```
SQLSTATE[HY000] [1045] Access denied for user 'waw_member_api'@'129.153.116.174'
```

根因：
1. MySQL 未授權 `waw_member_api` 從 `129.153.116.174`（Owner VPS）連入。
2. Owner VPS `.env` 完全沒有 `MEMBER_DB_*` 設定，config 預設走 `127.0.0.1:3307`（Connection refused）。

---

## 📋 具體實作項目

### 項目 1：在 Infra DB 授權 waw_member_api 外部連入

SSH 至 `141.148.165.50`，以有權限帳號執行：

```sql
-- 查現有授權
SHOW GRANTS FOR 'waw_member_api'@'%';
SHOW GRANTS FOR 'waw_member_api'@'129.153.116.174';

-- 若無授權，執行：
GRANT SELECT, INSERT, UPDATE ON waw_member_production.* 
    TO 'waw_member_api'@'129.153.116.174' 
    IDENTIFIED BY 'WawMember2026_SecureKey';
FLUSH PRIVILEGES;
```

> 權限範圍：僅 SELECT / INSERT / UPDATE，不給 DROP / DELETE / GRANT。

### 項目 2：補 Owner VPS .env MEMBER_DB 設定

在 `yd174` 的 `/www/wwwroot/iot.tg25.win/.env` 追加：

```
MEMBER_DB_HOST=141.148.165.50
MEMBER_DB_PORT=3306
MEMBER_DB_DATABASE=waw_member_production
MEMBER_DB_USERNAME=waw_member_api
MEMBER_DB_PASSWORD=WawMember2026_SecureKey
```

追加後執行：
```bash
php artisan config:clear
php artisan config:cache
```

---

## 🔍 驗收指標

1. **連線測試**（Owner VPS 遠端 Tinker）：
   ```
   DB::connection('mysql_member')->getPdo()
   ```
   必須回傳 PDO 物件，不得拋 Access Denied 或 Connection refused。

2. **實務查詢測試**：
   ```php
   DB::connection('mysql_member')->table('members')->count()
   ```
   回傳數字（含 0），無例外。

3. 回報至 `.taskflow/infra/outbox/`，附帶 GRANT 執行結果與 Tinker 測試截圖或輸出。

