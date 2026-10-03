# 回報：TASK_20261001_INA_EVALUATE_M7_SETTLEMENTS_SCHEMA

**回報時間**：2026-10-01
**負責人**：Ina (Infra)
**任務類型**：DB Schema 評估（**唯讀稽核，未執行任何 DDL/DML**）
**狀態**：✅ 評估完成，**待 HQ 核准後方可執行修復**
**目標庫**：Central DB `iotv9`（VPS infra / 141.148.165.50）

---

## 一、執行摘要

1. 已於 **VPS (infra) 本機**（非本機端）以唯讀腳本實測生產庫 `iotv9`，取得 `settlements` 及所有相關表的**真實 DDL**。
2. 確認工單所述 drift 屬實，且**範圍比工單描述更大**：工單只點出 `settlements` 一表，實測發現 **3 個阻斷點**（settlements / settlement_logs / daily_revenue_reports）。
3. 已定位**根因**：M7 原始建表 migration 全套（`2026_03_11_*`）位於 `_migration_archive/` **從未執行**，生產庫目前的結構是被舊版 migration 與 Infra M6 SQL 混合建立的殘留物。
4. 稽核全程唯讀（僅 `SHOW` / `DESCRIBE` / `information_schema` / `SELECT COUNT(*)`），**未對生產庫做任何變更**。

---

## 二、生產庫實測結果（READ-ONLY）

### 2.1 `settlements` 實際結構（0 筆資料）

| 欄位 | 型別 | Null | Key | 說明 |
|:---|:---|:---|:---|:---|
| id | bigint unsigned | NO | PRI | auto_increment |
| owner_id | bigint unsigned | NO | MUL | 所有者 FK -> users.id |
| amount | decimal(12,2) | NO | | 結算金額 |
| outstanding_deducted | decimal(12,2) | YES | | 從場地主欠款中扣除的金額 |
| effective_payment | decimal(12,2) | YES | | 扣除欠款後場地主實際收到的金額 |
| method | enum('bank_transfer','cash','other') | YES | | 結算方式 |
| status | enum('pending','completed','failed') | NO | | 結算狀態 |
| completed_at | datetime | YES | | |
| reference | varchar(255) | YES | | 關聯 ID |
| created_at | timestamp | YES | | |
| updated_at | timestamp | YES | | |

- **索引**：`PRIMARY(id)`、`settlements_owner_id_index(owner_id)`
- **結論**：此為**舊版「金流/撥款」表**（single-owner、amount/method/reference），與 M7 多主人分潤模型**完全不同**。

### 2.2 Schema Drift 對照（vs M7 業務程式碼期望）

**M7 需要但 DB 缺少（21 欄）**：
```
settlement_number, venue_id, device_owner_id, venue_owner_id,
period_start, period_end,
total_revenue, pre_tax_expenses, taxable_revenue, device_breakdown,
device_owner_amount, venue_owner_amount, device_owner_share, venue_owner_share,
confirmed_at, paid_at, closed_at, disputed_at,
dispute_reason, dispute_resolution, payment_proof_url
```

**DB 有但 M7 未使用（8 欄）**：
```
id(PK), owner_id, amount, outstanding_deducted, effective_payment, method, completed_at, reference
```
> ⚠️ 其中 `outstanding_deducted`、`effective_payment` 雖不在工單欄位清單，但**存在於 `app/Models/Settlement.php` 的 `$fillable`**，屬 M7 仍需保留的欄位（不可誤刪）。

**完全匹配（僅 3 欄）**：`status`（但 enum 值不符，見下）、`created_at`、`updated_at`

**`status` 值域衝突**：
- 生產庫：`enum('pending','completed','failed')`
- M7 期望：`enum('created','confirmed','paid','closed','disputed')`

### 2.3 其他阻斷點（工單未點出）

#### (A) `settlement_logs` — 同樣是舊結構 ❌
| 生產庫實際 | M7 程式碼期望（`SettlementLog::create`） |
|:---|:---|
| id, settlement_id, **event_type** enum('created','completed','failed','cancelled'), **remark** text, created_at | id, settlement_id, **user_id**, **action** enum(...), **from_status**, **to_status**, **metadata** json, **ip_address**, **user_agent**, created_at |

