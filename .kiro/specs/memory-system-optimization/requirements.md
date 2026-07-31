# Requirements Document

## Introduction

本需求文檔定義 HQ 記憶系統優化功能，旨在提升 AI Agent 對知識庫的存取效率、降低 token 消耗、改善內容組織結構。系統將採用混合載入策略、激進內容優化、程式化索引機制，並重建目錄架構以符合實際使用需求。

## Glossary

- **Memory_System**: HQ 的記憶系統，包含 `brains/knowledge/`、`brains/history/`、`brains/memory/` 三個主要目錄
- **Knowledge_Base**: 知識庫目錄 (`brains/knowledge/`)，存放專案規範、技術文檔、操作規則等持久化知識
- **Index_Engine**: 索引引擎，負責生成、維護、查詢記憶系統的索引結構
- **Content_Optimizer**: 內容優化器，負責重組、合併、拆分、標準化知識庫文檔
- **Loading_Strategy**: 載入策略，決定哪些內容自動載入、哪些按需查詢
- **Core_Rules**: 核心規則，指必須自動載入到 AI context 的關鍵文檔（如 CRITICAL_NO_TRIAL_AND_ERROR.md）
- **Technical_Details**: 技術細節，指可按需查詢的具體實作文檔（如 kiosk_bill_acceptor_interaction_flow.md）
- **Directory_Structure**: 目錄結構，指 `brains/` 下的資料夾組織方式
- **AI_Agent**: 使用記憶系統的 AI 代理（HQ、Allie、Susan 等）
- **Token_Budget**: AI Agent 的 context window 限制，需要透過優化降低消耗

## Requirements

### Requirement 1: 混合載入策略

**User Story:** 作為 AI Agent，我希望系統自動載入核心規則並提供技術細節的快速查詢機制，以便在不超出 token budget 的前提下獲取所需知識。

#### Acceptance Criteria

1. THE Memory_System SHALL 區分 Core_Rules 與 Technical_Details 兩類文檔
2. WHEN AI_Agent 啟動時，THE Memory_System SHALL 自動載入所有 Core_Rules 到 context
3. WHEN AI_Agent 需要 Technical_Details 時，THE Index_Engine SHALL 提供關鍵字查詢介面
4. THE Index_Engine SHALL 在 200ms 內回傳查詢結果的文件路徑與摘要
5. WHERE 文檔被標記為 Core_Rules，THE Memory_System SHALL 確保該文檔總大小不超過 5KB
6. THE Memory_System SHALL 提供配置文件定義哪些文檔屬於 Core_Rules

### Requirement 2: 激進內容優化

**User Story:** 作為知識庫維護者，我希望系統能自動重組、合併、拆分文檔，以便消除冗餘、改善可讀性、降低 token 消耗。

#### Acceptance Criteria

1. THE Content_Optimizer SHALL 識別並合併內容重複度超過 70% 的文檔
2. WHEN 文檔大小超過 10KB 時，THE Content_Optimizer SHALL 將其拆分為多個邏輯單元
3. THE Content_Optimizer SHALL 標準化所有文檔的 Markdown 格式（標題層級、列表格式、代碼區塊）
4. THE Content_Optimizer SHALL 移除過時或已棄用的內容（需人工確認標記）
5. THE Content_Optimizer SHALL 生成優化報告，列出所有變更項目與理由
6. WHERE 文檔包含多個獨立主題，THE Content_Optimizer SHALL 建議拆分方案
7. THE Content_Optimizer SHALL 保留原始文檔的備份於 `brains/.archive/` 目錄

### Requirement 3: 程式化索引機制

**User Story:** 作為開發者，我希望索引系統使用結構化格式（JSON/YAML）並提供 Python API，以便快速整合到現有工具鏈中。

#### Acceptance Criteria

1. THE Index_Engine SHALL 生成 JSON 格式的索引文件 (`brains/.index/knowledge_index.json`)
2. THE Index_Engine SHALL 為每個文檔提取以下元數據：
   - 文件路徑
   - 標題
   - 關鍵字列表（至少 5 個）
   - 摘要（不超過 200 字元）
   - 文檔類型（Core_Rules / Technical_Details / Historical_Record）
   - 最後更新時間
   - 文件大小
