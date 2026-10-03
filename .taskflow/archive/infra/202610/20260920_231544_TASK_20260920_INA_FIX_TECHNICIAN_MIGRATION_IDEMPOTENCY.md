# 補單：technician migration 必須冪等，並寫入 Laravel migrations 表

**派工時間**：2026-09-20
**派工者**：HQ
**執行者**：Ina
**優先級**：high
**前置任務**：TASK_20260920_INA_ADD_TECHNICIAN_ROLE（schema 已落地，本單只收口風險）
**阻塞**：未完成本單前，禁止 Sophie / Sidney 部署（deploy 腳本含 `php artisan migrate --force`）

---

## HQ 獨立核過的現況（不要再重跑 ALTER）

來源：Owner tinker 連 `iotv9`，不是信 outbox 文字。

| 項目 | 遠端事實 |
|---|---|
| `users.role` | `enum('admin','owner','staff','boss','partner','sub_agent','technician')` DEFAULT `owner` |
| `users.expires_at` | `datetime` NULL |
| `technician` 筆數 | 0 |
| `iotv9.migrations` 含 technician / expires_at | **空** |
| Owner 線上 HEAD | `aa689ce`（還沒 pull `f537334`） |
| SignalHub 線上 HEAD | `7c670f2`（還沒 pull `505dde0`） |

你直接跑 SQL 是對的；漏的是 Laravel 帳本。

現有兩份 migration **沒有冪等**：

- `PROJECT/Owner/database/migrations/2026_09_20_223000_add_technician_role_and_expires_at_to_users_table.php`
- `PROJECT/SignalHub/database/migrations/2026_09_20_223000_add_technician_role_and_expires_at_to_users_table.php`

兩邊 `up()` 都是裸 `ADD COLUMN expires_at`。`./dev_tools/waw_ops.sh deploy sophie|signalhub` 會 `git pull` + `php artisan migrate --force`，下一輪部署會撞 duplicate column。

Owner 與 SignalHub 共用 `iotv9`。同一支 migration 名稱兩邊都有，只能讓 **一邊** 真正執行；另一邊必須看到已記錄而 skip，或 `up()` 自己判斷已套用。

---

## 必做

### 1. 兩份 Laravel migration 改冪等

`up()` 規則：

1. 讀 `information_schema.COLUMNS` 的 `users.role` COLUMN_TYPE。已含 `technician` 就不要再 `MODIFY COLUMN role`。若必須改 ENUM，**必須保留現有全部值**（含 `boss`、`partner`），只追加缺的值。禁止用工單初稿那組缺值 ENUM 覆蓋。
2. `Schema::hasColumn('users', 'expires_at')` 為 false 才 `ADD COLUMN`。已存在就 skip。
3. `down()` 不要在本單改行為；本單重點是防 `up()` 爆炸。若改 `down()`，禁止在 production 跑 rollback。

### 2. 寫入 `iotv9.migrations`

插入一筆（只插一次，先查再插）：

- `migration` = `2026_09_20_223000_add_technician_role_and_expires_at_to_users_table`
- `batch` = 現有 max(batch)+1

因為 Owner / SignalHub 共用同一張 `migrations` 表、同一檔名，插 **一筆** 即可讓兩邊後續 `artisan migrate` 都 skip。不要插兩筆同名。

若你改用「只改冪等、不插 migrations 列」：`up()` 必須保證重跑零傷害。HQ 仍要求插列，避免每次 deploy 無意義重跑 ENUM MODIFY。

### 3. 遠端驗證（必須貼輸出，不要口頭）

在 Owner（`iot.tg25.win`）與 SignalHub（`signal.tg25.win`）各做一次，或證明兩邊連同一 `iotv9` 後做一次即可：

1. `SELECT migration, batch FROM migrations WHERE migration LIKE '%technician%' OR migration LIKE '%expires_at%';`
2. `php artisan migrate --pretend`（或 `migrate --force` 若你確認冪等）不得出現 `Duplicate column name 'expires_at'`，也不得把 ENUM 改回缺少 `boss`/`partner`/`technician`。
3. 再查一次：
   - `role` 仍含 `technician` 且保留 `boss`, `partner`
   - `expires_at` 仍 NULL datetime
4. Git commit + push：Owner、SignalHub。Infra SQL 檔若需註記「已於 2026-09-20 直接執行，Laravel 側改冪等」，一併更新。

禁止再對 production 重跑一次非冪等 `ADD COLUMN`。

---

## 不做

- 不改 Sophie UI / Sidney auth
- 不部署 Owner / SignalHub 應用碼（那是下一張工單）
- 不刪 `expires_at`、不改現有使用者 role

---

## 回報必含

- 兩份 migration 的最終 `up()` 片段或 commit hash
- `iotv9.migrations` 查詢輸出
- `php artisan migrate --pretend` 或實際 migrate 輸出
- 最終 `role` / `expires_at` SHOW COLUMNS 輸出
