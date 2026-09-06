# WAW 2.0 系統架構規格說明書 (WAW 2.0 Architecture Specification)

> **文件版本**：v2.0.0  
> **建立日期**：2026-06-05  
> **狀態**：Active / Authoritative  
> **編寫角色**：HQ (Hera)

本文件詳細規範 WAW 2.0 事件平台中「用戶-場地-機台」的解耦設計、資料庫結構、以及「流浪機/流浪店」的商業訂閱控制邏輯，作為 `waw-infra` 與 `waw-cloud` 開發之唯一依據。

---

## 一、 核心領域與實體拆分

系統核心資料庫將徹底廢除「機器與場地強綁定」的傳統設計，改為以「部署關係表」與「訂閱協議表」為核心的解耦結構：

```
[User (Store Owner)] ───擁有───> [Store (場地/店面)] 
                                      │
                                  部署歷史 (machine_deployments)
                                      │
[User (Machine Owner)] ──擁有───> [Machine (機器)]
                                      │
                                  分潤協議 (profit_sharing_agreements)
```

1. **場地 (Store)**：
   * 允許店鋪擁有者免費註冊。
   * 用於邏輯分組與設備在線地理定位。
   * 訂閱狀態（月租 1500）僅影響該店的營運工具功能（交班、LINE警報、營業看板）。
2. **機器 (Machine)**：
   * 指實體 ESP32 採集卡對應的硬體資產。
   * 必須歸屬於某個機台主。
   * 訂閱狀態（月租 300）是機器的計費基準。若無有效訂閱且被歸類為欠費狀態，系統將實施「軟性限制」：機器依然放行 MQTT 連線與掃碼開分，但會將月租按天折算累加至欠款總額中。若全新機器未與任何機台主綁定，則視為「流浪機」，由系統暫行託管。
3. **部署 (Deployment)**：
   * 機器與場地之間為「動態多對多關聯」。
   * 一台機器在同一時間只能部署於一家店。歷史部署記錄需完整保留，供財務報表追溯。

---

## 二、 資料表結構設計 (Database Schema)

### 1. `stores` (場地/店面表)
| 欄位名 | 類型 | 說明 |
| :--- | :--- | :--- |
| `id` | bigint (PK) | 主鍵 |
| `store_owner_id` | bigint (FK) | 關聯 `users.id`，場地所有人 |
| `name` | varchar | 店鋪名稱 |
| `address` | varchar | 物理地址 |
| `subscription_status` | enum | `active` (已訂閱), `expired` (已過期) |
| `subscription_expires_at`| datetime | 訂閱到期日 |
| `created_at` | timestamp | 建立時間 |

### 2. `machines` (機器資產表)
| 欄位名 | 類型 | 說明 |
| :--- | :--- | :--- |
| `id` | bigint (PK) | 主鍵 |
| `machine_owner_id` | bigint (FK) | 關聯 `users.id`，機器所有人。若為 null 則為流浪機 |
| `chip_id` | varchar (Unique)| ESP32 晶片 ID |
| `name` | varchar | 機器名稱 |
| `type` | varchar | 機器類型（彈珠台、娃娃機等） |
| `subscription_status` | enum | `active` (已授權), `expired` (未授權) |
| `subscription_expires_at`| datetime | 授權到期日 |
| `created_at` | timestamp | 建立時間 |

### 3. `machine_deployments` (機台部署歷史表)
本表用於記錄機器在各個店家之間的搬移歷史。
| 欄位名 | 類型 | 說明 |
| :--- | :--- | :--- |
| `id` | bigint (PK) | 主鍵 |
| `machine_id` | bigint (FK) | 關聯 `machines.id` |
| `store_id` | bigint (FK) | 關聯 `stores.id`，部署目標場地 |
| `status` | enum | `active` (當前部署), `inactive` (已撤除) |
| `deployed_at` | datetime | 部署/搬入時間 |
| `removed_at` | datetime | 撤機/搬出時間 |

> **約束條件**：
> * 對於任何給定的 `machine_id`，在同一時間點只能有一筆記錄的 `status` 為 `active`。

### 4. `profit_sharing_agreements` (分潤協議表)
| 欄位名 | 類型 | 說明 |
| :--- | :--- | :--- |
| `id` | bigint (PK) | 主鍵 |
| `machine_id` | bigint (FK) | 關聯 `machines.id` |
| `store_id` | bigint (FK) | 關聯 `stores.id` |
| `store_owner_share` | decimal (5,2) | 店主分成比例 (例如 0.40 代表 40%) |
| `machine_owner_share` | decimal (5,2) | 機台主分成比例 (例如 0.60 代表 60%) |
| `effective_from` | datetime | 協議生效起算時間 |
| `effective_to` | datetime | 協議失效時間 |

### 5. `machine_transactions` (交易流水表 - 帶分拆帳)
每當產生投幣、消費或掃碼開分事件時，除了記錄總額，必須**動態計算並固化**當下的分成金額與對象，避免後續修改分成比例或搬移機台時導致歷史帳目錯亂。
| 欄位名 | 類型 | 說明 |
| :--- | :--- | :--- |
| `id` | bigint (PK) | 主鍵 |
| `machine_id` | bigint (FK) | 關聯 `machines.id` |
| `store_id` | bigint (FK) | 關聯 `stores.id` (記錄交易發生時的部署場地) |
| `transaction_type` | varchar | 交易類型 (如 `scan_play`, `coin_insert`, `cash_exchange`) |
| `total_amount` | decimal (10,2)| 總交易金額 |
| `store_owner_id` | bigint (FK) | 當時的場地所有人 |
| `machine_owner_id` | bigint (FK) | 當時的機器所有人 |
| `store_owner_share_amount`| decimal (10,2)| 店面分成實得金額 |
| `machine_owner_share_amount`| decimal (10,2)| 機台主分成實得金額 |
| `system_cut_amount` | decimal (10,2)| 平台抽成額（如有） |
| `created_at` | timestamp | 交易時間 |

