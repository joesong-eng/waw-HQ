# 任務：TASK_20261005_INA_VERIFY_DEVICE_SESSIONS_SSOT

**派發時間**：2026-10-05
**優先級**：high
**負責人**：Ina (Infra / DB)
**性質**：釐清矛盾（先查再做，只讀）
**架構依據**：`ADR-002_MEMBER_DEVICE_SESSION_SSOT.md`
**前單**：`TASK_20261005_INA_EVALUATE_MACHINE_SESSIONS_DROP`（2026-10-05 06:00 回報）

---

## 背景：回報出現矛盾

你在前單回報的驗收 #3 寫：
> 「**device_sessions 筆數對照 → 表同樣不存在（migration 未執行），但 Model 已全面就位**」

但 **Mina 於 2026-10-03 的 `TASK_20261003_MINA_ALIGN_DEVICE_SESSION_SSOT`** 回報中，
以**遠端真實 API E2E** 呼叫 `/api/callback/settle` 與 `/credit`，明確出現：
> `SESSION_STATUS=ended  ended_at=2026-10-03 15:59:38 ← DeviceSession 正確轉 ended`
> `CLEANUP_OK sessions_left=0 bal_restored=2000`

**若 `device_sessions` 表不存在，Mina 的 E2E 不可能寫入成功。** 兩份回報直接矛盾。

Joe 研判：**極可能是查核對象（DB 連線）不對**，或前次修復未完整回報所致。本單要一次查清。

---

## 任務（只讀，禁止任何 DDL）

### 步驟 1：確認 Member 真正的 DB 連線
- 到 **yd177**（`129.146.103.177:39022`，Member 站 `win.tg25.win`）。
- 讀取 `/www/wwwroot/win.tg25.win/.env` 的 `DB_CONNECTION` / `DB_HOST` / `DB_DATABASE`（**遮罩密碼**）。
- 用 Laravel 自己的連線查（**這是唯一權威**）：
  ```bash
  ssh yd177 "cd /www/wwwroot/win.tg25.win && php artisan tinker --execute=\"echo config('database.default').PHP_EOL; echo DB::connection()->getDatabaseName().PHP_EOL;\""
  ```

### 步驟 2：以「Member 的真實連線」重查兩張表
- `Schema::hasTable('device_sessions')` → ?
- `Schema::hasTable('machine_sessions')` → ?
- `device_sessions` 筆數、最近 `started_at` / `ended_at`
- `migrations` 表中 `create_device_sessions_table` 是否為 `Ran`

### 步驟 3：澄清你前單的查核對象
- 你前單列的「win | yd174 (129.153.116.174)」——**yd174 是 Owner/SignalHub 主機**（見 `VPS_TOPOLOGY_CARD`），不是 Member。
- 請說明你前單實際查的是哪個 host / 哪個 DB，並確認是否查錯對象。

### 步驟 4：與 Mina 的 E2E 對帳
- 若 `device_sessions` **存在** → 說明 Mina 修復已完整落地，前單結論為「查錯 DB」誤判。
- 若 `device_sessions` **不存在** → 說明 Mina 的 E2E 無法成立，需進一步查其回報證據的真實性。

---

## 驗收指標（附實際指令與輸出）

1. yd177 `.env` 的 DB 設定（遮罩密碼）+ Laravel `getDatabaseName()` 輸出
2. `device_sessions` 存在與否 + 筆數 + 最近時間
3. `machine_sessions` 存在與否
4. `migrations` 表對照（`create_device_sessions_table` / `create_machine_sessions_table` 是否 Ran）
5. 明確結論：**Mina 修復是否完整落地？前單是否查錯對象？**

---

## 禁止

- **任何 DDL**（DROP / RENAME / CREATE / ALTER）
- 洩漏密碼（輸出需遮罩）
- 動 Member 以外專案

## 完成定義

矛盾釐清，5 項驗收有實際輸出，回報寫入 `.taskflow/infra/outbox/`。
