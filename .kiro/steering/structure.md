---
inclusion: always
---

# HQ Workspace 目錄結構

```
HQ/
├── .agent/workflows/          # 工作流程定義（deploy.md）
├── .kiro/
│   ├── steering/              # AI 引導文件（本目錄）
│   └── specs/                 # 功能規格文件
├── brains/
│   ├── knowledge/             # 知識庫（HQ 唯一寫入權）
│   │   ├── 01_agent_governance/   # Agent 協作規範
│   │   ├── 02_technical_standards/ # MQTT、WebSocket 技術標準
│   │   ├── 03_system_architecture/ # 系統架構
│   │   ├── 04_deployment_operations/ # 部署與基礎設施
│   │   ├── 05_business_flows/     # 業務流程（按域分目錄）
│   │   │   ├── kiosk_v0/          # IOTkiosk_v0 業務域
│   │   │   └── game_v0/           # IOTwawS3 業務域
│   │   ├── 06_deprecated/         # 已廢棄文件
│   │   ├── NAMING_AUTHORITY.md    # 名稱定義來源索引
│   │   └── kiosk_identification_system.md  # 識別碼體系
│   ├── history/               # 事件記錄、教訓、incident
│   └── memory/                # 持久化記憶
├── Temps/                     # 臨時文件、草稿
├── archive/                   # 已完成任務歸檔
├── pubdocs -> ../pubdocs      # symlink，跨 workspace 共享文件
├── README.md
└── TODO.md
```

## 各目錄用途速查

| 目錄 | 用途 |
|------|------|
| `brains/knowledge/` | 設計文件、技術標準、業務流程（唯一真理） |
| `brains/history/` | INCIDENT_、LESSON_、TASK_ 記錄 |
| `.kiro/specs/` | 功能規格（requirements / design / tasks） |
| `Temps/` | 草稿、臨時 HTML、討論用文件 |
| `pubdocs/` | 跨 workspace 共享（識別碼規格、協議文件） |
