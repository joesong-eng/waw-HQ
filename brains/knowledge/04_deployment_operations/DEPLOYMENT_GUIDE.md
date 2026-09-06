# V9 部署指南 (Deployment Guide)

> **版本**: 2.0  
> **最後更新**: 2026-05-08  
> **適用範圍**: 所有 V9 專案 (Alliance, Member, Owner, Infra, iHub)

---

## 📋 目錄

1. [伺服器資訊](#伺服器資訊)
2. [部署流程](#部署流程)
3. [常見問題處理](#常見問題處理)
4. [部署檢查清單](#部署檢查清單)
5. [緊急回滾](#緊急回滾)

---

## 伺服器資訊

### Member VPS (win.tg25.win)
- **HostName**: `129.146.103.177`
- **Port**: `39022`
- **User**: `ubuntu`
- **別名**: `yd47` (Oracle 2G/16M)
- **專案路徑**: `/www/wwwroot/win.tg25.win`
- **服務**: Reverb WebSocket

**連線指令**:
```bash
ssh yd47
# 或使用別名
ssh yd47
```

---

### Infra VPS (api.tg25.win)
- **HostName**: `141.148.165.50`
- **Port**: `39022`
- **User**: `ubuntu`
- **別名**: `infra`
- **專案路徑**: `/home/ubuntu/tg25-infra`
- **服務**: MQTT Listener, API

**連線指令**:
```bash
ssh infra
# 或使用別名
ssh infra
```

---

### Owner VPS (iot.tg25.win)
- **HostName**: `129.153.116.174`
- **Port**: `39022`
- **User**: `ubuntu`
- **別名**: `yd174`
- **專案路徑**: `/www/wwwroot/iot.tg25.win`
- **服務**: Owner 後台

**連線指令**:
```bash
ssh yd174
# 或使用別名
ssh yd174
```

---

### Alliance VPS (ali.tg25.win)
- **HostName**: `137.131.50.16`
- **Port**: `39022`
- **User**: `ubuntu`
- **專案路徑**: `/www/wwwroot/ali.tg25.win`
- **服務**: Alliance 後台

**連線指令**:
```bash
ssh yd16
```

---

### iHub VPS (ihub.tg25.win)
- **HostName**: `129.146.103.177` (與 Member 同機)
- **Port**: `39022`
- **User**: `ubuntu`
- **別名**: `ihub`
- **專案路徑**: `/www/wwwroot/ihub.tg25.win`
- **服務**: iHub Android APK

**連線指令**:
```bash
ssh yd47
# 或使用別名
ssh ihub
```

---

### SSH Config 設定範例

在 `~/.ssh/config` 加入：

```
Host yd47
    HostName 129.146.103.177
    Port 39022
    User ubuntu
    IdentityFile ~/.ssh/id_rsa

Host infra
    HostName 141.148.165.50
    Port 39022
    User ubuntu
    IdentityFile ~/.ssh/id_rsa

Host yd174
    HostName 129.153.116.174
    Port 39022
    User ubuntu
    IdentityFile ~/.ssh/id_rsa
```

---

## 部署流程

### Laravel 專案部署 (Member, Owner, Alliance)

#### 標準部署流程（無衝突情況）

```bash
ssh -p 39022 ubuntu@<HOST> "cd <PROJECT_PATH> && \
git pull origin main && \
pnpm install && pnpm build && \
php artisan migrate --force && \
php artisan view:clear && \
php artisan config:cache && \
php artisan cache:clear && \
sudo systemctl restart reverb"
```

#### 分步驟說明

**1. 代碼同步**
```bash
cd <PROJECT_PATH>
git pull origin main
```

**2. 前端依賴與建置**
```bash
pnpm install    # 安裝/更新 Node.js 依賴
pnpm build      # 建置前端資源（Vite）
```

**3. Laravel 維護指令**
```bash
php artisan migrate --force      # 執行資料庫遷移（生產環境）
php artisan view:clear           # 清除 Blade 模板快取（重要！）
php artisan config:cache         # 快取設定檔
php artisan cache:clear          # 清除應用程式快取
```

**4. 重啟服務**
```bash
# Member 專案（有 Reverb WebSocket）
sudo systemctl restart reverb
sudo systemctl status reverb

# Owner/Alliance 專案（無額外服務）
# 只需清除快取即可
```

---

### Infra 專案部署

```bash
ssh infra "cd /home/ubuntu/tg25-infra && \
git pull origin main && \
pip install -r requirements.txt && \
sudo systemctl restart mqtt-listener"
```

**分步驟說明**:

**1. 代碼同步**
```bash
cd /home/ubuntu/tg25-infra
git pull origin main
```

**2. Python 依賴**
```bash
pip install -r requirements.txt
```

**3. 重啟服務**
```bash
sudo systemctl restart mqtt-listener
sudo systemctl status mqtt-listener
```

---

### iHub 專案部署

```bash
ssh yd47 "cd /www/wwwroot/ihub.tg25.win && \
git pull origin main && \
npm install && npm run build"
```

**分步驟說明**:

**1. 代碼同步**
```bash
cd /www/wwwroot/ihub.tg25.win
git pull origin main
```

**2. 前端建置**
```bash
npm install
npm run build
```

---

## 常見問題處理

### 1. Git 衝突處理

#### 問題：本地有未提交的修改
```
error: Your local changes to the following files would be overwritten by merge:
Please commit your changes or stash them before you merge.
```

**解決方案 A：保留本地修改（推薦）**
```bash
cd <PROJECT_PATH>
git stash                    # 暫存本地修改
git pull origin main         # 拉取遠端更新
git stash pop                # 恢復本地修改
# 如有衝突，手動解決後：
git add .
git commit -m "merge: resolve conflicts"
```

**解決方案 B：放棄本地修改**
```bash
cd <PROJECT_PATH>
git reset --hard HEAD        # 放棄所有本地修改
git pull origin main         # 拉取遠端更新
```

---

#### 問題：分支分歧（divergent branches）
```
fatal: Need to specify how to reconcile divergent branches.
```

**解決方案**:
```bash
# 方案 1: Rebase（推薦，保持線性歷史）
git pull --rebase origin main

# 方案 2: Merge（產生合併 commit）
git pull --no-rebase origin main
```

---

### 2. 權限問題處理

#### 問題：Permission denied
```
rm: cannot remove 'file': Permission denied
error: unable to create file: Permission denied
```

**解決方案：修復檔案所有權**
```bash
cd <PROJECT_PATH>
sudo chown -R ubuntu:ubuntu .     # 將所有檔案所有權改為 ubuntu
# 或
sudo chown -R www:www .           # 將所有檔案所有權改為 www（視需求）
```

**Laravel Storage 和 Cache 權限**:
```bash
sudo chown -R www:www storage bootstrap/cache
sudo chmod -R 775 storage bootstrap/cache
```

---

### 3. Git 設定問題

#### 問題：Author identity unknown
```
fatal: unable to auto-detect email address
```

**解決方案：設定 Git 用戶資訊**
```bash
cd <PROJECT_PATH>
git config user.email "deploy@tg25.win"
git config user.name "Production Deploy"
```

---

### 4. Rebase 卡住處理

#### 問題：Interactive rebase in progress
```
interactive rebase in progress; onto xxxxx
```

**解決方案：中止 rebase**
```bash
cd <PROJECT_PATH>
git rebase --abort           # 中止 rebase
git reset --hard origin/main # 重置到遠端狀態
```

---

### 5. 服務問題處理

#### Reverb WebSocket 服務（Member）

**檢查狀態**:
```bash
sudo systemctl status reverb --no-pager
```

**重啟服務**:
```bash
sudo systemctl restart reverb
```

**查看日誌**:
```bash
sudo journalctl -u reverb -f
```

---

#### MQTT Listener 服務（Infra）

**檢查狀態**:
```bash
sudo systemctl status mqtt-listener --no-pager
```

**重啟服務**:
```bash
sudo systemctl restart mqtt-listener
```

**查看日誌**:
```bash
sudo journalctl -u mqtt-listener -f
```

---

## 部署檢查清單

### Laravel 專案（Member, Owner, Alliance）

部署完成後，確認以下項目：

- [ ] Git 狀態乾淨（`git status` 無未提交修改）
- [ ] 前端資源已建置（`public/build/` 目錄有最新檔案）
- [ ] Blade 快取已清除（修改的 .blade.php 檔案生效）
- [ ] Config 快取已更新（.env 變更生效）
- [ ] 服務運行中（如 Reverb）
- [ ] 網站可正常訪問
- [ ] WebSocket 連線正常（如適用）

---

### Infra 專案

- [ ] Git 狀態乾淨
- [ ] Python 依賴已安裝
- [ ] MQTT Listener 服務運行中
- [ ] MQTT 連線正常
- [ ] API 可正常訪問

---

### iHub 專案

- [ ] Git 狀態乾淨
- [ ] 前端資源已建置
- [ ] APK 可正常下載
- [ ] 網站可正常訪問

---

## 緊急回滾

如果部署後發現問題，快速回滾到上一個版本：

### Laravel 專案

```bash
cd <PROJECT_PATH>
git log --oneline -5                    # 查看最近 5 個 commit
git reset --hard <previous-commit-hash> # 回滾到指定 commit
pnpm build                              # 重新建置前端
php artisan view:clear                  # 清除快取
php artisan config:cache
sudo systemctl restart reverb           # 重啟服務（如適用）
```

---

### Infra 專案

```bash
cd /home/ubuntu/tg25-infra
git log --oneline -5
git reset --hard <previous-commit-hash>
pip install -r requirements.txt
sudo systemctl restart mqtt-listener
```

---

### iHub 專案

```bash
cd /www/wwwroot/ihub.tg25.win
git log --oneline -5
git reset --hard <previous-commit-hash>
npm install
npm run build
```

---

## 📚 相關文檔

- `INFRASTRUCTURE_REFERENCE.md` - 基礎設施快速參考
- `V9_OPS_AUTOMATION.md` - V9 自動化運維工具
- `../01_agent_governance/TASK_ROUTING_AND_COMPLETION.md` - 任務完成標準

---

**制定者**: HQ  
**最後更新**: 2026-05-08  
**版本**: 2.0

---

## 🔗 文件神經連結

### 強關聯（必讀）
> 執行部署前，必須先閱讀以下文件

- `INFRASTRUCTURE_REFERENCE.md` - 基礎設施快速參考，SSH 別名、DB 架構、服務管理
- `../NAMING_AUTHORITY.md` - 名稱定義來源索引，確保使用正確的專案名稱

### 中關聯（建議讀）
> 了解完整部署流程，建議閱讀

- `V9_OPS_AUTOMATION.md` - V9 自動化運維工具，一鍵部署指令
- `../01_agent_governance/TASK_ROUTING_AND_COMPLETION.md` - 任務完成標準，部署後驗證規範
- `../02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - MQTT 主題規範，Infra 部署相關

### 弱關聯（參考）
> 可選閱讀，提供額外背景

- `../05_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` - 識別碼體系，理解系統架構
- `../02_technical_standards/WEBSOCKET_CHANNEL_STANDARD.md` - WebSocket 頻道規範，Member Reverb 部署相關

### 排除混淆
> 容易混淆但實際無關的文件

- `../05_business_flows/game_v0_arcade/qrcode_url_unification_plan.md` - QR Code 統一計劃，與部署流程無直接關係（但部署後需驗證 QR Code 功能）
