# WAW 2.0 割接可行性評估


**[On-Demand]** — 上下文注入策略

**評估日期**: 2026-06-14  
**評估人**: Ina (Infra)  
**任務 ID**: CONS_20260613_001  

## 執行摘要

✅ **資料層基礎設施已就緒**（machines, machine_deployments, machine_transactions）  
❌ **缺少關鍵表與欄位**，無法完整實作 WAW 2.0 的「欠費運行」與「動態分潤」機制

---

## 核心缺口

### 1. profit_sharing_agreements 表（高風險）

**現狀**: 僅有 `profit_sharing_proposals`（審批流程表），無長期協議記錄表  
**影響**: 分潤比例無法歷史追溯，導致對帳錯誤  
**解決方案**:

```sql
CREATE TABLE profit_sharing_agreements (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  machine_id BIGINT UNSIGNED NOT NULL,
  store_id BIGINT UNSIGNED NOT NULL,
  store_owner_share DECIMAL(5,2) NOT NULL,
  machine_owner_share DECIMAL(5,2) NOT NULL,
  effective_from DATETIME NOT NULL,
  effective_to DATETIME NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 2. subscription_status 缺少 arrears 狀態（中風險）

**現狀**:
- ✅ `machines.subscription_status` = `ENUM('active','arrears','suspended')`
- ❌ `venues.subscription_status` = `ENUM('active','expired')` ← 缺 `arrears`
- ❌ `devices.subscription_status` = `ENUM('active','expired')` ← 缺 `arrears`

**影響**: 無法實作「欠費運行」機制  
**解決方案**:

```sql
ALTER TABLE venues MODIFY COLUMN subscription_status 
  ENUM('active','arrears','expired') NOT NULL DEFAULT 'active';
ALTER TABLE devices MODIFY COLUMN subscription_status 
  ENUM('active','arrears','expired') NOT NULL DEFAULT 'active';
```

### 3. kiosk_event_listener.py 未實作分潤固化（中風險）

**現狀**: 接收 `device/{chip_id}/event` 但未寫入 `machine_transactions`  
**缺口**: 
- 未調用 `TransactionWriter.write_transaction()`
- 未查詢 `profit_sharing_agreements` 取得分潤比例

**需新增邏輯**:
```python
# 當收到 device/{chip_id}/data 事件時：
1. 查 profit_sharing_agreements WHERE machine_id=? AND effective_from<=now()
2. 若無協議，使用 machines.share_device_owner / share_venue_owner 預設比例
3. 寫入 machine_transactions，固定當下比例
```

---

## Phase 1-3 可行性評估

| Phase | 內容 | 可行性 | 阻塞項目 |
|-------|------|--------|---------|
| Phase 1 | 基礎資料遷移（devices → machines） | ✅ 高 | 無阻塞 |
| Phase 2 | 部署關係切換（machine_deployments） | ✅ 高 | 無阻塞 |
| Phase 3 | 分潤協議與欠費機制 | ❌ 低 | profit_sharing_agreements 表缺失 |

---

## 建議執行順序

**階段 A：資料庫結構補強（必需）**
1. 建立 `profit_sharing_agreements` 表
2. 修正 `venues.devices.subscription_status` 加入 `arrears`
3. 確認 `users.outstanding_amount` 正確性

**階段 B：WAW 2.0 核心邏輯實作**
4. `kiosk_event_listener.py` 加入分潤固化邏輯
5. `credit-relay` 加入分潤協議管理 API
6. 新增 Cron Job 實作欠費累計

**階段 C：割接測試**
7. 測試環境驗證 `machine_transactions` 固化正確性
8. 測試欠費狀態下的「軟性限制」是否生效

---

## 神經連結

- ← [WAW 2.0 架構規範](../03_system_architecture/WAW2_ARCHITECTURE.md)
- ← [MQTT 主題標準](../02_technical_standards/MQTT_TOPIC_STANDARD.md)
- → [資料庫 Schema 標準](../02_technical_standards/DATABASE_SCHEMA_STANDARD.md)
