# 任務回報：TASK_20260916_INA_DEPRECATE_MACHINES_DUAL_WRITE

**完成時間**：2026-09-16 22:30
**執行者**：Ina (Infra Master)

## 執行結果

### 1. 清理 mqtt/scripts/listener.py

移除下列 machines 雙寫邏輯：
- update_device_heartbeat()：移除 UPDATE machines SET last_seen_at
- write_revenue_fact()：移除 UPDATE machines SET lifetime_pulse_in / lifetime_pulse_out
- update_device_status()：移除 UPDATE machines SET last_seen_at

所有心跳與脈衝事件現在**僅寫入 iotv9.devices**。

### 2. 清理 api/credit-relay/services/device_status_service.py

移除 _read_mysql() 中先查 iotv9.machines.last_seen_at 的冗餘 SQL。
Redis cache miss 時直接查 iotv9.devices.last_seen_at。

### 3. 更新 api/credit-relay/routers/device_status.py

更新 source 欄位說明（redis | iotv9.devices）與 404 錯誤訊息。

### 4. 語法驗證

- listener.py：python3 -m py_compile → OK
- device_status_service.py：python3 -m py_compile → OK
- grep 確認三個檔案零 machines 引用 → CLEAN

### 5. Git commit 與部署

- Commit：02090f9（refactor: remove machines dual-write, devices is sole SSOT）
- Push：main → github.com/joesong-eng/tg25-infra
- 遠端 pull：已成功 fast-forward 至 02090f9
- 重啟服務：mqtt-listener、credit-api 均 active

### 6. 驗收測試

GET http://127.0.0.1:8084/api/device/AABBCCDDEEFF/active-status
→ HTTP 404（設備不存在，正確行為）
→ 錯誤訊息：「找不到設備 AABBCCDDEEFF（Redis、iotv9.devices 都無記錄）」
→ machines 字樣已從回應中消失 ✅

### 注意事項

- iotv9.machines / machine_deployments / machine_transactions 三表維持原樣，僅停止應用層寫入，未 DROP。
- credit-api 服務 systemd unit 定義 port 8084，與 ps aux 一致（pid 80849）。

## 結論

✅ 完成

---
**回報者**：Ina (Infra Master)
**回報時間**：2026-09-16 22:30
