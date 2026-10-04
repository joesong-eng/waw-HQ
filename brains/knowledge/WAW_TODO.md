# WAW 待辦事項總表 (Master TODO)

維護者：HQ
最後更新：2026-10-05（HQ 收尾：補記 SignalHub 獨立站點已上線）
說明：此文件記錄跨專案的中長期待辦，避免遺忘。各 Agent 的即時任務走 .taskflow 系統。

---

## ⏸ Alliance UI 技術債（2026-09-21 暫緩，不派工）

- [ ] **[Allie]** 階段 C：全站按鈕 / Badge / Card 統一（計畫書 2.1–2.3）
- [ ] **[Allie]** 階段 D：拆 burning.blade.php（高風險，Joe 凍結）
- [ ] **[Allie]** 批次出貨 try-catch 與批次刪除 audit log
- [ ] **[Allie / Ina]** 登入 throttle 信任 Cloudflare 真實 IP
- 詳細：PROJECT/Alliance/docs/有空回頭再做的任務紀錄.md

---

## 🔴 SignalHub 核心流程

- [x] **[Sidney]** SignalHub 獨立站點建置（signal.tg25.win 已上線「WAW SignalHub」；repo: signal-hub-standalone）
- [x] **[Sidney]** 完成 Owner 後台「信號設定」選單入口整合
- [x] **[Ina]** 生產資料庫 iotv9 執行 SignalHub Migration（5張表建立完成）
- [ ] **[Sidney]** 跑通第一個完整樣板：店主建設定檔 → 腳位映射 → 統計規則 → ESP32 MQTT
- [ ] **[HQ]** 對外開發者文件（WAW IoT ESP32 韌體規格、MQTT 格式、QoS）
- [ ] **[HQ]** API 接入規格（OpenAPI 3.0 / PHP）
- [ ] **[HQ]** 開源策略文件（MIT 2.0）

### 已完成

- [x] **[HQ]** 四層架構概念設計（WAW標準局 / 平台商 / 店主 / 玩家）
- [x] **[HQ]** SignalHub 資料庫 Schema 設計（5張表）
- [x] **[HQ]** SignalHub 後台 UI 規格文件
- [x] **[Sophie]** Owner 後台 Migration 檔案建立
- [x] **[Sophie]** 5個 Model 建立（SignalProfile/PinMapping/StatRule/Webhook/Event）
- [x] **[Sophie]** SignalHubController 建立（18個 API 端點）
- [x] **[Sophie]** 4個 Blade View 建立（profiles/pins/stats/webhooks）
- [x] **[Sophie]** API 路由 + Web 路由掛載
- [x] **[HQ]** signal.tg25.win DNS CNAME 指向 play.tg25.win → 129.153.116.174
- [x] **[HQ]** ADR-003 訂閱表統一（廢除 owner_subscriptions，統一為 subscriptions）

---

## 🟡 WAW 2.0 過渡期遺留任務

> 部分任務已派工但尚未確認完工，需追蹤。

### 階段 1：devices 表 Schema 變更

- [ ] **[Ina]** 審核 Sophie 的請求，於 tg25-infra 跨寫 Migration 並於生產環境執行 devices 表變更。(⏳ 任務已派發)
- [ ] **[Ina]** 將 SQL 查詢的 pulse_ratio 變更為 pulse_to_token。(⏳ 任務已派發)

### 階段 2：權限與 API 雙向相容

- [x] **[Mina]** 後端 kiosk_token 與舊 token 雙向相容 (API & 登入會話隔離)。
- [x] **[Sophie]** 修改中間件，將 sub_agent 角色納入放行名單中。
- [x] **[Ina]** listener.py 補上 MEMBER_BILL_API_URL 環境變數加載。

### 階段 3：核心業務邏輯割接

- [ ] **[Ina]** 調整 FastAPI 路由順序（防 /by-node 被截斷），並將 Listener LWT 更新為唯讀化。(⏳ 任務已派發，待 VPS 部署)
- [x] **[Allie]** 修改 bindDevice() 邏輯，使之支持最新 draft/completed 狀態。
- [x] **[Coli]** 模擬脈衝可行性分析與 simulate_pulse 韌體實作 (v1.0.26 已發布至 OTA)。

### 階段 4：前端對齊與終端驗收

- [ ] **[Hubie]** 平板端參數更名為 kiosk_token，配合 API 聯調。(⏳ 任務已派發)
- [x] **[Mina]** 前端 welcome.blade.php 儲存更新為 kiosk_token。

---

## ⛔ 已廢棄

以下架構已於 2026-10-03 正式廢棄，不再採用：

- **Hermes + VPS Redis 多管道派工架構** — 現行唯一派工體系為 .taskflow 純檔案信箱。
- **hq_gateway.py / DecisionEngine** — 已刪除。
- **Redis Pub/Sub 派工** — 已刪除。

設計文件保留供歷史參考：brains/knowledge/03_system_architecture/MULTI_CHANNEL_DISPATCH_ARCHITECTURE.md

---

## 📋 注意事項

1. ❌ **嚴禁私自變更設計**：未經 HQ 審核批准，嚴禁私自建表、亂加欄位、修改 API 端口或變更通訊協定命名。
2. ❌ **禁止暴力停機**：不得引入中斷硬體通訊或掃碼開分的攔截代碼，必須嚴格執行「軟性欠費運行」機制。
3. ⚠️ **有困難立即回報**：執行過程中若有技術困難，禁止私自設法妥協修改，必須立即回報 HQ 重新評估。