→ 缺 7 欄，且 enum/欄位語意完全不同。

#### (B) `daily_revenue_reports` — 缺 `device_id` ❌
- M7 `SettlementService::generateMonthlySettlements()` 執行 `$reports->groupBy('device_id')` 且 eager load `device`，**依賴 `device_id` 欄位**。
- 生產庫實際欄位：id, venue_id, report_date, total_pulse, total_amount, is_locked, settlement_id, created_at, updated_at —— **無 `device_id`**。
- 另：`daily_revenue_reports.settlement_id` **沒有外鍵約束**（工單聲稱「已存在 FK」為誤）。

### 2.4 實際 FK 現況（與工單描述不符）

| 來源 | 目標 | 約束 | 備註 |
|:---|:---|:---|:---|
| `data_anomalies.settlement_id` | `settlements.id` | ON DELETE **SET NULL** | ✅ 存在（工單未提） |
| `settlement_logs.settlement_id` | `settlements.id` | **無 FK** | ❌ 工單稱「存在 FK」有誤 |
| `daily_revenue_reports.settlement_id` | `settlements.id` | **無 FK** | ❌ 工單稱「已存在」有誤 |

> 註：`ali_settlements` 為 Alliance 模組**獨立表**（partner_id 為主，10 筆資料，含 `settlement_number` varchar(50)），與 M7 無關，**不應混用**。

---

## 三、根因分析（Root Cause）

**核心根因：M7 原始建表 migration 全套被封存且從未在生產庫執行。**

```
PROJECT/Owner/database/migrations/_migration_archive/   ← 被封存，未執行
├── 2026_03_11_000001_create_settlements_table.php        (M7 完整欄位設計)
├── 2026_03_11_000002_create_settlement_logs_table.php    (M7 logs 設計)
├── 2026_03_11_000003_add_settlement_foreign_key_to_daily_revenue_reports.php
├── 2026_03_27_164632_add_device_id_to_daily_revenue_reports_table.php
└── 2026_03_27_164643_add_pre_tax_expenses_to_settlements_table.php
```

生產庫 `migrations` 表（共 62 筆）中，**完全沒有**上述 `2026_03_11_*` / `2026_03_27_*` 紀錄；與 settlements 相關的僅有：
```
batch 10  2026_06_15_011547_add_outstanding_fields_to_settlements_table  ← 對「舊結構」加欄位
```

**推論的實際發生鏈**：
1. 生產庫的 `settlements` / `settlement_logs` / `daily_revenue_reports` 早期由**舊版 DDL / Infra M6 SQL** 建立（`db/migrations/v9/M6_TABLES_CREATION.sql`，註解即寫「FK settlements.id（未來擴展）」）。
2. M7 於 2026-03 改版為多主人分潤模型，新 migration 建好後被移入 `_migration_archive/`，**從未對生產庫執行**。
3. 後續 2026-06 的 active migration（`add_outstanding_fields`、`create_daily_revenue_reports`）以「舊結構」為前提運行，甚至因 table 已存在而可能被 baseline（migration 記錄存在但實際 DDL 未套用 → 造成 `daily_revenue_reports` 有 migration 紀錄卻缺 `device_id` 的現象）。
4. 結果：M7 程式碼上線後，`GenerateMonthlySettlements` 對不存在的欄位寫入 → 9 月月結算生成失敗。

---

## 四、影響範圍

| 影響項 | 說明 |
|:---|:---|
| **月結算生成** | `GenerateMonthlySettlements` 直接失敗（P0 阻斷） |
| **結算狀態流轉** | confirm / markPaid / close / dispute 全數依賴缺失欄位 |
| **結算日誌** | `SettlementLog` 寫入失敗（欄位不符） |
| **每日營收報表** | 缺 `device_id`，無法按設備分組結算 |
| **資料損失風險** | 目前 3 張表皆為 **0 筆**，`venues` 4 筆、`devices` 20 筆 → **修復視窗安全，無歷史資料需搬遷** |

