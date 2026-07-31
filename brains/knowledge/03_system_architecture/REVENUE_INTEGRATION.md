# WAW 2.0 採集端與商務端對接規範


**[On-Demand]** — 上下文注入策略

## 1. 金流數據流向 (Flow)
MQTT (Ina) -> MqttListenerService -> Machine Model (Sophie) -> MachineTransactions Table

## 2. 代碼對接約定
- **Ina 的責任**:
  - 當收到 `device/+/data/credit_in`。
  - 呼叫 `WawIot\Models\Machine::findByChipId()`。
  - 將數據「固化」存入 `machine_transactions` 表。
- **固化必填欄位**:
  - `store_id`: 必須從 `machine->currentDeployment` 獲取。
  - `store_owner_id`: 從部署場地的關聯 user 獲取。
  - `machine_owner_id`: 從機台關聯 user 獲取。

## 3. SQL 加固 (Mandatory)
- **要求**: Ina 必須在執行 R20_PHASE9 時，順手執行 \`DB_SCHEMA_WAW2_DELTA.md\` 中的索引優化。
