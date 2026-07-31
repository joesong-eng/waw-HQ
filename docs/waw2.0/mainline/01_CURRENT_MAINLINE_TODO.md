# 📢 HQ TODO (WAW 2.0 大修與矛盾修復待辦清單)

> **最後更新**：2026-06-15 00:45 (UTC+8)  
> **當前階段**：階段二已完成 ──> 階段三待啟動  
> **注意**：大修涉及核心資料庫與 API，所有 Agent 必須嚴格按階段順序執行，嚴禁私自變更設計或亂加欄位。

---

## ✅ 第一階段：矛盾修復過渡割接 — COMPLETED 2026-06-10

### 完成摘要
- ✅ devices 表補欄位 Migration (Ina commit 007b829)
- ✅ pulse_ratio → pulse_to_token (listener.py:212)
- ✅ FastAPI 路由調整 + LWT 唯讀化
- ✅ Mina kiosk_token 雙向相容
- ✅ Allie bindDevice() 狀態機修正
- ✅ Coli simulate_pulse v1.0.26
- ✅ Hubie QR URL kiosk_token
- ✅ E2E 鏈路驗收（revenue_facts 2,653 筆）

---

## ✅ 第二階段：雙資料庫新表設計與 API 實作 — COMPLETED 2026-06-15

### 完成摘要

#### 設計階段（2026-06-10）
- ✅ **Ina (Infra)**：提交 `WAW2_INFRA_DB_DESIGN_INA_v3.md` (27.6KB)
- ✅ **Sophie (Owner)**：提交 `WAW2_CORE_DB_DESIGN_SOPHIE_v2.md` (37.8KB)

#### Migration 階段（2026-06-14）
- ✅ `profit_sharing_proposals.effective_until` 欄位新增
- ✅ `users.outstanding_amount` 欄位新增
- ✅ `profit_sharing_agreements` 表已建立

#### API 開發階段（2026-06-14）
- ✅ **Sophie**: PHP Laravel API（6 檔案，1301 行）
  - ProfitSharingService.php (465 行)
  - ProfitSharingAgreementService.php (298 行)
  - ProfitSharingController.php
  - ProfitSharingAgreementController.php
  - Models + Routes
- ✅ **Ina**: Python FastAPI（588 行）
  - routers/profit_sharing.py (212 行)
  - models/schemas.py (新增 4 個 models)
  - services/database.py (204 行)
  - daily_arrears_accumulation.py (Cron Job)

#### 部署階段（2026-06-15）
- ✅ **Sophie PHP API** (Commit ddfa188)
  - 16 條 API 路由已生效
  - 部署到 yd174: /www/wwwroot/iot.tg25.win
  - Laravel 快取已重建
  - curl 測試通過

- ✅ **Ina Python API** (Commit 9fe49be)
  - Router 已載入到 credit-api
  - 部署到 yd174: 141.148.165.50
  - 服務已重啟（PID: 3273869）
  - curl 測試通過

- ✅ **Ina Cron Job**
  - daily_arrears_accumulation.py 已部署
  - crontab 設定完成（每日 02:00）
  - Dry-run 測試通過

---

## 🟡 第三階段：服務割接與軟性欠費功能開發 — PLANNING

*規劃完成（2026-06-15 01:06），等待執行決策*

### 1. [waw-infra / waw-iot] 物理採集服務重構
- [ ] 實作 MQTT 接收狀態更新至 Redis 快取，若機器欠費，狀態標記為 `arrears`
- [ ] **軟性欠費放行**：即便狀態為 `arrears`，MQTT 與掃碼開分依然照常放行，不顯示警告
- [ ] **交易分潤固化**：消費事件觸發時，即時查詢分潤比例，寫入 `machine_transactions`

### 2. [waw-cloud / waw-business] 人與訂閱服務開發
- [x] **自動欠款累計**：Daily Cron Job 已部署（✅ 2026-06-15）
- [ ] **欠費扣款機制**：商戶儲值/續費/出金時，自動強制扣除 `outstanding_amount`
- [ ] **後台管理限制**：`arrears` 狀態時限制提現、交班、高級報表
- [ ] **高頻催收**：啟用 LINE Notify 每日欠費催收通知
- [ ] **Nginx 反向代理分流**：`/api/iot/*` → Port 8002，其他 → Port 8001

### 3. [waw-wallet] 玩家端與 [iHub] 平板端對接
- [ ] 驗證在 `arrears` 狀態下，掃碼與設備連線完全正常，玩家端無欠費警告

---

## 📋 待處理事項（技術債）

### 高優先
1. **DB_MANIFEST.md 需要更新**
   - 問題：記錄 `devices.outstanding_amount` 存在，但實際不存在
   - 實際：欠款欄位在 `users` 表
   - 發現者：Ina (2026-06-15)
   - 影響：可能導致未來任務誤判

2. **API 職責劃分文件**
   - 需明確 PHP (Sophie) 與 Python (Ina) API 的職責範圍
   - 建議：PHP 負責後台管理，Python 負責即時計算

### 中優先
3. **備份檔案清理**
   - `ProfitSharingService.php.backup` 已提交到 Git
   - 需確認不需要後可移除

4. **設計文件狀態更新**
   - 兩份設計文件仍為 "Draft - Pending HQ Review"
   - 但 Migration 已執行，需補充審核記錄或更新狀態

### 低優先
5. **知識庫補充**
   - 撰寫 `WAW2_PROFIT_SHARING_API_SPEC.md`
   - 撰寫 `WAW2_ARREARS_MECHANISM.md`
   - 撰寫 `WAW2_DEPLOYMENT_GUIDE.md`

---

## ⚠️ 鐵律與控管红線

1. ❌ **嚴禁私自變更設計**：未經 HQ 審核批准，嚴禁私自建表、亂加欄位、修改 API 端口或變更通訊協定命名。
2. ❌ **禁止暴力停機**：不得引入中斷硬體通訊或掃碼開分的攔截代碼，必須嚴格執行「軟性欠費運行」機制。
3. ⚠️ **有困難立即回報**：執行過程中若有技術困難，禁止私自設法妥協修改，必須立即回報 HQ 重新評估。

---

## 📂 重要文件位置

### 進度報告
- `waw2.0_mainline_docs/03_PROGRESS_SUMMARY_20260615.md` — 階段二完成報告
- `waw2.0_mainline_docs/00_CURRENT_START_HERE__JOE_READ_ME_FIRST.md` — 啟動備忘卡

### 設計文件
- `waw2.0_specs/WAW2_CORE_DB_DESIGN_SOPHIE_v2.md` (37.8KB)
- `waw2.0_specs/WAW2_INFRA_DB_DESIGN_INA_v3.md` (27.6KB)

### 架構規範
- `waw2.0_specs/WAW_2.0_ARCHITECTURE_SPEC.md` — 完整架構規範
- `brains/knowledge/` — 知識庫

