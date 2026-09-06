# 04_deployment_operations — 部署與運維

## 文件清單

| 文件 | 核心內容 | 查閱時機 |
|------|---------|---------|
| `INFRASTRUCTURE_REFERENCE.md` | SSH 別名表、DB 架構、Nginx 配置、服務管理 | 需要 SSH 或查 DB 時（**先查這裡**） |
| `DEPLOYMENT_GUIDE.md` | 各專案部署指令、Git 衝突處理、緊急回滾 | 需要部署任何專案時 |
| `V9_OPS_AUTOMATION.md` | MCP 工具使用（v9_deploy_project 等） | 使用 MCP 工具部署時 |

## 快速索引

| 需求 | 文件 |
|------|------|
| SSH 到任何伺服器 | `INFRASTRUCTURE_REFERENCE.md`（SSH 別名表） |
| 查詢資料庫 | `INFRASTRUCTURE_REFERENCE.md`（DB 架構） |
| 部署 Member / Owner / Alliance | `DEPLOYMENT_GUIDE.md` |
| 部署 iHub | `DEPLOYMENT_GUIDE.md`（注意：改完 src 必須 npm run build） |
| 部署 Infra | `DEPLOYMENT_GUIDE.md` |
| 緊急回滾 | `DEPLOYMENT_GUIDE.md` |
| 使用 MCP 一鍵部署 | `V9_OPS_AUTOMATION.md` |
