# WAW 業務邏輯、開洗分與清算對帳核心規格 (CHATGPT_BUSINESS_LOGIC.md)

> **文件身分**：WAW 專案業務與清算邏輯深探文件 (專供 ChatGPT 深度解析)  
> **關聯總索引**：`knowledge/CHATGPT_CONTEXT.md` (實體位置: `brains/knowledge/CHATGPT_CONTEXT.md`)  
> **最後校驗日期**：2026-09-24  
> **維護權限**：HQ (協調中心唯一寫入)  
> **狀態標記準則**：【已實作】/【已驗證】/【已設計但尚未實作】/【計畫中】/【未確認】

---

## 1. 核心金流三大不可違背定律 (Core Financial Tenets)

全系統所有業務邏輯、開洗分與資料庫設計，受以下三大基礎定律約束：

### 1.1 定律一：脈衝即真理 (Pulse is Physical Truth) 【已驗證】
- ESP32 邊緣硬體透過光耦與 PCNT 採集的物理脈衝，是全系統**唯一不可篡改的真理依據**。
- 所有在前端螢幕、手機 App 或後台報表看到的「代幣數」、「點數」、「台幣金額」，本質上都是對「物理脈衝」進行換算後的**投影顯示**。
- **儲存原則**：資料庫必須永久保存原始累計脈衝數 (`raw_value`) 與單次變更量 (`delta_value`)。

### 1.2 定律二：代幣必為整數 (Tokens are Integers) 【已驗證】
- 遊藝場會員錢包內的代幣 (`TOKEN`) 與彩票 (`TICKET`) 只能是整數（例如：持有 50 枚代幣，絕對不允許 50.5 枚）。
- **資料庫欄位強制規範**：所有涉及代幣、彩票的資料表欄位，必須使用 `INT` 或 `BIGINT`。
- **紅線禁令**：❌ 絕對嚴禁使用 `DECIMAL(16,2)` 或浮點數存放代幣餘額！

### 1.3 定律三：比例快照留存 (Snapshot Storage) 【已驗證】
- 換算比例（如 `pulse_to_token`, `token_value_twd`）可能會隨時間或場地促銷活動而調整。
- **審計原則**：每一筆開洗分交易或日結快照，必須在寫入時將「當下生效的換算比例」完整保存至交易快照欄位中。日後即使場地換算比例改變，歷史帳目仍可精確還原，杜絕帳務混亂。

---

## 2. 開洗分業務邏輯矩陣 (Credit In & Credit Out)

如前所述，電腦型聯網機台與傳統單機在開洗分邏輯上存在本質差別：

### 2.1 電腦型聯網機台開洗分 (SignalHub 模式) 【已實作】
- **開分 (Credit In / UI1)**：
  - **觸發源**：實體按鈕短接（服務員現場操作）。
  - **採集卡職責**：上報 `delta_value: 1` 與 `raw_value`，產生唯一 `delivery_id`。
  - **金額決定方**：**100% 由第三方遊戲伺服器決定**。SignalHub 轉發 Webhook 後，第三方伺服器比對現場 POS 收銀記錄，於回覆中填入實際點數 `actual_points: 500`。
  - **結算寫入**：SignalHub 收到回覆後，將 `actual_points` 寫入 `signal_webhook_deliveries.cleared_points`。
- **洗分 (Credit Out / UI2)**：
  - **觸發源**：實體洗分鍵按下。
  - **採集卡職責**：上報 `delta_value: 1`。
  - **結算流向**：第三方遊戲商回傳玩家在機台上的結算剩餘分數（例如 `actual_points: 3250`），吧台依此金額支付現金或發放彩票。

### 2.2 傳統街機手機掃碼開洗分 (game_v0 模式) 【已設計 / 部份驗證】
- **開分 (Member -> ESP32 OUT1)**：
  - 會員手機扣除 1 代幣。
  - 系統依據場地設定 `pulse_to_token = 0.5` 計算出應給予機台 2 個物理脈衝。
  - Infra 發送 MQTT 指令 `assign_credit`，ESP32 驅動繼電器連發 2 下方波。
- **洗分 (Member -> ESP32 OUT2)**：
  - 玩家在手機上點選「結束遊戲並洗分」。
  - 系統發送 MQTT `settle_credit`，ESP32 觸發機台 PIN_OUT2 洗分按鈕。
  - 機台退幣馬達或退幣計數器啟動，每跳動一下在 UI4 採集到一個反饋脈衝。
  - Member 依據反饋脈衝數，以 1:1 或約定比例將彩票 (`TICKET`) 退還至會員錢包。

---

## 3. 貨幣與代幣體系 (Currency Hierarchy)

在 `waw_member_production.member_wallets` 中支援五種貨幣類型：

