# 本機開發環境限制規範

> **版本**: 1.0.0  
> **建立日期**: 2026-08-16  
> **狀態**: Active / Authoritative  
> **維護者**: HQ  
> **適用對象**: 所有 Agent (Sophie, Mina, Ina, Allie, Hubie, Fio, Coli)

---

## 📋 核心規範

### ❌ 禁止在本機執行的操作

本機開發環境 **不具備完整的 Laravel 專案依賴** (無 vendor/)，因此禁止以下操作：

#### 1. 禁止本機測試或執行

- ❌ **禁止執行 `php artisan` 命令**
- ❌ **禁止執行 `composer install/update`**
- ❌ **禁止執行 `php artisan test`**
- ❌ **禁止執行 `php artisan serve`**
- ❌ **禁止執行任何需要 vendor/ 的 PHP 腳本**

#### 2. 禁止假設本機環境

- ❌ **禁止假設本機有完整的開發環境**
- ❌ **禁止建議在本機執行測試**
- ❌ **禁止提供本機測試指令**

---

## ✅ 正確的開發與測試流程

### 開發流程

1. **本機編輯**：在本機編輯程式碼、配置檔案
2. **Git 提交**：提交變更到 Git
3. **部署到 VPS**：透過部署腳本或 SSH 部署到對應 VPS
4. **VPS 測試**：在 VPS 上執行測試和驗證

### 測試方式

| 測試類型 | 執行位置 | 方式 |
|---------|---------|------|
| 語法檢查 | 本機 | IDE/編輯器內建檢查 |
| 單元測試 | VPS | `ssh <vps> "cd <path> && php artisan test"` |
| 功能測試 | VPS | 透過瀏覽器或 API 測試工具 |
| 整合測試 | VPS | 完整部署後端對端測試 |

---

## 📝 Agent 行為規範

### 當需要測試時

**錯誤做法**：
```bash
# ❌ 本機執行
cd /Users/ilawusong/Documents/WaW/PROJECT/Owner
php artisan test
```

**正確做法**：
```bash
# ✅ 遠端執行
ssh yd174 "cd /www/wwwroot/iot.tg25.win && php artisan test --filter=DeviceTest"
```

### 當需要驗證語法時

**錯誤做法**：
```bash
# ❌ 需要 vendor/
php artisan tinker
```

**正確做法**：
```bash
# ✅ 遠端驗證
ssh yd174 "cd /www/wwwroot/iot.tg25.win && php artisan tinker --execute='echo config("app.name");'"
```

### 當需要安裝依賴時

**錯誤做法**：
```bash
# ❌ 本機安裝（會失敗或污染環境）
composer install
```

**正確做法**：
```bash
# ✅ VPS 安裝
ssh yd174 "cd /www/wwwroot/iot.tg25.win && composer install --no-dev"
```

---

## 🎯 各 Agent 專案對照表

| Agent | 專案 | VPS | 路徑 | 域名 |
|-------|------|-----|------|------|
| Sophie | Owner | yd174 | `/www/wwwroot/iot.tg25.win` | iot.tg25.win |
| Mina | Member | yd47 | `/var/www/waw-wallet` | win.tg25.win |
| Ina | Infra | infra | `/var/www/waw-iot` | api.tg25.win |
| Allie | Alliance | yd16 | `/var/www/alliance` | ali.tg25.win |
| Hubie | iHub | yd47 | `/var/www/ihub` | ihub.tg25.win |

---

## 🔧 本機可以做的事

### ✅ 允許的本機操作

1. **編輯檔案**：使用編輯器修改程式碼
2. **Git 操作**：commit、push、pull、branch 等
3. **檔案搜尋**：grep、find、ripgrep 等
4. **文檔查閱**：讀取 markdown、註解等
5. **靜態分析**：IDE 內建的語法檢查
6. **腳本執行**：不依賴 vendor/ 的獨立腳本

### ⚠️ 特殊情況

- **Node.js 專案**（如 iHub）：可以在本機執行 `npm install`、`npm run dev`
- **靜態頁面**（如 mqtt-terminal.html）：可以直接在瀏覽器開啟
- **獨立腳本**（如 Python、Shell）：可以在本機執行

---

## 📚 相關文檔

- `INFRASTRUCTURE_REFERENCE.md` — VPS 連線與路徑資訊
- `DEPLOYMENT_GUIDE.md` — 部署流程與指令
- `HQ_DEPLOYMENT_SOP.md` — HQ 自動化部署標準
- `LOCAL_DEV_CUSTOMIZATIONS.md` — 本機環境客製化記錄

---

## 🔗 文件神經連結

### 強關聯

- `INFRASTRUCTURE_REFERENCE.md` — SSH 別名與 VPS 路徑對照
- `DEPLOYMENT_GUIDE.md` — 正確的部署與測試流程
- `HQ_DEPLOYMENT_SOP.md` — HQ 部署自動化工具

### 中關聯

- `LOCAL_DEV_CUSTOMIZATIONS.md` — 本機開發環境配置
- `V9_OPS_AUTOMATION.md` — 運維自動化工具使用

---

## ⚡ 快速檢查清單

在執行任何操作前，Agent 應自問：

- [ ] 這個操作需要 vendor/ 嗎？
- [ ] 這個操作需要資料庫連線嗎？
- [ ] 這個操作需要完整的 Laravel 環境嗎？

如果任何一個答案是「是」，則 **必須在 VPS 上執行**。

---

## 📝 變更歷史

| 日期 | 版本 | 修改者 | 變更內容 |
|------|------|--------|---------|
| 2026-08-16 | 1.0.0 | HQ | 初始版本，定義本機開發限制規範 |