---

## 五、修復方案提案（⚠️ 需 HQ 核准，Ina 尚未執行）

### 方案 A（建議）：三表對齊 M7 原始設計
以封存的 M7 migration 為**設計藍圖**，對生產庫執行一次性的對齊 migration。

**步驟**：
1. **`settlements`**：因 0 筆資料，採 `DROP + CREATE`（套用 `2026_03_11_000001` + `2026_03_27_164643` 完整定義），**保留** `outstanding_deducted` / `effective_payment`（Model $fillable 需要），`status` 改為 M7 enum，補齊全部索引。
2. **`settlement_logs`**：0 筆 → `DROP + CREATE`（套用 `2026_03_11_000002` 設計）。
3. **`daily_revenue_reports`**：0 筆 → `DROP + CREATE`（套用 active migration `2026_06_16_140202` 完整定義，含 `device_id`、對帳欄位、`settlement_id` FK）。
4. 建立 `settlement_logs.settlement_id`、`daily_revenue_reports.settlement_id` 外鍵。
5. 處理 `data_anomalies.settlement_id` 既有 FK（0 筆，可保留或重建）。

**優點**：一次到位、結構與程式碼完全一致。
**風險**：需在維護視窗執行；`data_anomalies` FK 需先處理。

### 方案 B（保守）：只 ALTER 補欄位
對 `settlements` 用 `ALTER TABLE ADD COLUMN` 逐欄補齊，保留舊欄位。
**缺點**：`status` enum 無法直接 ALTER（需轉換），且舊欄位（owner_id/amount/method…）會殘留造成混淆；`settlement_logs` 的欄位語意衝突仍難解。

### 方案 C：僅 `settlements`，其餘另案
僅修 `settlements`，`settlement_logs` / `daily_revenue_reports` 開新工單。
**缺點**：月結算仍會因 log 寫入失敗而中斷，無法真正解除 P0。

**Ina 建議採方案 A**（三表 0 筆，風險最低、一次解除 P0）。

---

## 六、外鍵 / 財務保護規範遵循

- 依鐵律：財務/歷史表外鍵**禁用 `ON DELETE CASCADE`**，改用 `RESTRICT`。
- ⚠️ 需注意：M7 封存設計中 `settlement_logs.settlement_id` 用 `cascade`、`daily_revenue_reports` 的 `venue_id` 用 `cascade`；提案執行前將**改為 `RESTRICT` 或 `SET NULL`** 並回報差異。

---

## 七、待 HQ 決策事項

1. **是否核准方案 A**（三表對齊 + 一次性 migration）？
2. **執行時段**：雖為 0 筆，是否仍安排維護視窗？
3. **舊欄位處置**：`settlements` 舊欄位（owner_id/amount/method/completed_at/reference）是否確定丟棄？（0 筆，建議丟棄）
4. **`outstanding_deducted` / `effective_payment`** 是否確認保留？（Model $fillable 有，建議保留）
5. **`ali_settlements`** 是否需一併檢視 Alliance 端一致性？（本次未動）

---

## 八、附件

| 項目 | 內容 |
|:---|:---|
| 稽核腳本（唯讀） | `PROJECT/Infra/db/scripts/audit_m7_settlements_schema.py` |
| Git commits | `6072fa4` (最終版) / `667a1da`~ 系列 |
| 執行位置 | VPS `infra`：`/home/ubuntu/tg25-infra`，`venv/bin/python3`，DB 連 `127.0.0.1` |
| 原始 JSON | 由腳本 `JSON_REPORT_BEGIN/END` 區塊輸出（可重跑） |

### 執行方式（唯讀，可重現）
```bash
ssh infra 'cd /home/ubuntu/tg25-infra && venv/bin/python3 db/scripts/audit_m7_settlements_schema.py'
```

---

**Ina 聲明**：本次僅執行唯讀稽核，**未對生產庫做任何 Schema 變更**。所有修復動作待 HQ 核准後執行，並將再次回報。

