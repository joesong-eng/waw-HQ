# 📢 HQ TODO (WAW 2.0 大修與矛盾修復待辦清單)

> **最後更新**：2026-06-21 UTC+8  
> **當前階段**：過渡期矛盾修復 ──> WAW 2.0 人物拆分與雙資料庫遷移銜接  
> **注意**：大修涉及核心資料庫與 API，所有 Agent 必須嚴格按階段順序執行，嚴禁私自變更設計或亂加欄位。

---

## 🔵 基礎設施：多管道派工架構（Hermes + VPS Redis）

> **設計文件**：`brains/knowledge/03_system_architecture_designs/MULTI_CHANNEL_DISPATCH_ARCHITECTURE.md`  
> **目標**：讓 Joe 人在外面時，可以透過 Telegram / Hermes 發任務給 Agent，全程閉環不需要回桌面

### bessie202 VPS 補齊

- [ ] **bessie202** 安裝 Redis（`apt install redis-server`）
- [ ] **bessie202** 同步 `hq_task_flow.sh` 到 `/www/wwwroot/HQ/scripts/`
- [ ] **bessie202** 同步 `agent_report_to_hq_v2.sh` 到 `/www/wwwroot/HQ/scripts/`
- [ ] **bessie202** 建立 SSH 憑證連到 yd174（Sophie/Ina 所在伺服器）
- [ ] **bessie202** `hq_gateway.py` 改接 VPS Redis，補環境變數，設為 systemd 常駐

### hq_task_flow.sh 修改

- [ ] 加入 `--source` 參數（`hermes` / `kiro` / `codex`，預設 `kiro`）
- [ ] payload 帶入 `source` 欄位
- [ ] `init_context_store` 寫入 `hq:thread:<id>:source`

### hq_gateway.py 修改

- [ ] DecisionEngine 收到回報時讀取 `source`
- [ ] `source=hermes` → Telegram Bot 通知，Hermes session 可繼續
- [ ] `source=kiro/codex` → 寫 inbox + Telegram 通知（不啟動 session）

### 各 Agent 伺服器

- [ ] **yd174**（Sophie / Ina）裝 Codex CLI，設定連 tg25-gateway
- [ ] **yd174** `agent_report_to_hq_v2.sh` 改 `redis-cli -h bessie202_ip PUBLISH`
- [ ] **yd47**（Mina / Hubie）同上
- [ ] **yd16**（Allie）同上

### 驗收

- [ ] 端對端測試：Telegram 說「叫 Sophie 查一下 Redis 版本」→ Telegram 收到結果
- [ ] 確認 Hermes session 收到回報後可繼續派工

---

## 🟢 第一階段：當前最優先 - 矛盾修復過渡割接 (對應 `PHASED_ROLLOUT_PLAN_20260528.md`)

### 1. 【階段 1: DB 結構與欄位補底】
- [x] **Sophie (Owner)**：已透過 HQ Message Hub 向 Ina 提交 devices 新欄位 Schema 變更請求。
- [ ] **Ina (Infra)**：審核 Sophie 的請求，於 `tg25-infra` 編寫 Migration 並於生產環境執行該 devices 表變更。 (⏳ 任務已派發)
- [ ] **Ina (Infra)**：將 SQL 查詢的 `pulse_ratio` 變更為 `pulse_to_token`。 (⏳ 任務已派發)

### 2. 【階段 2: 權限與 API 雙向相容】
- [x] **Mina (Member)**：後端 `kiosk_token` 與舊 `token` 雙向相容 (API & 登入會話隔離)。
- [x] **Sophie (Owner)**：修改中間件，將 `sub_agent` 角色納入放行名單中。
- [x] **Ina (Infra)**：`listener.py` 補上 `MEMBER_BILL_API_URL` 環境變數加載。

