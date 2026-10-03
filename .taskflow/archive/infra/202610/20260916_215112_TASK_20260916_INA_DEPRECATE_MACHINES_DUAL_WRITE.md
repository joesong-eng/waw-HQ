# 任務：TASK_20260916_INA_DEPRECATE_MACHINES_DUAL_WRITE

**派發時間**：2026-09-16 22:00  
**優先級**：HIGH（架構收斂 / 效能止血）  
**負責人**：Ina (Infra)  
**決策依據**：HQ 審議結論 — 廢棄 machines 換表遷移計畫，全面固化 devices 為唯一 SSOT

---

## 📋 決策背景與目標

經 HQ 與 Joe 審議 Ina 的架構評估報告（REPORT_20260916_INA_WAW2_PHASE2_DB_EVALUATION），確認：
1. 現行生產環境所有業務鏈（FastAPI, Member, Owner, Alliance, SignalHub）皆重度依賴 `iotv9.devices`。
2. 換表 `machines` 不僅欠缺 5 大核心欄位，且雙寫白白浪費 MySQL I/O、連線數與磁碟空間。
3. 經拍板決定：**終止換表遷移計畫，現行 `devices` 為永久唯一 SSOT。軟性欠費與訂閱欄位後續直接於 `devices` 擴充。**

本任務目標：**徹底清除應用層對 `machines` 的雙寫與冗餘查詢邏輯，停止資源浪費。**

---

## 🔧 具體執行項目

### 1. 清理 `mqtt/scripts/listener.py` 雙寫邏輯
- 移除心跳更新時對 `machines` 表的 `UPDATE machines SET last_seen_at = NOW()`（約 Line 188-193）。
- 移除累計脈衝更新時對 `machines` 表的 `lifetime_pulse_in` / `lifetime_pulse_out` 寫入（約 Line 360-377）。
- 移除連線狀態變更時對 `machines` 表的 `last_seen_at` 寫入（約 Line 424-430）。
- 確保所有心跳與脈衝**僅寫入 `iotv9.devices`**，精簡 SQL 執行次數。

### 2. 清理 `api/credit-relay/services/device_status_service.py` 查詢邏輯
- 移除降級查詢時先查 `iotv9.machines` 的冗餘 SQL（約 Line 97-105）。
- Redis 查無資料時，直接查 `iotv9.devices` 的 `last_seen_at`。
- 同步修正 `routers/device_status.py` 的文檔與回傳 source 欄位（不再有 `iotv9.machines`）。

### 3. 本地測試與生產部署
- 執行語法檢查與單元驗證，確保 Python 腳本無語法錯誤。
- 部署至 VPS `infra` (141.148.165.50)。
- 安全重啟相關常駐服務（如 systemd `waw-mqtt-listener` 或 FastAPI 服務）。
- 觀察 MQTT 監聽日誌，確認心跳與脈衝接收正常，無 MySQL 報錯。

⚠️ **注意**：先不要 DROP 線上 `machines` 表，維持表本體留存做歷史存檔，僅停止應用層對它的寫入與讀取。

---

## 📝 驗收標準與產出

1. `listener.py` 與 `device_status_service.py` 零 `machines` 引用。
2. 部署後重啟服務，MQTT 脈衝與心跳寫入 `devices` 正常無報錯。
3. `curl https://api.tg25.win/api/device/{chip_id}/active-status` 回應正常。
4. 撰寫回報至 `.taskflow/infra/outbox/REPORT_20260916_INA_DEPRECATE_MACHINES_DUAL_WRITE.md`。
5. 使用 `agent_report_to_hq_v2.sh` 通知 HQ。

