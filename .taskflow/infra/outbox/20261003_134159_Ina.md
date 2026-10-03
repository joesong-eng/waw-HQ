# 任務回報

任務 ID: TASK_20261003_INA_GRANT_MEMBER_DB_ACCESS_AND_FIX_OWNER_ENV
執行者: Ina (Infra / DB)
完成時間: 2026-10-03 12:30 CST
結論: 完成

## 項目 1: GRANT waw_member_api@129.153.116.174

前置查詢: waw_member_api 原有 Host = 127.0.0.1, 137.131.50.16 (無 129.153.116.174)

執行 SQL (via /etc/mysql/debian.cnf on infra):
  CREATE USER IF NOT EXISTS 'waw_member_api'@'129.153.116.174' IDENTIFIED BY 'WawMember2026_SecureKey';
  GRANT SELECT, INSERT, UPDATE ON waw_member_production.* TO 'waw_member_api'@'129.153.116.174';
  FLUSH PRIVILEGES;

SHOW GRANTS 驗證:
  GRANT USAGE ON *.* TO waw_member_api@129.153.116.174
  GRANT SELECT, INSERT, UPDATE ON waw_member_production.* TO waw_member_api@129.153.116.174

只有 SELECT/INSERT/UPDATE，未給 DELETE/DROP/GRANT。

## 項目 2: 補 Owner VPS .env MEMBER_DB 設定

主機: yd174 (129.153.116.174)
路徑: /www/wwwroot/iot.tg25.win/.env

追加 (python3 append，已確認未重複):
  MEMBER_DB_HOST=141.148.165.50
  MEMBER_DB_PORT=3306
  MEMBER_DB_DATABASE=waw_member_production
  MEMBER_DB_USERNAME=waw_member_api
  MEMBER_DB_PASSWORD=WawMember2026_SecureKey

config:clear + config:cache: INFO Configuration cached successfully.

## 驗收佐證

php 實測 (Owner VPS /www/wwwroot/iot.tg25.win, 測試檔執行後已刪除):
  {"pdo_class":"Pdo\Mysql","members_count":13}

- DB::connection('mysql_member')->getPdo() = PdoMysql OK
- ->table('members')->count() = 13 (無例外) OK

fileinfo warning 為既有非阻塞警告。

## 結論

兩項目完成，Owner 跨庫連線 waw_member_production 驗收通過。
