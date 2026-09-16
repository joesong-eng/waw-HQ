# 系統入口與域名分工

> **版本**: 1.0.0  
> **建立日期**: 2026-07-13  
> **狀態**: Active / Authoritative  
> **維護者**: HQ  
> **讀取策略**: On-Demand  

本文件定義 WAW 系統對外入口、系統入口、使用對象與 Agent 職責邊界。後續討論網站入口、域名、使用者分流、OTA 或 Infra 服務時，以本文件作為穩定分類依據。

---

## 一、給人或現場設備打開的入口

| 入口名稱 | 使用對象 | 網站域名 | 對應系統 | 負責 Agent | 定位 |
|---|---|---|---|---|---|
| 商戶後台 | 店家老闆、寄台老闆、機台主 | `https://iot.tg25.win` | `wawOwner` / `waw-business` | Sophie | 營收、交班、設備、部署、分潤、欠費、報表 |
| 聯盟後台 | 硬體供應商們、代理商、供應商、經銷夥伴 | `https://ali.tg25.win` | `Alliance` | Allie | 通路管理、下線管理、訂單、綁機、代理分潤 |
| 會員入口 | 玩家、會員 | `https://win.tg25.win` | `Member` / `waw-wallet` | Mina | 掃碼、儲值、開分、洗分、錢包餘額 |
| iHub / 紙鈔機終端 | 現場 Android 平板、兌幣機 WebView | `https://ihub.tg25.win` | `iHub` / `waw-exchange-console` | Hubie | 收鈔、出幣、現場狀態、設備操作畫面 |

---

## 二、幕後系統入口

| 入口名稱 | 域名 / 位址 | 使用對象 | 負責 Agent | 定位 |
|---|---|---|---|---|
| Infra API | `https://api.tg25.win` | 各系統、內部 API、部分下載服務 | Ina | IoT API、設備狀態、內部服務、APK 下載 |
| MQTT Broker | `mqtt.tg25.win:8883` | ESP32、iHub、韌體、Infra Listener | Ina | MQTT TLS 通訊、硬體事件上報、遠端指令 |
| 韌體下載 / OTA 檔案 | `https://hware.tg25.win` | 開發者、維護者、韌體 OTA | Fio / Coli / Ina | 韌體 `.bin` 檔案下載來源，OTA 前需確認 HTTP 200 |

---

## 三、不是一般網站入口的服務

以下服務不是給一般使用者登入或瀏覽的入口：

| 服務 | 原因 |
|---|---|
| `api.tg25.win` | 系統 API 與下載服務，不是操作後台 |
| `mqtt.tg25.win` | MQTT Broker，供硬體與服務連線 |
| `hware.tg25.win` | 韌體檔案下載與 OTA 來源，不是商戶或會員網站 |

---

## 四、角色分工口訣

**老闆看生意，硬體供應商管通路，會員玩遊戲，iHub 做現場兌幣，Infra 撐住資料庫、MQTT 與 API，韌體入口負責 OTA 檔案。**

---

## 五、治理規則

1. 新增或調整域名時，必須同步更新本文件。
2. 新增網站入口時，必須明確定義「使用對象、系統、Agent、是否給一般使用者登入」。
3. `api.tg25.win`、`mqtt.tg25.win`、`hware.tg25.win` 不應被描述為一般使用者網站。
4. OTA 控制 API 可掛在 `iot.tg25.win/api/v9/ota/...`，但韌體檔案下載來源以 `hware.tg25.win` 為準。

---

## 🔗 文件神經連結

### 強關聯

- `04_deployment_operations/INFRASTRUCTURE_REFERENCE.md` - 主機、域名、Nginx 與部署位置參考。
- `03_system_architecture/WAW_2.0_ARCHITECTURE_SPEC.md` - WAW 2.0 核心架構規格。
- `03_system_architecture/V9_SYSTEM_SPLITTING_DESIGN.md` - 人與物分離、單一入口後端分流設計。

### 中關聯

- `01_agent_governance/AGENT_RESPONSIBILITY_BOUNDARIES.md` - Agent 專案職責邊界。
- `02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - 域名、服務、Payload 與 Topic 命名標準。
- `04_deployment_operations/IHUB_APK_BUILD_TOOL.md` - iHub APK 與下載服務參考。

### 弱關聯

- `docs/fio/overview.md` - IOTkiosk_v0 韌體職責概覽。
- `docs/hubie/overview.md` - iHub Android APK 職責概覽。
