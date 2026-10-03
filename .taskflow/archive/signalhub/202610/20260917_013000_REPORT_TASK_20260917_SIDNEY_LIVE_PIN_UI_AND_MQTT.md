# 任務回報：TASK_20260917_SIDNEY_LIVE_PIN_UI_AND_MQTT

**完成時間**：2026-09-17 01:30
**執行者**：Sidney

## 執行結果

### 1. 資料庫 Migration
- 2026_09_17_000001_add_live_pin_to_signal_profiles：signal_profiles 新增 live_pin (tinyint, default 0) + live_timeout_sec (smallint, default 120)
- 2026_09_17_000002_add_session_fields_to_signal_events：signal_events 新增 event_type (varchar 40) + session_end_reason (varchar 20) + last_played_duration_seconds (smallint)
- 兩個 migration 均於遠端執行 DONE

### 2. 前端 UI（pins.blade.php）
- 在腳位設定卡片區下方、底部操作列上方插入「💓 存活感測 / 離場偵測 (Live Pin)」卡片
- 下拉選單：停用 / UI3 / UI4（x-model.number="livePin"）
- range slider：30~600 秒，步進 30（x-show="livePin > 0"）
- 初始化時從 API profile.live_pin / profile.live_timeout_sec 讀取
- savePins() payload 加入 live_pin + live_timeout_sec

### 3. 後端 API（SignalHubController::savePins）
- 新增 live_pin 驗證 Rule::in([0, 3, 4])
- 新增 live_timeout_sec 驗證 min:30|max:600
- 事務內儲存至 signal_profiles
- 儲存後若 profile.live_pin > 0 且有綁定 chip_id，呼叫 MqttService::sendLiveConfig
- indexPins 回傳 profile 補齊 live_pin + live_timeout_sec

### 4. MqttService（新建）
- app/Services/MqttService.php：透過 mosquitto_pub CLI 發布
- Topic：waw/v1/{site_id}/cmd/{chip_id}（無 site_id 則用 waw/v1/default/cmd/{chip_id}）
- Payload：{"command":"set_live_config","transaction_id":"txn_...","params":{"live_pin":N,"timeout_sec":N}}
- config/services.php 加入 mqtt 段（MQTT_BROKER/MQTT_PORT/MQTT_TLS/.env 驅動）

### 5. session_end 補齊
- 已加驗證 reason (nullable|string) + last_played_duration_seconds (nullable|integer)
- SignalEvent::create 補存 session_end_reason + last_played_duration_seconds

### 部署
- commit 9e86f80，HEAD=9e86f80
- 遠端 pull + migrate + optimize:clear 完成
- 無 500 報錯（fileinfo warning 非阻斷）

## 結論
✅ 完成

---
**回報者**：Sidney
**回報時間**：2026-09-17 01:30

