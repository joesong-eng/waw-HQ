# HQ 資料庫常識強制注入行動記錄

> **執行者**: HQ (Coordinator)
> **執行時間**: 2026-06-21 01:32 ~ 01:56 (UTC+8)
> **目的**: 全面解決 Agents 對資料庫位置、連線方式、變更流程的認知缺失

---

## 🎯 問題背景

Joe 指出：**Agents 都沒有完整的資料庫資訊，導致連線失敗或嘗試自行執行 migration**

### 典型案例：Allie
- 任務 `TASK_20260620_001` 回報 `needs_review`
- 原因：本地 3308 連線失敗 (Connection refused)
- 根因：不知道資料庫實際在 `infra` VPS，且需要 SSH 隧道

---

## ✅ 執行內容

### 1. 建立權威知識文件
**檔案**: `brains/knowledge/02_technical_standards/DATABASE_CONNECTION_AND_GOVERNANCE.md`

**核心內容**:
- 所有生產 DB 都在 `infra` (141.148.165.50)
- 除 Ina 外，無任何 Agent 有本地 DB 實體
- 連線方式：
  - Sophie/Allie/Hubie: 3308 (SSH Tunnel)
  - Mina: 3306 (內部網路)
  - Redis: 6380 (SSH Tunnel)
- 變更申請唯一窗口：Ina
- 嚴格禁止：自行 `migrate` / `ALTER TABLE` / 繞過 Ina

### 2. 更新知識庫索引
- 已將此規範加入 `DOCUMENT_INDEX.md` 的「🔴 最高指導規範」清單
- 違反後果：導致資料庫連接失敗或 schema 版本衝突

### 3. 發送兩輪強制任務

#### 第一輪 (01:32) - 記憶注入
| Agent | Task ID | 狀態 |
|-------|---------|------|
| Sophie | DB_KNOWLEDGE_INJECTION_20260621 | ✅ 已發送 |
| Mina | DB_KNOWLEDGE_INJECTION_20260621 | ✅ 已發送 |
| Ina | DB_KNOWLEDGE_INJECTION_20260621 | ✅ 已發送 |
| Allie | DB_KNOWLEDGE_INJECTION_20260621 | ✅ 已發送 |
| Hubie | DB_KNOWLEDGE_INJECTION_20260621 | ✅ 已發送 |
| Fio | DB_KNOWLEDGE_INJECTION_20260621 | ✅ 已發送 |
| Coli | DB_KNOWLEDGE_INJECTION_20260621 | ✅ 已發送 |

#### 第二輪 (01:56) - SOP 部署落地
| Agent | Task ID | 狀態 |
|-------|---------|------|
| Sophie | DB_KNOWLEDGE_SOP_DEPLOY_20260621 | ✅ 已發送 |
| Mina | DB_KNOWLEDGE_SOP_DEPLOY_20260621 | ✅ 已發送 |
| Ina | DB_KNOWLEDGE_SOP_DEPLOY_20260621 | ✅ 已發送 |
| Allie | DB_KNOWLEDGE_SOP_DEPLOY_20260621 | ✅ 已發送 |
| Hubie | DB_KNOWLEDGE_SOP_DEPLOY_20260621 | ✅ 已發送 |
| Fio | DB_KNOWLEDGE_SOP_DEPLOY_20260621 | ✅ 已發送 |
| Coli | DB_KNOWLEDGE_SOP_DEPLOY_20260621 | ✅ 已發送 |

---

## 📋 驗收標準

各 Agent 必須回報以下內容（不接受口頭回報）：

1. ✅ 已讀文件路徑（必須為 `brains/knowledge/02_technical_standards/DATABASE_CONNECTION_AND_GOVERNANCE.md`）
2. ✅ 已寫入哪個記憶或 SOP 位置（檔案路徑或 AGENTS.md）
3. ✅ 負責專案的 DB 連線方式確認
4. ✅ 確認禁止自行 `migrate` / `ALTER TABLE`
5. ✅ 附 log 或檔案修改證明（git diff / 截圖）

---

## 🚨 後續監控

### 預期效果
- Allie 不會再嘗試連線本地 3308
- Sophie/Mina/Hubie 清楚知道資料在 `infra`
- 所有 DB schema 變更統一向 Ina 申請
- 減少「試錯式連線」與「私下 migration」

### 失敗指標
若 7 日內仍有 Agent：
- 嘗試本地執行 `php artisan migrate`
- 回報「本地 MySQL 連不上」
- 未經 Ina 批准自行 `ALTER TABLE`

則視為**注入失敗**，需重新設計 Agent 記憶機制。

---

## 📎 相關文件

- `brains/knowledge/02_technical_standards/DATABASE_CONNECTION_AND_GOVERNANCE.md` (權威文件)
- `brains/knowledge/01_agent_governance_rules/DB_MIGRATION_WORKFLOW.md` (變更流程)
- `brains/knowledge/04_ops_and_deployments/INFRASTRUCTURE_REFERENCE.md` (SSH 別名與 DB 架構)
- `brains/knowledge/DOCUMENT_INDEX.md` (已更新)

---

**執行完畢。等待 Agents 回報部署證明。**
