---
inclusion: always
---

# Workspace 常識

HQ workspace 的環境事實與操作常識。

---

## 按需參考文件（用到時才查）

**遇到以下情況，可按需查閱對應文件（不需要每次啟動都讀）：**

| 情況 | 必查文件 |
|------|---------|
| 需要 SSH 到任何伺服器 | `brains/knowledge/04_ops_and_deployments/INFRASTRUCTURE_REFERENCE.md`（SSH 別名表） |
| 需要知道某個專案在哪台伺服器（Owner/Member/Alliance/Infra/iHub） | `brains/knowledge/04_ops_and_deployments/INFRASTRUCTURE_REFERENCE.md`（SSH 別名速查表） |
| 需要查詢資料庫 | `brains/knowledge/04_ops_and_deployments/INFRASTRUCTURE_REFERENCE.md`（DB 架構） |
| 需要部署任何專案 | `brains/knowledge/04_ops_and_deployments/DEPLOYMENT_GUIDE.md` |
| 需要確認任何名稱的正確寫法 | `brains/knowledge/NAMING_AUTHORITY.md` |
| 需要發 MQTT 指令或解讀 MQTT 訊息 | `brains/knowledge/02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` |
| 需要用 WebSocket 頻道或事件名稱 | `brains/knowledge/02_protocols_and_standards/WEBSOCKET_CHANNEL_STANDARD.md` |
| 需要了解識別碼（chip_id / node_id） | `brains/knowledge/NAMING_AUTHORITY.md` |
| 需要發任務給 Agent | `brains/knowledge/01_agent_governance/MESSAGE_HUB_PROTOCOL.md` |
| 需要了解業務流程（kiosk 兌幣） | `brains/knowledge/05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` |
| 需要了解業務流程（遊戲機開分） | `brains/knowledge/05_product_and_business_flows/game_v0_arcade/GAME_V3_CORE_SPECIFICATION.md` |

---

## 各專案伺服器速查（固定，不需要查文件）

| 專案 | 網域 | SSH 別名 | 專案路徑 |
|------|------|---------|---------|
| Member | `win.tg25.win` | `yd47` | `/www/wwwroot/win.tg25.win` |
| iHub | `ihub.tg25.win` | `yd47` | `/www/wwwroot/ihub.tg25.win` |
| Owner | `iot.tg25.win` | `yd174` | `/www/wwwroot/iot.tg25.win/wawv9` |
| Infra | `api.tg25.win` | `infra` | `/home/ubuntu/tg25-infra` |
| Alliance | `ali.tg25.win` | `yd16` | `/www/wwwroot/ali.tg25.win` |

**嚴禁試錯**：不知道專案在哪台伺服器時，直接查上表，不得猜測或逐台 SSH 嘗試。

---

## 固定事實（不需要查文件）

- `pubdocs/` 是 symlink，實際路徑：`/Users/ilawusong/Documents/sysWawIot/pubdocs`
- HQ workspace 只能讀寫 `/Users/ilawusong/Documents/sysWawIot/HQ/`，其他專案路徑用 `execute_bash` 讀取
- 所有 SSH 必須用別名（`yd47`、`infra`、`yd174`、`yd16`、`PM`），不得用完整 IP
- 所有 DB 實體在 `infra`（`141.148.165.50`），查 DB 透過各專案的 `artisan tinker`
