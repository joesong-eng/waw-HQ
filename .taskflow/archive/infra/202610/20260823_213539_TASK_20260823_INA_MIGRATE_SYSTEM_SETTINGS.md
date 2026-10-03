# 任務：TASK_20260823_INA_MIGRATE_SYSTEM_SETTINGS

**派發時間**：2026-08-23 21:35  
**優先級**：high  
**負責人**：infra

---

## 📋 任務內容

請 Ina (Infra) 協助在生產資料庫 (iotv9) 執行建立 system_settings 資料表的 Migration，以解決後端服務查詢缺失表導致的 SQL 報錯。

Migration 檔案位置：
PROJECT/Owner/database/migrations/2026_08_23_000001_create_system_settings_table.php

SQL 結構參考：
CREATE TABLE IF NOT EXISTS  (
  uid=501(ilawusong) gid=20(staff) groups=20(staff),12(everyone),61(localaccounts),79(_appserverusr),80(admin),81(_appserveradm),98(_lpadmin),702(com.apple.sharepoint.group.2),701(com.apple.sharepoint.group.1),33(_appstore),100(_lpoperator),204(_developer),250(_analyticsusers),395(com.apple.access_ftp),398(com.apple.access_screensharing),399(com.apple.access_ssh),400(com.apple.access_remote_ae) bigint(20) unsigned NOT NULL AUTO_INCREMENT,
   varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
   text COLLATE utf8mb4_unicode_ci,
   varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'string',
   varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   timestamp NULL DEFAULT NULL,
   timestamp NULL DEFAULT NULL,
  PRIMARY KEY (uid=501(ilawusong) gid=20(staff) groups=20(staff),12(everyone),61(localaccounts),79(_appserverusr),80(admin),81(_appserveradm),98(_lpadmin),702(com.apple.sharepoint.group.2),701(com.apple.sharepoint.group.1),33(_appstore),100(_lpoperator),204(_developer),250(_analyticsusers),395(com.apple.access_ftp),398(com.apple.access_screensharing),399(com.apple.access_ssh),400(com.apple.access_remote_ae)),
  UNIQUE KEY  (),
  KEY  ()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

預設資料：
INSERT INTO  (, , , , , )
VALUES 
('device_session_inactivity_timeout', '30', 'integer', '設備閒置超時（分鐘）', NOW(), NOW()),
('device_session_absolute_timeout', '480', 'integer', '設備絕對超時（分鐘）', NOW(), NOW())
ON DUPLICATE KEY UPDATE  = NOW();

請 Ina 執行後更新 DB_MANIFEST.md 並提交回報。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260823_INA_MIGRATE_SYSTEM_SETTINGS

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：infra

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：infra  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-08-23 21:35
