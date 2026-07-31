# Ina 實作任務：遊戲機脈衝資料流 DB 與 Infra 修正


**[On-Demand]** — 上下文注入策略

> 日期：2026-06-20  
> 發起：HQ  
> 任務類型：DB 結構變更執行 + Infra 代碼修正  
> 優先級：High  
> 強制規範：`brains/knowledge/01_agent_governance_rules/DB_MIGRATION_WORKFLOW.md`

---

## 一、任務前提

本任務已完成 Sophie / Mina / Ina 三方諮詢，進入實作階段。

### 核心決策
- `pulse_to_token` / `pulse_to_display` 沿用現有命名，不新創 `coin_to_pulse`。
- ESP32 MQTT 上報 `count` 是累計脈衝數，來自 NVS 累加值。
- `revenue_facts` 需要同時保存：
  - `cumulative_count`：ESP32 上報的累計脈衝數。
  - `delta_value`：本次增量脈衝數，現有欄位保留。
- 代幣餘額必須是整數，不支援半枚代幣。
- DB 變更只能由 Ina 設計 DDL、備份 `.sql` 並直接執行；其他 Agent 不寫 migration、不執行 ALTER。

---

## 二、DB 變更需求（由 Ina 設計並執行 DDL）

請先查現況，再自行設計 raw SQL，備份為 `.sql` 文件後執行。不可要求 Sophie / Mina 提 Laravel migration。

### 1. `iotv9.revenue_facts`
需求：新增欄位保存 ESP32 累計脈衝數。

- 欄位語義：`cumulative_count` = ESP32 NVS 累計脈衝數。
- 現有 `delta_value` 保留，語義 = 本次增量脈衝數。
- 請先 `DESCRIBE revenue_facts` 和 `SHOW CREATE TABLE revenue_facts`。
- 若已有等價欄位，不重複新增，回報現有欄位名稱與語義。

### 2. `iotv9.machines`
需求：分開保存入金與出金累計脈衝。

- 需要支援：`lifetime_pulse_in`、`lifetime_pulse_out`。
- 現有 `lifetime_pulse` 用途未明，請先查代碼與 DB 現況，不可直接刪除或改語義。
- 請回報 `lifetime_pulse` 目前是否被寫入或讀取。

### 3. Owner 側 `device_orphan_logs`
需求：建立 Owner 側孤兒脈衝記錄能力。

- 用途：ESP32 有脈衝上報，但 `chip_id` 找不到機台或無法歸屬營收事實時，保留原始採集事實。
- 欄位需覆蓋：`chip_id`、`type`、`cumulative_count`、`delta_count`、估算代幣、估算金額、原因、事件時間。
- 請自行設計欄位類型與索引。

### 4. Member DB 結構變更協助
Mina 端需要以下 DB 結構調整，但執行者仍是 Ina：

- `member_wallets.balance`：代幣餘額改為整數語義。
- `wallet_transactions`：新增或確認交易快照欄位：`delta_count`、`pulse_to_token`、`coin_value`。
- `wallet_transactions`：評估是否將 `cumulative_amount` 改名為 `cumulative_count`，或先保留舊欄位並新增相容欄位。
- `device_orphan_logs`：評估是否將 `cumulative_amount` 改名為 `cumulative_count`，或先保留舊欄位並新增相容欄位。

重要：改名前必須先完成影響範圍掃描，避免破壞 Member 現有代碼。

---

## 三、Infra 代碼修正需求

### 1. 先做影響範圍掃描
在修改 `cumulative_amount` → `cumulative_count` 前，請先掃描：

- `tg25-infra` 全專案
- `Member` 端相關 Controller / Model / View
- 若可查，確認韌體 MQTT 上報只使用 `count`，不依賴 `cumulative_amount`

回報需列出受影響檔案與建議相容策略。

### 2. `credit_in` 需轉發給 Member
你已回報 `handle_credit_in` 目前只寫 Redis / `revenue_facts`，沒有轉發 Member。請修正：

- 收到 `credit_in` 後，除了寫 Owner 事實表，還要轉發 Member。
- Payload 必須帶完整累計脈衝數。
- 建議新格式：`cumulative_count`。
- 如 Member 尚未完成新欄位接收，需短期相容同時傳 `cumulative_count` 與 `cumulative_amount`，並在回報中說明。

### 3. `credit_out` 轉發欄位相容策略
目前 `credit_out` 使用 `cumulative_amount`。請依影響掃描結果決定：

- 若 Mina 已支援 `cumulative_count`：改為 `cumulative_count`。
- 若 Mina 尚未支援：短期同時送兩個欄位，避免中斷現有功能。

### 4. `revenue_facts` 寫入
當 `revenue_facts` 新增 `cumulative_count` 後：

- 寫入 `delta_value` 時也要寫入本次 MQTT `count` 作為 `cumulative_count`。
- 首次基準線與 Redis 遺失時，必須用 DB 最後一筆 `cumulative_count` 作為恢復依據，不能只依賴 Redis。

---

## 四、驗證要求

回報時必須附證據，不接受口頭「已完成」。

### DB 證據
- `DESCRIBE revenue_facts;`
- `DESCRIBE machines;`
- `SHOW CREATE TABLE device_orphan_logs;`（如已建立）
- Member 相關表的 `DESCRIBE` 結果。
- Ina 備份的 `.sql` 文件路徑。

### 代碼證據
- 修改檔案列表。
- `git diff -- <modified files>` 摘要或貼關鍵片段。
- listener 測試 log：至少包含一筆 `credit_in` 與一筆 `credit_out` 的轉發結果。

### 影響範圍證據
- `cumulative_amount` / `cumulative_count` 搜尋結果摘要。
- 韌體端是否受影響的判斷依據。

---

## 五、回報格式

```markdown
# Ina 回報：TASK_INA_DB_AND_INFRA_20260620

## DB 現況檢查
- revenue_facts: ...
- machines: ...
- Member tables: ...

## DDL 執行結果
- SQL 備份路徑：...
- 執行 log：...

## 影響範圍掃描
- cumulative_amount 使用處：...
- 韌體影響：有/無，依據：...
- 相容策略：...

## Infra 代碼修改
- 修改檔案：...
- credit_in 轉發：已完成/未完成，原因：...
- credit_out 欄位：...

## 驗證結果
- credit_in 測試 log：...
- credit_out 測試 log：...

## 阻塞/疑問
- ...
```