| 貨幣代碼 | 貨幣名稱 | 數值型態 | 用途與流向 | 換算基準 |
| :--- | :--- | :--- | :--- | :--- |
| **`CASH`** | 法定現金 | DECIMAL(10,2) | 玩家儲值的新台幣餘額 (TWD) | 1.00 TWD |
| **`TOKEN`** | 遊戲代幣 | **INT (整數)** | 專用於機台開分投幣 | 由場地設定 (例: 10元 = 1枚) |
| **`POINT`** | 活動點數 | INT (整數) | 促銷、簽到贈送點數 | 平台行銷用 |
| **`TICKET`** | 遊戲彩票 | **INT (整數)** | 機台洗分退回或出彩之點數 | 可於櫃檯兌換禮品或回存 |
| **`COIN`** | 實體硬幣 (舊) | INT (整數) | 早期相容欄位，現行流程已凍結 | 歷史記錄 |

---

## 4. 營運分潤、拆帳與訂閱模型 (Revenue Sharing & Subscription)

WAW 2.0 徹底廢除了傳統「機台與場地硬編碼綁定」模式，改為動態部署與分成合約：

### 4.1 三方角色與資產權利
1. **場地擁有者 (Venue Owner / 店主)**：
   - 擁有實體店面 (`venues`)。
   - 負責負擔店面租金、水電、現場吧台人員。
2. **機台擁有者 (Machine Owner / 機主)**：
   - 擁有實體採集卡與機台硬體資產 (`devices`)。
   - 負責機台採購、硬體保養與維修。
3. **平台方 (WAW HQ)**：
   - 提供雲端物聯網通訊、清算對帳平台與運維支持。

### 4.2 營收拆帳計算 (Split Formula)
當機台部署於某場地並產生營收時，依據 `device_deployments` 或分成協議計算：
- **淨營收 (Net Revenue)** = 總開分金額 - 總洗分金額
- **場地主分成** = `Net Revenue * venue_owner_share` (例如 40%)
- **機台主分成** = `Net Revenue * owner_share` (例如 60%)
- 每一筆帳務均記錄於 `device_transactions` 作為每月出帳憑證。

### 4.3 雙重月租訂閱控制 (Dual Subscription Model) 【已設計】
- **場地月租**：每月 NT$ 1,500。解鎖店面營運進階功能（交班系統、LINE 即時警報、全店營收大看板）。
- **機台月租**：每台每月 NT$ 300。
  - **欠費軟性限制 (Soft Restriction)**：若機台主欠繳月租，系統**不切斷**機台的 MQTT 連線與玩家現場開分（避免引起現場客訴糾紛）；但系統會每日自動按日折算月租，累加至機台主之欠款帳單中，並限制其後台提現功能。

---

## 5. 會話生命週期與三層容錯防護 (Session Lifecycle & 3-Layer Protection)

為了防止「玩家開分後未玩即離開」、「惡意佔用機台」或「斷網造成資金卡死」，實作三層會話守護機制：

```
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 1: ESP32 本地活動定時器 (120 秒物理無活動監測)                     │
│  - 韌體內部計時器。機台按鈕每次閉合或搖桿晃動 (PIN_SENSE_ACTIVITY)，      │
│    計時器立即重置為 120 秒。                                            │
│  - 若連續 120 秒無任何硬體信號，韌體自動發布 session_timeout MQTT 封包。 │
├────────────────────────────────────────────────────────────────────────┤
│ Layer 2: 雲端診斷心跳守護 (5 分鐘 Heartbeat)                            │
│  - 採集卡每 5 分鐘主動上報 status 健康診斷包。                          │
│  - 雲端排程每分鐘掃描，若超過 10 分鐘無心跳，標記設備連線異常。          │
├────────────────────────────────────────────────────────────────────────┤
│ Layer 3: MQTT LWT (Last Will and Testament) 瞬斷遺囑                    │
│  - 採集卡於 TCP 握手時向 Mosquitto Broker 註冊遺囑。                    │
│  - 一旦硬體遭惡意拔除電源或斷網，Broker 毫秒級向雲端發布 offline 遺囑。  │
│  - 雲端立即凍結該機台進行中的 session，防止他人盜用。                   │
└────────────────────────────────────────────────────────────────────────┘
```

### 5.1 孤兒分數處置 (Orphan Credit Handling)
- **業務現象**：現場偶有玩家開分後，因突發狀況未洗分直接離場，機台留有剩餘分數。
- **處置方針**：
  - 系統寫入 `device_orphan_logs`。
  - 依據遊藝場實體營運慣例，視為「現場操作遺留」，系統記錄稽核但不予補償，下位玩家投幣或服務員洗分時將作為日結沖銷依據。

---

## 6. 資料遺失防範與異常偵測 (Fault Tolerance & Anti-Fraud)

### 6.1 斷網零漏失：里程表差值算法 (Odometer Delta Algorithm)
傳統系統若斷網，中途發生的投幣事件全部丟失。WAW 採集卡採用類似汽車機械里程表的 `raw_value`：
- 斷網期間，硬體 PCNT 持續計數，累加 `raw_value`。
- 恢復連線後，上報當前最新 `raw_value`。
- 後端演算法：
  ```
  遺漏補償脈衝數 (Lost Pulses) = 當前 raw_value - 資料庫最後記錄 raw_value
  ```
- 後端一次性將補償脈衝寫入日誌，完美保障總帳零誤差。

