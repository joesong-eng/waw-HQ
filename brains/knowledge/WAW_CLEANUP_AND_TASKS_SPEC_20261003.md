# WAW 舊派工系統清除與待辦收斂 SPEC

> **文件類型**：行動規格書（Action Spec / Master TODO）
> **建立日期**：2026-10-03
> **維護者**：HQ
> **狀態**：Phase 1-2 已完成；Phase 3 待執行
> **適用範圍**：全 WaW 系統（HQ + 7 專案）
> **觸發來源**：Joe 指示「重新整體整理還有哪些沒做好」+「刪除舊派工系統，以後不要有混淆的機會」

---

## 0. 背景與目的

本系統自 2026-08 起已將派工機制統一為 **`.taskflow` 純檔案信箱**，但舊派工系統
（Redis Pub/Sub、Message Hub、`.taskbox`、`_agent/`、`hq_gateway.py`、launchd 常駐服務）
的**殘骸與文件**散落全系統，造成：

1. **實際危害**：舊 launchd 服務仍在崩潰循環（exit 78）；agent 規則檔仍教舊制路徑。
2. **認知混淆**：治理文件、pubdocs、skills 手冊同時存在新舊兩套指引。
3. **待辦黑洞**：跨專案未結項目散落各處，無單一追蹤清單。

本 SPEC 的目標：**徹底移除舊派工系統，讓 `.taskflow` 成為唯一權威，並將剩餘待辦收斂為可追蹤步驟。**

---

## 1. 唯一權威原則（Acceptance Baseline）

| 項目 | 唯一正確 |
|:---|:---|
| 派工 | `./dev_tools/waw_ops.sh task <agent> <task_id> --file <工單.md> [priority]` |
| 回報 | `bash ../../dev_tools/agent_report_to_hq_v2.sh <agent> <回報.md>` |
| 信箱 | `.taskflow/<agent>/{inbox,outbox}/` |
| 協議 | `brains/knowledge/01_agent_governance/SIMPLE_FILE_DISPATCH_PROTOCOL.md` |

**禁止**：任何 Redis Pub/Sub、Message Hub、`hq_gateway.py`、`.taskbox/*.json`、`_agent/` 路徑。

---

## 2. Phase 0 — 盤點（本次 Session 起點檢查）

| # | 檢查項 | 工具 | 結論 |
|:--|:---|:---|:---|
| 0.1 | 各 Agent 信箱狀態 | `waw_ops.sh status` | 僅 owner / signalhub 有待處理單 |
| 0.2 | 派工日誌 | `task_flow.log` | 7 個 Agent 已長期未派工 |
| 0.3 | 舊派工目錄殘留 | `find` / `git ls-files` | `_agent/` `core/` `.kiro/` `.kilo/` `scripts/` `services/` |
| 0.4 | 各專案 git 實況 | `git status` | iHub / IOTkiosk_v0 / IOTwawS3 大量 WIP |
| 0.5 | 常駐服務 | `launchctl list` | 3 個舊服務崩潰循環中 |
| 0.6 | 文件引用 | `grep` | 治理/pubdocs/skills 多處教舊制 |

---

## 3. Phase 1 — 舊派工系統清除 ✅ 已完成

### 3.1 HQ 層

- [x] 刪除 `_agent/`（101 檔，舊 HQ 信箱/封存）
- [x] 刪除 `core/`（36 檔，Redis listener / Message Hub v2 / hq_gateway / templates）
- [x] 刪除 `.kiro/`（45 檔，舊 agent-manager 設定）
- [x] 刪除 `.kilo/`（未追蹤，移入 `trash/`）
- [x] 刪除 `scripts/`（舊版重複工具）
- [x] 刪除 `services/`（舊 launchd plist）
- [x] 刪除 `dev_tools/waw_ops.sh.backup` 等殘留備份

**Commit**：`d51f2e1`、`2750284`

### 3.2 專案層

