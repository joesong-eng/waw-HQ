# Sidney 工作回報 — 2026-09-21

回報人：Sidney（SignalHub 負責人）
回報對象：HQ
狀態：已完成部署驗證

---

## 一、本次完成的工作項目

### 1. Webhook Payload 加入開分點數倍率

原本 Webhook 推送的 amount 只有 delta_value x pin_ratio，沒有乘上機台的 pulse_to_display。
老李那邊設置一開分 = 100 分，但合作方收到的 amount 永遠是 1（delta 次數），根本不知道要開幾分。

變更後，Webhook POST body 新增：
  - points_per_pulse：每脈衝點數（源自 devices.pulse_to_display）
  - amount：本次應開/洗點數（delta_value x points_per_pulse）

範例：連按 3 次，pulse_to_display=100，amount=300

### 2. SignalHub 機台管理頁面重構

原本機台管理只查 signal_profiles，Owner（Sophie）後台裡已有的設備（如風神01）在 SignalHub 看不到。

重構後：
  - API 改以 devices 為主體查詢（LEFT JOIN signal_profiles）
  - 新增一鍵快速設置按鈕，為未設置的設備建立 SignalProfile + 預設 8 腳位
  - 頁面改為單一設備列表，未設置的顯示橘色「未設置」標示

### 3. 架構分界：電腦型只顯示在 SignalHub

傳統機板型設備不走 SignalHub，不需腳位映射也不需 Webhook，只需在 Sophie 設置 pulse_to_display。
SignalHub 機台管理現已過濾，只顯示 config_json.machine_category = pc_game 的設備。

### 4. Sophie 設備列表新增 SignalHub 設定狀態

DeviceController 新增批次查詢 signal_profiles，電腦型設備名稱旁顯示：
  - 綠色「SignalHub 已設定」
  - 橘色「SignalHub 未設定」

讓 Sophie 一眼判斷兩邊的設置進度。

---

## 二、HQ 需要配合的事項

### 【重要】更新公開指南頁面

URL：https://signal.tg25.win/signal-hub/guide

1. Webhook Payload 欄位說明新增 points_per_pulse 與 amount
   說明 WAW 側根據 pulse_to_display 自動換算後帶入，合作方直接用 amount 開分即可

2. 新增「機台類型架構說明」區塊
   - 電腦型（PC-Based）：採集卡透明中繼，分數由遊戲商雲端決定
   - 傳統機板型：不走 SignalHub，機板自體閉環控制

3. 新增「雙系統設置分工」說明
   - Sophie（Owner）負責：pulse_to_display、場地、機台類型
   - Sidney（SignalHub）負責：採集卡腳位映射、Webhook 端點
   - 兩邊都設置完成，機台才能正常運作

### 【次要】Sophie 機台列表 signal_hub_configured 欄位已備好

後端 API 已有 signal_hub_configured 布林值，前端電腦型設備旁已顯示徽章。
若 Sophie 需要在詳情頁也顯示、或加入篩選功能，請另行派工 Sophie 跟進。

---

## 三、部署狀態

- SignalHub（signal.tg25.win）：Commit 0d0bbd7，已部署驗證
- Owner（iot.tg25.win）：Commit 3da6080，已部署驗證
