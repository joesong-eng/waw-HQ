# 任務回報：DB 遷移 廢除 owner_subscriptions（HQ 裁定確認 + 待命）

- **任務 ID**：TASK_20261004_INA_DROP_OWNER_SUBSCRIPTIONS
- **執行者**：Ina (Infra / DB)
- **回報時間**：2026-10-04 02:55 CST
- **結論**：✅ 已確認 HQ 三點裁定，**進入待命**；尚未對生產 DB 執行任何 DDL/DML

---

## 一、HQ 裁定確認

| 問題 | HQ 裁定 | Ina 確認 |
|------|---------|----------|
| Q1：subscriptions.id=30/31 是否即 owner_id=12 遷移目標 | 是，資料已存在，**不需再 INSERT** | ✅ 已實測 id=30/31（subscriber_id=12, target_id=43, status=active）；**步驟 2 INSERT 作廢** |
| Q2：subscription_audit_logs 是否保留 | **保留，不 DROP**（ADR-003 已修訂：它是 subscriptions 現行稽核表） | ✅ 已確認 ADR-003 修訂版（mtime 2026-10-04 02:53）第 3.2 節載明「不 DROP subscription_audit_logs（保留）」 |
| Q3：執行順序 | **反轉**：先 Sophie + Sidney 改代碼並部署，完成後 Ina 才 DROP owner_subscriptions（僅此一表） | ✅ 已確認 ADR-003 第 3 節「修訂後執行順序」；**待命等 HQ 通知** |

---

## 二、待命期間準備（已完成，未執行）

### 2.1 DROP 前基線快照（實測）
owner_subscriptions（將被 DROP 的表，共 2 筆）：
| id | owner_id | owner_type | plan_name | started_at | expires_at | status |
|----|----------|------------|-----------|------------|------------|--------|
| 1 | 12 | device_owner | device_service | 2026-09-15 10:14:22 | 2027-12-31 23:59:59 | active |
| 2 | 11 | device_owner | device_service | 2026-09-15 10:14:22 | 2027-12-31 23:59:59 | active（孤兒） |

### 2.2 安全性前置檢查（已確認）
- ✅ **無任何 FK 指向 owner_subscriptions**（REFERENTIAL_CONSTRAINTS = 0）→ DROP 不會連鎖失敗
- ✅ subscription_audit_logs **無 FK**，與 owner_subscriptions 無約束關係 → 可獨立保留
- ✅ subscriptions 表（保留）35 筆，subscriber_id=12 已有 id=30/31

### 2.3 待執行 SQL（經 HQ 核准後才執行）
```sql
-- 前置：mysqldump 備份 owner_subscriptions（保險）
-- mysqldump iotv9 owner_subscriptions > backups/owner_subscriptions_YYYYMMDD.sql

-- 唯一變更（僅此一表）
DROP TABLE iotv9.owner_subscriptions;

-- 不執行：DROP subscription_audit_logs（依 HQ Q2 保留）
-- 不執行：INSERT INTO subscriptions ...（依 HQ Q1 資料已存在）
```

### 2.4 執行後驗收計畫
1. `SHOW TABLES FROM iotv9 LIKE 'owner_subscriptions'` → 空
2. `SELECT * FROM iotv9.subscription_audit_logs` → 仍存在（2 筆）
3. `SELECT * FROM iotv9.subscriptions WHERE subscriber_id=12` → id=30/31 仍在
4. Owner / SignalHub 站點 curl 存活檢查

---

## 三、依賴方狀態（解鎖條件）

DROP 的前置條件為 Sophie + Sidney 完成代碼去引用並部署。目前：
- Sophie：`TASK_20261004_SOPHIE_CLEANUP_OWNER_SUBSCRIPTION_REFS`（inbox 待處理）
- Sidney：`TASK_20261004_SIDNEY_SWITCH_TO_SUBSCRIPTION_MODEL`（inbox 待處理）
- 遠端 Owner VPS（129.153.116.174, commit 5ffd437）目前**仍含 OwnerSubscription 引用**（未去引用）

→ **待 HQ 通知兩位完成後，Ina 立即執行 DROP。**

---

## 四、狀態

⏸️ **待命中**。已備妥修正版 SQL（欄位對齊實測 schema、僅 DROP owner_subscriptions），收到 HQ 執行通知即立刻執行並回報驗收佐證。

---

**執行者簽章**：Ina（Infra / DB）

