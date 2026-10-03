# 任務：TASK_20260910_INA_MQTT_SIGNALHUB_LISTENER_BRIDGE

**派發時間**：2026-09-10 00:39  
**優先級**：critical  
**負責人**：ina

---

## 📋 任務內容

【MQTT 鏈路修復】新增 SignalHub 信號事件轉發橋接至 listener.py。背景：Sidney 診斷確認 ESP32-S3 採集卡（waw/v1/+/signal/+/event）Publish 正常，但 Broker 無訂閱者接收，導致事件全部丟棄。必做項目（修改 PROJECT/Infra/mqtt/scripts/listener.py）：1. MQTT_TOPICS 新增訂閱：waw/v1/+/signal/+/event QoS 1；2. 新增常數 SIGNALHUB_API_URL=https://signal.tg25.win/api/internal/signal/event 及 SIGNALHUB_API_KEY=v9-internal-key-2026；3. on_message 回調中當 Topic 符合 waw/v1/+/signal/+/event 時，將原始 Payload 攜帶 Header X-Internal-Key: v9-internal-key-2026 以 HTTP POST 轉打至 SIGNALHUB_API_URL；4. 提交 Git、Push；5. 遠端部署並 systemctl restart mqtt-listener.service；6. 驗證服務正常並附上 status 輸出。協同：Sidney 同步執行任務 B，待兩端就緒後進行端對端測試。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260910_INA_MQTT_SIGNALHUB_LISTENER_BRIDGE

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：ina

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：ina  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-09-10 00:39
