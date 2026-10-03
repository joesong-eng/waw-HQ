# 任務回報：DB 遷移 — DROP TABLE owner_subscriptions（完成）

- **任務 ID**：TASK_20261004_INA_DROP_OWNER_SUBSCRIPTIONS
- **執行者**：Ina (Infra / DB)
- **完成時間**：2026-10-04 03:29 CST
- **結論**：✅ **完成**（DROP TABLE owner_subscriptions 成功；subscription_audit_logs 依令保留；兩站存活）

---

## 一、執行前置驗證（先查再做 + 真實反饋）

### 1.1 依賴方代碼去引用已確認（本機 + 遠端雙重驗證）
| 專案 | 本機 commit | 遠端 commit | grep OwnerSubscription |
|------|-------------|-------------|------------------------|
| Owner | 6a2d53d | 6a2d53d（已部署） | 0 hits ✅ |
| SignalHub | 2f6e8bd | 2f6e8bd（已部署） | 0 hits（僅 Subscription.php 一行註解）✅ |

遠端路徑：Owner = 129.153.116.174:/www/wwwroot/iot.tg25.win；SignalHub = 129.153.116.174:/www/wwwroot/signal.tg25.win

### 1.2 安全性檢查
- ✅ 全庫 **無任何 FK 指向 owner_subscriptions**（REFERENTIAL_CONSTRAINTS = 0）
- ✅ 無 trigger / view 引用
- ✅ subscription_audit_logs 無 FK，與本表無約束關係 → 可獨立保留

### 1.3 DROP 前備份（保險）
```
sudo mysqldump --defaults-file=/etc/mysql/debian.cnf iotv9 owner_subscriptions \
  > /home/ubuntu/tg25-infra/backups/owner_subscriptions_drop_20261004_032737.sql
```
- 備份檔：`/home/ubuntu/tg25-infra/backups/owner_subscriptions_drop_20261004_032737.sql`（2,949 bytes，含 CREATE TABLE + 2 筆資料）

---

## 二、執行 SQL（僅此一表）

```sql
DROP TABLE iotv9.owner_subscriptions;
-- 未執行：DROP subscription_audit_logs（依 HQ Q2 保留）
-- 未執行：INSERT INTO subscriptions（依 HQ Q1 資料已存在）
```
- 連線：`sudo mysql --defaults-file=/etc/mysql/debian.cnf`（未使用明文密碼）
- 執行結果：`drop_exit=0`（成功）

---

## 三、驗收佐證（實測輸出）

### 驗收 1：owner_subscriptions 表不存在 ✅
```
SELECT COUNT(*) FROM information_schema.TABLES
  WHERE TABLE_SCHEMA='iotv9' AND TABLE_NAME='owner_subscriptions';
+------------+
| exists_cnt |
+------------+
|          0 |
+------------+

SELECT * FROM iotv9.owner_subscriptions LIMIT 1;
ERROR 1146 (42S02): Table 'iotv9.owner_subscriptions' doesn't exist
```

### 驗收 2：subscription_audit_logs 保留 ✅
```
SHOW TABLES FROM iotv9 LIKE 'subscription_audit_logs';
+-------------------------------------------+
| Tables_in_iotv9 (subscription_audit_logs) |
+-------------------------------------------+
| subscription_audit_logs                   |
+-------------------------------------------+
SELECT COUNT(*) FROM iotv9.subscription_audit_logs;  -- = 2
```

### 驗收 3：subscriptions 表 subscriber_id=12 記錄仍在 ✅
```
+----+---------------+--------------+-----------+--------+---------------------+---------------------+
| id | subscriber_id | service_type | target_id | status | started_at          | expires_at          |
+----+---------------+--------------+-----------+--------+---------------------+---------------------+
| 30 |            12 | device       |        43 | active | 2026-09-15 10:14:08 | 2027-12-31 23:59:59 |
| 31 |            12 | device       |        43 | active | 2026-09-15 10:14:22 | 2027-12-31 23:59:59 |
+----+---------------+--------------+-----------+--------+---------------------+---------------------+
```

### 驗收 4：iotv9 現存 subscription 相關表 ✅
```
subscription_audit_logs
subscriptions
```
（owner_subscriptions 已消失）

### 驗收 5：站點存活 ✅
```
curl -sI https://iot.tg25.win/     -> HTTP 302（登入導向，正常）
curl -sI https://signal.tg25.win/  -> HTTP 302（登入導向，正常）
curl -sI https://api.tg25.win/     -> HTTP 200
```

---

## 四、驗收指標對照（工單 / ADR-003）

| # | 驗收項 | 結果 |
|---|--------|------|
| 1 | SELECT * FROM owner_subscriptions → 表不存在 | ✅ ERROR 1146 |
| 2 | SELECT * FROM subscription_audit_logs → 表不存在 | ⛔ **改為保留**（依 HQ Q2 裁定，非「不存在」） |
| 3 | SELECT * FROM subscriptions WHERE subscriber_id=12 → 有記錄 | ✅ id=30/31 |
| 4 | 兩站站點存活 | ✅ 302 / 302 |

> 註：原工單驗收 #2 與 HQ Q2 裁定衝突，依 HQ 最新裁定「保留 subscription_audit_logs」執行，該表仍存在（此為預期結果）。

---

## 五、結論

✅ **任務完成**。owner_subscriptions 表已成功 DROP，且：
1. 前置代碼去引用（Sophie 6a2d53d / Sidney 2f6e8bd）已本機+遠端雙重驗證。
2. subscription_audit_logs 依令保留（2 筆稽核資料完好）。
3. subscriptions 表 subscriber_id=12 記錄（id=30/31）未受影響。
4. 兩站 + Infra API 站點存活正常。
5. DROP 前已備份（/home/ubuntu/tg25-infra/backups/owner_subscriptions_drop_20261004_032737.sql）。

**Ina（Infra / DB）已執行完畢，等待 HQ 後續指示。**

---

**執行者簽章**：Ina（Infra / DB）

