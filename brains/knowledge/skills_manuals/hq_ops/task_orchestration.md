# Skill: HQ 任務協調（`.taskflow` 派工）

> **版本**：2.0
> **建立**：2026-08-01 ｜ **改版**：2026-10-05（對齊 `.taskflow` 純檔案派工）
> **適用角色**：HQ（唯一使用者）
> **核心規則**：設計先行 → 派工 → 以實證驗收 → 結案歸檔

---

## 什麼時候用這個 Skill

每當 Joe 要求 HQ 對任何 Agent 下指令，且工作內容涉及：

- 修改程式碼、設定檔、migration
- 新建或刪除檔案、資料表、API
- 改變部署配置、基礎設施、MQTT 設定
- 跨 Agent 協作（影響超過一個專案）

**一律走本 Skill 的派工流程。** 純查詢可省略工單，但仍須以實證回覆。

> ⛔ 舊的兩階段 consult / Redis / `.taskbox` / `hq_gateway.py` 流程**已廢除**，不再使用。

---

## Step 1：設計先行（Design First）

派工前 HQ 必須確認：

1. **資料來源**：SSOT 表 / 模型（對照 ADR-002、ADR-003）
2. **通訊主題**：MQTT / WebSocket（對照 `02_technical_standards/`）
3. **系統邊界**：屬哪個 Agent 的專案、是否跨專案
4. **驗收指標**：可量測的指令 / HTTP 碼 / log（不接受口頭聲明）

---

## Step 2：建立工單（Write the work order）

長工單一律先寫成 Markdown 檔案，再以 `--file` 派發（避免 Shell 截斷與跳脫損壞）：

```bash
# 短任務
./dev_tools/waw_ops.sh task <agent> <task_id> "<描述>" [priority]

# 長工單（強烈推薦）
./dev_tools/waw_ops.sh task <agent> <task_id> --file <工單.md> [priority]
```

工單**必須包含**：

- 任務 ID / 派發時間 / 優先級 / 負責人
- **背景**：為什麼要做、架構依據（ADR / SPEC 路徑）
- **明確步驟**：做什麼、改哪些檔案
- **驗收指標**：每項附「實際指令 + 預期輸出」
- **禁止事項**：不得觸碰的範圍
- **完成定義**：回報寫入 `.taskflow/<agent>/outbox/`

落點：`.taskflow/<agent>/inbox/YYYYMMDD_HHMMSS_TASK_<ID>.md`

---

## Step 3：Agent 執行與回報

Agent 在**其專案目錄**內執行（見下方對照表），完成後：

- 回報寫入 `.taskflow/<agent>/outbox/`，或執行
  `bash ../../dev_tools/agent_report_to_hq_v2.sh <agent> <report_path>`
- 回報**必須附實證**：指令輸出、HTTP 回應、SQL SELECT 結果、git commit hash
- 遇方案外決策 → 停止並回報阻塞，不得自行擴大範圍

---

## Step 4：HQ 驗收與結案

1. **全量讀取**回報（`outbox/*.md` 一律整檔讀取，禁止切片）
2. 以 `evidence` 中的 log / diff / API 回應驗收，不以口頭聲明驗收
3. 有問題 → 重新派工（帶具體問題）
4. 通過 → 結案歸檔：

```bash
./dev_tools/waw_ops.sh close <agent> <關鍵字>
```

歸檔至 `.taskflow/archive/<agent>/<YYYYMM>/`。

---

## 常用指令速查

```bash
./dev_tools/waw_ops.sh status              # 各 Agent 信箱狀態
./dev_tools/waw_ops.sh log                 # 最近派工日誌
./dev_tools/waw_ops.sh report <agent>      # 讀取最新回報
./dev_tools/waw_ops.sh close <agent> <key> # 結案歸檔
./dev_tools/waw_ops.sh deploy <agent>      # 遠端部署
./dev_tools/waw_ops.sh remote <agent> "<cmd>"  # 遠端執行指令
```

---

## 防呆清單（HQ 每次派工前自問）

- [ ] 有沒有確認資料來源 / MQTT 主題 / 系統邊界？
- [ ] 工單是否含**可量測的驗收指標**？
- [ ] 是否已指定**禁止事項**與**完成定義**？
- [ ] 長工單是否以 `--file` 派發（而非塞進 CLI）？
- [ ] 是否知道要讀哪個 `outbox/` 驗收？

---

## 適用 Agent 與工作目錄

| Agent | 工作目錄 | 主要職責 |
|-------|---------|---------|
| Sophie | `PROJECT/Owner` | 營運商後台 |
| Mina | `PROJECT/Member` | 玩家前端 |
| Ina | `PROJECT/Infra` | 資料庫、MQTT、基礎設施 |
| Allie | `PROJECT/Alliance` | 供應商代理商 |
| Hubie | `PROJECT/iHub` | Android APK |
| Fio | `PROJECT/IOTkiosk_v0` | 兌幣卡韌體 |
| Coli | `PROJECT/IOTwawS3` | 遊戲採集卡韌體 |
| Sidney | `PROJECT/SignalHub` | 信號中心與開放標準 |

---

## 🔗 文件神經連結

- **派工協議（權威）**：`../../01_agent_governance/SIMPLE_FILE_DISPATCH_PROTOCOL.md`
- **總控腳本**：`../../../../dev_tools/waw_ops.sh`
- **治理規範**：`AGENT_EXECUTION_PROTOCOL.md`、`AGENT_RESPONSIBILITY_BOUNDARIES.md`
- **待辦總表**：`../../WAW_TODO.md`
