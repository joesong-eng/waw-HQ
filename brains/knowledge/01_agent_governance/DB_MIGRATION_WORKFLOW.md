# 資料庫變更工作流程

> **適用範圍**：所有需要變更 MySQL 資料庫結構的場景（包含分布式專案）  
> **主導人**：Ina (Infra Master - 唯一主持與協調者)  
> **流程類型**：Request-Review-Execute (RRE)

**注意**：本專案為大型分布式架構，各子專案（如 waw-cloud, waw-wallet）使用不同技術棧。Laravel 專案的 `migrations` 表不代表物理資料庫的唯一真相，所有實體結構的變更與對齊必須由 Ina 統一主持與核准。

---

## 🎯 核心原則

**資料庫是系統的心臟，任何變更都必須經過嚴格審查與測試。**

### 三不原則
1. ❌ **不自行執行 ALTER TABLE**（除非是 Ina 本人）
2. ❌ **不跳過 Migration 檔案直接改 Schema**
3. ❌ **不在生產環境直接測試**
4. ❌ **不允許非 Ina 角色在生產環境直接執行 `php artisan migrate`**（避免與實體 schema 衝突）

### 三必須原則
1. ✅ **必須透過 HQ Message Hub 提交需求**
2. ✅ **必須等待 Ina 審核與執行**
3. ✅ **必須有完整的 Rollback 計劃**

---

## 🌐 分布式資料庫對齊規則 (Distributed Schema Alignment Rules)

在分散式開發中，由於資料庫結構變更與代碼部署可能非同步進行，Laravel 等框架的 `migrations` 歷史常與生產環境物理 DDL 產生狀態不一致（例如：欄位已存在，但 Laravel 的 migrations 表顯示該遷移為 Pending）。

為防止部署時執行遷移拋錯，**所有 Schema 與 migration 狀態的對齊均由 Ina 唯一主持**，並依情況採用以下對齊策略：

### 策略 A：資料庫補票（手動註冊遷移記錄）
- **適用場景**：該變更已在資料庫執行完畢，代碼層面的 migration 檔案需要對齊，不希望在生產環境重複執行 DDL 語句。
- **執行方式**：由 Ina 於資料庫 `migrations` 表中，手動插入對應的遷移檔案名稱，標記為已完成（Ran），防止 Laravel 再次執行該 SQL。

### 策略 B：防禦式 Migration 重構（代碼端安全防護）
- **適用場景**：需要確保多環境（開發、測試、生產）部署時皆能自動調適，不發生 Duplicate Column 等錯誤。
- **執行方式**：由 Ina 指導開發 Agent（如 Sophie 或 Mina），在 migration 檔案的 `up()` 方法中使用 `Schema::hasColumn` 或 `Schema::hasTable` 進行防禦式包裹。
  ```php
  if (!Schema::hasColumn('devices', 'column_name')) { ... }
  ```

---

## 📋 工作流程

### 階段 1：需求提交 (Request)

**誰需要提交？**
- Sophie (Owner) - 需要新增或修改 devices, venues 等表
- Mina (Member) - 需要新增或修改 users, transactions 等表
- Hubie (iHub) - 需要新增或修改 kiosk 相關表
- Allie (Alliance) - 需要新增或修改 profit_sharing 等表

**如何提交？**

透過 HQ Message Hub 發送需求：

```bash
# 在你的專案目錄執行
./scripts/agent_report_to_hq.sh <agent_name> _agent/DB_MIGRATION_REQUEST.md
```

**需求文件範本** (`_agent/DB_MIGRATION_REQUEST.md`)：

