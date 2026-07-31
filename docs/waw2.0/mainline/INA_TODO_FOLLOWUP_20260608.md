# Ina TODO Follow-up - 2026-06-08

> 狀態：已透過 HQ Message Hub 發出正式跟進任務  
> 任務 ID：`TASK_20260608_INA_TODO_FOLLOWUP`  
> Outbox：`_agent/outbox/to_Ina.json`

---

## 2026-06-08 06:37 修正

第一次使用舊 `hq_publish_task.sh` 並傳入小寫 `ina`，產生了 `_agent/outbox/to_ina.json`。但 v2 Agent 檢查腳本會讀取首字母大寫檔名：`_agent/outbox/to_Ina.json`。

已改用 `scripts/hq_task_flow.sh task ina ...` 重新發布，現在正式任務位於：

- `_agent/outbox/to_Ina.json`

注意：目前 `_agent/outbox/to_Ina.json.read` 的時間早於本次任務發布，只能代表舊測試任務曾被讀取，不能代表 Ina 已讀本次跟進任務。

---

## 發給 Ina 的重點

Ina 可能沒有同步使用 `TODO.md`，因此 HQ 已明確告知：以這張 HQ Message Hub 任務為準，不需要依賴 TODO 系統。

請 Ina 跟進 WAW 2.0 過渡期三個阻塞點，並提供實際證明：

1. 審核 Sophie 的 `2026_06_06_000000_ensure_device_v2_fields.php`，並於生產環境執行 `devices` 表補欄位 migration。
   - 需要回報：migration output、`SHOW COLUMNS` 或等價查表證明。

2. 將 Infra SQL 查詢從 `pulse_ratio` 改為 `pulse_to_token`。
   - 需要回報：修改檔案、grep 結果、服務重啟 log。

3. 確認 FastAPI `/by-node` 路由順序與 Listener LWT 唯讀化已部署到 VPS。
   - 需要回報：git hash、`systemctl` / `pm2` 狀態、API curl 或 log 證明。

---

## HQ 判定規則

未收到 log、API、DB 查詢或部署狀態證明前，`TODO.md` 對應項目不得標為完成。

目前仍視為：

- `devices` migration：待 Ina 生產執行與證明。
- `pulse_ratio` -> `pulse_to_token`：待 Ina 修改與證明。
- `/by-node` 與 LWT 唯讀化：代碼回報完成，但待 VPS 部署驗收證明。
