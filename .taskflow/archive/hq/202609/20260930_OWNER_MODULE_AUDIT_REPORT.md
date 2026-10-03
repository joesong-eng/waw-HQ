# Owner 後台模組完成度盤點報告

> **From**: Sophie (Owner)  
> **To**: HQ  
> **Date**: 2026-09-30  
> **Subject**: iot.tg25.win 全模組完成度盤點與待辦排序

---

## 📊 模組完成度總覽

| 模組 | 名稱 | 狀態 | 完成度 |
|:---:|:---|:---:|:---:|
| M1 | 人員與權限管理 | ✅ | 100% |
| M2 | 訂閱服務（雙軌） | ✅ | 100% |
| M3 | 設備管理 | ✅ | 100% |
| **M4** | **場地與分潤** | ⚠️ | **85%** |
| **M5** | **通知系統** | ⚠️ | **70%** |
| **M6** | **統計與報表** | ⚠️ | **65%** |
| **M7** | **對帳結算** | 🔴 | **60%** |
| M8 | 帳單與續約 | ✅ | 100% |
| **M9** | **即時監控與設定** | ⚠️ | **75%** |
| M10 | SignalHub | ✅ | 100% |

---

## 🔴 P0 嚴重缺口（應立即處理）

### 1. M7 對帳結算 — API 路由未掛載

**問題**：`SettlementController` 已完整實作（confirm / approve / dispute / resolveDispute / downloadPdf / generate），但 `routes/api.php` 裡完全沒有 settlement 相關 API 路由。前端 Blade 直接呼叫的 API 端點不存在，對帳操作無法運作。

**待補 8 條路由**：
- `GET /api/v9/settlements` — 列表
- `GET /api/v9/settlements/{id}` — 詳情
- `POST /api/v9/settlements/{id}/confirm` — 場地主確認
- `POST /api/v9/settlements/{id}/approve` — 設備主批准
- `POST /api/v9/settlements/{id}/dispute` — 提起爭議
- `POST /api/v9/settlements/{id}/resolve-dispute` — Admin 解決爭議
- `GET /api/v9/settlements/{id}/download-pdf` — PDF 下載
- `POST /api/v9/settlements/generate` — 手動生成月結

### 2. M6 報表 — lockAll() 缺 Admin 權限檢查

**問題**：`ReportController::lockAll()` 有 `TODO: 添加 Admin 權限檢查`，目前任何登入用戶都能觸發全量日報鎖定 Job。

---

## ⚠️ P1 功能缺口

### 3. M4 場地總覽 — index.blade.php 為 placeholder

**問題**：`m4/index.blade.php` 顯示「模組建置中」佔位頁。後端 API 已就緒，缺前端入口頁整合 venues + profit-sharing-proposals + stats。

### 4. M5 通知系統 — 多處 stub

| 項目 | 位置 | 說明 |
|:---|:---|:---|
| Telegram 通知 | `NotificationService:297` | `TODO: Implement Telegram integration` — 空方法 |
| Webhook 失敗告警 | `ProcessWebhookDelivery:154,182` | `TODO: 發送通知給店主` / `TODO: 發送告警通知` |
| 結算爭議通知 | `SettlementService:635` | `TODO:` 標記，爭議通知未實作 |
| 設備 lost/stolen | `DeviceController:1018` | `TODO: lost/stolen` 處理邏輯缺失 |

### 5. M6 統計與報表 — KPI 多處 stub

| 項目 | 位置 | 說明 |
|:---|:---|:---|
| 今日交易筆數 | `StatisticsController:98` | `'todayTransactions' => 0` 寫死為 0 |
| 報表頁面 | `StatisticsController:136` | 註解 `// 保持原有實現，後續重構` |
| lockAll Admin | `ReportController:164` | `TODO: 添加 Admin 權限檢查` |
| Dashboard API | `DashboardSummaryController` | 只回傳 device count + revenue sum，缺趨勢/對比 |

### 6. M9 即時監控與設定 — WebSocket 未廣播

| 項目 | 位置 | 說明 |
|:---|:---|:---|
| WebSocket 推播 | `MqttHeartbeatHandler:71` | `broadcastStatusUpdate` 空實作 |
| 脈衝廣播 | `MqttPulseDataHandler:105` | 同上，脈衝事件未廣播 |
| 歷史警報 | `m9/alerts.blade.php` | 只顯示即時 WS 事件，無歷史警報查詢 |

---

## 📋 P2 底層服務 TODO

| 服務 | 位置 | 說明 |
|:---|:---|:---|
| `InternalPulseController::creditOut` | `:134` | 返回 501 not_implemented |
| `BusinessRuleEngine::loadCustomRules` | `:122` | 場地自訂規則返回空陣列 |
| `ParameterErrorHandler::recalculateRevenue` | `:226` | 收入重算返回 pending stub |
| `ParameterCacheManager::getCacheStats` | `:247` | 快取統計只回傳 TTL 值 |
| `ErrorMonitor:337` | — | LINE 告警整合未實作 |

---

## 🎯 建議優先順序

| 優先 | 任務 | 預估 | 指派 |
|:---:|:---|:---:|:---|
| **P0** | M7 補上 settlement API 路由（8 條） | 0.5h | Sophie |
| **P0** | M6 `lockAll()` 加 Admin 權限檢查 | 0.5h | Sophie |
| **P1** | M4 index.blade.php 場地總覽入口頁 | 2h | Sophie |
| **P1** | M5 結算爭議通知 + Webhook 失敗告警 | 3h | Sophie |
| **P2** | M6 報表 KPI 交易筆數實作 | 4h | Sophie |
| **P2** | M9 歷史警報查詢頁 | 3h | Sophie |
| **P2** | M9 WebSocket broadcast stubs 補實作 | 2h | Sophie |
| **P3** | 底層服務 TODO 清理 | 4h | Sophie |

---

## 📌 備註

- M1/M2/M3/M8/M10 已完成，無待辦
- M7 SettlementController 代碼完整，只差路由註冊 — 這是最快能修的
- WebSocket 相關需與 Infra (Ina) 確認 Reverb 配置
- `creditOut` 目前由 Infra 直接寫入 DB，Owner 端 stub 可保持不動

---

*報告由 Sophie 自動盤點產生*


---

## 🏛️ HQ 審核與決策記錄 (Review & Decision)

- **審核時間**：2026-09-30 01:25
- **審核人**：HQ / Joe
- **決策結論**：
  1. ✅ **盤點結果確認無誤**：M1/M2/M3/M8/M10 已達成 100% 完備。
  2. ⚠️ **採納 P0 缺陷修復建議**：
     - M7 Settlement 8 條缺漏路由補齊。
     - M6 ReportController lockAll 權限門禁。
  3. 📦 **本提案工單正式結案歸檔**。後續修復由 HQ 另起獨立 `TASK` 派發給 Sophie，不在此報告堆疊代碼。

---
