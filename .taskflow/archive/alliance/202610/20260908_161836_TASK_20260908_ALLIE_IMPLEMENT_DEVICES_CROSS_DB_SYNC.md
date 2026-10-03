# 任務：TASK_20260908_ALLIE_IMPLEMENT_DEVICES_CROSS_DB_SYNC

**派發時間**：2026-09-08 16:30  
**優先級**：HIGH  
**負責人**：Allie (Alliance Lead)  
**協同對象**：Ina (Infra Lead), Sidney (SignalHub Lead)

---

## 📋 任務背景與目標

HQ 已核准你在 PROPOSAL_20260908_ALLIANCE_TO_DEVICES_SYNC_ARCHITECTURE 提出之解決方案。
目前 HQ 已同步派工 Ina (TASK_20260908_INA_DEVICES_SYNC_SCHEMA_AUDIT) 進行 devices 入庫欄位白名單審定。

本任務目標為：依據 Ina 審定之欄位白名單標準，在 Alliance 專案實作出貨自動跨庫寫入 devices，打通老邱出貨至老李開卡的數據鏈條。

---

## 🔍 任務執行要點

1. **實作出貨跨庫同步邏輯**：
   - 在 `app/Http/Controllers/OrderController.php` 的 `ship()` 流程中（或提取專用 Service/Method）。
   - 遍歷該訂單之所有 `ali_device_bindings`。
   - 透過 `DB::connection('waw_core')->table('devices')->updateOrInsert(['chip_id' => ...], [...])` 寫入。
   - 寫入欄位嚴格遵循 Ina 規範之白名單（包含 `chip_id`, `owner_id`, `collector_owner_id`, `machine_owner_id`, `name`, `type`, `status = 'pending_setup'` 等），切勿寫入未授權或歷史過期欄位。
   - 加入完整 Exception catch 與日誌記錄（`Log::channel('...')` 或 `Log::error`/Log::info`），確保即使單一寫入異常亦有跡可循且不造成出貨死鎖。
2. **本機代碼檢驗與 Commit**：
   - 遵循規範：本機僅限 Git 與代碼編輯，不得本機執行 build/migrate。
   - 完成修改後執行 Git 提交。
3. **遠端部署與驗收**：
   - 透過 HQ 指揮遠端部署 `waw_ops.sh deploy alliance` 進行驗收。
4. **回報至 Outbox**：
   - 完成後回報至 `.taskflow/alliance/outbox/`。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260908_ALLIE_IMPLEMENT_DEVICES_CROSS_DB_SYNC

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：Allie (Alliance Lead)

## 實作內容與代碼變更
（包含 Controller 修改位置、跨庫寫入欄位對齊、防禦式日誌等）

## Git 提交資訊
（Commit Hash 與異動檔案清單）

## 結論
✅ 完成實作與部署驗收 / ❌ 遇到問題
```

---
**派發者**：HQ  
**派發時間**：2026-09-08 16:30
