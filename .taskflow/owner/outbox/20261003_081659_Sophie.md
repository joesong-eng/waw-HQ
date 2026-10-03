# 任務提報與模組完工狀態總結：全模組已完工交付，提報生產環境 CheckPendingMachines 異常請求派單

**提報日期**：2026-10-03
**提報者**：Sophie (Owner 後台守護者)
**接收者**：HQ / Joe
**優先級**：P2 (每日排程異常)
**關聯模組**：Owner (iot.tg25.win / yd174)

---

## 一、目前 Owner 模組完工現況

截至 2026-10-02 晚間，所有已派發之修復與補全工單已全數執行、通過遠端真實驗證並部署上線：

| 模組 | 項目 | 狀態 | 最新 Commit / 驗證成果 |
|:---:|:---|:---:|:---|
| **M1** | 人員與權限管理 | ✅ 100% | 技師登入與權限管理穩定 |
| **M2** | 雙軌訂閱服務 | ✅ 100% | 周期計費、欠費鎖定、通知泡泡正常 |
| **M3** | 設備管理與響應式 | ✅ 100% | 行動端卡片與邊距優化完成 |
| **M4** | 場地總覽與分潤 | ✅ 100% | 場地總覽入口頁（`m4/index.blade.php`）已整合完成 |
| **M5** | 通知系統 | ✅ 100% | Webhook 失敗告警通知、命名空間引用修復完成 |
| **M6** | 統計與報表 | ✅ 100% | 今日交易 KPI 實作、`lockAll` Admin 權限門禁完成 |
| **M7** | 對帳結算 | ✅ 100% | 8 條 API 路由掛載、爭議處理與結算單生成流水線通過實測 |
| **M8** | 帳單與續約 | ✅ 100% | 營運商續約流程穩定 |
| **M9** | 即時監控與廣播 | ✅ 100% | `DeviceUpdated` WebSocket 廣播接通、修正 `InternalPulseController` 實例化致命錯誤 |
| **M10** | SignalHub | ✅ 100% | 外部合作夥伴協議與公網 API 穩定 |

- **版本狀態**：本機與遠端 `yd174` 同步（HEAD: `9784365`）。
- **工作目錄**：乾淨無未提交變更。
- **工單狀態**：`owner/inbox` 內工單已全數驗證交付，回報單已入 Outbox。

---

## 二、生產環境發現之異常（待派單）

在每日日誌巡檢中發現，今日凌晨 00:00:05 排程執行報錯：

### 異常現象
- **排程指令**：`machines:check-pending` (`App\Console\Commands\CheckPendingMachines`)
- **報錯訊息**：
  ```
  SQLSTATE[42S02]: Base table or view not found: 1146 Table 'iotv9.machines' doesn't exist
  (SQL: select * from `machines` where `status` = pending_setup and `created_at` < ... and `machine_owner_id` is not null)
  ```

### 根因分析
1. WAW 2.0 架構規範已明確指出：無需建立 `machines` 表，全系統以 `devices` 表作為實體設備主表。
2. `CheckPendingMachines` 仍依賴 `App\Models\Machine`，其 `$table = 'machines'` 且查詢欄位為 `machine_owner_id`。
3. 生產資料庫 `iotv9`（Infra）無 `machines` 表，導致每夜定時檢查通訊卡未上線警報時拋出 QueryException。

---

## 三、建議修復方案與派工請求

1. **改造 CheckPendingMachines**：
   - 將 `Machine` 模型依賴替換為 `Device` 模型（對應 `devices` 表）。
   - 欄位對齊：`owner_id`、`name`、`status = 'pending_setup'`。
   - 驗證：執行 `php artisan machines:check-pending --dry-run` 確認無 SQL 錯誤。
2. **清理 legacy Machine 模型引用**：
   - 審查 `App\Models\Machine` 及相關 Observer / Policy 之存廢，避免其他潛在隱患。

請 HQ 審閱並派發工單，Sophie 隨時待命執行。

