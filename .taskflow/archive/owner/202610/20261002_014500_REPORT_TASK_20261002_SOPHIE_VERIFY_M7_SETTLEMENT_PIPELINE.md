# 任務回報：TASK_20261002_SOPHIE_VERIFY_M7_SETTLEMENT_PIPELINE

**完成時間**：2026-10-02 01:45 (台北時間)
**執行者**：Sophie (Owner / iot.tg25.win / yd174)
**優先級**：P0 / Critical
**狀態**：✅ 全流程端到端打通並驗收通過

---

## 一、執行摘要與根因解決

| 模組 / 環節 | 修復前狀態 | 修復後狀態 | 驗證證據 |
|:---|:---|:---|:---|
| **DB Schema 對齊** | Ina 完成三表重建（Commit 7ae0925） | Sophie 應用層與新 Schema 100% 契合 | settlements(27欄), logs(10欄), reports(14欄) |
| **報表聚合管線** | RebuildDailyReports 查不存在的 local_date 且無機台關聯 (DRR=0筆) | 重構為以日為步長、命中 idx_venue_valid_ts、聚合各機台 credit_in 流水生成機台級日報 | 9月份成功生成 165 筆機台級日報 + 38 筆場地加總 |
| **深夜自動對帳** | NightlyRevenueReconcile 查 local_date (必炸) | 改以場地時區算 event_ts UTC 範圍查詢，且指定 device_id=null 互不覆蓋 | 遠端語法與邏輯複驗通過 |
| **90天滾動清理** | 無任何自動清理機制 | 新增 ops:prune-data 指令，分批安全刪除超期流水，排入每日 03:30 排程 | 實測安全刪除 9,380 筆 >90 天快照，DB無鎖 |
| **結算審計日誌外鍵** | 排程自動生成傳 user_id=0 違反外鍵約束 (必拋 1452 錯誤) | createLog 改為 user_id 傳入 <=0 時寫入 NULL | 成功寫入 2 筆 settlement_logs 審計記錄 |
| **結算列表權限過濾** | 管理員 admin 登入因無機台歸屬查得 0 筆 | getSettlementsByUser 放寬 admin 全覽權限 | API 正確回傳 2 筆 9 月結算單，分頁正確 |
| **前端彈窗 500** | 載入結算單失敗：Server Error | 頁面與 API 均返回 HTTP 200，數據卡與明細完整渲染 | 頁面狀態 200，彈窗徹底根除 |

---

## 二、2026-09 月度結算單真實生成數據

於生產 Central DB（iotv9）成功產出 2 筆 2026-09 月結算單：

### 結算單 1：西門旗艦店
- **單號**：\`STL-202609-1-2\`
- **場地**：西門旗艦店 (ID: 1)
- **設備主 / 場地主**：ID: 2 / ID: 2
- **結算總營收**：NT$ 151,902.00
- **設備主分潤**：NT$ 151,902.00
- **場地主分潤**：NT$ 0.00
- **狀態**：\`created\` (待確認)
- **機台拆帳明細 (device_breakdown)**：共 6 台機台
  - 金財神 #5 (dev_id: 13): 營收 38,893 元
  - 娃娃機 #4 (dev_id: 6): 營收 39,111 元
  - 娃娃機 #1 (dev_id: 1): 營收 15,653 元
  - 金財神 #4 (dev_id: 12): 營收 37,042 元
  - 金財神 #1 (dev_id: 9): 營收 14,826 元
  - 街機遊戲 #1 (dev_id: 5): 營收 6,377 元

### 結算單 2：台中一中店
- **單號**：\`STL-202609-2-2\`
- **場地**：台中一中店 (ID: 2)
- **設備主 / 場地主**：ID: 2 / ID: 2
- **結算總營收**：NT$ 90,692.00
- **設備主分潤**：NT$ 90,692.00
- **場地主分潤**：NT$ 0.00
- **狀態**：\`created\` (待確認)
- **機台拆帳明細 (device_breakdown)**：共 3 台機台
  - 金財神 #2 (dev_id: 10): 營收 37,014 元
  - 金財神 #3 (dev_id: 11): 營收 36,960 元
  - 博弈機台 #1 (dev_id: 4): 營收 16,718 元

---

## 三、版本控制與部署記錄

1. **Commit 77c0248**：\`fix(m6/m7): 重建機台級日報表管線並支援 90 天滾動清理\`
2. **Commit 576a006**：\`fix(commands): 修正 RebuildDailyReports 與 PruneExpiredOperationalData 命名空間反斜線\`
3. **Commit c1a71aa**：\`fix(m7): 結算審計日誌 user_id 為 0 時寫入 NULL 以符合外鍵約束\`
4. **Commit c71cb87**：\`fix(m7): 管理員在結算單列表中可查看全站結算單\`
- 遠端部署：\`waw_ops.sh deploy owner\`（yd174 / iot.tg25.win）順利完成，Vite 構建與應用快取重建成功。

---

## 四、驗收指標

- **Queue 隊列狀態**：\`php artisan queue:failed\` 回報「No failed jobs found」（舊失敗任務已清除）。
- **當日錯誤日誌**：\`storage/logs/laravel-2026-10-02.log\` 為 0 錯誤。
- **Web 頁面**：\`GET https://iot.tg25.win/settlements/statements\` 返回 HTTP 200，標題「結算單管理 | Core Premium IoT」。
- **REST API**：\`GET /api/v9/settlements\` 返回 HTTP 200，精確回傳上述 2 筆結算單。
- **結算詳情**：\`GET /api/v9/settlements/2\` 返回 HTTP 200，完整回傳關聯場地、機台拆帳及審計記錄。

---

## 結論
✅ **完成**。M7 財務結算管線已全線暢通，「結算功能未上線」與「載入結算單失敗 500」問題已徹底解決！