```markdown
# 資料庫變更需求

> **提交者**：<Agent 名稱>  
> **日期**：<YYYY-MM-DD>  
> **優先級**：High/Normal/Low  
> **目標表**：<table_name>

## 變更目的
<簡述為什麼需要這個變更>

## 變更內容
<具體描述要新增/修改/刪除什麼欄位>

範例：
- 新增欄位：`ticket_mode` ENUM('virtual', 'physical', 'direct') NULL
- 修改欄位：`pulse_ratio` 改名為 `pulse_to_token`
- 刪除欄位：`old_field_name`（請說明為何可以刪除）

## 影響範圍
<哪些 API、哪些功能會受影響？>

## Rollback 計劃
<如果上線後發現問題，如何回退？>
```

### 階段 2：審核與設計 (Review)

**Ina 的職責**：

1. **審核需求合理性**
   - 是否符合資料庫設計原則？
   - 是否與現有結構衝突？
   - 是否有更好的替代方案？

2. **撰寫 Migration 檔案**
   - Laravel: `database/migrations/YYYY_MM_DD_XXXXXX_description.php`
   - 使用 Schema Builder，不寫 Raw SQL
   - 包含 `up()` 和 `down()` 方法

3. **回覆提交者**
   - 透過 HQ Message Hub 回報進度
   - 說明 Migration 檔案位置
   - 告知預計執行時間

### 階段 3：執行與驗證 (Execute)

**Ina 的執行步驟**：

1. **本地測試**
   ```bash
   php artisan migrate --pretend  # 預覽 SQL
   php artisan migrate           # 本地執行
   php artisan migrate:rollback  # 測試回退
   ```

2. **Staging 環境測試**
   ```bash
   ssh staging-server
   cd /path/to/project
   php artisan migrate --force
   ```

3. **生產環境執行**（需要 Joe 確認）
   ```bash
   ssh production-server
   cd /path/to/project
   # 備份資料庫（必須）
   mysqldump -u user -p database > backup_YYYYMMDD.sql
   # 執行 Migration
   php artisan migrate --force
   ```

4. **驗證結果**
   ```bash
   # 檢查表結構
   DESCRIBE table_name;
   # 測試相關 API
   curl http://localhost/api/test
   ```

5. **回報完成**
   - 透過 HQ Message Hub 通知提交者
   - 更新 `_agent/DB_MIGRATION_LOG.md`

---

## 🚨 緊急情況處理

### Q: 如果我需要緊急變更資料庫怎麼辦？

**A**: 透過 HQ Message Hub 留言，Ina 上線後會處理。如果真的很緊急，可以：

1. 透過 HQ Message Hub 標註 `[緊急]`
2. 同時通知 Joe
3. 在留言中說明：
   - 什麼功能壞了？
   - 影響多少用戶？
   - 為什麼現在必須改？

### Q: Ina 不在線上，但我必須執行怎麼辦？

**A**: 
1. ⚠️ **絕對不要直接改生產環境資料庫**
2. 可以在 Staging 環境測試
3. 撰寫詳細的 Migration 檔案
4. 透過 HQ Message Hub 記錄你的操作
5. 等 Ina 上線後由她審核並正式部署

---

## 📊 Migration 檔案範例

### 新增欄位
```php
<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            $table->enum('ticket_mode', ['virtual', 'physical', 'direct'])
                  ->nullable()
                  ->after('pulse_to_display')
                  ->comment('出金模式');
        });
    }

    public function down(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            $table->dropColumn('ticket_mode');
        });
    }
};
```

### 重新命名欄位
```php
public function up(): void
{
    Schema::table('devices', function (Blueprint $table) {
        $table->renameColumn('pulse_ratio', 'pulse_to_token');
    });
}

public function down(): void
{
    Schema::table('devices', function (Blueprint $table) {
        $table->renameColumn('pulse_to_token', 'pulse_ratio');
    });
}
```

---

## 🔗 相關文件

- `MESSAGE_HUB_PROTOCOL.md` - HQ Message Hub 通訊協定
- `AGENT_COLLABORATION_PROTOCOL.md` - Agent 協作規範
- `../../../README_MESSAGE_HUB.md` - HQ Message Hub 使用說明

---

**維護者**：Ina (Infra Master)  
**最後更新**：2026-06-06
