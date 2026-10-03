
# 任務：TASK_20260903_COLI_SERIAL_DUAL_MODE_COMPATIBILITY

**派發時間**：2026-09-03 12:47  
**優先級**：High  
**負責人**：Coli (IOTwawS3 韌體工程師)

---

## 📋 任務核心要求

1. **現有 iot.tg25.win 零破壞防護評估（最高優先級）**：
   - 審查現有 MQTT Topics (`waw/v1/{site_id}/signal/{chip_id}/event`、`device/{chip_id}/command` 等)。
   - **嚴格確保**：新增 USB Serial 輸出/輸入邏輯時，原有的 MQTT 連線、狀態回報、心跳、脈衝上報邏輯**完全不受任何影響**。
   - 評估 USB CDC Serial 是否在 FreeRTOS 中採用獨立低優先級任務或事件監聽，保證 USB 拔插或串口阻塞時，不影響主核心的 GPIO 採集與 MQTT 推播。

2. **USB CDC 雙向通訊實作**：
   - 採集卡按鍵觸發時，透過 Serial 輸出單行 JSON：
     ```json
     {"delivery_id":982341,"event":"credit_in","chip_id":"df1e4c4b1105","machine":"M001","pin":"UI1","raw":10582,"delta":1,"ts":1725339600}
     ```
   - 支援讀取現場電腦回寫之單行 JSON，並解析 `cleared_points`。

3. **產出相容性安全評估報告**。

