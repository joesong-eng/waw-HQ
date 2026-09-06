# WAW 知識庫整頓與 Agent 環境認知重構報告

> **執行日期**: 2026-09-06  
> **執行者**: HQ  
> **版本**: 1.0.0  
> **狀態**: Completed

---

## 📋 執行背景

2026-09-06 發現 Sidney (SignalHub Agent) 在執行任務時出現嚴重的「環境認知真空」問題：

```bash
ssh root@129.153.116.174 'mysql -u root -pRUQxp84NnQYf47Ec iotv9 << "EOSQL"
```

此指令暴露出 4 大致命缺陷：
1. 使用 raw IP 直連，不知道本機已配置 SSH 別名 `yd174`
2. 使用預設 Port 22 與 root 帳號（Oracle Cloud 實際為 Port 39022 / ubuntu）
3. 在 CLI 明文打上資料庫 root 密碼
4. 混淆資料庫實體位置（`iotv9` 在 `infra`，不在 `yd174`）

經全面檢討，發現整個 Agent 體系存在：
- **知識庫文檔嚴重冗餘**：5 組「雙胞胎目錄」新舊並存，內容衝突
- **環境常識缺失**：Agent 啟動時無系統性環境注入機制
- **過期資訊污染**：大量 backup 檔案與廢棄路徑殘留

---

## ✅ 執行成果

### 一、知識庫去重與標準化（階段 1）

#### 1.1 消除 5 組雙胞胎目錄

| 舊目錄（已刪除） | 標準目錄（保留） | 合併檔案數 |
|-----------------|----------------|-----------|
| `01_agent_governance_rules/` | `01_agent_governance/` | 12 個 |
| `02_protocols_and_standards/` | `02_technical_standards/` | 12 個 |
| `03_system_architecture_designs/` | `03_system_architecture/` | 7 個 |
| `04_ops_and_deployments/` | `04_deployment_operations/` | 13 個 |
| `05_product_and_business_flows/` | `05_business_flows/` | 5 個 |

**成果**：知識庫已統一為標準五大分類 + `06_alliance_system/`。

#### 1.2 修復全域鏈接

- 批次更新 **46 個 Markdown 文件**中的內部鏈接
- 將所有指向舊目錄名的路徑自動校正為統一標準

#### 1.3 封存歷史備份

- 將 4 個 `.backup` / `.bak` 檔案移入 `brains/history/` 封存隔離

---

### 二、建立權威環境拓撲卡（階段 2）

#### 2.1 創建 `VPS_TOPOLOGY_CARD.md`（SSOT）

路徑：`brains/knowledge/04_deployment_operations/VPS_TOPOLOGY_CARD.md`

**核心內容**：
1. **4 大紅線禁令**：
   - 禁用 raw IP / Port 22 / root 帳號
   - 禁 CLI 明文密碼
   - 資料庫實體定位（`iotv9` 在 `infra`）
   - 本機代碼純淨原則
2. **完整 SSH 別名對照表**（8 台 VPS）
3. **資料庫架構與查詢標準**
4. **`waw_ops.sh` 工具優先使用規範**

#### 2.2 納入最高強制規範

- 在 `DOCUMENT_INDEX.md` 的「最高指導規範」表中新增：
  ```
  | VPS_TOPOLOGY_CARD.md 🔴 | 全域主機拓撲、SSH 別名、DB 架構與連線禁令 | 
  | 所有系統 / Agent | 盲打 IP、使用預設 Port 22、明文密碼外洩、連錯 DB |
  ```

#### 2.3 修正過期路徑

- 將歷史文件中的 `/www/wwwroot/iot.tg25.win/wawv9` 與 `waw-core` 全面修正為 `/www/wwwroot/iot.tg25.win`

---

### 三、全面重構 Agent 專案 AGENTS.md（階段 3）

| Agent | 專案目錄 | 重構內容 |
|-------|---------|---------|
| **Sidney** | `PROJECT/SignalHub` | 新增完整環境卡：`yd174`, `/www/wwwroot/signal.tg25.win`, 明確 DB 位於 `infra` |
| **Sophie** | `PROJECT/Owner` | 清理過期路徑，注入 `yd174` 環境卡 |
| **Mina** | `PROJECT/Member` | 補齊身分與環境卡：`yd177`, `/www/wwwroot/win.tg25.win` |
| **Ina** | `PROJECT/Infra` | 補齊 Central DB 職責，標明 `infra` 為唯一 DB 規劃者 |
| **Allie** | `PROJECT/Alliance` | **全新建立**（原先完全缺失）：`yd16`, `/www/wwwroot/ali.tg25.win` |
| **Hubie** | `PROJECT/iHub` | 統一路徑與任務信箱：`yd177`, `/www/wwwroot/ihub.tg25.win` |
| **Fio** | `PROJECT/IOTkiosk_v0` | 注入韌體專屬常識卡，標明為 ESP32 嵌入式專案 |
| **Coli** | `PROJECT/IOTwawS3` | 注入韌體專屬常識卡，同步 WAW-USS 標準 |

