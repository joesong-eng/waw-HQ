# sysWawIot 全系統矛盾修復分階段割接計劃 (PHASED_ROLLOUT_PLAN_20260528)
> **設計者**: hHQ (HHQM)  
> **日期**: 2026-05-28  
> **目標**: 確保 5 大 Bug 在不中斷生產環境、不引發集成混亂的前提下，安全、有序地逐步上線。  
> **核心原則**: **向下相容 (Backward Compatibility) 先行、資料庫補底先行、分批部署、每步驗收。**

由於涉及 5 個模組的跨倉變更，若進行「一次性 Big Bang 部署」，極易因 API 欄位不匹配或路由衝突引發連鎖崩潰。特此將執行階段 (EXECUTION) 拆解為**四個安全割接階段**：

---

## 🗺️ 割接四階段路線圖

```
【階段 1: DB 結構補底】 ──> 【階段 2: 權限與 API 相容】 ──> 【階段 3: 核心邏輯割接】 ──> 【階段 4: 前端對齊與驗收】
  • 補齊 Owner 4個欄位         • Member 後端上線 (相容)        • FastAPI 路由順序變更         • iHub 前端參數更名
  • Infra 查詢欄位對齊         • Owner 中間件 sub_agent       • Alliance 狀態機修正          • E2E 模擬器聯調測試
                               • listener.py 環境變數          • listener.py LWT 唯讀化
```

---

## 📋 階段細節與執行步驟

### 🟢 【階段 1】DB 結構補底與欄位對齊 (Database Schema Alignment)
* **目的**：解決 Bug 4。消除資料庫結構與代碼查詢之間的不一致，杜絕高頻 SQL 查詢引發崩潰。
* **步驟**：
  1. **hSophie (wawOwner)**：
     * 在離峰時間（系統維護期）執行安全修復 Migration，使用 `Schema::hasColumn` 補齊 devices 表中因先前 table lock 遺漏的四個欄位：`ticket_mode`、`out_pulse_to_ticket`、`ticket_value`、`direct_prize_cost`。
     * **驗收標準**：手動或經由腳本執行 `DESCRIBE devices;` 確認四欄位均已安全建立。
  2. **hIna (tg25-infra)**：
     * 將 `/api/credit-relay/services/database.py` (Line 323) 的 `SELECT pulse_ratio` 改為 `SELECT pulse_to_token`。
     * **驗收標準**：Infra 啟動，進行設備參數讀取測試，確認不再拋出 SQL Column Not Found 異常。

---

### 🟢 【階段 2】權限開放與 API 雙向相容 (Permission Gates & API Fallbacks)
* **目的**：解決 Bug 1 (前半)、Bug 3 (後半)、Bug 5。確保後端在前端切換參數名之前，已經具備接收新舊兩種格式的能力。
* **步驟**：
  1. **hMina (Member)**：
     * 修改 `Member/routes/web.php` 與後端 `KioskController.php` (Line 188)，使其**同時支持並驗證 `kiosk_token` 與舊的 `token` 參數**（實施雙向相容）。
     * **驗收標準**：Member 後端部署上線，使用 Postman 模擬帶有 `token` 及 `kiosk_token` 的請求，皆能正確解析不報 401/422。
  2. **hSophie (wawOwner)**：
     * 修改 `EnsureIotAccess.php` 中間件，將 `sub_agent` 加入放行陣列。
     * **驗收標準**：以 `sub_agent` 子帳號登入 Owner Portal，確認能成功載入首頁，無 403 報錯。
  3. **hIna (tg25-infra)**：
     * 在 `listener.py` 中補上 `MEMBER_BILL_API_URL` 環境變數加載，並提供預設 Fallback。
     * **驗收標準**：`listener.py` 可順利讀取 env config。

---

### 🟢 【階段 3】核心業務邏輯割接 (Core Routing & Business Logic)
* **目的**：解決 Bug 2、Bug 3 (前半)。調整核心路由優先順序與出廠狀態機限制。
* **步驟**：
  1. **hIna (tg25-infra)**：
     * 調整 `routers/device.py` 路由順序，將 `/by-node/{node_id}`（L255）移到 `/{chip_id}`（L222）之上。
     * 修改 `listener.py` 中 `update_device_status()`，只更新 `last_seen_at`，不再 SET 越權狀態。
     * **驗收標準**：重啟 Infra API，請求 `/api/v1/devices/by-node/KIOSK_TEST`，確認能正確匹配且不被 `/{chip_id}` 攔截。
  2. **hAlie (Alliance)**：
     * 修改 `OrderController.php` L377 的 `bindDevice()` 邏輯，使之支持最新 `draft/completed` 狀態。
     * **驗收標準**：以 `draft` 狀態訂單執行設備綁定 API，確認能成功綁定。

---

### 🟢 【階段 4】前端對齊與終端驗收 (Frontend Unification & Verification)
* **目的**：解決 Bug 1 (後半)。前端開始全量使用新參數名，結束過渡期。
* **步驟**：
  1. **hHubie (iHub)**：
     * 修改 `main.js` L252，將二維碼 URL parameter 改為 `kiosk_token`。
     * **驗收標準**：iHub 重新 build 並部署至 `yd47` 生產環境。
  2. **hMina (Member)**：
     * 更新 `welcome.blade.php`，將內部儲存與讀取變更為 `kiosk_token`，避免 localStorage 污染。
     * **驗收標準**：Member 前端部署上線。
  3. **全系統 E2E 聯調驗收**：
     * 用手機模擬掃描新生成的 iHub 二維碼，確認 URL 為 `https://win.tg25.win/kiosk?kiosk=KIOSK_XXX&kiosk_token=XXX`。
     * 確認跳轉至 Member 系統無 localStorage 污染，且 Line 登入依然保持登入態。
     * 點擊 Kiosk 支付綁定，確認 API 返回 200，設備成功扣款開分。

---

## 🛡️ 安全回滾預案 (Rollback Protocol)
* **若 階段 1 / 階段 2 失敗**：
  由於均為向下相容變更，可直接回滾代碼至上一個 Commit，不影響現行業務運作。
* **若 階段 3 失敗**：
  FastAPI 路由順序若引發未預期 500，可將 `/api/credit-relay/routers/device.py` 即時切換回備份檔，並維持 Alliance 端的舊綁定限制。
* **若 階段 4 失敗**：
  iHub 前端可直接回滾部署 `dist` 目錄。Member 後端因為保留了雙向相容 (Fallback)，因此即使前端未更名完成，系統依然具備完全的自癒能力。
