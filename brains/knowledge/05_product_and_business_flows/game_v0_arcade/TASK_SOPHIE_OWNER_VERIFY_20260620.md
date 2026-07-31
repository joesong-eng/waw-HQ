# Sophie 任務：Owner 側欄位語義與後台影響驗證


**[On-Demand]** — 上下文注入策略

> 日期：2026-06-20  
> 發起：HQ  
> 任務類型：Owner 代碼與後台影響驗證  
> 優先級：High

---

## 一、任務前提

DB 結構變更由 Ina 唯一執行。Sophie 不寫 migration、不執行 ALTER、不自行改 DB schema。

本任務目標是協助 HQ / Ina 確認 Owner 端代碼影響範圍，並在 Ina 完成 DB 變更後驗證後台能正確讀取與展示。

---

## 二、需要驗證的設計決策

- `revenue_facts.delta_value` = 本次增量脈衝數。
- `revenue_facts.cumulative_count` = ESP32 NVS 累計脈衝數，將由 Ina 新增。
- `machines.lifetime_pulse_in/out` = 入金/出金累計脈衝數，將由 Ina 新增。
- 現有 `machines.lifetime_pulse` 不可直接刪除或改語義，需先確認用途。
- `pulse_to_token` / `pulse_to_display` 沿用現有命名。
- 金額為交易快照結果，不是採集真理。

---

## 三、Sophie 驗證任務

### 1. Owner 代碼影響範圍掃描
請掃描 waw-core 中以下欄位使用處：

- `lifetime_pulse`
- `lifetime_credit_in`
- `lifetime_credit_out`
- `delta_value`
- `pulse_to_token`
- `pulse_to_display`
- `revenue_facts`

請回報：
- 哪些頁面或 API 使用。
- 是否會受到新增 `cumulative_count`、`lifetime_pulse_in/out` 影響。
- 有無任何地方把 `lifetime_credit_in/out` 當作脈衝數使用。

### 2. 後台顯示建議
請確認 Owner 後台 `/devices` 或機台詳情頁是否需要新增顯示：

- 入金累計脈衝：`lifetime_pulse_in`
- 出金累計脈衝：`lifetime_pulse_out`
- 目前 `lifetime_pulse` 是否應隱藏或標註為舊欄位

### 3. Ina 完成 DB 後的驗證
等 Ina 回報 DB 變更完成後，請只做讀取驗證：

- 確認 Model fillable / casts 是否需更新。
- 確認後台查詢不報錯。
- 確認報表仍使用 `delta_value` / `amount` 正常統計。

---

## 四、回報證據

- `rg` 搜尋結果摘要。
- 修改檔案列表（如有）。
- 後台頁面截圖或 API response。
- 若發現現有代碼把欄位語義用錯，需列出檔案與行號。

---

## 五、回報格式

```markdown
# Sophie 回報：TASK_SOPHIE_OWNER_VERIFY_20260620

## 欄位影響掃描
- lifetime_pulse: ...
- lifetime_credit_in/out: ...
- revenue_facts: ...

## 後台影響
- /devices: ...
- 報表: ...

## 需要 Ina/HQ 決策
- ...

## 驗證證據
- ...
```