- [x] 7 個 `PROJECT/*/_agent/`（共 177 檔）
- [x] 各專案 `DISPATCH_BOARD.md`
- [x] `scripts/agent_redis_listener.py`（6 專案）
- [x] `ina-redis-listener.service` / `.logrotate` / `archive_agent_tasks.sh`（Infra）
- [x] `hq_agent_tools/`、`_agent_legacy_before_taskbox/`（Member/iHub）

**Commit**：Owner `a7a1fa8`、Member `ad4950d`、Infra `1181ba8`、Alliance `2722b8b`、
iHub `25a964d`、IOTkiosk_v0 `5ef06a2`、IOTwawS3 `63dadcd`

### 3.3 常駐服務卸載（關鍵）

- [x] `launchctl bootout` 三個舊服務（supervisor / messagehub.v2 / redis.keeper）
- [x] 移除 `~/Library/LaunchAgents/` 對應 plist（移入 `trash/`）
- [x] 移除舊服務 log

### 3.4 Git Hook 清除

- [x] 移除 Owner `pre-commit`（指向已刪 `_agent/neural_governance_check.py`）
- [x] 移除 Member `pre-commit`（舊 Chat Bridge RFI 身分驗證）

**驗收**：`launchctl list` 無舊服務；`find` 無 `_agent/`；`waw_ops.sh status` 正常。

---

## 4. Phase 2 — 文件對齊 ✅ 已完成

- [x] `pubdocs/DISPATCH_GUIDE.md` 重寫為 `.taskflow` 版
- [x] `shared/TASK_DISPATCH_GUIDE.md` 重寫為 `.taskflow` 版
- [x] `skills/{dispatch_task,report_task}.sh` 改指向 `dev_tools/`
- [x] `.taskflow/README.md` 路徑更新
- [x] `brains/knowledge/01_agent_governance/` 12 份治理文件對齊
- [x] 知識庫 `README.md` / `DOCUMENT_INDEX.md` / `WAW_TODO.md` 對齊
- [x] 舊制度文件（`MESSAGE_HUB_*`、`AUTOFLOW_*`、`CLI_AGENT_DISPATCH`、`HQ_AUTOFLOW`）加「已廢棄」橫幅
- [x] `skills_manuals/**` 對齊

**Commit**：`fe458b6`（root）、各專案 docs commit

---

## 5. Phase 3 — 待辦收斂（TODO，按優先序執行）

### 🔴 P1-1｜SignalHub 訂閱機制未落地

- **現況**：`PROJECT/SignalHub/app/Models/User.php:127` 引用 `hasOne(OwnerSubscription::class)`，
  但 Model 不存在；無 `SubscriptionController`；routes 無訂閱路由。
- **依據**：`20260915_103000_PROPOSAL_SIDNEY_TO_HQ_SIGNALHUB_SUBSCRIPTION_DESIGN.md`
- **步驟**：
  1. [ ] HQ 裁定訂閱 Schema 與方案定價（沿用 `config/subscription.php`）
  2. [ ] 派單 Sidney：建 `OwnerSubscription` Model + Migration
  3. [ ] 派單 Sidney：建 `SubscriptionController` + 路由
  4. [ ] 派單 Sophie：Owner 後台訂閱管理頁對接
- **負責**：HQ（裁定）→ Sidney → Sophie
- **驗收**：`owner_subscriptions` 表可讀寫；訂閱狀態 API 回 200。

### 🔴 P1-2｜SignalHub 版控殘留檔

- **現況**：11 個 `.bak/.old/.contaminated/.new_template` 殘留檔。
- **狀態**：✅ 已派單 `TASK_20261003_SIDNEY_PURGE_RESIDUE_FILES`（P3）
- **步驟**：
  1. [x] 工單已派發
  2. [ ] Sidney 執行 `git rm` / 刪檔
  3. [ ] 驗收：`git ls-files | grep -E '\.bak|\.old'` = 0 hits
- **負責**：Sidney

### 🟠 P2-1｜Member 未跟上 Device SSOT

