# HQ 知識庫

> **只有 HQ 可寫入。Agent 如需更新，透過 HQ Message Hub 向 HQ 提交，由 HQ 審核後寫入。**

---

## 目錄結構

```
brains/knowledge/
├── 01_agent_governance/     # Agent 協作規範（執行、職責、任務路由）
├── 01_agent_governance/     # HQ Message Hub 系統文件
├── 02_technical_standards/  # 技術標準（MQTT、WebSocket、硬體脈衝）
├── 03_system_architecture/  # 系統架構（文件已移至業務域目錄）
├── 04_deployment_operations/ # 部署與基礎設施
├── 05_business_flows/       # 業務流程（按域分目錄）
│   ├── kiosk_v0_exchange/            # IOTkiosk_v0 業務域
│   └── game_v0_arcade/             # IOTwawS3 業務域
├── 06_deprecated/           # 已棄用文件
├── DOCUMENT_INDEX.md        # 完整文件清單
├── NAMING_AUTHORITY.md      # 名稱定義來源索引
└── NEURAL_LINKS_PROGRESS.md # 文件神經連結建置進度
```

## 核心規則

- 兩種韌體主題不可混淆：`kiosk/{chip_id}/`（kiosk_v0）vs `device/{chip_id}/`（game_v0）
- 發任務前三確認：資料來源、通訊主題、系統邊界
- 完整文件清單見 `DOCUMENT_INDEX.md`

---

## 🆕 最新更新 (2026-08-19)

### 系統架構文檔
- **[WAW Core System Assessment](./03_system_architecture/WAW_CORE_SYSTEM_ASSESSMENT.md)**
  - Laravel 11 IoT 平台完整評估
  - 基於代碼分析，非 .env.example
  - 包含架構、API、業務流程、技術債

### 評估方法論
- ✅ 從代碼與 config 檔案分析
- ✅ 明確標註需從生產環境確認的項目
- ✅ 整合知識庫既有文檔
- ❌ 不依賴 .env.example 評估生產環境

