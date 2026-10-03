# 任務工單：TASK_20260930_SOPHIE_INTEGRATE_M9_HISTORICAL_ALERTS

**派發時間**：2026-09-30 04:15 (台北時間)  
**優先級**：P2 (警報中心歷史記錄載入與持久化整合)  
**指派對象**：Sophie (Owner Agent)  
**驗收人**：HQ / Joe

---

## 🎯 任務目標

在 `PROJECT/Owner/resources/views/iot/modules/m9/alerts.blade.php`（警報中心）中：
目前該頁面僅靠 WebSocket (`window.Echo`) 監聽即時事件，當頁面重新整理或店主登入查看時，列表一律為空（顯示「目前無警報」），完全無法追溯過去發生的設備警報與重要系統告警。

**本次任務目標**：
在 `alerts.blade.php` 初始化時，串接既有的 `GET /api/v9/notifications` API，載入該用戶歷史的設備高危告警 (`device_alert`) 與通知記錄，並與即時 WebSocket 事件無縫合併，形成「歷史可查 + 即時跳動」的完整警報中心。

---

## 📋 具體實作要求

### 一、視圖初始化時載入歷史記錄 (`resources/views/iot/modules/m9/alerts.blade.php`)
在 Alpine 元件 `alertsPage()` 中：
1. 新增 `fetchHistoryAlerts()` 方法：
   - 呼叫 `GET /api/v9/notifications?per_page=50`。
   - 將回傳的通知列表格式化加入 `this.alerts`：
     - 若為 `device_alert` / 告警類型，對應相應標籤（例如【高危告警】、擺錘異常、失竊或感測器異常）。
     - 保留原始時間戳 `created_at`、未讀狀態 `is_read` 與目標跳轉連結 `action_url`。
2. 在 `init()` 流程中：
   - 先執行 `await this.fetchHistoryAlerts()` 填補歷史卡片。
   - 再啟動 `window.Echo` 監聽即時更新，有新事件時透過 `unshift()` 插在最前。

### 二、已讀操作對接持久化 API
當用戶點擊單筆警報或「全部已讀」時：
- 單筆標記已讀：呼叫 `PUT /api/v9/notifications/{id}/read`（若該筆來自 DB）。
- 全部標記已讀：呼叫 `POST /api/v9/notifications/mark-all-read`，確保下次重新整理後已讀狀態仍能持久化保留。

---

## 📦 驗收標準 (Acceptance Criteria)

1. **功能測試**：
   - 打開 `https://iot.tg25.win/alerts`，能自動拉取 DB 中已有的歷史通知記錄（不再永遠是一片空白）。
   - 點擊「全部已讀」後，未讀數正確歸零，重整頁面狀態依然保持已讀。
2. **Git 與遠端部署**：
   - Commit message 格式：`feat(m9): integrate historical notifications into alerts center`
   - Push 至遠端 main 分支並完成 `waw_ops.sh deploy owner`。
3. **回報格式**：
   - 依據 `SIMPLE_FILE_DISPATCH_PROTOCOL.md` 將回報送達 `.taskflow/owner/outbox/`。
   - 檢附遠端部署成功之 git log 與實裝說明。

---
**派發者**：HQ  

