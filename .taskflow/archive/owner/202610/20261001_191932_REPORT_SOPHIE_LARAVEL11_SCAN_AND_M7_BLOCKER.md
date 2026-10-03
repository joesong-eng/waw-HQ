# 掃描回報：Laravel 11 相容性全面掃描 + M7 月結算重大阻塞

**掃描時間**：2026-10-01
**執行者**：Sophie (Owner)
**觸發**：JOE 指示「掃一下」（延伸自 TASK_20261001_SOPHIE_FIX_SETTLEMENTS_CONTROLLER_500）

---

## 一、Laravel 11 相容性掃描結果

專案：laravel/framework ^11.31、php ^8.2、無 app/Http/Kernel.php（已是 Laravel 11 骨架）。

| 檢查項目 | 結果 |
| :--- | :--- |
| $this->middleware() 建構子呼叫殘留 | OK，0 處（本次已修完 SettlementController / ReportController） |
| protected $middleware 屬性式中介層 | OK，0 處 |
| ValidatesRequests / $this->validate() | OK，0 處（未使用） |
| 舊式 Illuminate\Routing\Controller 引用 | OK，0 處 |
| $redirectTo 屬性 | OK，0 處 |
| $dates 屬性（Laravel 10 移除） | OK，0 處 |
| 已移除 helper（array_except / str_slug 等） | OK，0 處 |
| 已移除 Facade（Input） | OK，0 處 |
| RouteServiceProvider 舊式引用 | OK，0 處 |
| 基底 Controller | OK，乾淨（僅 AuthorizesRequests，45 支 Controller 全部正確繼承） |
| 自訂中介層 alias 註冊 | OK，7 個全數註冊於 bootstrap/app.php |
| **結論** | **除已修 2 檔外，全專案無其他 Laravel 11 相容性問題** |

---

## 二、生產日誌掃描：發現 M7 月結算「必定失敗」的真 Bug（已修復）

### 現象
10/1 00:00 排程 GenerateMonthlySettlements 執行失敗，重試 3 次後 production.CRITICAL：

    年月格式錯誤，應為 YYYY-MM: 2026-09-01 00:00:00
    at app/Services/SettlementService.php:39
    #0 app/Jobs/GenerateMonthlySettlements.php(67)

### 根因
SettlementService::generateMonthlySettlements(string $yearMonth) 簽章要求 YYYY-MM 字串，
但 GenerateMonthlySettlements Job 誤傳 Carbon 物件：

    $settlementService->generateMonthlySettlements($this->periodStart, $this->periodEnd)   // 錯誤

Carbon 被隱式轉為 "2026-09-01 00:00:00"，未通過 ^\d{4}-\d{2}$ 正則 -> 拋 InvalidArgumentException。

註：另兩處呼叫（DailyRevenueLock、SettlementController@generate）原本即傳正確的 Y-m 字串，不受影響。

### 修復
commit ffb5dbb：改為 $this->periodStart->format('Y-m')，已 push + deploy owner（遠端 HEAD = ffb5dbb）。
格式驗證：2026-09-01 00:00:00 -> 不匹配；2026-09 -> 匹配 ✅

### 影響
- 2026-09 的月度結算單 **未生成**（settlements 表相關資料 0 筆）。
- Queue 內留有 1 筆失敗 Job：a67ee6ce-4c7f-4020-b852-81cb38cda689。
- **未執行 queue:retry**：補生成會產生真實財務結算單，屬財務行為，需 HQ 決策後為之。

---

## 三、重大阻塞：M7 settlements 表結構與程式碼完全不符（需 Ina 處理）

### 證據
生產 settlements 表實際欄位：

    id, owner_id, amount, outstanding_deducted, effective_payment, method, status, completed_at, reference, created_at, updated_at

程式碼（SettlementService / SettlementController / Settlement model / SettlementPolicy）期望欄位：

    settlement_number, venue_id, device_owner_id, venue_owner_id, period_start, period_end,
    total_revenue, device_owner_amount, venue_owner_amount, device_owner_share, venue_owner_share, ...

### 進一步查證
- M7 建表 migration 2026_03_11_000001_create_settlements_table.php **位於 database/migrations/_migration_archive/**，
  於 commit 519cf6f (refactor: migrate branding from V9/wawv9 to WAW-Core) 被歸檔。
- DB migrations 表 **查無此筆**（以 like %settle% 查詢僅回 2026_06_15_011547_add_outstanding_fields...）。
- 該建表 migration 從未對本生產庫執行；現有 settlements 表由**其他（較舊、已不在 repo）來源**建立。
- 生產 settlement_logs 表存在，且 FK 指向 settlements。
- settlements 表現有資料筆數 = **0**。

### 影響（嚴重）
**即使修好第二項的傳參 bug，M7 月結算仍會失敗** —— Settlement::create() 會因欄位不存在而拋
SQLSTATE[42S22] Unknown column。亦即 **M7 結算功能在生產環境從未真正可用**。

### 建議處置（屬 DB Schema 變更，依鐵律不自行執行 Migration）
1. 由 Ina 評估：現有 settlements（owner_id/amount 版）是否為 legacy 資料表？有無其他模組依賴？
2. 若確認無用 -> 提出遷移方案（重建為 M7 schema，或另開新表名）。
3. 若有用 -> 需與 M7 表分離（改名），避免衝突。
4. 附帶：settlement_logs 與 daily_revenue_reports.settlement_id 的 FK 需一併檢視。

已另備請求文件：.taskflow/infra/inbox/..._REQUEST_SOPHIE_M7_SETTLEMENTS_TABLE_SCHEMA.md

---

## 四、待 HQ 決策事項
1. 是否授權補生成 2026-09 月度結算單（queue:retry a67ee6ce 或 POST /api/v9/settlements/generate year_month=2026-09）？
   - 前提：第三項 schema 問題須先由 Ina 修復，否則仍會失敗。
2. 是否確認「M7 結算功能上線狀態」——目前實質為**未上線**。

## 結論
- ✅ Laravel 11 相容性：除已修 2 檔外全專案乾淨。
- ✅ 已修並部署 1 個「月結算必定失敗」真 bug（ffb5dbb）。
- 🔴 發現架構級阻塞：M7 settlements 表 schema 不符，功能實質未上線 -> 已升級 Ina。

