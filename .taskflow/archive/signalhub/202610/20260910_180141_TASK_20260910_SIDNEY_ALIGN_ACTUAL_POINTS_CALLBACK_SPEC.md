# 任務：TASK_20260910_SIDNEY_ALIGN_ACTUAL_POINTS_CALLBACK_SPEC

**派發時間**：2026-09-10  
**優先級**：high  
**負責人**：Sidney (SignalHub)  
**主管單位**：HQ 協調中心  

---

## 📋 背景說明

經 HQ 與 Joe 檢核，目前採集卡端僅能採集物理按鍵觸發次數（delta_value），因採集卡不設定點數比例，營業統計完全依賴遊戲廠商回調「實際開了多少分」。
然而系統歷史上早期僅規劃洗分（cleared_points），後續擴充開分時，多處文件、前端範例與模擬器仍殘留 cleared_points 與 actual_points 混用的情況，且未明確強制要求遊戲商「開分亦必須回調 actual_points」。

為確保遊戲商對接規範嚴密、避免開分無法記帳與前後端名稱混亂，現指派 Sidney 進行全盤規格與程式碼對齊修正。

---

## 🎯 任務目標與具體執行範圍

### 1. 對接文檔與程式碼範例全面對齊 (docs & views)
- 檢查並更新 `PROJECT/SignalHub/docs/THIRD_PARTY_INTEGRATION_GUIDE.md`：
  - 將所有對接回調與串口回寫範例中的 `cleared_points` 全面統一為 **`actual_points`**。
  - 強調說明：開分（credit_in / UI1）與洗分（credit_out / UI2）均必須在回調中回傳 `actual_points`（非負整數），否則後台無法進行營業統計與拆帳。
- 檢查並更新 `PROJECT/SignalHub/resources/views/signal-hub/webhooks.blade.php`：
  - 修正 PHP、Node.js、Python 及 USB CDC 串口範例，統一輸出與接收回調欄位為 `actual_points`。

### 2. 回調校驗邏輯與防呆增強 (Controllers & Jobs)
- 檢查 `PROJECT/SignalHub/app/Http/Controllers/Api/V9/CallbackAckController.php` 與 `app/Jobs/ProcessWebhookDelivery.php`：
  - 確保首選解析 `actual_points`（保留對舊版 `cleared_points` 的向下相容相容性）。
  - 當收到 `credit_in` 或 `credit_out` 事件之回調時，若廠商未提供 `actual_points`（或為 null），應記錄警告 Log，避免靜默漏記帳務。

### 3. Model 語意相容增強 (SignalWebhookDelivery.php)
- 在 `App\Models\SignalWebhookDelivery` 中：
  - 新增 Accessor / Mutator 或別名屬性，讓程式碼可直接存取 `$delivery->actual_points`，內部映射至資料表 `cleared_points` 欄位，徹底消除開分卻存入 cleared_points 的認知斷層。

### 4. 前端 UI 與模擬器優化 (Views)
- 檢查 `PROJECT/SignalHub/resources/views/signal-hub/deliveries.blade.php`：
  - 列表與詳情彈窗欄位顯示名稱應具備動態語意：若為 UI1 (開分/投幣) 顯示「開分點數」，若為 UI2 (洗分/退幣) 顯示「洗分點數」，通用情況顯示「實際點數」。
- 檢查 `PROJECT/SignalHub/resources/views/signal-hub/simulator.blade.php`：
  - 修正串口模擬與 Webhook 模擬回寫的欄位，統一為 `actual_points`。

---

## 📝 回報要求
完成後請產出詳細報告至 `.taskflow/signalhub/outbox/`，包含：
1. 修改之檔案清單與 diff 摘要
2. 對接文件範例對照
3. 測試驗證截圖或 curl / API 測試結果

