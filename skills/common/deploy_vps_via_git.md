# 🚀 技能：Git 協定遠端部署與安全限制 (Git Push & Pull Deploy SOP)

> **適用對象**：全系統 AI Agent (Ina / Sophie / Mina / Allie / Hubie 等)
> **目的**：標準化「本地提交 -> Github -> VPS 拉取」的部署割接流程，禁止任何 Agent 私自直接推送或在生產環境執行未授權變更。

---

## 🛑 安全防線與禁制令

1. **嚴禁私自推送**：
   - 除非任務描述（Task JSON）中明確指示「請將變更提交並推送至 GitHub 進行割接」，否則 **禁止任何 Agent 主動執行 `git commit`、`git push` 或 `deploy_vps.sh` 等部署命令**。
2. **防線引導與導流**：
   - 當 Agent 完成修改且「沒有明確部署授權」時，應在任務回報（Report）中**標記狀態為 `needs_review`**。
   - 回報摘要中，必須明確附上此部署 SOP 的連結與建議執行命令，引導 Joe（人類管理員）進行確認與手動推送。

---

## 🛠️ 標準複用部署指令集 (IP 與路徑替換版)

### 本地端 (開發主機)
完成代碼修改與本地測試後，**由 Joe 或被明確授權的 Agent** 執行：

```bash
# 1. 進入對應的本地專案目錄
cd {LOCAL_PROJECT_PATH}

# 2. 本地 Git 提交與推送
git add .
git commit -m "{TAG}: {DESCRIPTION}"
git push origin {BRANCH}
```

### 伺服器端 (遠端 VPS)
透過 SSH 連線至對應 VPS 執行拉取與重置：

```bash
# 3. 連線至遠端 VPS 並拉取代碼 (根據主機別名與專案路徑替換)
ssh {SSH_ALIAS} "cd {VPS_PROJECT_PATH} && git fetch origin {BRANCH} && git reset --hard origin/{BRANCH}"
```

#### 📌 各專案替換對照表

| 專案 | 本地路徑 `{LOCAL_PROJECT_PATH}` | 主機別名 `{SSH_ALIAS}` | 遠端路徑 `{VPS_PROJECT_PATH}` | 主分支 `{BRANCH}` |
| :--- | :--- | :--- | :--- | :--- |
| **Ina (Infra)** | `tg25-infra` | `infra` | `/home/ubuntu/tg25-infra` | `main` |
| **Sophie (Owner/Business)** | `waw-business` | `yd174` | `/www/wwwroot/iot.tg25.win/wawv9` | `main` |
| **Mina (Member)** | `Member` | `yd47` | `/www/wwwroot/win.tg25.win` | `main` |
| **Allie (Alliance)** | `Alliance` | `yd16` | `/www/wwwroot/ali.tg25.win` | `main` |
| **Hubie (iHub)** | `iHub` | `yd47` | `/www/wwwroot/ihub.tg25.win` | `main` |

---

## 🔄 服務重啟與編譯 (部署後處理)

根據更動的代碼類型，在拉取後視需要於伺服器端附加執行以下指令：

- **Laravel 專案**（Member / Business）：
  ```bash
  ssh {SSH_ALIAS} "cd {VPS_PROJECT_PATH} && php artisan optimize:clear"
  ```
- **前端變更**（Tailwind / Alpine.js）：
  ```bash
  ssh {SSH_ALIAS} "cd {VPS_PROJECT_PATH} && pnpm install && pnpm run build"
  ```
- **Infra Python 服務**（mqtt-listener / credit-api）：
  ```bash
  ssh {SSH_ALIAS} "sudo systemctl restart {SERVICE_NAME}"
  ```
- **iHub 專案**（WebView 內容）：
  ```bash
  ssh {SSH_ALIAS} "cd {VPS_PROJECT_PATH} && npm install && npm run build"
  ```

---

## 🔗 文件神經連結

### 強關聯（必讀）
> 修改或參考本部署技能前，必須先閱讀以下文件

- `brains/knowledge/04_ops_and_deployments/DEPLOYMENT_GUIDE.md` - 遠端 VPS 部署與割接指南
- `brains/knowledge/04_ops_and_deployments/INFRASTRUCTURE_REFERENCE.md` - 基礎設施別名與資料庫快速參考
- `brains/knowledge/DOCUMENT_INDEX.md` - 知識庫總索引檔案

### 中關聯（建議讀）
> 深入了解 Agent 的職責與通訊流程，建議閱讀

- `brains/knowledge/01_agent_governance/MESSAGE_HUB_PROTOCOL.md` - 任務派發與 Pub/Sub 協議
- `brains/knowledge/01_agent_governance_rules/AGENT_RESPONSIBILITY_BOUNDARIES.md` - Agent 職責邊界限制
