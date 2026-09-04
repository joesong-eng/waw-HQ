
# 任務：TASK_20260903_INA_SIGNALHUB_SCHEMA_AND_LOG_MAINTENANCE

**派發時間**：2026-09-03 12:47  
**優先級**：Normal  
**負責人**：Ina (Infra Database Lead)

---

## 📋 任務核心要求

1. **資料庫 Schema 審查與遷移**：
   - 審查 `signal_profiles` 是否具備 `machine_number`、`machine_name`、`serial_enabled` 欄位。
   - 審查 `signal_webhook_deliveries` 是否具備 `cleared_points` 欄位。
2. **通知渠道整合確認**：
   - 確保 SignalHub 能順暢調用現有 LINE/Telegram 告警管道。