---

## 三、 金流分潤與對帳業務規則

1. **交易發生時的分成固化邏輯**：
   * 當 `waw-infra` 收到消費事件後，必須：
     1. 查出 `machines` 對應的 `machine_owner_id`。若機器欠費，交易依然放行不中止，照常開分，但分成記錄照常寫入。
     2. 查出當前 `status = active` 的 `machine_deployments`，獲取其 `store_id` 及對應的 `store_owner_id`。
     3. 查出對應的 `profit_sharing_agreements` 分成比例。若無協議，則預設比例為：機台主 100%，店鋪 0%。
     4. 計算分成金額，將各方 ID 與金額直接寫入 `machine_transactions` 表中。
2. **流浪機與流浪店的對帳單處理**：
   * 若交易發生時，機台未與任何機台主綁定（流浪機），則該筆金額的 `store_owner_share_amount` 或 `machine_owner_share_amount` 依然會計算，但對應的 `machine_owner_id` 將標記為空並將分成款寫入特定的「託管暫存帳戶 (Escrow Account)」，直至該實體被重新訂閱或綁定認領為止。

---

## 四、 寬限期、欠費累計與軟性限制機制 (Soft Arrears & Alert Mechanism)

為了保障現場店家的正常營收、避免因忘記繳費或結算延遲導致營業中斷，系統禁止採取「直接中斷硬體通訊或掃碼開分」的暴力停機手段。系統採用「持續服務、累計欠款、限制管理功能、高頻催收」的軟性控制機制。

### 1. 訂閱狀態定義 (Subscription States)
* `active` (正常)：已繳費，所有功能完全正常。
* `arrears` (欠費運行)：訂閱已過期，但為保障營運，機器照常通訊、玩家照常掃碼開分。此狀態下系統開始累計欠款。
* `suspended` (完全中止)：僅在惡意欠費超過特定天數（如 30 天）且經人工審核後，才由後台手動切換至此狀態，切斷通訊。

### 2. 欠費運行時的軟性限制規則

#### A. 機器通訊與開分不中斷 (Non-disruptive Operations)
* **MQTT 通訊**：即使狀態為 `arrears`，MQTT Listener 依然放行連線，正常接收 `device/{chip_id}/event` 原始數據，確保營收數據不丟失。
* **玩家掃碼開分**：API 照常放行付款與開分，不向玩家展示任何欠費警告，保障用戶體驗。

#### B. 後台管理功能限制 (Management Limitations)
當商戶處於 `arrears` 狀態時，`waw-business` 後台會實施以下限制：
* **限制結帳與提現**：暫停該店家的「交班結算」與「餘額提現」功能。所有收到的營業額將暫時保留在平台託管賬戶，直至清償欠款。
* **限制看板與報表**：隱藏高級營業報表與營業看板，僅顯示基本列表。
* **頂部常駐警報**：商家登入後台時，頂部常駐紅色閃爍警告：「您的服務已欠費，部分管理功能已被限制，請儘速繳費以恢復完整功能。」

#### C. 自動欠款累計與扣除 (Arrears Debt Accumulation)
* 系統每天定時任務（Cron Job）檢查處於 `arrears` 的機器與場地，按天折算月租金額，累加寫入 `users.outstanding_amount` (累計欠款)。
* 當商戶進行下一次儲值、月租續費或出金提現時，系統會**強制自動扣除** `outstanding_amount`，清償後狀態自動回歸 `active`。

#### D. 高頻 LINE / 簡訊催付 (Active Notification)
* 當進入 `arrears` 狀態，`Notification Domain` 會啟動每日催付機制，通過 LINE Notify 或簡訊向場地主/機台主發送通知：「您的機台 [XXX] 已進入欠費運行第 N 天，累計欠款 X 元，請儘速續費以避免影響出金。」
---

## 🔗 文件神經連結

### 強關聯（必讀）
> 修改本架構規格前，必須先閱讀以下文件

- `brains/knowledge/03_system_architecture/V9_SYSTEM_SPLITTING_DESIGN.md` - V9 系統拆分與資料庫解耦遷移設計書，了解新舊架構過渡細節。
- `brains/knowledge/01_agent_governance/DB_MIGRATION_WORKFLOW.md` - 資料庫變更與部署審批規範。

### 中關聯（建議讀）
> 了解系統的通訊和標準，建議閱讀

- `brains/knowledge/02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - MQTT 主題唯一真理。
- `brains/knowledge/02_technical_standards/WEBSOCKET_CHANNEL_STANDARD.md` - WebSocket 頻道與事件唯一真理。

### 弱關聯（參考）
> 提供部署參考背景

- `brains/knowledge/04_deployment_operations/INFRASTRUCTURE_REFERENCE.md` - 基礎設施主機別名與數據庫配置。

### 排除混淆
> 容易混淆但無關的文件

- `brains/knowledge/05_business_flows/kiosk_v0_exchange/KIOSK_UX_AND_SCREEN_DESIGN.md` - 前端 Kiosk UI 設計，與後端系統架構無關。
