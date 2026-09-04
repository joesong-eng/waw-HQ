# WaW 專案環境與部署配置

**文件版本**: v1.0  
**最後更新**: 2026-09-01  
**維護者**: HQ

---

## 📂 專案根目錄

```
/Users/ilawusong/Documents/WaW
```

---

## 🌐 伺服器與部署配置

### 伺服器別名對照表

| 別名 | 主機 IP | 用途 | 面板 |
|------|---------|------|------|
| yd174, v9, Owner, blc | 129.153.116.174:39022 | Owner + SignalHub | 寶塔面板 |
| yd177, yd47, ihub, mina | 129.146.103.177:39022 | Member + iHub | 寶塔面板 |
| yd16, alliance | 137.131.50.16:39022 | Alliance | 寶塔面板 |
| infra, db | 141.148.165.50:39022 | MySQL + Infra 服務 | 標準 Linux |
| bessie202, HQ, PM, HQconter | 132.226.87.202:39022 | HQ 總部 | 標準 Linux |

### SSH 配置位置

```
/Users/ilawusong/.ssh/config
```

所有伺服器使用：
- User: ubuntu
- IdentityFile: ~/.ssh/id_rsa
- Port: 39022 (除特殊標註)

---

## 📦 Agent 專案部署對照表

| Agent | 別名 | 伺服器 | 部署路徑 | 類型 | 域名 | 服務 |
|-------|------|--------|----------|------|------|------|
| **Sophie** | owner | yd174 | /www/wwwroot/iot.tg25.win | Laravel | iot.tg25.win | - |
| **Mina** | member | yd177 | /www/wwwroot/win.tg25.win | Laravel | win.tg25.win | reverb |
| **Allie** | alliance | yd16 | /www/wwwroot/ali.tg25.win | Laravel | ali.tg25.win | - |
| **Hubie** | ihub | yd177 | /www/wwwroot/ihub.tg25.win | Node.js | ihub.tg25.win | - |
| **Sidney** | signalhub, signal | yd174 | /www/wwwroot/signal.tg25.win | Laravel | signal.tg25.win | - |
| **Ina** | infra | infra | /home/ubuntu/tg25-infra | Python | - | mqtt-listener |
| **Fio** | kiosk, iotkiosk_v0 | - | - | - | - | - |
| **Coli** | waws3, iotwaws3 | - | - | - | - | - |

---

---

**本文件位置**: `brains/knowledge/ENVIRONMENT.md`  
**讀取方式**: 各專案透過 `knowledge/` symlink 讀取  
**維護者**: HQ（Agent 只讀）

---

## 🏗️ 本地專案目錄結構

