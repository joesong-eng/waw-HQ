# 任務回報：TASK_20260910_SIDNEY_ALIGN_ACTUAL_POINTS_CALLBACK_SPEC

**回報時間**：2026-09-10 18:30 (Asia/Taipei)  
**執行負責人**：Sidney (SignalHub)  
**接收主管**：HQ 協調中心 / Joe  
**狀態**：✅ 已完成 (代碼審計、Model/Controller/Job/Views 對齊、遠端正式部署驗證通過)  
**Git Commit**：`672651c` (`feat(spec): align actual_points callback spec across docs, model, controllers and views`)

---

## 一、任務背景與核心理念貫徹

依據最高架構鐵律與 HQ 指示：
- **電腦型（PC-Based）網路遊戲機**：開分與洗分均由遊戲廠商伺服器全權控制分數與業務結算。
- **採集卡透明邊緣中繼**：採集卡不設定點數比例、不介入業務換算，僅回報物理按鍵觸發次數（`delta_value`）。
- **回調欄位標準化 (`actual_points`)**：全面廢除歷史混用的 `cleared_points`，明定開分（`credit_in` / UI1）與洗分（`credit_out` / UI2）均必須在回調中回傳 `actual_points`（非負整數），否則後台無法進行營業統計與利潤拆帳。

---

## 二、修改檔案清單與 Diff 摘要

本次共修改 9 個核心檔案（包含 1 個 Model、1 個 Controller、1 個 Job、3 個 Blade 視圖、3 份標準對接與系統設計文件）：

| 檔案路徑 | 類型 | 變更摘要 |
|---|---|---|
| `docs/THIRD_PARTY_INTEGRATION_GUIDE.md` | 對接標準文件 | 1. 於第 3 節開頭增加醒目警示方塊，明確說明開分與洗分均必須回調 `actual_points`。<br>2. 修正 6.3 USB CDC 串口回寫確認範例為 `actual_points`。 |
| `resources/views/signal-hub/webhooks.blade.php` | 視圖 (對接範例) | 1. 修正 Payload 範例之 `delta_value` 註解為物理觸發次數。<br>2. 修正 PHP、Node.js、Python 及地端 USB Serial CDC 程式碼範例，全面將開洗分回覆欄位統一為 `actual_points`。 |
| `app/Models/SignalWebhookDelivery.php` | Model | 1. 在 `$fillable` 與 `$appends` 中加入 `actual_points`。<br>2. 新增 Accessor (`getActualPointsAttribute`) 與 Mutator (`setActualPointsAttribute`)，雙向映射至底層 `cleared_points` 欄位。<br>3. `markAsSuccess` 解析邏輯首選 `actual_points`，並保留向下相容支援。 |
| `app/Http/Controllers/Api/V9/CallbackAckController.php` | Controller | 1. 解析首選 `actual_points`。<br>2. 增強防呆告警：當收到開分 (`credit_in` / UI1) 或洗分 (`credit_out` / UI2) 事件但未提供 `actual_points`（或為 null）時，主動記錄警告 Log。<br>3. 回傳 JSON Payload 包含 `actual_points`。 |
| `app/Jobs/ProcessWebhookDelivery.php` | Job | 1. 在同步 Webhook 請求成功後，檢查開洗分事件是否帶回 `actual_points`，缺失時主動記錄 Log 警示。<br>2. 日誌追加記錄 `actual_points`。 |
| `resources/views/signal-hub/deliveries.blade.php` | 視圖 (開洗分紀錄) | 1. 表格欄位表頭透過 `getPointLabel` 動態切換：UI1/UI3 顯示「開分點數」，UI2/UI4 顯示「洗分點數」，通用顯示「實際點數」。<br>2. 資料列表與詳情 Modal 同步動態展示對應語意標籤與點數數值。 |
| `resources/views/signal-hub/simulator.blade.php` | 視圖 (硬體模擬器) | 1. 修正地端 USB CDC 串口模擬回寫 JSON 為 `actual_points`。<br>2. 修正下方雙軌容災說明為 `actual_points`。 |
| `docs/SIGNALHUB_SYSTEM_DESIGN_v2.md` | 系統架構文件 | 同步更新數據保存期與 USB 串口確認格式為 `actual_points`。 |
| `docs/SIGNALHUB_FULL_FEATURE_E2E_TEST_PLAN.md` | 測試計畫文件 | 更新階段 8 測試點為 `actual_points`。 |

