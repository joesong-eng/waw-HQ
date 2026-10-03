# 執行回報：新增 technician 角色與 expires_at 欄位

**回報時間**：2026-09-20 (台北時間)
**執行者**：Ina (Infra Master)
**任務**：TASK_20260920_INA_ADD_TECHNICIAN_ROLE
**狀態**：✅ 完成

---

## 執行摘要

### 1. DB Migration：新增 technician 角色 ENUM

**資料庫**：iotv9 (Production)
**目標表**：users
**欄位**：role

**變更前**：
role ENUM('admin','owner','staff','boss','partner','sub_agent') NOT NULL DEFAULT 'owner'

**變更後**：
role ENUM('admin','owner','staff','boss','partner','sub_agent','technician') NOT NULL DEFAULT 'owner'

> 注意：工單建議的 ENUM 值缺少 boss 和 partner，已修正為保留所有現有值 + 新增 technician。

### 2. DB Migration：新增 expires_at 欄位

**目標表**：users
**新增欄位**：expires_at DATETIME NULL DEFAULT NULL

ALTER TABLE iotv9.users ADD COLUMN expires_at DATETIME NULL DEFAULT NULL COMMENT '帳號效期（NULL=永不過期，技術人員臨時帳號用）' AFTER line_binding_expires_at;

### DESCRIBE users 驗證結果

| Field | Type | Null | Key | Default |
|:---|:---|:---|:---|:---|
| id | bigint unsigned | NO | PRI | None |
| name | varchar(255) | NO | | None |
| email | varchar(255) | NO | UNI | None |
| phone | varchar(20) | YES | MUL | None |
| email_verified_at | timestamp | YES | | None |
| password | varchar(255) | NO | | None |
| role | enum('admin','owner','staff','boss','partner','sub_agent','technician') | NO | | owner |
| partner_id | bigint unsigned | YES | MUL | None |
| root_id | bigint unsigned | YES | MUL | None |
| status | tinyint | NO | | 1 |
| line_id | varchar(255) | YES | | None |
| tg_id | varchar(255) | YES | | None |
| outstanding_amount | decimal(12,2) | NO | | 0.00 |
| remember_token | varchar(100) | YES | | None |
| created_at | timestamp | YES | | None |
| updated_at | timestamp | YES | | None |
| line_binding_code | varchar(6) | YES | | None |
| line_binding_expires_at | timestamp | YES | | None |
| expires_at | datetime | YES | | None |

---

## 建立的檔案

### Migration 檔案

1. Owner (Laravel): PROJECT/Owner/database/migrations/2026_09_20_223000_add_technician_role_and_expires_at_to_users_table.php
2. SignalHub (Laravel): PROJECT/SignalHub/database/migrations/2026_09_20_223000_add_technician_role_and_expires_at_to_users_table.php
3. Infra (SQL): PROJECT/Infra/db/migrations/20260920_add_technician_role_and_expires_at_to_users.sql

### Model 更新

1. Owner User Model (PROJECT/Owner/app/Models/User.php):
   - fillable 新增 expires_at
   - casts 新增 expires_at => datetime
   - 新增 isExpired() 方法

2. SignalHub User Model (PROJECT/SignalHub/app/Models/User.php):
   - fillable 新增 expires_at
   - casts 新增 expires_at => datetime
   - 新增 isExpired() 方法

---

## Git 提交紀錄

| 專案 | Commit | 訊息 |
|:---|:---|:---|
| Owner | f537334 | feat: add technician role ENUM and expires_at column |
| SignalHub | 505dde0 | feat: add technician role ENUM and expires_at column |
| Infra | 6f70f58 | feat: add technician role and expires_at SQL migration |

三個專案均已 push 至 GitHub origin/main。遠端 Infra 已 git pull 同步。

---

## 後續建議

1. Sophie (Owner): 需在 Owner 後台用戶管理控制器和視圖加入 technician 角色選項與 expires_at 日期選擇器
2. Sidney (SignalHub): 需在 SignalHub 認證中介層檢查 expires_at 是否過期，過期帳號應被拒絕登入
3. API 層: Owner 的 DELETE /users/{id} 端點（帳號生命週期管理）尚待 Sophie 實作

---

**Ina (Infra Master) - 任務完成**
