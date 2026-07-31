# 知識庫文件索引 (Neural & Hierarchical Index)

> **最後更新**：2026-06-08  
> **編寫角色**：HQ (Hera)  
> **索引原則**：大分類在最外圍，檔名自解釋，拒絕流浪與信息碎片化。

---

## 🔴 最高指導規範 (MANDATORY STANDARDS)

在進行任何代碼修改前，所有 Agent 必須先閱讀對應領域的最高指導文件：

| 規範文件 | 規範內容 | 適用範圍 | 違反後果 |
| :--- | :--- | :--- | :--- |
| `02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` 🔴 | 變數命名、API Header、MQTT Topic 與 Payload 唯一真理 | 所有系統 | 變數或主題不一致，造成系統通訊與金流中斷 |
| `02_protocols_and_standards/WEBSOCKET_CHANNEL_STANDARD.md` 🔴 | WebSocket 頻道與事件類型標準 | Member / iHub | 前端無法收到即時事件，用戶體驗中斷 |
| `02_protocols_and_standards/QRCODE_FORMAT_STANDARD.md` | QR Code URL 格式與參數名稱 | iHub / Alliance / Member | 用戶無法掃碼，服務完全中斷 |
| `NAMING_AUTHORITY.md` 🔴 | 全系統名稱定義來源唯一真理索引 | 所有系統 | 識別碼混用，資料關聯錯誤 |

---

## 📂 頂級分類結構 (Top-Level Directories)

### 01_agent_governance_rules/ (Agent 治理規章)
定義 AI Agent 的執行協議、職責保護、軍令與文檔防流浪機制：
- `README.md` (已完成) — Agent 治理規章導覽與目錄說明。
- `AGENT_EXECUTION_PROTOCOL.md` (已完成) — 禁止試錯、診斷流程、執行前三確認。
- `AGENT_RESPONSIBILITY_BOUNDARIES.md` (已完成) — 職責邊界、禁止跨專案修改。
- `AGENT_COLLABORATION_PROTOCOL.md` (已完成) — HQ Message Hub 用法、知識沉澱規範。
- `TASK_ROUTING_AND_COMPLETION.md` (已完成) — 任務路由與完成驗收標準.
- `INTERACTION_COMMON_SENSE.md` (已完成) — 人機交互與 Agent 溝通通識。
- `CRITICAL_NO_TRIAL_AND_ERROR.md` (已完成) — 核心軍令：禁止試錯式修改程式碼原則。
- `DOCUMENT_CONSISTENCY_RULES.md` (已完成) — 文檔一致性與命名標準規範。
- `FILE_REGISTRATION_SYSTEM.md` (已完成) — 文件註冊與三層保護防流浪機制說明。
- `DB_MIGRATION_WORKFLOW.md` (已完成) — 資料庫變更與部署審批規範。
- `SYSTEM_FIX_PLAN_20260528.md` (已完成) — 全系統五大矛盾修復計劃。
- `PHASED_ROLLOUT_PLAN_20260528.md` (已完成) — 全系統矛盾修復分階段割接計劃。

### 02_protocols_and_standards/ (協定與標準)
全系統底層通訊、硬體 SDK 與 Payload 格式的唯一強制性標準：
- `TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` (已完成) — 變數命名、Port、Header、Topic 與 Payload 標準。
- `WEBSOCKET_CHANNEL_STANDARD.md` (已完成) — WebSocket 頻道與事件唯一真理。
- `QRCODE_FORMAT_STANDARD.md` (已完成) — QR Code 格式唯一真理。
- `ESP32_COMMON_SDK_SPEC.md` (已完成) — ESP32 共用核心 SDK 技術規格與分工標準。
- `HARDWARE_PULSE_MAPPING.md` (待補充) — 脈衝轉換與硬體訊號映射。
- `SIGNAL_FLOW_MONITOR.md` (待補充) — 信號流監控與可視化設計。

### 03_system_architecture_designs/ (系統架構設計)
系統整體解耦、人與物物理拆分及過渡割接方案：
- `WAW_2.0_ARCHITECTURE_SPEC.md` (已完成) — WAW 2.0 事件平台核心架耦規格書。
- `V9_SYSTEM_SPLITTING_DESIGN.md` (已完成) — waw-business 與 waw-iot 雙子專案物理拆分設計書。

