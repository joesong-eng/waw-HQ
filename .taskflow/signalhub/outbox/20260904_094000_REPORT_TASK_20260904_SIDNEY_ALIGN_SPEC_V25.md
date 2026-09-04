
# 任務回報：TASK_20260904_SIDNEY_ALIGN_SPEC_V25

- **任務 ID**：`TASK_20260904_SIDNEY_ALIGN_SPEC_V25`
- **執行 Agent**：Sidney (SignalHub Lead)
- **回報對象**：HQ
- **日期時間**：2026-09-04 09:40:00 (UTC+8)
- **狀態**：✅ 100% 對齊完成 (ALIGNED)

---

## 📋 對齊項目清單與落實成果

### 1. 廢除固定倍率，全面支援 `actual_points` 開洗分回傳
- **落實狀況**：
  - `ProcessWebhookDelivery.php` 已升級為同時相容解析小猴回傳之 `actual_points` 與 `cleared_points`（自動存入 `signal_webhook_deliveries.cleared_points` 大點數整數欄位）。
  - 精靈 UI 介面已優化，UI1/UI2 僅保留功能定義（開分/洗分），移除前端死板倍率換算，回歸小猴端回報真實點數。

### 2. 小猴主動上報「分數歸零 (session_end)」API
- **落實狀況**：
  - 新增 API 路由：`POST /api/v9/signal-hub/inbound/session-end`。
  - 在 `SignalHubController::sessionEnd` 實作驗簽與資料庫寫入，當機台分數歸零離場時自動記錄事件流水，支援在線雷達空機標記與局時分析。

### 3. 三步精靈 UI 與雙軌通道
- **落實狀況**：
  - 待設置卡片（`testdevice999` / 10 台線上機台）支援一鍵喚醒 3 步精靈。
  - Step 1 機台編號 (`machine_number`) / 名稱 (`machine_name`)。
  - Step 2 開洗分腳位定義 (UI1 / UI2)。
  - Step 3 USB Serial 開關 + 小猴自訂 Webhook URL。

### 4. 10 秒極速定案與 0.6MB/2 天日誌系統
- **落實狀況**：
  - 0s / 3s / 6s 三波衝刺，10 秒超時自動觸發告警。
  - `storage/logs/signal_events/` 超過 600KB 自動滾動切檔，排程維護保留 48 小時。

---

## 🎯 結論
SignalHub 前端與 API 已完全與 **v2.5 設計文檔**（雙軌通訊、10秒定案、actual_points、session_end）**100% 嚴格對齊**，待命進行後續聯調！