### 6.2 冪等性防重複結算 (Idempotency Key)
- 每一筆採集卡事件附帶全域唯一自增之 `delivery_id` (6 碼以上數字)。
- 後端資料庫在 `signal_webhook_deliveries` 對 `delivery_id` 設置 `UNIQUE` 索引。
- 重複抵達的 Webhook 重試封包將被直接識別並回傳現有結算結果，杜絕重複加分或重複扣款。

### 6.3 密鑰驗簽與重放攻擊防護 (HMAC-SHA256 Anti-Replay)
- 所有第三方 Webhook 包含 `X-WAW-Signature` 與 `occurred_at` 時間戳。
- 接收端必須校驗時間戳誤差在 300 秒（5 分鐘）以內，超過則視為無效過期請求。
- 雜湊簽名由伺服器與第三方各自計算並進行常數時間比對 (`hash_equals`)，阻絕中間人竄改 (Tampering)。


---

## 7. 核心資料庫結構規格 (Database DDL Specifications) 【已驗證】

### 7.1 場地表 (\`iotv9.venues\`)
\`\`\`sql
CREATE TABLE \`venues\` (
  \`id\` bigint unsigned NOT NULL AUTO_INCREMENT,
  \`name\` varchar(191) NOT NULL COMMENT '場地/店面名稱',
  \`address\` varchar(191) DEFAULT NULL COMMENT '實體地址',
  \`token_value_twd\` decimal(8,2) NOT NULL DEFAULT '10.00' COMMENT '每枚代幣對應新台幣價值',
  \`owner_id\` bigint unsigned NOT NULL COMMENT '場地所有人 users.id',
  \`subscription_status\` enum('active','arrears','expired') NOT NULL DEFAULT 'active',
  \`subscription_expires_at\` datetime DEFAULT NULL,
  \`created_at\` timestamp NULL DEFAULT NULL,
  \`updated_at\` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (\`id\`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
\`\`\`

### 7.2 設備資產表 (\`iotv9.devices\`)
\`\`\`sql
CREATE TABLE \`devices\` (
  \`id\` bigint unsigned NOT NULL AUTO_INCREMENT,
  \`chip_id\` varchar(32) NOT NULL COMMENT '12碼十六進位 MAC (例: df1e4c4b1105)',
  \`node_id\` varchar(32) DEFAULT NULL COMMENT '產品編號 (例: device_001)',
  \`venue_id\` bigint unsigned DEFAULT NULL COMMENT '當前部署場地',
  \`owner_id\` bigint unsigned DEFAULT NULL COMMENT '機台擁有者 users.id',
  \`status\` enum('active','offline','maintenance') NOT NULL DEFAULT 'offline',
  \`last_seen_at\` datetime DEFAULT NULL,
  \`created_at\` timestamp NULL DEFAULT NULL,
  \`updated_at\` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (\`id\`),
  UNIQUE KEY \`uniq_chip_id\` (\`chip_id\`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
\`\`\`

### 7.3 信號派送審計表 (\`iotv9.signal_webhook_deliveries\`)
\`\`\`sql
CREATE TABLE \`signal_webhook_deliveries\` (
  \`id\` bigint unsigned NOT NULL AUTO_INCREMENT,
  \`delivery_id\` bigint unsigned NOT NULL COMMENT '全域唯一自增序號',
  \`device_id\` bigint unsigned NOT NULL,
  \`profile_id\` bigint unsigned NOT NULL,
  \`event_type\` varchar(32) NOT NULL COMMENT 'credit_in, credit_out 等',
  \`pin_code\` varchar(16) NOT NULL COMMENT 'UI1 ~ UI4',
  \`raw_value\` bigint unsigned NOT NULL COMMENT '硬體累計脈衝里程表',
  \`delta_value\` int unsigned NOT NULL DEFAULT '1',
  \`cleared_points\` bigint DEFAULT NULL COMMENT '實際結算點數 (同 actual_points)',
  \`status\` enum('pending','success','failed') NOT NULL DEFAULT 'pending',
  \`retry_count\` tinyint unsigned NOT NULL DEFAULT '0',
  \`occurred_at\` datetime NOT NULL,
  \`created_at\` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (\`id\`),
  UNIQUE KEY \`uniq_delivery_id\` (\`delivery_id\`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
\`\`\`

### 7.4 會員錢包表 (\`waw_member_production.member_wallets\`)
\`\`\`sql
CREATE TABLE \`member_wallets\` (
  \`id\` bigint unsigned NOT NULL AUTO_INCREMENT,
  \`member_id\` bigint unsigned NOT NULL,
  \`currency_type\` enum('CASH','TOKEN','POINT','TICKET','COIN') NOT NULL,
  \`balance\` bigint NOT NULL DEFAULT '0' COMMENT '代幣/彩票強制整數 INT',
  \`frozen_balance\` bigint NOT NULL DEFAULT '0' COMMENT '開分中凍結餘額',
  \`created_at\` timestamp NULL DEFAULT NULL,
  \`updated_at\` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (\`id\`),
  UNIQUE KEY \`uniq_member_currency\` (\`member_id\`,\`currency_type\`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
\`\`\`
