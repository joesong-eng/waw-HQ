# 執行回報：technician migration 冪等修補

**回報時間**：2026-09-20 (台北時間)
**執行者**：Ina (Infra Master)
**任務**：TASK_20260920_INA_FIX_TECHNICIAN_MIGRATION_IDEMPOTENCY
**狀態**：✅ 完成

---

## 問題摘要

前置任務 (TASK_20260920_INA_ADD_TECHNICIAN_ROLE) 直接以 SQL 執行了 ALTER TABLE，
schema 正確落地，但遺漏了兩件事：

1. **Laravel migrations 帳本未記錄** — iotv9.migrations 表中沒有此 migration 的記錄
2. **migration up() 不冪等** — 裸 ADD COLUMN 會在下次部署 php artisan migrate --force 時撞 Duplicate column

---

## 修補內容

### 1. 改寫 migration 為冪等版本

兩份 migration 的 up() 重寫為先查 information_schema 再決定是否 ALTER：

**Owner**: 2026_09_20_223000_add_technician_role_and_expires_at_to_users_table.php
**SignalHub**: 2026_09_20_223000_add_technician_role_and_expires_at_to_users_table.php

up() 核心邏輯：
- role: SELECT COLUMN_TYPE → 如果不含 technician 才 MODIFY COLUMN
- expires_at: SELECT COLUMN_NAME → 如果不存在才 ADD COLUMN

### 2. 補入 iotv9.migrations 表記錄

INSERT INTO migrations (migration, batch) VALUES
  ('2026_09_20_223000_add_technician_role_and_expires_at_to_users_table', 19)

結果：id=62, batch=19

### 3. 更新 Infra SQL migration 為冪等版

20260920_add_technician_role_and_expires_at_to_users.sql 改為含 information_schema 檢查的版本

---

## 驗證結果

### iotv9.migrations 表

| id | migration | batch |
|:---|:---|:---|
| 62 | 2026_09_20_223000_add_technician_role_and_expires_at_to_users_table | 19 |

### SHOW COLUMNS FROM users LIKE 'role'

| Field | Type | Null | Default |
|:---|:---|:---|:---|
| role | enum('admin','owner','staff','boss','partner','sub_agent','technician') | NO | owner |

### SHOW COLUMNS FROM users LIKE 'expires_at'

| Field | Type | Null | Default |
|:---|:---|:---|:---|
| expires_at | datetime | YES | None |

### php artisan migrate --pretend --force

- **Owner** (iot.tg25.win): "Nothing to migrate." ✅
- **SignalHub** (signal.tg25.win): "Nothing to migrate." ✅

兩邊都正確識別 migration 已在 migrations 表中（batch=19），不會重跑。

### technician 用戶數

count=0（符合預期，尚未開立任何 technician 帳號）

---

## Git 提交紀錄

| 專案 | Commit | 訊息 |
|:---|:---|:---|
| Owner | 749ca95 | fix: make technician migration idempotent |
| SignalHub | d10d3a0 | fix: make technician migration idempotent |
| Infra | 633b0f0 | fix: make SQL migration idempotent |

三個專案均已 push 至 GitHub origin/main。遠端均已 git pull 同步。

---

## 冪等保證分析

### 場景：部署腳本執行 php artisan migrate --force

1. Laravel 查 iotv9.migrations → 找到 batch=19 記錄 → 跳過此 migration → "Nothing to migrate"
2. 即使 migrations 表被意外刪除，up() 也會先查 information_schema：
   - role 已含 technician → 跳過 MODIFY
   - expires_at 已存在 → 跳過 ADD COLUMN
3. 零傷害，重跑安全

### 場景：全新資料庫 restore

1. migrations 表為空 → Laravel 執行 migration
2. up() 查 information_schema → role 不含 technician → 執行 MODIFY
3. up() 查 information_schema → expires_at 不存在 → 執行 ADD COLUMN
4. 正確建立 schema

---

**Ina (Infra Master) - 補單完成，風險已收口**