3. THE Index_Engine SHALL 提供 Python 模組 (`brains/index_engine.py`) 支援以下操作：
   - `search(keyword: str) -> List[Document]`
   - `get_core_rules() -> List[Document]`
   - `get_by_category(category: str) -> List[Document]`
   - `rebuild_index() -> None`
4. WHEN 知識庫文檔被修改時，THE Index_Engine SHALL 在 5 秒內自動更新索引
5. THE Index_Engine SHALL 支援模糊搜尋與同義詞匹配（如 "MQTT" 匹配 "mqtt", "message queue"）
6. THE Index_Engine SHALL 記錄查詢日誌於 `brains/.index/query.log`

### Requirement 4: 激進目錄重組

**User Story:** 作為系統架構師，我希望重新設計 `brains/` 目錄結構，以便更符合實際使用場景，不受現有引用限制。

#### Acceptance Criteria

1. THE Memory_System SHALL 採用以下新目錄結構：
   ```
   brains/
   ├── core/           # 核心規則（自動載入）
   ├── technical/      # 技術文檔（按需查詢）
   ├── operational/    # 操作指南（按需查詢）
   ├── historical/     # 歷史記錄（歸檔）
   ├── .index/         # 索引文件
   └── .archive/       # 備份文件
   ```
2. THE Memory_System SHALL 將現有 `knowledge/` 目錄的文檔重新分類到 `core/`、`technical/`、`operational/` 三個目錄
3. THE Memory_System SHALL 將 `history/` 目錄重命名為 `historical/`
4. THE Memory_System SHALL 生成遷移腳本 (`scripts/migrate_memory_structure.py`) 自動執行目錄重組
5. THE Memory_System SHALL 更新所有引用舊路徑的文檔（如 `DOCUMENT_INDEX.md`）
6. WHERE 文檔引用其他文檔的路徑，THE Memory_System SHALL 自動更新為新路徑
7. THE Memory_System SHALL 提供回滾機制，可恢復到重組前的狀態

### Requirement 5: 核心規則自動載入

**User Story:** 作為 AI Agent，我希望啟動時自動獲得所有核心規則，以便立即遵守專案規範，無需手動查詢。

#### Acceptance Criteria

1. THE Memory_System SHALL 定義核心規則清單於 `brains/core/.manifest.json`
2. THE Memory_System SHALL 確保 `brains/core/` 目錄下所有文檔總大小不超過 50KB
3. WHEN AI_Agent 請求核心規則時，THE Memory_System SHALL 回傳合併後的單一 Markdown 文檔
4. THE Memory_System SHALL 在合併文檔中保留原始文件的來源標記
5. THE Memory_System SHALL 提供 CLI 工具 (`scripts/load_core_rules.py`) 輸出核心規則內容
6. WHERE 核心規則文檔被更新，THE Memory_System SHALL 通知所有活躍的 AI_Agent 重新載入

### Requirement 6: 技術細節按需查詢

**User Story:** 作為 AI Agent，我希望在需要時快速查詢技術細節，以便獲取精確資訊而不浪費 token budget。

#### Acceptance Criteria

1. THE Index_Engine SHALL 支援自然語言查詢（如 "kiosk 收鈔流程"）
2. WHEN AI_Agent 提交查詢時，THE Index_Engine SHALL 回傳最相關的 3 個文檔摘要
3. THE Index_Engine SHALL 提供 "展開" 功能，可獲取完整文檔內容
4. THE Index_Engine SHALL 記錄查詢頻率，用於優化索引權重
5. WHERE 查詢結果為空，THE Index_Engine SHALL 建議相關關鍵字
6. THE Index_Engine SHALL 支援多關鍵字組合查詢（AND / OR 邏輯）

### Requirement 7: 內容重複檢測與合併

**User Story:** 作為知識庫維護者，我希望系統自動檢測重複內容，以便合併冗餘文檔，降低維護成本。

#### Acceptance Criteria

