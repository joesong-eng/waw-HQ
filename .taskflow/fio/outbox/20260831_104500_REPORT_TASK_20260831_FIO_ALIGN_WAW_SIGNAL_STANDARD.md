# 任務回報：TASK_20260831_FIO_ALIGN_WAW_SIGNAL_STANDARD

**完成時間**：2026-08-31 10:45  
**執行者**：fio

## 執行結果

依據 `PROJECT/SignalHub/docs/WAW_SIGNAL_STANDARD_v1.0.md` 規範，已完成 IOTkiosk_v0 韌體與文件之全域標準化對齊：

1. **保留 104U 紙鈔機狀態機與防卡鈔邏輯**：
   - 完整維持 `src/modules/bill_acceptor.c` 之 ICT 104U UART (9600 8E1) 狀態機 (`UNINIT`, `POWER_UP`, `IDLE`, `ESCROW`, `STACKING`, `REJECTING`, `DISABLED`, `FAULT`)。
   - 保留 2s 自動發送 Hold (0x18) 延長硬體暫存機制與 15s 韌體 Fail-Safe 最終超時退鈔邏輯。
   - 掉電保護之 `lifetime_total` 與 `lifetime_bill_count` 雙重 NVS 備份機制完整運作。

2. **收鈔入箱 (Stacked) 映射維護至 64-bit 里程表 `raw_value`**：
   - 升級 `signal_collector` 模組支援 WAW-USS 8 通道（UI1~UI4 64-bit 單調里程表與即時電位、UO1~UO4 輸出狀態）。
   - 在 `EVT_BILL_CONFIRMED` 觸發吃鈔入箱 (Stacked) 時，自動調用 `signal_collector_add_bill_stacked(amount)` 將面額累加至 UI1 `raw_value`，並即刻寫入 NVS。
   - 徹底解決斷網漏帳與網路重傳問題，雲端以 `delta_value = current_raw_value - last_raw_value` 進行增量對帳。

3. **對齊標準 MQTT Topic 與 JSON Payload 結構**：
   - **Client ID**：標準化為 `waw-esp32-{chip_id}`（12 位大寫 MAC）。
   - **標準主題**：
     - 事件上報：`waw/v1/{site_id}/signal/{chip_id}/event`（門檻即時 / 60s 定期上報 signals 物件與 64-bit `raw_value`）。
     - 設備狀態與 LWT：`waw/v1/{site_id}/signal/{chip_id}/status`。
     - 控制指令：`waw/v1/{site_id}/signal/{chip_id}/cmd`（支援 `stack`, `reject`, `hold`, `enable`, `disable`, `pulse_output`, `reboot`）。
     - 指令回執：`waw/v1/{site_id}/signal/{chip_id}/ack`。
   - **相容層保留**：同步保留 `kiosk/{chip_id}/event`、`kiosk/{chip_id}/status`、`device/{chip_id}/info` 等主題，確保現有系統平滑過渡。

4. **同步更新專案設計文件與說明文檔**：
   - 更新 `README.md`、`docs/MQTT_PROTOCOL.md`、`docs/IHUB_INTEGRATION.md`、`docs/PITFALLS.md`。

## 結論
✅ 完成

---
**回報者**：fio  
**回報時間**：2026-08-31 10:45
