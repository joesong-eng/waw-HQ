# Member (win.tg25.win) 部署指南

## SSH 連線設定

### 伺服器資訊
- **HostName**: `129.146.0.47`
- **Port**: `39022`
- **User**: `ubuntu`
- **IdentityFile**: `~/.ssh/id_rsa`
- **別名**: `yd47` (Oracle 2G/16M member host)

### 連線指令
```bash
# 直接連線
ssh -p 39022 ubuntu@129.146.0.47

# 或使用 SSH config 別名（需在 ~/.ssh/config 設定）
ssh yd47
```

### SSH Config 設定範例
```
Host yd47
    HostName 129.146.0.47
    Port 39022
    User ubuntu
    IdentityFile ~/.ssh/id_rsa
```

---

## 部署流程

### 標準部署流程（無衝突情況）

```bash
ssh -p 39022 ubuntu@129.146.0.47 "cd /www/wwwroot/win.tg25.win && \
git pull origin main && \
pnpm install && pnpm build && \
php artisan migrate --force && \
php artisan view:clear && \
php artisan config:cache && \
php artisan cache:clear && \
sudo systemctl restart reverb"
```

### 分步驟說明

1. **代碼同步**
   ```bash
   cd /www/wwwroot/win.tg25.win
   git pull origin main
   ```

2. **前端依賴與建置**
   ```bash
   pnpm install    # 安裝/更新 Node.js 依賴
   pnpm build      # 建置前端資源（Vite）
   ```

3. **Laravel 維護指令**
   ```bash
   php artisan migrate --force      # 執行資料庫遷移（生產環境）
   php artisan view:clear           # 清除 Blade 模板快取（重要！）
   php artisan config:cache         # 快取設定檔
   php artisan cache:clear          # 清除應用程式快取
   ```

4. **重啟 WebSocket 服務**
   ```bash
   sudo systemctl restart reverb    # 重啟 Reverb WebSocket 服務
   sudo systemctl status reverb     # 檢查服務狀態
   ```

---

## 常見問題與處理

### 1. Git 衝突處理

#### 問題：本地有未提交的修改
```
error: Your local changes to the following files would be overwritten by merge:
Please commit your changes or stash them before you merge.
```

#### 解決方案 A：保留本地修改（推薦）
```bash
cd /www/wwwroot/win.tg25.win
git stash                    # 暫存本地修改
git pull origin main         # 拉取遠端更新
git stash pop                # 恢復本地修改
# 如有衝突，手動解決後：
git add .
git commit -m "merge: resolve conflicts"
```

#### 解決方案 B：放棄本地修改
```bash
cd /www/wwwroot/win.tg25.win
git reset --hard HEAD        # 放棄所有本地修改
git pull origin main         # 拉取遠端更新
```

#### 問題：分支分歧（divergent branches）
```
fatal: Need to specify how to reconcile divergent branches.
```

#### 解決方案：使用 rebase 或 merge
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

#### 解決方案：修復檔案所有權
```bash
cd /www/wwwroot/win.tg25.win
sudo chown -R ubuntu:ubuntu .     # 將所有檔案所有權改為 ubuntu
# 或
sudo chown -R www:www .           # 將所有檔案所有權改為 www（視需求）
```

#### 問題：Storage 和 Cache 權限
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

#### 解決方案：設定 Git 用戶資訊
```bash
cd /www/wwwroot/win.tg25.win
git config user.email "deploy@tg25.win"
git config user.name "Production Deploy"
```

---

### 4. Rebase 卡住處理

#### 問題：Interactive rebase in progress
```
interactive rebase in progress; onto xxxxx
```

#### 解決方案：中止 rebase
```bash
cd /www/wwwroot/win.tg25.win
git rebase --abort           # 中止 rebase
git reset --hard origin/main # 重置到遠端狀態
```

---

### 5. WebSocket 服務問題

#### 檢查 Reverb 服務狀態
```bash
sudo systemctl status reverb --no-pager
```

#### 重啟服務
```bash
sudo systemctl restart reverb
```

#### 查看服務日誌
```bash
sudo journalctl -u reverb -f
```

---

## 部署檢查清單

部署完成後，確認以下項目：

- [ ] Git 狀態乾淨（`git status` 無未提交修改）
- [ ] 前端資源已建置（`public/build/` 目錄有最新檔案）
- [ ] Blade 快取已清除（修改的 .blade.php 檔案生效）
- [ ] Config 快取已更新（.env 變更生效）
- [ ] Reverb 服務運行中（`systemctl status reverb` 顯示 active）
- [ ] 網站可正常訪問（https://win.tg25.win）
- [ ] WebSocket 連線正常（工程頁面顯示 Online）

---

## 緊急回滾

如果部署後發現問題，快速回滾到上一個版本：

```bash
cd /www/wwwroot/win.tg25.win
git log --oneline -5                    # 查看最近 5 個 commit
git reset --hard <previous-commit-hash> # 回滾到指定 commit
pnpm build                              # 重新建置前端
php artisan view:clear                  # 清除快取
php artisan config:cache
sudo systemctl restart reverb           # 重啟服務
```

---

## 相關文件

- **部署 SOP**: `_agent/workflows/deploy.md`
- **WebSocket 設定**: 見 deploy.md 中的 WebSocket 章節
- **Infra API 文件**: `docs/._apis.md`

---

*Last updated: 2026-05-07 by Mina AI*
*Reviewed and approved by HQ*
