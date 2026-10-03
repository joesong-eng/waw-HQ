# 工單：TASK_20260916_SIDNEY_REMOVE_MACHINES_VALIDATOR

**派發時間**：2026-09-16 22:45  
**優先級**：HIGH  
**負責人**：Sidney (SignalHub Lead)  
**前置決策**：HQ 已核准終止 machines 體系，全面固化 devices 為唯一 SSOT

---

## 任務內容

配合資料庫即將 DROP machines 表，需先清理 SignalHub 後台對 machines 表的外鍵驗證規則，避免 DROP 表後觸發 HTTP 500。

### 1. 修改 app/Http/Controllers/Api/V9/SignalHubController.php
- 第 72 行（store 方法）：
  - 將 'machine_id' => 'nullable|integer|exists:machines,id' 改為 'machine_id' => 'nullable|integer'
- 第 126 行（update 方法）：
  - 將 'machine_id' => 'nullable|integer|exists:machines,id' 改為 'machine_id' => 'nullable|integer'

### 2. 部署與驗收
- 檢查代碼無語法錯誤。
- 部署至 SignalHub 伺服器 (sidney / signal.tg25.win)。
- 清理 route/config 快取（php artisan optimize:clear）。
- 驗證 Profile 建立與更新 API 運作正常。

---

## 回報格式
完成後使用 agent_report_to_hq_v2.sh 提交報告至 HQ outbox。