\`\`\`
/Users/ilawusong/Documents/WaW/
├── PROJECT/
│   ├── Owner/              # Sophie - IOTv9 Owner 專案
│   ├── Member/             # Mina - Member 專案
│   ├── Alliance/           # Allie - Alliance 專案
│   ├── iHub/               # Hubie - iHub 專案
│   ├── SignalHub/          # Sidney - SignalHub 專案
│   ├── Infra/              # Ina - Infra 服務
│   ├── IOTkiosk_v0/        # Fio - Kiosk 專案
│   └── IOTwawS3/           # Coli - WaW S3 專案
├── brains/
│   └── knowledge/          # HQ 知識庫 (僅 HQ 寫入)
│       ├── 01_agent_governance/
│       ├── 02_technical_standards/
│       ├── 03_system_architecture/
│       ├── 04_deployment_operations/
│       ├── 05_business_flows/
│       └── ENVIRONMENT.md  # 本文件 ⭐
├── .taskflow/              # Taskflow 派工系統
└── dev_tools/              # 開發運維工具
\`\`\`

**各專案讀取方式**:
- 各專案目錄都有 \`knowledge/\` symlink → \`../../brains/knowledge/\`
- 因此可透過 \`knowledge/ENVIRONMENT.md\` 讀取本文件
- 例如: \`PROJECT/Owner/knowledge/ENVIRONMENT.md\` 實際讀取 \`brains/knowledge/ENVIRONMENT.md\`

**HQ 負責維護知識庫**，Agent 只能讀取。

---

---

## 🔧 寶塔面板部署結構

### 標準目錄結構

```
/www/
├── wwwroot/                # 網站根目錄 ⭐
│   ├── iot.tg25.win/       # Owner (yd174)
│   ├── signal.tg25.win/    # SignalHub (yd174)
│   ├── win.tg25.win/       # Member (yd177)
│   ├── ihub.tg25.win/      # iHub (yd177)
│   └── ali.tg25.win/       # Alliance (yd16)
├── server/
│   ├── nginx/              # Nginx 配置
│   ├── php/                # PHP 版本
│   ├── mysql/              # MySQL 資料庫
│   └── panel/              # 寶塔面板
│       └── vhost/nginx/    # 虛擬主機配置
├── backup/                 # 備份目錄
└── wwwlogs/                # 網站日誌
```

### 重要路徑

- **網站根目錄**: `/www/wwwroot/<domain>/`
- **Nginx 配置**: `/www/server/panel/vhost/nginx/*.conf`
- **PHP**: `/www/server/php/`
- **日誌**: `/www/wwwlogs/<domain>/`

---

## 🚀 標準部署流程

### Laravel 專案 (Owner, Member, Alliance, SignalHub)

```bash
cd /www/wwwroot/<domain>
git pull origin main
pnpm install                    # 若有前端資源
pnpm build                      # 若有前端資源
php artisan migrate --force
php artisan view:clear
php artisan config:cache
php artisan cache:clear
# 若有服務: sudo systemctl restart <service>
```

**使用 waw_ops.sh**:
```bash
./dev_tools/waw_ops.sh deploy owner
./dev_tools/waw_ops.sh deploy mina
./dev_tools/waw_ops.sh deploy signalhub
```

### Node.js 專案 (iHub)

```bash
cd /www/wwwroot/<domain>
git pull origin main
npm install
npm run build
```

### Python 專案 (Infra)

```bash
cd /home/ubuntu/tg25-infra
git pull origin main
pip install -r requirements.txt
sudo systemctl restart mqtt-listener
```

---

## 🛠️ 開發工具

### waw_ops.sh 總控腳本

```bash
# 位置
./dev_tools/waw_ops.sh

# 功能
task <agent> <task_id> "<描述>" [priority]  # 派工
status                                       # 查看狀態
report <agent>                              # 讀取回報
deploy <agent>                              # 部署專案
remote <server> "<command>"                 # 遠端執行
```

### Agent 別名對照

| 輸入 | 對應 Module |
|------|-------------|
| sophie, owner | owner |
| mina, member | member |
| ina, infra | infra |
| allie, alliance | alliance |
| hubie, ihub | ihub |
| fio, kiosk, iotkiosk_v0 | fio |
| coli, waws3, iotwaws3 | coli |
| signalhub, signalhub, signal | signalhub |

---

## 📝 Taskflow 派工系統

```
.taskflow/
├── owner/inbox/       # Sophie 收件箱
├── owner/outbox/      # Sophie 回報
├── member/inbox/      # Mina 收件箱
├── member/outbox/     # Mina 回報
├── infra/inbox/       # Ina 收件箱
├── infra/outbox/      # Ina 回報
├── alliance/inbox/    # Allie 收件箱
├── alliance/outbox/   # Allie 回報
├── ihub/inbox/        # Hubie 收件箱
├── ihub/outbox/       # Hubie 回報
├── fio/inbox/         # Fio 收件箱
├── fio/outbox/        # Fio 回報
├── coli/inbox/        # Coli 收件箱
├── coli/outbox/       # Coli 回報
├── signalhub/inbox/      # Sidney 收件箱
├── signalhub/outbox/     # Sidney 回報
├── archive/           # 封存區
└── task_flow.log      # 派工日誌
```

---

## 🔐 權限與用戶

### 寶塔面板伺服器
- **SSH 用戶**: ubuntu
- **Web 用戶**: www
- **Web 組**: www
- **PHP-FPM**: 以 www 用戶運行

### 檔案權限
```bash
# Laravel storage 和 bootstrap/cache
chown -R www:www storage bootstrap/cache
chmod -R 775 storage bootstrap/cache
```

---

## 📚 相關文件

- **派工協議**: `brains/knowledge/01_agent_governance/SIMPLE_FILE_DISPATCH_PROTOCOL.md`
- **啟動協議**: `brains/knowledge/01_agent_governance/AGENT_STARTUP_PROTOCOL.md`
- **MQTT 規範**: `brains/knowledge/02_technical_standards/MQTT_TOPIC_STANDARD.md`
- **SSH 配置**: `/Users/ilawusong/.ssh/config`

---

## ⚠️ 重要注意事項

1. **本地機器僅用於代碼和 Git 操作**
   - ❌ 不在本地運行 `pnpm run build`
   - ❌ 不在本地運行 Composer/Artisan
   - ❌ 不在本地啟動 PHP/Web 伺服器
   - ✅ 所有運行時操作在遠端 VPS 執行

2. **使用 waw_ops.sh 進行遠端操作**
   - 標準化部署流程
   - 統一的遠端命令執行
   - 自動化錯誤處理

3. **寶塔面板路徑**
   - Web 專案部署在 `/www/wwwroot/`
   - 不是 `/var/www/`

4. **Git 分支**
   - 所有專案統一使用 `main` 分支

---

**維護說明**: 此文件應隨著專案環境變更及時更新。任何新增伺服器、域名、部署路徑的變更都應記錄於此。

