# WAW 2.0 主線修改文件集中目錄

> 建立日期：2026-06-08  
> 最後更新：2026-06-15 01:12 (UTC+8)  
> 目的：把散落在 HQ、brains、archive、waw2.0_specs 的 WAW 2.0 主線修改與決策文件集中，避免環境工具整理時讓主任務失焦。

---

## 目前主線焦點

1. 先完成「過渡期矛盾修復」驗收。
   - Ina 執行/確認 `devices` 新欄位 migration。
   - Ina 將 `pulse_ratio` 查詢改為 `pulse_to_token`。
   - Ina 部署 listener / FastAPI 修正。
   - Hubie 完成 iHub `kiosk_token` 更名並與 Member 聯調。

2. 過渡期驗收後，才進入 WAW 2.0 雙資料庫新表設計審查。
   - `waw_infra`：`stores`、`machines`、`machine_deployments`、`machine_transactions`。
   - `waw_core`：`profit_sharing_agreements`、`users.outstanding_amount`。

3. 第三階段才做服務割接與軟性欠費功能。
   - `waw-iot` 負責物理採集、Redis 狀態、交易分潤固化。
   - `waw-business` 負責訂閱、欠款累計、後台限制、催收。
   - 鐵律：欠費不阻斷 MQTT 與玩家掃碼開分，營業不中斷。

---

## 閱讀順序

| 順序 | 文件 | 用途 |
| --- | --- | --- |
| 0 | `00_CURRENT_START_HERE__JOE_READ_ME_FIRST.md` | 當前啟動備忘卡，先看今天該做什麼。 |
| 1 | `01_CURRENT_MAINLINE_TODO.md` | WAW 2.0 大修與過渡期任務清單。 |
| 1.5 | `02_PROGRESS_SUMMARY_20260608.md` | **WAW 2.0 完整進度總結報告（2026-06-08）** |
| 1.6 | `03_PROGRESS_SUMMARY_20260615.md` | **階段二完成報告（2026-06-15）** |
| 1.7 | `04_PHASE3_EXECUTION_PLAN.md` | **階段三執行計劃（2026-06-15）** |
| 2 | `10_WAW_2.0_ARCHITECTURE_SPEC.md` | WAW 2.0 核心資料表與事件平台架構。 |
| 3 | `11_V9_SYSTEM_SPLITTING_DESIGN.md` | V9 拆成 `waw-business` / `waw-iot` 的設計。 |
| 4 | `20_WAW_2.0_CORE_TASKS.md` | 核心待辦摘要。 |
| 5 | `21_DISPATCH_BOARD_RELEVANT_TASKS.md` | HQ 派工板，含 R20/R21 與相關歷史任務。 |
| 6 | `30_SYSTEM_FIX_PLAN_20260528.md` | 全系統五大矛盾修復計劃。 |
| 7 | `31_PHASED_ROLLOUT_PLAN_20260528.md` | 分階段割接計劃與驗收標準。 |
| 8 | `40_TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` | API、Port、Header、Payload 命名唯一標準。 |
| 9 | `41_AGENT_RESPONSIBILITY_BOUNDARIES.md` | Agent 職責邊界與禁止跨專案亂改規範。 |
| 10 | `50_KNOWLEDGE_DOCUMENT_INDEX.md` | brains 知識庫總索引。 |
| 11 | `60_WAW_2.0_MEETING_TRANSCRIPT_20260605.md` | WAW 2.0 架構重構與決策會議完整記錄。 |

---

## 原始來源

| 集中檔案 | 原始路徑 |
| --- | --- |
| `00_CURRENT_START_HERE__JOE_READ_ME_FIRST.md` | `JOE_READ_ME_FIRST.md` |
| `01_CURRENT_MAINLINE_TODO.md` | `TODO.md` |
| `02_PROGRESS_SUMMARY_20260608.md` | HQ 整理的完整進度總結 |
| 1.6 | `03_PROGRESS_SUMMARY_20260615.md` | **階段二完成報告（2026-06-15）** |
| 1.7 | `04_PHASE3_EXECUTION_PLAN.md` | **階段三執行計劃（2026-06-15）** |
| `10_WAW_2.0_ARCHITECTURE_SPEC.md` | `brains/knowledge/03_system_architecture_designs/WAW_2.0_ARCHITECTURE_SPEC.md` |
| `11_V9_SYSTEM_SPLITTING_DESIGN.md` | `brains/knowledge/03_system_architecture_designs/V9_SYSTEM_SPLITTING_DESIGN.md` |
| `20_WAW_2.0_CORE_TASKS.md` | `waw2.0_specs/CORE_TASKS.md` |
| `21_DISPATCH_BOARD_RELEVANT_TASKS.md` | `archive/completed/DISPATCH_BOARD.md` |
| `30_SYSTEM_FIX_PLAN_20260528.md` | `brains/knowledge/01_agent_governance_rules/SYSTEM_FIX_PLAN_20260528.md` |
| `31_PHASED_ROLLOUT_PLAN_20260528.md` | `brains/knowledge/01_agent_governance_rules/PHASED_ROLLOUT_PLAN_20260528.md` |
| `40_TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` | `brains/knowledge/02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` |
| `41_AGENT_RESPONSIBILITY_BOUNDARIES.md` | `brains/knowledge/01_agent_governance_rules/AGENT_RESPONSIBILITY_BOUNDARIES.md` |
| `50_KNOWLEDGE_DOCUMENT_INDEX.md` | `brains/knowledge/DOCUMENT_INDEX.md` |
| `60_WAW_2.0_MEETING_TRANSCRIPT_20260605.md` | `archive/completed/WAW_2.0_MEETING_TRANSCRIPT_20260605.md` |

---

## 判斷原則

- 收錄：直接提到 WAW 2.0、`waw-business`、`waw-iot`、V9 拆分、雙庫遷移、軟性欠費、過渡期矛盾修復、或目前派工主線的文件。
- 未收錄：一般 Message Hub v2、iHub build、Android build cache、單純 kiosk exchange v2 完成報告、與 WAW 2.0 主線無直接關係的環境工具文件。
- 這裡是「閱讀集中區」，原始權威文件仍以 `brains/knowledge/` 為準；需要正式更新知識庫時，仍由 HQ 審核後寫回 brains。
