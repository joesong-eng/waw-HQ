# 本地開發環境客製化記錄

> **用途**：記錄對本地開發工具（Hermes、IDE、Shell 等）的客製化修改，方便日後恢復或重新設定。

---

## Hermes Agent 客製化

### 移除啟動畫面 ASCII Art 圖案

**修改日期**：2026-05-19

**修改原因**：移除 Hermes 啟動時顯示的 Caduceus（雙蛇杖）ASCII art 圖案

**修改內容**：
- **檔案**：`/Users/ilawusong/.hermes/hermes-agent/hermes_cli/banner.py`
- **修改**：將 `HERMES_CADUCEUS` 變數設為空字串 `""`，並移除所有 ASCII art 行

**備份位置**：
```
/Users/ilawusong/.hermes/hermes-agent/hermes_cli/banner.py.backup
```

**恢復方法**：
```bash
# 恢復原始圖案
cp /Users/ilawusong/.hermes/hermes-agent/hermes_cli/banner.py.backup \
   /Users/ilawusong/.hermes/hermes-agent/hermes_cli/banner.py
```

**注意事項**：
- ⚠️ 執行 `hermes update` 會覆蓋此修改，需要重新套用
- 如需永久保留，建議使用 Hermes 的 skin 配置機制（待研究）

---

## Shell 配置

### Hermes Workspace 快捷指令

**位置**：`~/.zshrc`（或 `~/.bashrc`）

**功能**：定義 `hermes hq`、`hermes member` 等快捷指令，自動切換到對應 workspace

**配置內容**：
```bash
hermes () {
    case "$1" in
        (hq) echo "🚀 切換到 HQ 工作區..."
            cd /Users/ilawusong/Documents/sysWawIot/HQ
            shift
            eval "$HERMES_BIN" "$@" ;;
        (member) echo "🚀 切換到 Member 工作區..."
            cd /Users/ilawusong/Documents/sysWawIot/Member
            shift
            eval "$HERMES_BIN" "$@" ;;
        # ... 其他 workspace
        (*) eval "$HERMES_BIN" "$@" ;;
    esac
}
```

---

## SSH 別名配置

**位置**：`~/.ssh/config`

**用途**：定義各伺服器的 SSH 別名（`yd47`、`infra`、`yd174`、`yd16`、`PM`）

**詳細配置**：參考 `INFRASTRUCTURE_REFERENCE.md`

---

## IDE 配置

### VS Code / Cursor

（待補充）

---

## 維護建議

1. **定期備份**：重要的客製化配置應定期備份到 `~/Documents/sysWawIot/HQ/Temps/backups/`
2. **版本記錄**：每次修改都應更新本文件，記錄修改日期和原因
3. **測試恢復**：定期測試恢復流程，確保備份有效
4. **文件同步**：如有多台開發機，應同步此文件到其他機器

---

## 變更歷史

| 日期 | 修改項目 | 修改者 | 備註 |
|------|---------|--------|------|
| 2026-05-19 | 移除 Hermes ASCII art | HQ | 初次記錄 |
