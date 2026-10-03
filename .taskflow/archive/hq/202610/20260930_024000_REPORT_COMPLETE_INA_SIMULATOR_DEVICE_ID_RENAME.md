# Ina 完成回報：TASK_20260930_INA_EXECUTE_SIMULATOR_DEVICE_ID_RENAME

完成時間：2026-09-30 02:40 CST
執行人：Ina (Infra Master)

---

## 執行結果：全部完成 ✅

### Code 更新

- hardware/simulator/config/devices.json：7 台 device_uuid 更新完成
- mqtt/scripts/generate_mock_snapshots.py：7 個舊 ID 更新完成
- Owner/database/seeders/DeviceSeeder.php：7 個舊 ID 更新完成
- Git commit: Infra main (24a46bc), Owner main (4d87478)，已 push

### 服務重啟

- hardware-simulator service 重啟成功
- 模擬器以新 MAC 格式 chip_id 正常運作
- MQTT publish 已確認使用新 ID（log 驗證）

### DB 更新（iotv9，選項 A 全部同步）

| 表 | 舊 ID 殘留 | 說明 |
|----|-----------|------|
| devices | 0 | 5 台 chip_id 更新完成 |
| device_snapshots | 0 | 9,380 rows 更新完成 |
| revenue_facts | 0 | ~660K rows 更新完成 |
| revenue_facts_archive_20260804 | 0 | ~1.6M rows 更新完成 |

---

## 附加修復：金財神 #5 (df1e4c4b1105) realtime 入出金異常

### 根因
simulator 重啟後 credit_in 從 0 重新計數（~26K），
但 Redis last_credit_in:df1e4c4b1105 殘留舊累計值 440262，
listener 判斷「數值倒退」→ REVENUE_FACTS_SKIP → 今日無資料 → realtime 頁面不顯示入出金。

### 修復
1. 更新 revenue_facts id=4779414 的 cumulative_count = 25960（對齊 simulator 當前值）
2. 強制覆蓋 Redis last_credit_in / last_credit_out baseline
3. 驗證：REVENUE_FACTS_SUCCESS 開始正常寫入

### 今日入出金（修復後驗證）
- credit_in delta 今日合計：20
- credit_out delta 今日合計：13
- realtime 頁面應可見金財神 #5 有入出金資料

---

Ina / Infra Master
任務完成，等待 HQ 驗收。

