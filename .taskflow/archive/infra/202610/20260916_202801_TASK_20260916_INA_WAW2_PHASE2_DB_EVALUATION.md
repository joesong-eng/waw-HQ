# 任務：TASK_20260916_INA_WAW2_PHASE2_DB_EVALUATION

**派發時間**：2026-09-16 17:30  
**優先級**：HIGH（架構評估 / 只看不改）  
**負責人**：Ina (Infra)  
**指導方針**：嚴格遵守 HQ TODO 鐵律（嚴禁私自變更設計、嚴禁暴力停機、只評估不寫碼）

---

## 📋 任務目標

WAW 2.0 計畫將現行單一 `iotv9` 資料庫拆分為物理基礎層（`waw_infra`）與商業邏輯層（`waw_core`），並引入「軟性欠費」與「固化分潤交易流水」。
鑑於該重構涉及核心資料庫拓撲與全系統各 Agent 既有資料鏈，**影響層面極廣**。請 Ina 針對 Phase 2 雙庫新表 Migration 設計與遷移路徑進行深度架構評估與影響分析。

⚠️ **警告：本任務為純架構與可行性評估，嚴禁修改線上生產環境任何資料表結構、觸發器或程式碼！**

---

## 🔍 評估範圍與具體要求

### 1. 現狀資料鏈盤點與影響分析 (Current State & Impact Analysis)
- **現行依賴盤點**：盤點目前哪些服務直接讀寫 `iotv9.devices`（包含 FastAPI、Listener、Owner、Member、Alliance、SignalHub）。
- **跨庫觸發器連鎖衝擊**：9/14 剛上線的 `alliance_db.ali_device_bindings` -> `iotv9.devices` 跨庫觸發器，若未來目標表改為 `machines`，影響為何？
- **SignalHub 設備分配衝擊**：Sidney 剛於 9/16 完成閉環的 `device_assignments` 與 `devices.owner_id` 設備歸屬與退貨生命週期，拆庫後如何與 `machines` 及 `machine_deployments` 銜接？

### 2. 雙庫新表架構設計審查 (Schema Review for waw_infra)
評估 TODO.md 中規劃的 4 張新表：
1. `stores` (場地/店面)
2. `machines` (機器主表，取代舊 `devices`)
3. `machine_deployments` (部署與移機歷史軌跡)
4. `machine_transactions` (固化分潤交易流水)

請提出：
- 建議的 DDL 初稿（欄位名稱、型態、主外鍵索引、字元集 utf8mb4）。
- 如何解決跨庫無法建立實體 Foreign Key Constraint 的資料一致性問題？

### 3. 無損遷移路徑設計 (Zero-Downtime Migration Strategy)
- 舊 `devices` 表累積的歷史設備資料，如何無縫無損移轉至 `machines`？
- 過渡期過渡方案評估：
  - 方案 A：資料庫 View / Trigger 雙向鏡像（相容舊 API）。
  - 方案 B：應用程式層雙寫（Dual-write）。
  - 方案 C：階段性路由切換。
- 哪種方案對線上運行（投幣、開分、洗分、即時 Webhook）風險最低？

### 4. 軟性欠費技術可行性分析 (Arrears Soft-Mode Technical Feasibility)
- 物理採集層（FastAPI / MQTT Listener）標記設備狀態為 `arrears` 時：
  - 評估在維持高頻消費事件（100ms 級別開分、落鈔、洗分）不中斷的前提下，向商業層查詢分潤比例並固化寫入 `machine_transactions` 的延遲與高併發衝擊。
  - Redis 快取分潤比率的淘汰與失效機制設計。

### 5. 風險矩陣與分階段實施建議 (Risk Matrix & Rollout Phases)
- 列出 Top 3～5 個潛在致命架構風險（如資料庫連線池耗盡、分散式交易不一致、回滾困難等）與防禦機制。
- 建議的實施階段規劃（如：Phase 2.1 影子新表建置 -> 2.2 背景同步與校驗 -> 2.3 讀切換 -> 2.4 寫切換 -> 2.5 舊表封存）。

---

## 📝 產出要求與驗收標準

1. 產出繁體中文架構評估報告，寫入：
   `.taskflow/infra/outbox/REPORT_20260916_INA_WAW2_PHASE2_DB_EVALUATION.md`
2. 報告需包含具體 DDL 提案、架構流向 ASCII 圖或 Mermaid 圖、風險矩陣與建議工期。
3. 完成後使用 `agent_report_to_hq_v2.sh` 回報至 HQ。

