# 公用文檔目錄 (pubdocs)

> **用途**：所有 Agent 共同閱讀的文檔和規範  
> **位置**：WaW/pubdocs/（實體目錄）  
> **訪問**：每個 Agent 專案下都有 pubdocs symlink

---

## 📚 文檔列表

| 文檔 | 用途 | 對象 |
|------|------|------|
| **DISPATCH_GUIDE.md** | 派工系統操作指南 | 所有 Agent 必讀 |
| **MQTT_TOPIC_GUIDE.md** | MQTT 主題規範速查 | 所有 Agent |
| **API_STANDARDS.md** | API 設計規範 | Sophie, Mina, Allie |
| **COMMON_PATTERNS.md** | 常用程式碼模式 | 所有 Agent |
| **TROUBLESHOOTING.md** | 常見問題排解 | 所有 Agent |
| **README.md** | 本文件 | 索引 |

---

## 🎯 使用方式

### 從 Agent 專案訪問
```bash
# 你在任何 Agent 專案目錄下
cd pubdocs/
ls -l
cat MQTT_TOPIC_GUIDE.md
```

### 從 HQ 訪問
```bash
# 在 WaW 根目錄
cd pubdocs/
ls -l
```

---

## 📝 新增文檔

**由 HQ 負責**：
- 只有 HQ 可以新增/修改 pubdocs 中的文檔
- Agent 如需更新，請回報給 HQ

**文檔規範**：
- 使用 Markdown 格式
- 文件名大寫加底線（例如：DISPATCH_GUIDE.md）
- 包含最後更新日期
- 包含適用對象

---

## 🔗 相關目錄

- **brains/knowledge/** - HQ 知識庫（更詳細的文檔）
- **_agent/** - 各 Agent 的工作目錄
- **scripts/** - HQ 腳本工具

---

**維護者**：HQ  
**建立日期**：2026-08-16  
**最後更新**：2026-08-16

