# 任務：TASK_20260908_SIDNEY_SIMULATOR_PULSE_WINDOW_AGGREGATION

**派發時間**：2026-09-08 19:40  
**優先級**：HIGH  
**負責人**：Sidney (SignalHub Lead)
**協同對象**：Coli (IOTwawS3 Lead)

---

## 📋 任務背景與核心問題

目前在硬體信號模擬器（`/signal-hub/simulator`）中，輸入腳位（UI1~UI4）每次點擊皆立即觸發一次 POST `/api/v9/signal-hub/simulator/gpio`，固定帶入 `pulse_count: 1`。
這導致測試時：
- 服務員在模擬器連續快速點擊 3 次 UI1（開分）。
- 產生了 3 筆獨立的 Webhook 事件，每筆皆為 `delta_value: 1`。

**與真實硬體行為不符**：
真實 ESP32-S3 採集卡（Coli 韌體 `REPORT_DELAY_MS: 600ms`）具備時間窗口防抖匯聚機制。現場服務員連續快速按 3 下時，採集卡在連按結束後只會送出**一次事件**，其中 `delta_value: 3`，合作端接收到後直接加 3000 分。

---

## 🛠️ 執行要求

### 1. 模擬器前端實作時間窗口防抖匯聚（`simulator.blade.php`）
- 在 Alpine.js 實作針對輸入腳位（UI1~UI4）的 **時間窗口緩衝計時器**（建議窗口：**400ms ~ 500ms**）。
- 當使用者連續快速點擊輸入按鈕時：
  - 本地前端計數即時跳動反應（畫面上數字即時遞增，給予流暢視覺反饋）。
  - 將脈衝增量累積至該腳位的緩衝池（例如 `pendingPulses[pinCode] += 1`）。
  - 重置防抖計時器（Debounce Timer）。
- 當使用者停止點擊超過 500ms：
  - 觸發實際的 POST 請求，一次性將累積的脈衝數作為 `pulse_count` 送出（例如 `pulse_count: 3`）。
  - 清空該腳位的累積緩衝池。
- 輸出繼電器（UO1~UO4）為狀態切換（Toggle），維持原樣即時觸發，不套用防抖窗口。

### 2. 驗證與預期效果
- 在模擬器連按 3 下 UI1。
- 畫面上即時顯示連擊反饋。
- 停頓後後端產生單一筆事件：`raw_value` 累加 3，`delta_value: 3`。
- Webhook 派送日誌中只產生一筆記錄，`發送值: 3`，合作端回調帶回 `actual_points: 3000`。

### 3. Git 提交與遠端部署驗證
- 完成修改並進行 Git commit/push。
- 執行 `./dev_tools/waw_ops.sh deploy signalhub` 部署至生產環境並驗收。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260908_SIDNEY_SIMULATOR_PULSE_WINDOW_AGGREGATION

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：Sidney (SignalHub Lead)

## 實作內容
（說明前端時間窗口計時器與 pulse_count 匯聚邏輯）

## Git 提交資訊
（Commit Hash 與異動檔案）

## 驗收確認
- [ ] 連按 3 下 UI1，只發出一次 POST 請求
- [ ] 後端生成 delta_value = 3 的單一事件
- [ ] 派送記錄確認發送值為整數 3
```

---
**派發者**：HQ  
**派發時間**：2026-09-08 19:40