- **現況**：`PROJECT/Member/app/Models/MachineSession.php`（舊命名）＋
  `CallbackController.php:59/138` 以 `machine_id` 比對。
- **說明**：Owner/Infra 已全面改 Device 語意，Member 未同步。
- **步驟**：
  1. [ ] HQ 確認 `machine_sessions` 表是否需更名/保留
  2. [ ] 派單 Mina：對齊 Device SSOT（Model 命名或加註）
- **負責**：HQ（裁定）→ Mina
- **驗收**：Member 內 `Machine` 語意與 Owner/Infra 一致。

### 🟡 P3-1｜Owner README 過時引用

- **現況**：`PROJECT/Owner/README.md` 仍描述已刪的 `Machine.php` / `MachineExtensions.php`。
- **狀態**：✅ 已派單 `TASK_20261003_SOPHIE_FIX_README_STALE_MODEL_REFS`（P3）
- **步驟**：
  1. [x] 工單已派發
  2. [ ] Sophie 修正 3 處引用
- **負責**：Sophie

### 🟡 P3-2｜專案 WIP 未提交清理

- **現況**：
  | 專案 | dirty | 最後 commit | 說明 |
  |:---|:--:|:---|:---|
  | iHub | 36 | 2026-05-28 | `.kiro/`、`AI_CONTEXT.md`、`src/main.js` 等既有 WIP |
  | IOTkiosk_v0 | 86 | 2026-05-20 | firmware `.bin` 刪除、`.kiro/`、`src/*.c` 等既有 WIP |
  | IOTwawS3 | 7 | 2026-09-17 | `AGENTS.md`、firmware、`wifi_service.c` |
  | SignalHub | 2 | 2026-09-21 | `profiles.blade.php.bak`（Sidney 工單範圍） |
- **步驟**：
  1. [ ] 逐專案確認 WIP 歸屬（是否為 Agent 未提交成果）
  2. [ ] 派單對應 Agent 整理並提交或丟棄
- **負責**：Hubie / Fio / Coli / Sidney

### ⚪ P4｜WAW_TODO.md 歷史殘留清理

- **現況**：`brains/knowledge/WAW_TODO.md` 含大量已廢除的「多管道派工架構（Hermes + VPS Redis）」待辦。
- **步驟**：
  1. [ ] 標記該段落為已廢棄（Hermes/Redis 派工不採用）
  2. [ ] 保留仍有效的業務待辦（Alliance UI 技術債、SignalHub 核心流程）
- **負責**：HQ

---

## 6. 驗收總表

| # | 驗收項 | 指令 | 期望 |
|:--|:---|:---|:---|
| 1 | 舊服務已卸載 | `launchctl list \| grep -iE 'hq\|redis\|messagehub'` | 空 |
| 2 | 舊目錄已移除 | `ls _agent core .kiro .kilo scripts services` | 皆不存在 |
| 3 | 專案舊目錄已移除 | `find PROJECT -maxdepth 2 -name _agent` | 空 |
| 4 | 工具鏈正常 | `./dev_tools/waw_ops.sh status` | 8 Agent 正常列出 |
| 5 | 無現行舊制引用 | `grep -rn 'core/hq_\|hq_gateway\|_taskbox' dev_tools skills AGENTS.md` | 空 |
| 6 | P1 訂閱落地 | SignalHub 訂閱 API | 200 |
| 7 | 殘留檔歸零 | `git -C PROJECT/SignalHub ls-files \| grep -E '\.bak\|\.old'` | 空 |

---

## 7. 變更記錄

| 日期 | 項目 | 狀態 |
|:---|:---|:---|
| 2026-10-03 | Phase 0 盤點 | ✅ |
| 2026-10-03 | Phase 1 舊系統清除（HQ + 7 專案 + launchd） | ✅ |
| 2026-10-03 | Phase 2 文件對齊 | ✅ |
| 2026-10-03 | Phase 3 待辦收斂 | ⏳ 進行中 |

---

**維護者**：HQ
**最後更新**：2026-10-03
