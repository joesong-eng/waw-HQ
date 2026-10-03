# 任務回報：TASK_20260831_INA_SIGNALHUB_MIGRATION（審核階段）

**回報時間**：2026-08-31 09:30  
**執行者**：ina

## 執行結果

執行正式 migration 前，依 Ina 鐵律「先查再做」完成生產 DB 審核，發現以下 3 個問題需 HQ 裁決：

---

### ⚠️ 問題一：`machines` 表與 `devices` 表同時存在，signal_profiles FK 有歧義

生產 DB：
- `machines` 表：15 筆，獨立表（chip_id, name, type, subscription_status 等）
- `devices` 表：20 筆，另一張獨立表（ESP32 採集卡記錄）

Owner 的 migration 在 `signal_profiles` 同時設了兩個 FK：
```php
$table->unsignedBigInteger('device_id')->nullable();  // FK devices.id
$table->unsignedBigInteger('machine_id')->nullable();  // FK machines.id
```

兩張表資料不重疊、結構不同，Ina 無法自行判斷 SignalHub 的「信號設定檔」主要錨點。
**需要 HQ 說明：signal_profiles 應以哪張表為主？**

---

### ⚠️ 問題二：`webhook_events` 已存在 — 不重複但需確認命名

生產 DB 已有 `webhook_events`（LINE bot 事件流水，4 筆）。
`signal_webhooks` 是新建的 Webhook 端點設定表，用途不同，**不重複**。
但命名上容易混淆，請 HQ 確認是否需要更明確的前綴。

---

### ⚠️ 問題三：migration 使用 onDelete('cascade') 可能危害信號歷史數據

`signal_pin_mappings` 和 `signal_stat_rules` 對 `signal_profiles` 使用實體外鍵 CASCADE 刪除。
`signal_events` 是信號流水表（高頻寫入），其 `pin_mapping_id` 和 `profile_id` 若因 CASCADE 失效，
歷史事件將無法追溯，違反 Ina DB 守則（財務/歷史表禁用 CASCADE）。

**建議**：改為 `RESTRICT` 或 `SET NULL`（已有 signal_events 資料後不可刪 profile）。
需要 HQ 確認是否接受此修改。

---

### ✅ 確認無障礙的部分

- 5 張 signal 表在生產 DB 均不存在（`SHOW TABLES LIKE 'signal%'` 空）
- 建表本身無技術障礙
- 問題釐清後 Ina 可立即執行

---

## 結論

⏸️ **暫停執行，等待 HQ 裁決上述 3 個問題後再行 migration**

---
**回報者**：ina  
**回報時間**：2026-08-31 09:30

