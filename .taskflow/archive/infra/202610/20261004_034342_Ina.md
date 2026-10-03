# 任務回報：DROP TABLE owner_subscriptions（完成 / 重複派工確認）

- **任務 ID**：TASK_20261004_INA_EXECUTE_DROP_OWNER_SUBSCRIPTIONS
- **執行者**：Ina (Infra / DB)
- **回報時間**：2026-10-04 03:43 CST
- **結論**：✅ **目標狀態已達成**（owner_subscriptions 不存在；audit_logs 保留；兩站存活）

> ⚠️ **重要說明**：本工單的 DROP 操作，已於 **2026-10-04 03:28** 由前一張工單
> `TASK_20261004_INA_DROP_OWNER_SUBSCRIPTIONS` 執行完成（該次已回報 outbox）。
> 本工單為**同一操作的再次派發**。本次依「先查再做 + 真實反饋」鐵律，重新執行全部
> 前置驗證與驗收，確認目標狀態一致，**未再重複執行 DROP（表已不存在，重複 DROP 無意義）**。

---

## 一、前置條件驗證（本工單步驟 1：遠端雙保險）

| 檢查 | 指令 | 結果 |
|------|------|------|
| Owner 遠端 commit | `git log -1` @ iot.tg25.win | `c1072bc` ✅ |
| Owner 遠端引用 | `grep -rn owner_subscriptions app/` | **0 hits**（rc=1）✅ |
| SignalHub 遠端 commit | `git log -1` @ signal.tg25.win | `2f6e8bd` ✅ |
| SignalHub 遠端引用 | `grep -rn owner_subscriptions app/` | 僅 1 行**註解**（Subscription.php:13「表已廢止」），非程式引用 ✅ |

---

## 二、DROP 執行狀態

- **DROP 已於 2026-10-04 03:28 執行**（前一工單）：`DROP TABLE iotv9.owner_subscriptions;` → exit=0
- **DROP 前備份**：`/home/ubuntu/tg25-infra/backups/owner_subscriptions_drop_20261004_032737.sql`（2,949 bytes）
- 本工單步驟 2 無需再執行（表已不存在）。

---

## 三、驗收佐證（本次重驗，實測輸出）

### 驗收 1：owner_subscriptions = 0 rows ✅
```
SHOW TABLES FROM iotv9 LIKE 'owner_subscriptions';   -> 空
SELECT COUNT(*) FROM information_schema.TABLES
  WHERE TABLE_SCHEMA='iotv9' AND TABLE_NAME='owner_subscriptions';  -> 0
SELECT 1 FROM iotv9.owner_subscriptions LIMIT 1;
  -> ERROR 1146 (42S02): Table 'iotv9.owner_subscriptions' doesn't exist
```

### 驗收 2：subscription_audit_logs = 1 row（保留）✅
```
SHOW TABLES FROM iotv9 LIKE 'subscription_audit_logs';
+-------------------------------------------+
| Tables_in_iotv9 (subscription_audit_logs) |
+-------------------------------------------+
| subscription_audit_logs                   |
+-------------------------------------------+
SELECT COUNT(*) FROM iotv9.subscription_audit_logs;  -> 2
```

### 驗收 3：subscriptions 表保留，subscriber_id=12 記錄仍在 ✅
```
+----+---------------+-----------+--------+
| id | subscriber_id | target_id | status |
+----+---------------+-----------+--------+
| 30 |            12 |        43 | active |
| 31 |            12 |        43 | active |
+----+---------------+-----------+--------+
```

### 驗收 4：站點存活 ✅
```
curl -sI https://iot.tg25.win/     -> HTTP 302（登入導向，健康）
curl -sI https://signal.tg25.win/  -> HTTP 302（登入導向，健康）
curl -sI https://api.tg25.win/     -> HTTP 200
```
> 註：工單寫「HTTP 200」，實測 Owner/SignalHub 首頁回 302（登入導向）屬正常行為，站點健康。

---

## 四、驗收指標對照（本工單）

| # | 驗收項 | 期望 | 實測 | 結果 |
|---|--------|------|------|------|
| 1 | SHOW TABLES LIKE 'owner_subscriptions' | 0 rows | 0 rows | ✅ |
| 2 | SHOW TABLES LIKE 'subscription_audit_logs' | 1 row | 1 row | ✅ |
| 3 | 兩站站點存活 | HTTP 200 | 302/302（導向，健康） | ✅ |

---

## 五、結論

✅ **完成**。owner_subscriptions 表確認不存在，subscription_audit_logs 與 subscriptions 均保留完好，兩站存活。

**提醒 HQ**：本工單與 03:28 完成的 `TASK_20261004_INA_DROP_OWNER_SUBSCRIPTIONS` 為重複派工，
兩張工單可一併結案歸檔（`waw_ops.sh close infra DROP_OWNER_SUBSCRIPTIONS`）。
另 `.taskflow/TODO_20261004.md` 中 Ina 的 DROP 條目仍標「進行中」，建議更新為完成。

---

**執行者簽章**：Ina（Infra / DB）

