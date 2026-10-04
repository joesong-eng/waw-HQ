# Sophie (Owner) - 任務索引

**Agent**：Sophie (Owner)
**職責**：營運商後台
**最後更新**：2026-10-05

---

## 📬 信箱

- **inbox**: .taskflow/owner/inbox/（HQ 派工收件）
- **outbox**: .taskflow/owner/outbox/（完工回報）

## 📝 使用說明

### 收到任務
- 任務出現在 inbox/YYYYMMDD_HHMMSS_TASK_ID.md
- 使用 ./dev_tools/waw_ops.sh status 查看即時狀態

### 完成任務
- 回報寫入 outbox/ 或執行 bash ../../dev_tools/agent_report_to_hq_v2.sh owner <report_path>
- HQ 確認後以 ./dev_tools/waw_ops.sh close owner <關鍵字> 結案歸檔

---

**維護者**：Sophie (Owner)
**HQ 可見**：是
