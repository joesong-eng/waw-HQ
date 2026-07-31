# WAW 2.0 資料庫增量更新規格 (DDL)

- **狀態**: 已批准 (By HQ)
- **套用範圍**: waw_core / iotv9 資料庫
- **設計者**: Ina (Infra Master)

## 1. 現有表補底 (ALTER)

```sql
-- 1. 更新 venues (場地表)
ALTER TABLE venues 
  ADD COLUMN subscription_status ENUM('active', 'expired') NOT NULL DEFAULT 'active' COMMENT '場地訂閱狀態',
  ADD COLUMN subscription_expires_at DATETIME NULL COMMENT '訂閱到期日';

-- 2. 更新 devices (機台表)
ALTER TABLE devices 
  ADD COLUMN subscription_status ENUM('active', 'expired') NOT NULL DEFAULT 'active' COMMENT '設備授權狀態',
  ADD COLUMN subscription_expires_at DATETIME NULL COMMENT '授權到期日',
  ADD COLUMN outstanding_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '設備累計欠費金額';
```

## 2. 新建核心表 (CREATE)

```sql
-- 3. 新建 machine_deployments (機台部署歷史軌跡表)
CREATE TABLE machine_deployments (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  machine_id BIGINT UNSIGNED NOT NULL,
  store_id BIGINT UNSIGNED NOT NULL,
  status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
  deployed_at DATETIME NOT NULL,
  removed_at DATETIME NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_machine_id (machine_id),
  INDEX idx_store_id (store_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 新建 machine_transactions (機台分潤分成固化交易流水表)
CREATE TABLE machine_transactions (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  machine_id BIGINT UNSIGNED NOT NULL,
  store_id BIGINT UNSIGNED NOT NULL,
  transaction_type VARCHAR(50) NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  store_owner_id BIGINT UNSIGNED NOT NULL,
  machine_owner_id BIGINT UNSIGNED NOT NULL,
  store_owner_share_amount DECIMAL(10,2) NOT NULL,
  machine_owner_share_amount DECIMAL(10,2) NOT NULL,
  system_cut_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```