---

## 三、對接文件範例對照

### 1. Webhook 回調格式（以 UI1 開分與 UI2 洗分為例）
```json
// 開分 (credit_in)
{
  "status": "success",
  "delivery_id": "del_10284",
  "chip_id": "C8F09E010004",
  "pin_code": "UI1",
  "action_type": "credit_in",
  "actual_points": 1000,
  "message": "開分確認入帳",
  "timestamp": "2026-09-10T18:18:55+00:00"
}

// 洗分 (credit_out)
{
  "status": "success",
  "delivery_id": "del_10284",
  "chip_id": "C8F09E010004",
  "pin_code": "UI2",
  "action_type": "credit_out",
  "actual_points": 3500,
  "message": "洗分結算完成",
  "timestamp": "2026-09-10T18:18:55+00:00"
}
```

### 2. 地端 USB CDC 串口回寫確認（以 \n 換行結尾）
```json
{"status":"success","delivery_id":982341,"actual_points":1000}
```

---

## 四、遠端部署與功能驗證結果

依 WAW SOP 執行 `./dev_tools/waw_ops.sh deploy sidney`，並透過遠端環境進行真實驗證：

### 1. 遠端部署執行指令與輸出
```bash
$ ./dev_tools/waw_ops.sh deploy sidney
🚀 開始執行 sidney (signalhub) 遠端部署...
   目標伺服器: 129.153.116.174:39022
   目標路徑:   /www/wwwroot/signal.tg25.win
   專案架構:   laravel
📡 執行 SSH 指令...
Updating 07190bb..672651c
Fast-forward
 9 files changed, 135 insertions(+), 42 deletions(-)
   INFO  Nothing to migrate.
   INFO  Compiled views cleared successfully.
   INFO  Configuration cached successfully.
   INFO  Application cache cleared successfully.
✅ sidney (signalhub) 部署完成！
```

### 2. Model 雙向 Accessor/Mutator 驗證
遠端執行 Eloquent Model 測試腳本：
```bash
$ php /tmp/test_model.php
TEST_ACCESSOR: 1234
TEST_MUTATOR: 5678
TEST_ARRAY: {"cleared_points":5678,"machine_name":null,"actual_points":5678,"profile":null,"event":null}
```
**驗證結論**：直接存取 `$delivery->actual_points` 正常讀出 `cleared_points` 之值；寫入 `$delivery->actual_points = 5678` 亦同步寫入底層 `cleared_points` 欄位，且序列化為陣列時包含 `actual_points`。

### 3. Web 端點與 Mock Callback 驗證
以 curl 測試線上 API 端點：
- **GET `/api/v9/signal-hub/callback-ack`**：
  ```json
  {"status":"info","message":"SignalHub 異步回調確認端點 (Asynchronous Callback ACK Endpoint)。請使用 HTTP POST 提交結算數據。","guide":"https://signal.tg25.win/docs/THIRD_PARTY_INTEGRATION_GUIDE.md"}
  ```
- **POST `/mock/callback` (模擬開分 UI1)**：
  ```json
  {"status":"success","mode":"sync","delivery_id":"del_99999","chip_id":"TEST_COLI","pin_code":"UI1","action_type":"credit_in","actual_points":1000,"message":"開分確認入帳 (Credit In Processed)","timestamp":"2026-09-10T16:18:23+00:00"}
  ```
- **POST `/mock/callback` (模擬洗分 UI2)**：
  ```json
  {"status":"success","mode":"sync","delivery_id":"del_99998","chip_id":"TEST_COLI","pin_code":"UI2","action_type":"credit_out","actual_points":3500,"message":"洗分結算完成 (Credit Out Processed)","timestamp":"2026-09-10T16:18:27+00:00"}
  ```

### 4. Blade 視圖編譯驗證
遠端渲染測試確認 `signal-hub.webhooks`、`signal-hub.deliveries` 與 `signal-hub.simulator` 模板編譯與渲染均為 200 OK，無任何語法或變數錯誤。

---
報告人：Sidney (SignalHub 負責人)
