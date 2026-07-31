# _agent 目錄說明

此目錄用於 HQ 與各 Agent 之間的通訊。

---

## 📂 目錄結構

```
_agent/
├── inbox/              # 收件匣 - Agent 回報
├── outbox/             # 發件匣 - 待派發任務
├── archive/            # 歷史歸檔
│   ├── history/        # 舊的諮詢單、報告
│   └── replies/        # 舊的回覆文件
├── status.md           # 狀態總結
└── README.md           # 本文件
```

---

## 📥 inbox/ - 收件匣

Agent 回報的訊息會自動存入此處。

**檔案命名格式**: `YYYYMMDD_HHMMSS_{agent_name}.json`

---

## 📤 outbox/ - 發件匣

HQ 發布的待辦任務。Agent 啟動時會自動檢查。

**檔案命名格式**: `to_{agent_name}.json`

---

## 📦 archive/ - 歷史歸檔

舊訊息會自動歸檔至此。

---

## 🔗 相關文件

- **HQ Message Hub**: `README_MESSAGE_HUB.md`
- **腳本工具**: `scripts/README.md`
- **知識庫**: `brains/knowledge/`

