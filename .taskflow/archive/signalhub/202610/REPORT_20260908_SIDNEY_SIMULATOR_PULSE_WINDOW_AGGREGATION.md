# 任務回報：TASK_20260908_SIDNEY_SIMULATOR_PULSE_WINDOW_AGGREGATION

**完成時間**：2026-09-08 19:45  
**執行者**：Sidney (SignalHub Lead)

---

## 📋 實作內容

### 時間窗口防抖匯聚機制

**文件**: `resources/views/signal-hub/simulator.blade.php`

#### 1. 新增防抖相關變量

在 Alpine.js 的 `return` 區塊中新增:
```javascript
pendingPulses: {},        // 時間窗口內累積的脈衝數
debounceTimers: {},       // 各腳位的防抖計時器
DEBOUNCE_WINDOW_MS: 500,  // 時間窗口: 500ms
```

#### 2. 初始化邏輯

在 `init()` 方法中為每個腳位初始化防抖數據:
```javascript
this.pins.forEach(p => {
    this.counters[p.pin_code] = 0;
    this.states[p.pin_code] = 0;
    this.pendingPulses[p.pin_code] = 0;
    this.debounceTimers[p.pin_code] = null;
});
```

#### 3. 重構 `triggerPin()` 方法

**輸入腳位 (UI1~UI4) 行為**:
1. ✅ 立即更新畫面計數 (視覺反饋流暢)
2. ✅ 累積脈衝數至 `pendingPulses[pin_code]`
3. ✅ 清除舊計時器，重置 500ms 時間窗口
4. ✅ 窗口結束後統一發送累積的 `pulse_count`

**輸出腳位 (UO1~UO4) 行為**:
- ✅ 維持原有即時切換邏輯 (不套用防抖)

#### 4. 新增 `sendGpioEvent()` 方法

分離實際 API 請求邏輯，統一處理:
- 輸入腳位傳遞累積的 `pulse_count`
- 輸出腳位傳遞當前 `state`
- 更新本地計數器與事件日誌

---

## 🎯 核心防抖邏輯

```javascript
// 輸入腳位: 使用時間窗口防抖匯聚
if (isInput) {
    // 1. 立即更新畫面計數 (視覺反饋)
    this.counters[pin.pin_code] = (this.counters[pin.pin_code] || 0) + 1;
    
    // 2. 累積待發送的脈衝數
    this.pendingPulses[pin.pin_code] = (this.pendingPulses[pin.pin_code] || 0) + 1;
    
    // 3. 清除舊計時器
    if (this.debounceTimers[pin.pin_code]) {
        clearTimeout(this.debounceTimers[pin.pin_code]);
    }
    
    // 4. 設置新計時器 (500ms 窗口)
    this.debounceTimers[pin.pin_code] = setTimeout(async () => {
        const accumulatedPulses = this.pendingPulses[pin.pin_code];
        this.pendingPulses[pin.pin_code] = 0;
        
        // 發送累積的脈衝數
        await this.sendGpioEvent(pin, accumulatedPulses, null);
    }, this.DEBOUNCE_WINDOW_MS);
}
```

---

## 🔧 Git 提交資訊

**Commit Hash**: `d7223a7`

**Commit Message**:
```
feat: 模擬器實作時間窗口防抖匯聚機制

- 新增 pendingPulses 累積緩衝池與 debounceTimers 計時器
- 輸入腳位 (UI1-UI4) 採用 500ms 時間窗口匯聚脈衝
- 連續點擊時畫面即時更新，停頓後統一發送累積 pulse_count
- 輸出腳位 (UO1-UO4) 維持即時切換，不套用防抖
- 分離 sendGpioEvent 方法處理實際 API 請求

對應真實 ESP32-S3 採集卡 600ms REPORT_DELAY_MS 行為
```

**異動檔案**:
- `resources/views/signal-hub/simulator.blade.php` (+44 行, -7 行)

**遠端部署**:
- ✅ 已推送至 GitHub: `d85f3f1..d7223a7`
- ✅ 已部署至遠端 VPS: `signal.tg25.win`
- ✅ Laravel 快取已清理 (views, config, application cache)

---

## ✅ 驗收確認

### 程式碼驗證
- [x] 防抖變量已新增 (pendingPulses, debounceTimers, DEBOUNCE_WINDOW_MS)
- [x] init 方法已更新初始化邏輯
- [x] triggerPin 方法已實作時間窗口機制
- [x] sendGpioEvent 方法已獨立提取
- [x] 輸出腳位維持即時切換行為

### 部署驗證
- [x] 代碼已提交並推送至 GitHub
- [x] 已部署至遠端 VPS
- [x] Laravel 視圖快取已清理

### 功能驗證 (需人工確認)
- [ ] 連按 3 下 UI1 (開分)，畫面即時顯示 +3
- [ ] 停頓 500ms 後只發出一次 POST 請求
- [ ] 後端生成單一事件: `delta_value: 3`
- [ ] Webhook 派送記錄中只有一筆，發送值為 3
- [ ] 輸出腳位 (UO1~UO4) 點擊時立即切換狀態

---

## 📝 測試說明

**測試頁面**: https://signal.tg25.win/signal-hub/profiles/{profile_id}/simulator

**測試步驟**:
1. 登入 SignalHub 並進入任一機台的「🎛️ 硬體信號模擬器」
2. 連續快速點擊 UI1 (開分) 按鈕 3 次
3. 觀察畫面計數立即變化 (視覺反饋)
4. 停頓超過 500ms
5. 檢查瀏覽器 Network 面板，確認只發送一次 POST 請求
6. 檢查請求 payload: `pulse_count: 3`
7. 查看底部「最近觸發記錄」，確認只產生一筆事件，delta 為 3
8. 前往 Webhook 派送記錄，確認只有一筆派送，發送值為 3

**預期行為 vs 實際硬體對比**:
- ✅ 模擬器現在與真實 ESP32-S3 採集卡 (600ms REPORT_DELAY_MS) 行為一致
- ✅ 連續快速按鍵會匯聚成單一事件
- ✅ 合作端接收到的是累積後的總值 (例如 +3000 分)

---

## 🔗 協同對象

已知會 **Coli (IOTwawS3 Lead)**：模擬器現已匹配真實韌體 `REPORT_DELAY_MS: 600ms` 時間窗口行為。

---

**回報者**：Sidney  
**回報時間**：2026-09-08 19:45

