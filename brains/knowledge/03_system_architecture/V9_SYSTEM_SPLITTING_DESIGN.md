# V9 系統拆分與數據庫解耦遷移設計書 (V9 System Splitting & DB Decoupling Migration Design)

> **文件版本**：v2.0.0 (人與物分離架構)  
> **建立日期**：2026-06-05  
> **狀態**：Active / Authoritative  
> **編寫角色**：HQ (Hera)

本設計書詳述如何將原有的 V9 單體系統，以「人（業務金流）與物（高頻採集）」為核心維度，物理拆分為兩個子專案，並透過「前端統一、後端分流」與「事件聯動」機制實作系統完全解耦。

---

## 一、 核心拆分理念：人與物分離

為了應對系統高頻寫入與強事務安全性的混合負載，我們將系統依網域邊界拆分為兩個子專案：

### 1. waw-business (人與金流服務)
* **定位**：低頻率、高安全性、強事務。
* **核心邊界**：
  - 用戶帳戶、管理角色與權限。
  - 機台月租訂閱管理與計費（續費、逾期）。
  - 商家分潤協議 (`profit_sharing_agreements`) 管理。
  - 出金、對帳單與財務報表。
* **資料庫 (`waw_core`)**：`users`、`owner_subscriptions`、`profit_sharing_agreements` 等。

### 2. waw-iot (物與部署服務)
* **定位**：高頻率、低延遲、高併發。
* **核心邊界**：
  - 機台資產 (`machines`) 與場地分類 (`stores`)。
  - 機台在線部署動態歷史軌跡 (`machine_deployments`)。
  - 交易流水記錄與分潤即時固化。
  - MQTT 採集心跳、離線 LWT 檢測、脈衝開分中繼。
* **資料庫 (`waw_infra`)**：`machines`、`stores`、`machine_deployments`、`machine_transactions` (固化分潤交易)、`telemetry_logs`。

---

## 二、 系統架構：前端統一，後端分流

為了不增加使用者與開發者的複雜度，用戶仍訪問同一個站點 `https://iot.tg25.win`，由 Nginx 在後端進行請求分流。

```
                     用戶瀏覽器 (iot.tg25.win)
                               │
                               ▼
                       ┌──────────────┐
                       │ Nginx 伺服器  │
                       └──────┬───────┘
                              │
           ┌──────────────────┴──────────────────┐
    (畫面與金流 API)                     (高頻硬體/採集 API)
    /admin/* 或 /api/business/*           /api/iot/*
           │                                    │
           ▼                                    ▼
  ┌─────────────────┐                  ┌─────────────────┐
  │  waw-business   │                  │     waw-iot     │
  │  (人與訂閱服務)  │                  │  (物與採集服務)  │
  │  [資料庫: core]  │                  │  [資料庫: infra] │
  └─────────────────┘                  └─────────────────┘
```

### Nginx 路由分流規則 (Example Config)
```nginx
server {
    listen 443 ssl;
    server_name iot.tg25.win;

    # 1. 靜態畫面與常規後台業務（人、訂閱、分成）
    location / {
        proxy_pass http://127.0.0.1:8001; # waw-business 監聽埠
        proxy_set_header Host $host;
    }

    # 2. 高頻物聯網與開分採集 API
    location /api/iot/ {
        proxy_pass http://127.0.0.1:8002; # waw-iot 監聽埠
        proxy_set_header Host $host;
    }
}
```

---

## 三、 事件型態與跨專案聯動機制 (Events & Synchronization)

當系統拆分後，「人」與「物」之間透過事件進行即時數據同步，包含以下核心事件：

### 1. 通訊與物理事件 (waw-iot -> waw-business)
當設備狀態或計數改變時，由 `waw-iot` 主動調用 API 或派發 Webhook 通知 `waw-business`：
* **`EVT_ONLINE` / `EVT_OFFLINE` (在線與 LWT 離線事件)**：
  - 當 MQTT 監聽器收到 LWT 遺言或連線包時觸發。
  - **行為**：`waw-iot` 更新 Redis 狀態，並異步調用 `waw-business` 的 API，使營運商網頁能即時在前端地圖與卡片上顯示機台最新狀態。
* **`EVT_PULSE_DETECTED` (物理脈衝投幣事件)**：
  - 投幣脈衝由硬體上報至 `waw-iot`。
  - **行為**：`waw-iot` 即時查詢 `waw-business` 取得該機台的分潤協議比例，計算並固化兩方分成金額後，寫入 `machine_transactions` 流水表。

### 2. 業務與控制事件 (waw-business -> waw-iot)
當用戶變更商務狀態時，由 `waw-business` 主動通知 `waw-iot` 以便執行攔截：
* **`EVT_SUBSCRIPTION_EXPIRED` (訂閱過期事件)**：
  - 當營運商未準時繳交月租時，由 `waw-business` 觸發。
  - **軟性聯動**：`waw-iot` 收到後，將該機台狀態更新為 `arrears` (欠費運行) 並同步至 Redis。**機器通訊與玩家掃碼開分依然保持正常放行**，但 `waw-business` 後台會限制該商戶的提現、結帳與報表功能，系統每日折算租金累加至欠款總額，並發送 LINE Notify 催付通知。
* **`EVT_DEPLOYMENT_CHANGED` (部署遷移事件)**：
  - 當機台被指派搬移至新場地時，由 `waw-business` 觸發。
  - **行為**：`waw-iot` 接收並在 `machine_deployments` 表中新增一筆 `active` 部署記錄，舊部署標記為 `inactive`，實現軌跡追溯。

### 3. 即時通訊事件 (WebSocket 事件)
* **`SessionTerminated` (會話強終事件)**：
  - 當玩家金流結束、時間到期或管理員手動在後台切斷時觸發。
  - **行為**：`waw-business` 調用 `waw-iot` 的廣播 API，`waw-iot` 通過 WebSocket (Laravel Reverb) 即時向玩家手機前端推送強終信號，清除 localStorage 狀態並跳轉。

---

## 🔗 文件神經連結

### 強關聯（必讀）
> 修改本重構設計前，必須先閱讀以下文件

- `brains/knowledge/03_system_architecture/WAW_2.0_ARCHITECTURE_SPEC.md` - WAW 2.0 核心資料表解耦規格書
- `brains/knowledge/01_agent_governance/DB_MIGRATION_WORKFLOW.md` - 資料庫變更與部署審批規範

### 中關聯（建議讀）
> 了解系統目前的業務流程，建議閱讀

- `brains/knowledge/05_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md` - 遊戲機 Session 生命週期
- `brains/knowledge/05_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` - 兌幣機現有通訊流程

### 弱關聯（參考）
> 提供部署參考背景

- `brains/knowledge/04_deployment_operations/INFRASTRUCTURE_REFERENCE.md` - 基礎設施主機別名與數據庫配置

### 排除混淆
> 容易混淆但無關的文件

- `brains/knowledge/05_business_flows/kiosk_v0_exchange/KIOSK_UX_AND_SCREEN_DESIGN.md` - 前端 Kiosk UI 設計，與後端系統架構無關