### 04_ops_and_deployments/ (運維與部署)
主機配置、SSH 別名、自動化部署與緊急回滾指南：
- `INFRASTRUCTURE_REFERENCE.md` (已完成) — SSH 別名表、DB 架構、Nginx 配置。
- `DEPLOYMENT_GUIDE.md` (已完成) — 各專案部署指令與緊急回滾。
- `V9_OPS_AUTOMATION.md` (已完成) — MCP 工具與自動化運維指令指南。
- `LOCAL_DEV_CUSTOMIZATIONS.md` (已完成) — 本地開發環境客製化設定。
- `HQ_DEPLOYMENT_SOP.md` (已完成) — HQ 部署與自動化維護標準作業程序。
- `MEMBER_DEPLOYMENT_GUIDE.md` (已完成) — 會員端後台系統部署指南。
- `IHUB_APK_BUILD_TOOL.md` (已完成) — iHub APK 自動化建置工具指南。
- [scripts/README.md](file:///Users/ilawusong/Documents/sysWawIot/HQ/scripts/README.md) 🟢 (已更新) — HQ 核心維護腳本與全自動任務分發觸發工具手冊。

### 05_product_and_business_flows/ (產品與業務流)
依業務域分離的產品需求與底層交互流程細則：

#### 1. kiosk_v0_exchange/ (兌幣機業務域)
- `KIOSK_EXCHANGE_FLOW.md` (已完成) — 兌幣機物理與金流交互流程規格書。
- `KIOSK_IDENTIFICATION_SYSTEM.md` (已完成) — 兌幣機識別碼與綁定體系。
- `KIOSK_UX_AND_SCREEN_DESIGN.md` (已完成) — 兌幣機 UI 與三螢幕顯示設計規範。
- `KIOSK_ENGINEERING_DASHBOARD.md` (已完成) — 兌幣機工程測試看板設計。

#### 2. game_v0_arcade/ (遊戲機業務域)
- `GAME_V3_CORE_SPECIFICATION.md` (已完成) — 遊戲機 3.0 系統架構與業務流程規格書。
- `GAME_V0_FLOW_AND_SESSION.md` (已完成) — 遊戲機開分與會話生命週期流程。
- `DEVICE_IDENTIFICATION_SYSTEM.md` (已完成) — 遊戲機設備識別系統。
- `REDEMPTION_VENDING_ARCHITECTURE.md` (已完成) — 彩票/代幣雙軌資產與販賣機控制架構。

---

## 根目錄文件

| 文件 | 說明 | 狀態 |
|------|------|------|
| `DOCUMENT_INDEX.md` | 本文檔：知識庫完整文件索引 | 已啟用 |
| `README.md` | 知識庫總目錄與核心規則說明 | 已啟用 |
| `NAMING_AUTHORITY.md` | 全系統名稱定義來源唯一真理索引 | 已啟用 |
| `NEURAL_LINKS_PROGRESS.md` | 文件神經連結建置進度追蹤 | 已啟用 |

---

## 引用與防孤兒協議
1. **新建文件**：必須先在對應目錄大類註冊，填寫說明，並在文檔末尾附上「## 🔗 文件神經連結」。
2. **修訂文件**：同步檢查強關聯文件，避免信息分叉。

## 🔧 Message Hub v2.0 核心模組

| 檔案 | 說明 | 行數 |
|------|------|------|
| `scripts/message_hub_v2/__main__.py` | 主程式入口 | 146 |
| `scripts/message_hub_v2/config.py` | Agent 路由配置 | ~70 |
| `scripts/message_hub_v2/router.py` | 事件路由引擎 | 97 |
| `scripts/message_hub_v2/task_manager.py` | 任務管理模組 | 188 |
| `scripts/message_hub_v2/http_server.py` | HTTP API 伺服器 | 203 |
| `scripts/message_hub_v2/redis_listener.py` | Redis Pub/Sub 監聽 | 184 |

> ⚠️ **Firmware Agent 分工**：Fio→IOTkiosk_v0 (kiosk/+)，Coli→IOTwawS3 (device/+)

## 🔗 Agent 通訊協定

| 文件 | 說明 | 狀態 |
|------|------|------|
| `01_agent_governance/MESSAGE_HUB_PROTOCOL.md` 🟢 | HQ Message Hub 自動化通訊系統 | ✅ 已啟用 |
| `01_agent_governance/CODEX_EXEC_GUIDE.md` 🟢 | Codex 執行指南與軍令 | ✅ 已啟用 |
| `01_agent_governance/MESSAGE_HUB_V2.md` 🟢 | Message Hub V2 架構與多 Agent 協同標準 | ✅ 已啟用 |
| `01_agent_governance/MESSAGE_HUB_V2_DEPLOYMENT.md` 🟢 | Message Hub V2 部署設定與程序 | ✅ 已啟用 |
| `01_agent_governance/MESSAGE_HUB_V2_STATUS.md` 🟢 | Message Hub V2 當前運行狀態 | ✅ 已啟用 |


## 📢 公用文件（所有 Agent 可見）

| 文件 | 位置 | 說明 |
|------|------|------|
| `SHARED_MESSAGE_HUB_GUIDE.md` 🟢 | `../SHARED_MESSAGE_HUB_GUIDE.md` | HQ Message Hub 使用指南（Agent 版） |
| `scripts/README.md` 🟢 | [scripts/README.md](file:///Users/ilawusong/Documents/sysWawIot/HQ/scripts/README.md) | HQ 核心維護與全自動任務分發觸發工具手冊 |


## ⚠️ 已廢棄的通訊方式

| 文件 | 說明 | 狀態 |
|------|------|------|
| `01_agent_governance/CHAT_BRIDGE_DEPRECATION.md` ❌ | Chat Bridge 廢棄公告 | 已於 2026-06-06 廢棄 |