**成果**：8 位 Agent 的 `AGENTS.md` 第一屏均已注入專屬「環境與連線常識卡」。

---

### 四、啟動協議升級與工具強化（階段 4）

#### 4.1 升級 AGENT_STARTUP_PROTOCOL.md (v2.2.0)

- 新增 Sidney 適用範圍（共 8 位 Agent）
- 將「步驟 1：環境識別」強制升級為「環境識別與載入系統常識」
- 要求 Agent 必須主動閱讀所屬 `AGENTS.md` 與 `VPS_TOPOLOGY_CARD.md`

#### 4.2 強化 waw_ops.sh 防呆機制

**修改位置**：`dev_tools/waw_ops.sh` 的 `cmd_deploy` Laravel 段落

**修改前**：
```bash
pnpm install && pnpm build && php artisan migrate ...
```

**修改後**：
```bash
if [ -f package.json ]; then pnpm install && pnpm build; fi && php artisan migrate ...
```

**成果**：徹底解決 SignalHub (無前端 build) 過去命中 `ERR_PNPM_NO_PKG_MANIFEST` 的崩潰問題。

---

## 📊 統計數據

| 項目 | 數量 |
|------|------|
| 刪除重複目錄 | 5 組 |
| 合併檔案 | 49 個 |
| 修復內部鏈接 | 46 個檔案 |
| 封存歷史備份 | 4 個檔案 |
| 新建權威文檔 | 1 個 (VPS_TOPOLOGY_CARD.md) |
| 重構 Agent AGENTS.md | 8 個專案 |
| 升級啟動協議 | 1 個 (v2.0.0 → v2.2.0) |
| 強化維運工具 | 1 個 (waw_ops.sh) |

---

## 🎯 預期效果

1. **消除環境認知真空**：Agent 啟動時第一眼即可看到所屬主機、連線別名與禁令。
2. **杜絕盲打 IP 與明文密碼**：統一走 SSH 別名，嚴禁 CLI 洩密。
3. **防止資料庫拓撲混淆**：明確 `iotv9` 在 `infra`，Web 伺服器禁直連 MySQL。
4. **文檔檢索精準化**：消除冗餘與衝突，Agent 檢索不再碰壁。
5. **維運工具防呆**：`waw_ops.sh` 自動適配有/無前端 build 的 Laravel 專案。

---

**維護者**: HQ  
**下次檢討**: 當新增 Agent 或新增 VPS 時，必須同步更新 `VPS_TOPOLOGY_CARD.md` 與對應 `AGENTS.md`。

---

## 📝 補充更新（2026-09-06 下午）

### 追加注入：禁止直接修改遠端文件的鐵律

**背景**：為防止 Agent 在遠端 VPS 上直接編輯代碼，導致版本失控與本機代碼不同步。

**執行內容**：
- 為全部 8 位 Agent 的 `AGENTS.md` 注入「嚴禁直接修改遠端文件」章節
- 明確規範：本機修改 → Git commit/push → 遠端 pull 的標準流程
- 定義例外情況：僅 `.env` 等配置文件可在遠端直接修改
- 列舉嚴禁做法：SSH 遠端 vim 編輯、sed -i 修改代碼等
- 說明版本控制的 5 大好處

**影響 Agent**：
- Sidney (SignalHub)
- Sophie (Owner)
- Mina (Member)
- Allie (Alliance)
- Hubie (iHub)
- Ina (Infra)
- Fio (IOTkiosk_v0)
- Coli (IOTwawS3)

**預期效果**：
- 杜絕遠端直接修改代碼的行為
- 確保所有代碼變更都有 Git 歷史記錄
- 保持本機與遠端代碼同步
- 出問題時可快速回滾與定位

---

## 📊 最終統計

| 項目 | 數量 |
|------|------|
| 知識庫目錄合併 | 5 組 |
| 文件鏈接修復 | 46 個 |
| Agent AGENTS.md 重構 | 8 個 |
| 新建權威文檔 | 1 個 (VPS_TOPOLOGY_CARD.md) |
| 注入環境卡 | 8 個 Agent |
| 注入部署規範 | 5 個 Web Agent |
| 注入遠端編輯禁令 | 8 個 Agent |
| 工具強化 | 1 個 (waw_ops.sh) |
| 啟動協議升級 | v2.0.0 → v2.2.0 |

---

**維護者**: HQ  
**完成時間**: 2026-09-06 14:20 (UTC+8)
