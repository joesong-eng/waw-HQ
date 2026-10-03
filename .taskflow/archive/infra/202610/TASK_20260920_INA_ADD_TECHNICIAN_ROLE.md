# 任務：新增 technician 角色與 expires_at 欄位

**派工時間**：2026-09-20  
**派工者**：HQ  
**執行者**：Ina  
**優先級**：high  
**關聯背景**：Sophie 報告 20260920_REPORT_TECH_OPERATOR_ROLE_SEPARATION_SPEC.md

---

## 任務背景

老李（owner）需要能為技術對接人員（小猴）開立臨時帳號，讓小猴登入 signal.tg25.win 完成 SignalHub 設定。  
目前 `users.role` ENUM 不含 `technician`，且無帳號效期機制，導致老李無法安全地臨時委任技術人員。

---

## 執行項目

### 1. Migration：新增 technician 到 role ENUM

**資料庫**：iotv9（Production，透過 Infra 遠端執行）  
**目標表**：`users`  
**欄位**：`role`

Migration 檔案建立於 Owner 專案：`PROJECT/Owner/database/migrations/`

```php
// 建議 migration 內容
Schema::table('users', function (Blueprint $table) {
    // MySQL ENUM 修改需用 DB::statement
    DB::statement("ALTER TABLE users MODIFY COLUMN role ENUM('admin','owner','staff','sub_agent','technician') NOT NULL DEFAULT 'owner'");
});
```

**驗證**：遠端執行後確認 ENUM 值已更新。

---

### 2. Migration：新增 expires_at 欄位

**目標表**：`users`  
**欄位**：`expires_at` datetime NULL（預設 NULL = 永不過期）

```php
Schema::table('users', function (Blueprint $table) {
    $table->dateTime('expires_at')->nullable()->after('status');
});
```

**用途**：老李開 technician 帳時可選填效期，到期帳號自動視為停用。  
**驗證**：遠端確認欄位存在、nullable、預設 NULL。

---

### 3. User Model 更新

**檔案**：`PROJECT/Owner/app/Models/User.php`  
- `$fillable` 加入 `'expires_at'`  
- `casts()` 加入 `'expires_at' => 'datetime'`

SignalHub 的 `PROJECT/SignalHub/app/Models/User.php` 同步相同修改。

---

## 驗證要求

1. 遠端 `php artisan migrate` 成功（無 error）
2. `DESCRIBE users;` 確認 role ENUM 含 technician、expires_at 欄位存在
3. Git commit + push（Owner 專案）

---

## 回報格式

完成後提交至 `.taskflow/infra/outbox/`，內容包含：
- Migration 檔案名稱與 commit hash
- 遠端 DESCRIBE 結果截圖或文字輸出
- 是否有任何衝突或 downtime 風險

