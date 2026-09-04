# WAW 待辦事項總表 (Master TODO)

> 維護者：HQ
> 最後更新：2026-08-31
> 說明：此文件記錄跨專案的中長期待辦，避免遺忘。各 Agent 的即時任務走 .taskflow 系統。

---

## 🔴 SignalHub 核心流程（當前進行中）

- [ ] **[Sidney]** SignalHub 獨立站點建置（signal.tg25.win / play.tg25.win）
- [x] **[Sidney]** 完成 Owner 後台「信號設定」選單入口整合
- [x] **[Ina]** 生產資料庫 iotv9 執行 SignalHub Migration（5張表建立完成）
- [ ] **[Sidney]** 跑通第一個完整樣板：店主建設定檔 → 腳位映射 → 統計規則 → 看到數據
- [ ] **[Coli + Sidney]** ESP32 信號 → MQTT → signal_events 流水寫入端對端測試
- [ ] **[Sidney]** Webhook 推送端對端測試（模擬第三方接收）

---

## 🟡 開放標準（規劃中，流程完成後進行）

- [ ] **[Sidney]** 對外開發者文件（WAW IoT Signal Standard 接入手冊）
  - ESP32 韌體規格（MQTT Topic、Payload 格式、QoS 標準）
  - API 接入規格（OpenAPI 3.0 格式）
  - Webhook 簽名驗簽範例（多語言：Python / Node / PHP）
- [ ] **[HQ]** 授權/計費機制設計（按設備數收月租 or 按信號量計費）
- [ ] **[Sidney]** API Key 管理介面（第三方申請 API Key、查看用量、計費）
- [ ] **[Coli]** ESP32 韌體開源版本（移除 WAW 業務邏輯，保留 WAW MQTT 標準）

---

## 🟡 商業設計（規劃中）

- [ ] **[HQ]** 定價模型決策
  - 採集卡硬體售價（一次性）
  - 雲端接入月租（按設備數）
  - API 進階用量計費（按呼叫次數 or 信號量）
  - 後台管理功能訂閱（企業版）
- [ ] **[HQ]** 第三方平台商授權協議草稿
- [ ] **[HQ]** 開源策略文件（MIT / Apache 2.0 / 商業雙授權）

---

## 🔵 AI 動態頁面（未來版本，當前流程完成後）

> **概念**：在站點駐入 AI，與用戶對話，動態提供所需的呈現頁面。
> 頁面可以是現有頁面，也可以根據用戶當下需求即時生成。
> 先把所有功能流程做完，再來做這個部分。

- [ ] **[Sidney / HQ]** AI 駐點站點架構設計
  - 對話入口整合（浮動 AI 助理按鈕）
  - 意圖識別 → 路由到現有頁面 or 即時生成
  - 即時生成頁面的安全沙箱機制
- [ ] **[Sidney]** 現有頁面的 AI 可描述化（每頁加 meta 說明供 AI 索引）
- [ ] **[HQ]** AI 動態生成頁面的數據權限邊界設計

---

## 🟢 已完成

- [x] **[HQ]** 四層架構概念設計（WAW標準局 / 平台商 / 店主 / 玩家）
- [x] **[HQ]** SignalHub 資料庫 Schema 設計（5張表）
- [x] **[HQ]** SignalHub 後台 UI 規格文件
- [x] **[Sophie]** Owner 後台 Migration 檔案建立
- [x] **[Sophie]** 5個 Model 建立（SignalProfile/PinMapping/StatRule/Webhook/Event）
- [x] **[Sophie]** SignalHubController 建立（18個 API 端點）
- [x] **[Sophie]** 4個 Blade View 建立（profiles/pins/stats/webhooks）
- [x] **[Sophie]** API 路由 + Web 路由掛載
- [x] **[HQ]** signal.tg25.win DNS CNAME 指向 play.tg25.win → 129.153.116.174
