# 任務回報：TASK_20260908_SIDNEY_WEBHOOK_RETENTION_AND_MOCK_INTEGRATION

- **任務 ID**：`TASK_20260908_SIDNEY_WEBHOOK_RETENTION_AND_MOCK_INTEGRATION`
- **執行 Agent**：Sidney (SignalHub Lead)
- **決策者 / 評審**：Joe (Boss / 最高決策者)
- **回報對象**：HQ (Taskflow 總指揮)
- **日期時間**：2026-09-08 12:00:00 (UTC+8)
- **狀態**：✅ 100% 達成並已部署生產驗證 (COMPLETED & VERIFIED)

---

## 📋 本次任務重點與落實成果

### 1. Webhook 介面重構與小猴 Mock 接收端開發
- **暗黑沉浸式 UI**：徹底移除不協調的白底卡片與冗餘贅述，統一為專業暗黑色系 (`slate-900 / slate-950`)。
- **Mock 接收端終端 (`/mock/callback`)**：
  - 專門模擬第三方（遊戲商/小猴）伺服器，接收由 SignalHub 推送的 Webhook POST 請求。
  - 即時終端視窗 (Terminal Console) 雙向印出「收到的硬體脈衝 Payload」與「即時產生的回覆 Response」。
  - 採用記憶體快取滑動視窗（Sliding Window），固定僅保留最新 50 筆，TTL 24 小時，絕不佔用資料庫。

### 2. 首創「雙軌返回模式」與容錯架構
- **模式一：同步原路返回 (Sync - 首選標準)**：
  - 合作方在單一 HTTP 連線中 3 秒內直接回傳 HTTP 200 JSON（包含 `actual_points`）。
  - 零狀態掛起，平均 30~50ms 內完成點數結算。
- **模式二：異步 reply_url (Async - 爛網路容錯補救措施)**：
  - 當合作方處理速度慢或網路不穩時，合作方 0.1 秒秒回簽收 ACK (`{"status":"received","mode":"async"}`)，避免 SignalHub Worker 長時間掛起。
  - 合作方後台計算完成後，背景主動 HTTP POST 結算點數至請求中附帶的 `reply_url` (`https://signal.tg25.win/api/v9/signal-hub/callback-ack`)。
  - 兩套模式在 `/mock/callback` 頂部提供按鈕即時切換測試，並經實測驗證通過。

### 3. 糾正售貨機思維：回歸純硬體採集開放標準 (WAW-USS)
- **廢除偽倍率**：全面拔除 `amount`、`unit`、`pulse_ratio`（脈衝換算比例）等舊式自動售貨機欄位。
- **純粹硬體上報**：採集卡與 SignalHub 僅上報硬體累計脈衝 (`raw_value`) 與單次觸發差額 (`delta_value: 1`)。
- **金額解耦**：實際開洗分點數由合作方業務引擎全權判定，並透過 `actual_points` 回傳，後台無縫入庫。

### 4. 資料生命週期與儲存空間防爆機制 (Data Retention & Pruning Policy)
為防範 24 小時高頻營業機台將資料庫與磁碟空間撐爆，實作分層保存策略：
- **🚨 失敗超時記錄**：保留 **14 天**後自動徹底清理。
- **📦 通訊封包瘦身 (Payload Slimming)**：保留 **30 天**。超過 30 天的成功推送記錄，自動將佔用 85% 空間的 `request_payload`、`request_headers`、`response_body` 設為 `NULL` 釋放磁碟空間，但完整保留核心流水號、機台、腳位、時間與 `actual_points` 點數供長期對帳。
- **📊 歷史總帳與硬體事件**：保留 **90 天**後自資料庫徹底刪除。
- **Artisan 自動排程**：
  - 新建指令：`php artisan signal:prune-deliveries`（支援 `--dry-run`、自訂天數）。
  - 支援 Laravel 11 原生 Model `Prunable` trait。
  - 設定遠端 crontab 每日凌晨 03:00 自動執行資料庫清理，03:30 執行日誌清理。

### 5. 系統設計規範對齊
- `docs/SIGNALHUB_SYSTEM_DESIGN_v2.md` 升級至 v2.7（完整收錄雙向通訊協議、4 重安全防偽、Session End 歸零通知、第 6 章資料防爆機制）。
- `docs/THIRD_PARTY_INTEGRATION_GUIDE.md` 同步更新至 v2.1。

---

## 🚀 部署與遠端驗證數據
- **Git 版本**：`577afb4` (branch: `main`)
- **遠端主機**：`129.153.116.174:39022` (`signal.tg25.win`)
- **部署工具**：`waw_ops.sh deploy sidney` (零停機成功)
- **遠端驗證紀錄**：
  - `php artisan signal:prune-deliveries --dry-run` 執行回傳 0 錯誤。
  - `php artisan schedule:list` 確認 03:00 prune 指令已排程就緒。
  - 端點 `https://signal.tg25.win/mock/callback` 與 `https://signal.tg25.win/signal-hub/deliveries` 運作正常。

