任務回報：TASK_20261001_SOPHIE_OPTIMIZE_DASHBOARD_PERF

**完成時間**：2026-10-01 08:33 (Asia/Taipei)
**執行者**：Sophie (Owner)
**優先級**：P1
**關聯 commit**：`b9e56c6`（waw-business: main）
**前置**：Ina `1ceeda4` 已建立 `idx_venue_valid_ts`（7日查詢 47.9s → 0.20s）

---

## 執行結果

### 1. SQL 與快取優化 ✅

**移除快取閉包外的脫靶查詢**
- `StatisticsController::dashboard()` 原本額外呼叫 `countTodayTransactions()`，
  該方法位於 `getDashboardData()` 快取**之外**，每次請求都觸發一次
  `revenue_facts` 全表掃描（`WHERE venue_id IN (...) AND transaction_type='credit_in' AND is_valid=1 AND event_ts >= today`）。
- 已**完全移除**該方法與呼叫（含 `RevenueFact` / `Carbon` 未用 import），
  改直接複用 `DashboardDataService` 快取閉包內已算好的 `transaction_count`。

**資料流打通**
- `DashboardDataService::buildKPIs()` 補上 `transactions` / `avg_price` / `daily_avg` 欄位
  （原本 only `value/trend/percent`，導致前端只能顯示硬編碼 0）。
- `StatisticsController::formatKPIsForView()` 改為讀取上述欄位，移除 `'transactions' => 0` 佔位。

**快取 TTL 確認合理**
| 快取 | Key | TTL | 評估 |
|:---|:---|:---|:---|
| dashboard_data | `dashboard_data_<venueIds+tz>` | 300s | 合理（5 分鐘，跨日資料） |
| rev_month | `rev_month_<venueIds+start>` | 600s | 合理（月營收獨立防爆表） |
| dash_summary | `dash_summary_<venueIds>` | 60s | 合理（骨架頁輕量摘要） |

### 2. 前端外部資源阻塞移除 ✅

- 移除 `dashboard.blade.php` 第 7 行 `@import url('https://fonts.googleapis.com/...')`
  （Google Fonts 外部阻塞下載）。
- 改用系統字型堆疊：
  - 正文：`system-ui, -apple-system, 'PingFang TC', 'Microsoft JhengHei', sans-serif`
  - 數字：`ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`
- Chart.js 的 `titleFont` / `bodyFont` / 軸刻度字型同步改為系統字型。
- **遠端驗證**：`grep -c 'fonts.googleapis' dashboard.blade.php` → **0**

### 3. 顯示語意修正（JOE 指示）✅

原本頁首「今日投幣」與 KPI 卡「投幣次數」語意不清，且 `transactionCount` 實為
**動作筆數**（投幣 + 開分 + 退幣 + 洗分），與金額無關。

依 JOE 決定統一為「**交易次數**」：
- 頁首：`今日投幣` → `今日交易 N 次`
- KPI 卡：`投幣次數` → `交易次數`
- 綁定改為 `kpis.today.transactions`（真實資料，非硬編碼 0）

### 4. 遠端部署與驗證 ✅

**部署**
```
../../dev_tools/waw_ops.sh deploy owner
✅ owner (owner) 部署完成！
（git pull b9e56c6 + pnpm build + migrate + optimize:clear）
```

**遠端程式碼驗證**
```
HEAD = b9e56c6
grep -c 'fonts.googleapis' dashboard.blade.php = 0
40: font-family: system-ui, -apple-system, 'PingFang TC', ...
567: <span>今日交易</span>
614: <span class="kpi-sub-label">交易次數</span>
```

**KPI 資料流驗證（Tinker 實測 user_id=2）**
```json
{"today":{"value":1166,"transactions":4851},"week":{"value":2336,"transactions":12066,"daily_avg":292}}
```
→ `transactions` 正確帶值，不再為 0

**瀏覽器實測（iot.tg25.win/statistics/dashboard）**
- 登入 `owner@tg25.win` → 正常載入，無白屏
- 頁首顯示「今日交易 **4,943** 次」
- 今日營收卡「交易次數 **4,943**」✅
- 場地對比、7 日趨勢圖正常渲染
- 系統字型已套用（非 Google Fonts）

---

## 待辦（未完成，需確認）

**Item 3「骨架屏 + Ajax 異步化」尚未執行**

原因：此項為架構性改動，需新增 dashboard JSON API
（目前僅有輕量 `/api/v9/dashboard/summary`，僅回 device_count / today_revenue），
並改寫 Blade 為「先渲染骨架 → fetch 填資料」。

**我的評估（建議）**：
經 Ina 索引優化後，DB 端瓶頸已解除（當日查詢 3.98ms），
SSR 首屏延遲主因（慢查詢 + 外部字型阻塞）**已於本次修復**。
骨架屏屬於「觀感優化」而非「效能瓶頸」，建議：
1. 先觀察本次修復後的首屏表現（建議由 JOE 實測）
2. 若仍覺白屏明顯，再投入 Item 3（工時較大，需新增 API + 改寫模板）

**⚠️ 附註**：全域 layout `layouts/app.blade.php` 仍有 Outfit 字型外部載入
（影響全站，非本工單範圍），如需一併處理請另開工單。

---

## 結論

✅ Item 1 完成（SQL 收斂 + 快取優化 + 資料流打通）
✅ Item 2 完成（外部字型阻塞移除）
✅ 顯示語意修正（交易次數）
✅ 遠端部署 + 瀏覽器實測通過
⏸️ Item 3 骨架屏 — 待 JOE 確認是否投入

