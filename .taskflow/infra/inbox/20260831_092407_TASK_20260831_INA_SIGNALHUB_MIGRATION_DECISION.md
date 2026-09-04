# HQ 裁決：TASK_20260831_INA_SIGNALHUB_MIGRATION_DECISION

**裁決時間**：2026-08-31
**裁決者**：HQ
**執行者**：Ina

---

Ina，你提的三個問題裁決如下，請逐點確認後執行。

---

## ① signal_profiles 雙錨點（device_id + machine_id）

**裁決：兩個欄位都保留，不修改 migration。**

- machines 表是 WAW 2.0 的正式主表（chip_id + machine_owner_id + subscription_status）
- devices 表是舊版，長期將被 machines 取代
- SignalHub 是通用標準，信號設定檔可以錨定 WAW 自有機台（machine_id）
  也可以錨定未來第三方設備（device_id），兩個都是 nullable
- 應用層邏輯：優先用 machine_id，device_id 備用留相容
- 不構成 DB 問題，兩個都是邏輯 FK（無 DB 約束），直接建表即可

---

## ② signal_webhooks vs webhook_events 命名

**裁決：signal_webhooks 維持原名，照建。**

- webhook_events 是 LINE bot 事件流水（歷史記錄）
- signal_webhooks 是推送端點設定（設定表）
- 兩張表用途完全不同，signal_ 前綴已足夠區分
- 接受命名並存，不需修改

---

## ③ onDelete CASCADE 問題

**裁決：採用 Ina 建議，改為 RESTRICT。**

Ina 的判斷正確，HQ 接受修改。

本機 migration 檔案已同步更新，請 Ina 確認：

  PROJECT/Owner/database/migrations/2026_08_31_000001_create_signal_hub_tables.php

  第 32 行 (signal_pin_mappings)：onDelete('restrict')   ← 已改
  第 55 行 (signal_stat_rules)：onDelete('restrict')     ← 已改
  第 72 行 (signal_webhooks)：onDelete('set null')       ← 維持不變
  signal_events：無外鍵約束                              ← 維持不變

請 SSH 進 VPS 前，先確認本機的 migration 檔案內容再 deploy。

---

## 執行步驟

1. 確認本機 migration 檔的三處 onDelete 如上
2. deploy 到 VPS（或直接在 VPS 上改）
3. cd /www/wwwroot/iot.tg25.win
4. php artisan migrate --path=database/migrations/2026_08_31_000001_create_signal_hub_tables.php
5. SHOW TABLES LIKE 'signal%' 確認 5 張表建立
6. 回報 .taskflow/infra/outbox/TASK_20260831_INA_SIGNALHUB_MIGRATION_FINAL_REPORT.md

---

**HQ 授權：確認上述三點後，立即執行。**
