# 文件註冊系統說明

> **版本**: 1.0  
> **建立日期**: 2026-05-24  
> **目的**: 防止在 `brains/knowledge/` 目錄下創建流浪文件

---

## 🎯 核心理念

**所有在 `brains/knowledge/` 目錄下的 .md 文件，必須先在 `DOCUMENT_INDEX.md` 中註冊，才能提交到 Git。**

這是為了：
1. 防止製造流浪文件
2. 確保所有文件都有明確的用途說明
3. 維護知識庫的組織性和可維護性

---

## 🛡️ 三層保護機制

### 第一層：Kiro Hook（即時提醒）

**觸發時機**：創建 .md 文件時

**行為**：
- 自動檢查文件是否已在 `DOCUMENT_INDEX.md` 中註冊
- 如果未註冊，在 Kiro 對話窗口中顯示警告
- 提供具體的修正步驟

**特點**：
- ✅ 即時反饋
- ❌ 不阻止文件創建
- 📝 提供指導

---

### 第二層：Git Pre-commit Hook（阻止提交）

**觸發時機**：執行 `git commit` 時

**行為**：
- 檢查即將提交的 .md 文件是否已註冊
- 如果有未註冊的文件，**阻止提交**
- 顯示詳細的錯誤訊息和修正步驟

**特點**：
- ✅ 強制約束
- ✅ 阻止錯誤進入 Git 歷史
- 📝 清晰的錯誤訊息

**位置**：`.git/hooks/pre-commit`

---

### 第三層：定期清理腳本（清理流浪文件）

**執行方式**：手動執行

**命令**：
```bash
./scripts/check_orphaned_files.sh
```

**行為**：
1. 掃描 `brains/knowledge/` 目錄下的所有 .md 文件
2. 檢查哪些文件未在 `DOCUMENT_INDEX.md` 中註冊
3. 提供三種處理選項：
   - **移動**：移動到 `Temps/orphaned/`（可恢復）
   - **刪除**：永久刪除（需要二次確認）
   - **取消**：僅顯示列表

**特點**：
- ✅ 定期清理
- ✅ 可恢復（移動選項）
- ⚠️ 需要手動執行

---

## 📋 正確的文件創建流程

### 步驟 1：先註冊

打開 `brains/knowledge/DOCUMENT_INDEX.md`，在對應章節添加：

```markdown
## 01_agent_governance/

| 文件 | 說明 |
|------|------|
| `NEW_FILE.md` | 新文件的用途說明 |
```

### 步驟 2：創建文件

創建文件：`brains/knowledge/01_agent_governance/NEW_FILE.md`

**此時**：
- ✅ Kiro Hook 會確認文件已註冊
- ✅ 提醒添加神經連結

### 步驟 3：添加神經連結

在文件底部添加：

```markdown
## 🔗 文件神經連結

### 強關聯（必讀）
> 修改本文件內容前，必須先閱讀以下文件
- `相關文件.md` - 說明

### 中關聯（建議讀）
> 了解完整上下文，建議閱讀
- `相關文件.md` - 說明

### 弱關聯（參考）
> 可選閱讀，提供額外背景
- `相關文件.md` - 說明

### 排除混淆
> 容易混淆但實際無關的文件
- `相關文件.md` - 說明
```

### 步驟 4：提交

```bash
git add brains/knowledge/DOCUMENT_INDEX.md
git add brains/knowledge/01_agent_governance/NEW_FILE.md
git commit -m "docs: add NEW_FILE"
```

**此時**：
- ✅ Git Hook 會檢查並允許提交

---

## ❌ 錯誤流程示例

### 錯誤 1：直接創建文件（未先註冊）

```bash
# 直接創建文件
touch brains/knowledge/01_agent_governance/NEW_FILE.md

# 嘗試提交
git add brains/knowledge/01_agent_governance/NEW_FILE.md
git commit -m "add file"
```

**結果**：
```
❌ 提交被阻止：發現流浪文件

以下文件未在 DOCUMENT_INDEX.md 中註冊：
  ✗ 01_agent_governance/NEW_FILE.md

📋 修正步驟：
  1. 打開 brains/knowledge/DOCUMENT_INDEX.md
  2. 在對應章節添加文件註冊
  3. 重新執行 git commit
```

### 錯誤 2：只註冊不提交索引