1. THE Content_Optimizer SHALL 使用文本相似度演算法（如 TF-IDF + Cosine Similarity）檢測重複內容
2. WHEN 兩個文檔相似度超過 70% 時，THE Content_Optimizer SHALL 標記為候選合併項目
3. THE Content_Optimizer SHALL 生成合併預覽，顯示合併後的文檔結構
4. THE Content_Optimizer SHALL 要求人工確認後才執行合併操作
5. THE Content_Optimizer SHALL 在合併後的文檔中註明來源文件
6. THE Content_Optimizer SHALL 將被合併的原始文件移至 `brains/.archive/`

### Requirement 8: 文檔拆分與模組化

**User Story:** 作為 AI Agent，我希望大型文檔被拆分為邏輯單元，以便只載入需要的部分，節省 token budget。

#### Acceptance Criteria

1. WHEN 文檔大小超過 10KB 時，THE Content_Optimizer SHALL 分析其章節結構
2. THE Content_Optimizer SHALL 根據 Markdown 標題層級（H2, H3）拆分文檔
3. THE Content_Optimizer SHALL 為拆分後的文檔生成目錄文件（如 `kiosk_flows/README.md`）
4. THE Content_Optimizer SHALL 確保拆分後的每個文檔包含必要的上下文（如 Glossary）
5. WHERE 文檔包含交叉引用，THE Content_Optimizer SHALL 自動更新引用路徑
6. THE Content_Optimizer SHALL 保留原始大型文檔於 `brains/.archive/`

### Requirement 9: 格式標準化

**User Story:** 作為知識庫維護者，我希望所有文檔遵循統一格式，以便提升可讀性與 AI 解析效率。

#### Acceptance Criteria

