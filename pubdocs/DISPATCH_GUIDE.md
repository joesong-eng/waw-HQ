# 派工系統操作指南 (Agent 必讀)

> **適用對象**：所有 Agent (Sophie, Mina, Ina, Allie, Hubie, Fio, Coli, Sidney)
> **最後更新**：2026-10-03
> **版本**：v5.0 純檔案系統 (.taskflow)

---

## 🎯 唯一派工體系

本專案唯一指揮體系為 **HQ 透過 `.taskflow` 純檔案信箱派工**。

> ⛔ 舊版 Redis Pub/Sub、`.taskbox/*.json`、`_agent/inbox` 已於 2026 全面廢除，**不再使用**。

---

## 1️⃣ 如何接收任務

**任務位置**：

```
WaW/.taskflow/<你的目錄>/inbox/<task_id>.md
```

| Agent | 目錄 |
|-------|------|
| Sophie | `owner` |
| Mina | `member` |
| Ina | `infra` |
| Allie | `alliance` |
| Hubie | `ihub` |
| Fio | `fio` |
| Coli | `coli` |
| Sidney | `signalhub` |

**啟動時檢查**：進入專案後先 `ls .taskflow/<你的目錄>/inbox/`，讀取最新的 `.md` 任務檔。

---

## 2️⃣ 如何處理任務

1. 完整讀取 inbox 中的 `.md` 任務檔（**不得切片，需全量讀取**）
2. 理解驗收指標與邊界條件
3. 執行任務
4. 產出回報文件（見下方）

---

## 3️⃣ 如何回報完成

**回報檔案格式**（`.md`）：

```markdown
# 任務回報：<task_id>

**完成時間**：YYYY-MM-DD HH:MM
**執行者**：<Agent名稱>

## 執行結果
（做了什麼、改了哪些檔案）

## 驗證佐證
（實際指令輸出 / API 回傳 / 截圖 / log）

## 結論
✅ 完成 / ❌ 遇到問題
```

**提交方式（二選一）**：

```bash
# 方式 A：直接寫入自己的 outbox
cp /tmp/report.md ../../.taskflow/<你的目錄>/outbox/

# 方式 B：使用標準回報腳本
bash ../../dev_tools/agent_report_to_hq_v2.sh <Agent名稱> /tmp/report.md
```

---

## 📌 鐵律

- **不接受口頭報告**：必須附截圖、log 或 API 回傳結果。
- **工單全量讀取**：`.taskflow/**/inbox/*.md` 與 `outbox/*.md` 必須完整讀取，禁止切片。
- **只能寫自己的 outbox**：每個 Agent 只寫入自己的 outbox，不越權。

---

**維護者**：HQ
**最後更新**：2026-10-03