```bash
# 在 DOCUMENT_INDEX.md 中註冊了，但忘記 add
git add brains/knowledge/01_agent_governance/NEW_FILE.md
git commit -m "add file"
```

**結果**：
```
❌ 提交被阻止：發現流浪文件
```

**原因**：Git Hook 檢查的是**即將提交的** `DOCUMENT_INDEX.md` 版本，如果沒有 add，就是舊版本。

**修正**：
```bash
git add brains/knowledge/DOCUMENT_INDEX.md
git add brains/knowledge/01_agent_governance/NEW_FILE.md
git commit -m "docs: add NEW_FILE"
```

---

## 🔧 例外情況

以下文件**不需要**在 `DOCUMENT_INDEX.md` 中註冊：

1. **元文件**：
   - `DOCUMENT_INDEX.md` 本身
   - `README.md`
   - `NEURAL_LINKS_PROGRESS.md`
   - `FILE_REGISTRATION_SYSTEM.md`（本文件）

2. **臨時文件**：
   - `Temps/` 目錄下的所有文件

3. **特殊目錄**：
   - `.git/` 目錄下的文件
   - `.kiro/` 目錄下的文件

---

## 🛠️ 維護指令

### 檢查流浪文件

```bash
./scripts/check_orphaned_files.sh
```

### 測試 Git Hook

```bash
# 創建測試文件（未註冊）
touch brains/knowledge/test_orphan.md

# 嘗試提交（應該被阻止）
git add brains/knowledge/test_orphan.md
git commit -m "test"

# 清理測試文件
rm brains/knowledge/test_orphan.md
```

### 繞過 Git Hook（緊急情況）

```bash
# 僅在緊急情況使用！
git commit --no-verify -m "emergency commit"

# 但必須：
# 1. 在 HQ Message Hub 說明原因
# 2. 事後補註冊
# 3. 記錄到 brains/history/
```

---

## 📊 統計資訊

查看註冊文件數量：

```bash
# 統計 DOCUMENT_INDEX.md 中的文件數
grep -c '\.md`' brains/knowledge/DOCUMENT_INDEX.md

# 統計實際文件數
find brains/knowledge -name "*.md" -type f | wc -l
```

---

## 🔍 故障排除

### 問題 1：Git Hook 沒有執行

**檢查**：
```bash
ls -la .git/hooks/pre-commit
```

**修正**：
```bash
chmod +x .git/hooks/pre-commit
```

### 問題 2：清理腳本無法執行

**檢查**：
```bash
ls -la scripts/check_orphaned_files.sh
```

**修正**：
```bash
chmod +x scripts/check_orphaned_files.sh
```

### 問題 3：Kiro Hook 沒有觸發

**檢查**：
1. 打開 Kiro 的 Agent Hooks 面板
2. 確認「檢查 Markdown 文件註冊」Hook 存在且啟用
3. 檢查 file pattern 是否正確：`brains/knowledge/**/*.md`

---

## 📚 相關文件

- `DOCUMENT_INDEX.md` - 文件索引（註冊中心）
- `NEURAL_LINKS_PROGRESS.md` - 神經連結建置進度
- `.git/hooks/pre-commit` - Git Hook 腳本
- `scripts/check_orphaned_files.sh` - 清理腳本

---

## 🔗 文件神經連結

### 強關聯（必讀）
> 使用文件註冊系統前，必須先閱讀以下文件

- `DOCUMENT_INDEX.md` - 文件索引，所有文件的註冊中心
- `NEURAL_LINKS_PROGRESS.md` - 神經連結建置進度，了解文件組織理念

### 中關聯（建議讀）
> 了解完整文件管理體系，建議閱讀

- `01_agent_governance/AGENT_EXECUTION_PROTOCOL.md` - Agent 執行協議，了解文件管理規範
- `01_agent_governance/AGENT_COLLABORATION_PROTOCOL.md` - Agent 協作協議，了解知識沉澱規範

### 弱關聯（參考）
> 可選閱讀，提供額外背景

- `NAMING_AUTHORITY.md` - 名稱定義來源索引，了解命名規範

### 排除混淆
> 容易混淆但實際無關的文件

- `05_business_flows/` 下的業務流程文件 - 與文件註冊系統無直接關係

---

*制定者：HQ | 版本：1.0 | 最後更新：2026-05-24*