### 3. 【階段 3: 核心業務邏輯割接】
- [ ] **Ina (Infra)**：調整 FastAPI 路由順序（防 `/by-node` 被截斷），並將 Listener LWT 更新為唯讀化。 (⏳ 任務已派發，待 VPS 部署)
- [x] **Allie (Alliance)**：修改 `bindDevice()` 邏輯，使之支持最新 `draft/completed` 狀態。
- [x] **Coli (Firmware)**：模擬脈衝可行性分析與 `simulate_pulse` 韌體實作 (v1.0.26 已發布至 OTA)。

### 4. 【階段 4: 前端對齊與終端驗收】
- [ ] **Hubie (iHub)**：平板端參數更名為 `kiosk_token`，配合 API 聯調。 (⏳ 任務已派發)
- [x] **Mina (Member)**：前端 `welcome.blade.php` 儲存更新為 `kiosk_token`。

---

## 🟡 第二階段：銜接過渡 - WAW 2.0 雙庫新表 Migration 設計審查 (Design First)

*所有 Migration 設計必須提交至 HQ 審核，通過後才可在生產環境執行！*

- [ ] **Ina (Infra)**：於 `tg25-infra` 設計 `waw_infra` 庫的 4 張新表建表 Migration：
  - `stores` (場地/店面)
  - `machines` (機器)
  - `machine_deployments` (部署歷史軌跡)
  - `machine_transactions` (固化分潤交易流水)
- [ ] **Sophie (Owner)**：於 `wawOwner` 設計 `waw_core` 庫的新表與變更 Migration：
  - `profit_sharing_agreements` (分潤協議)
  - `users.outstanding_amount` (新增累計欠費欄位，儲存金額整數)
- [ ] **HQ Center**：確認舊 `devices` 表數據遷移至 `machines` 的 Migration 無損路徑，審核欄位對齊後派發執行工單。

---

## 🔴 第三階段：WAW 2.0 服務割接與軟性欠費功能開發

### 1. [waw-infra / waw-iot] 物理採集服務重構
- [ ] 實作 MQTT 接收狀態更新至 Redis 快取，若機器欠費，狀態標記為 `arrears`。
- [ ] **軟性欠費放行**：即便狀態為 `arrears`，MQTT 與掃碼開分依然照常放行，不顯示警告，確保營業不中斷。
- [ ] **交易分潤固化**：消費事件觸發時，即時查詢 `waw-business` 的分潤比例，計算兩方分成金額後寫入 `machine_transactions`。

### 2. [waw-cloud / waw-business] 人與訂閱服務開發
- [ ] **自動欠款累計**：實作 Daily Cron Job，定時檢查 `arrears` 機台，按天折算月租累加至 `users.outstanding_amount`。
- [ ] **欠費扣款機制**：商戶進行儲值、續費或出金提現時，系統自動強制扣除 `outstanding_amount`。
- [ ] **後台管理限制**：當商戶為 `arrears` 狀態時，限制其提現、交班結算及高級報表，頂部常駐警告。
- [ ] **高頻催收**：啟用 `Notification Domain` 通過 LINE Notify 進行每日欠費催收通知。
- [ ] **Nginx 反向代理分流**：設定 Nginx 路由代理，將 `/api/iot/*` 轉發至 Port 8002，其餘轉發至 Port 8001。

### 3. [waw-wallet] 玩家端與 [iHub] 平板端對接
- [ ] 驗證在 `arrears` 狀態下，掃碼與設備連線完全正常，玩家端無任何欠費警告提示。

---

## ⚠️ 鐵律與控管红線
1. ❌ **嚴禁私自變更設計**：未經 HQ 審核批准，嚴禁私自建表、亂加欄位、修改 API 端口或變更通訊協定命名。
2. ❌ **禁止暴力停機**：不得引入中斷硬體通訊或掃碼開分的攔截代碼，必須嚴格執行「軟性欠費運行」機制。
3. ⚠️ **有困難立即回報**：執行過程中若有技術困難，禁止私自設法妥協修改，必須立即回報 HQ 重新評估。