1. THE Content_Optimizer SHALL 強制執行以下格式規範：
   - 標題層級：H1 為文檔標題，H2 為主要章節，H3 為子章節
   - 列表格式：使用 `-` 作為無序列表標記，使用 `1.` 作為有序列表標記
   - 代碼區塊：必須指定語言標記（如 ```python）
   - 表格：使用標準 Markdown 表格語法
   - 連結：使用相對路徑引用專案內文檔
2. THE Content_Optimizer SHALL 自動修正不符合規範的格式
3. THE Content_Optimizer SHALL 生成格式檢查報告 (`brains/.reports/format_check.md`)
4. WHERE 文檔包含非標準格式無法自動修正，THE Content_Optimizer SHALL 標記為需人工處理
5. THE Content_Optimizer SHALL 提供 pre-commit hook 檢查新增文檔的格式

### Requirement 10: 過時內容清理

**User Story:** 作為知識庫維護者，我希望系統協助識別過時內容，以便保持知識庫的時效性與準確性。

#### Acceptance Criteria

1. THE Content_Optimizer SHALL 掃描文檔中的時間標記（如 "2026-04-24"）
2. WHEN 文檔超過 90 天未更新且包含 "TODO" 或 "待確認" 標記時，THE Content_Optimizer SHALL 標記為可能過時
3. THE Content_Optimizer SHALL 檢測文檔中提及的已棄用系統（如 `ali.tg25.win`）
4. THE Content_Optimizer SHALL 生成過時內容報告 (`brains/.reports/outdated_content.md`)
5. WHERE 文檔被標記為 "DEPRECATED"，THE Content_Optimizer SHALL 建議移至 `brains/.archive/`
6. THE Content_Optimizer SHALL 要求人工確認後才執行刪除或歸檔操作

### Requirement 11: 索引自動更新

**User Story:** 作為開發者，我希望索引系統自動追蹤文檔變更，以便索引始終保持最新狀態。

#### Acceptance Criteria

1. THE Index_Engine SHALL 使用檔案系統監控機制（如 `watchdog` 函式庫）追蹤 `brains/` 目錄變更
2. WHEN 文檔被新增、修改、刪除時，THE Index_Engine SHALL 在 5 秒內更新索引
3. THE Index_Engine SHALL 記錄索引更新日誌於 `brains/.index/update.log`
4. WHERE 索引更新失敗，THE Index_Engine SHALL 發送通知並記錄錯誤
5. THE Index_Engine SHALL 提供手動重建索引的 CLI 命令 (`python scripts/rebuild_index.py`)
6. THE Index_Engine SHALL 在系統啟動時驗證索引完整性，若不一致則自動重建

### Requirement 12: 查詢日誌與分析

**User Story:** 作為系統管理者，我希望記錄所有查詢行為，以便分析使用模式、優化索引權重、改善文檔組織。

#### Acceptance Criteria

1. THE Index_Engine SHALL 記錄每次查詢的以下資訊：
   - 查詢時間
   - 查詢關鍵字
   - 查詢來源（AI_Agent 名稱）
   - 回傳結果數量
   - 查詢耗時
2. THE Index_Engine SHALL 提供查詢統計報告 (`brains/.reports/query_stats.md`)，包含：
   - 最常查詢的關鍵字 TOP 10
   - 查詢頻率最高的文檔 TOP 10
   - 平均查詢耗時
   - 查詢失敗率
3. THE Index_Engine SHALL 根據查詢頻率調整索引權重
4. WHERE 某文檔查詢頻率高於閾值（每日 10 次），THE Index_Engine SHALL 建議將其加入 Core_Rules
5. THE Index_Engine SHALL 提供查詢日誌清理機制，保留最近 30 天的記錄

### Requirement 13: 遷移腳本與回滾機制

**User Story:** 作為系統管理者，我希望目錄重組過程可控且可逆，以便在出現問題時快速恢復。

#### Acceptance Criteria

1. THE Memory_System SHALL 提供遷移腳本 (`scripts/migrate_memory_structure.py`) 執行目錄重組
2. THE 遷移腳本 SHALL 在執行前創建完整備份於 `brains/.backup/`
3. THE 遷移腳本 SHALL 生成遷移報告 (`brains/.reports/migration_report.md`)，列出所有變更項目
4. THE 遷移腳本 SHALL 提供 `--dry-run` 選項，預覽變更而不實際執行
5. THE Memory_System SHALL 提供回滾腳本 (`scripts/rollback_migration.py`) 恢復到遷移前狀態
6. THE 回滾腳本 SHALL 驗證備份完整性後才執行恢復操作
7. WHERE 遷移過程中發生錯誤，THE 遷移腳本 SHALL 自動觸發回滾機制

### Requirement 14: 文檔引用更新

**User Story:** 作為開發者，我希望目錄重組後所有文檔引用自動更新，以便避免斷鏈與錯誤引用。

#### Acceptance Criteria

1. THE Memory_System SHALL 掃描所有文檔中的相對路徑引用（Markdown 連結格式）
2. WHEN 文檔被移動到新路徑時，THE Memory_System SHALL 自動更新所有引用該文檔的連結
3. THE Memory_System SHALL 檢測並修正斷鏈（404 引用）
4. THE Memory_System SHALL 生成引用更新報告 (`brains/.reports/reference_update.md`)
5. WHERE 引用無法自動更新（如外部連結），THE Memory_System SHALL 標記為需人工處理
6. THE Memory_System SHALL 提供引用驗證工具 (`scripts/validate_references.py`) 檢查所有連結有效性

### Requirement 15: CLI 工具整合

**User Story:** 作為開發者，我希望透過命令列工具操作記憶系統，以便整合到現有開發流程中。

#### Acceptance Criteria

1. THE Memory_System SHALL 提供統一的 CLI 入口 (`scripts/memory_cli.py`)
2. THE CLI 工具 SHALL 支援以下子命令：
   - `search <keyword>` - 搜尋文檔
   - `load-core` - 載入核心規則
   - `optimize` - 執行內容優化
   - `rebuild-index` - 重建索引
   - `migrate` - 執行目錄遷移
   - `rollback` - 回滾遷移
   - `stats` - 顯示查詢統計
   - `validate` - 驗證引用完整性
3. THE CLI 工具 SHALL 提供 `--help` 選項顯示使用說明
4. THE CLI 工具 SHALL 支援 `--verbose` 選項輸出詳細日誌
5. THE CLI 工具 SHALL 回傳標準退出碼（0 = 成功，非 0 = 失敗）
6. THE CLI 工具 SHALL 支援 JSON 格式輸出（`--format json`）供其他工具解析

## Summary

本需求文檔定義了 HQ 記憶系統優化的 15 個核心需求，涵蓋混合載入策略、激進內容優化、程式化索引機制、目錄重組等關鍵功能。系統將透過自動化工具提升知識庫的可用性、降低 AI Agent 的 token 消耗、改善內容組織結構，並提供完整的遷移與回滾機制確保系統穩定性。
