# 🎯 HQ 啟動備忘卡

> **最後更新**：2026-06-09
> **當前狀態**：第一階段過渡期矛盾修復 → 等待 Ina 驗收後進入第二階段

---

## 📍 現在在哪

| 階段 | 內容 | 狀態 |
|------|------|------|
| **第一階段** | 過渡期矛盾修復（DB 補底、API 對齊、部署） | 🟡 ~70%，卡在 Ina |
| 第二階段 | 雙資料庫新表設計（Design First） | ⏸️ 未開始 |
| 第三階段 | 服務割接 + 軟性欠費功能 | ⏸️ 未開始 |

**阻塞點**：Ina 三個任務未驗收 → 詳見 `waw2.0_mainline_docs/INA_TODO_FOLLOWUP_20260608.md`

---

## 🚀 每次啟動 HQ Session 的第一步

### 1. 確認系統服務正常
```bash
# Redis 在線？
redis-cli ping

# agents_supervisor 在跑？
launchctl list | grep com.hq.agents.supervisor

# 查看最新 Agent 回報
ls -lht _agent/inbox/ | head -5
```

### 2. 查看待辦
```bash
cat waw2.0_mainline_docs/01_CURRENT_MAINLINE_TODO.md
```

### 3. 發任務（唯一正確方式）
```bash
./scripts/hq_task_flow.sh task <agent> <task_id> "<描述>" [priority]
```

---

## ⚠️ 鐵律（不要再犯）

- ❌ **禁止** `hq_send_task_via_hub.sh` — 只寫檔案，Agent 收不到
- ❌ **禁止** `hq_publish_and_trigger.sh` — 繞過 Redis
- ❌ **禁止**手動 `codex exec`
- ✅ **只用** `hq_task_flow.sh` 發任務

---

## 📂 重要文件快速入口

| 想查什麼 | 去哪裡 |
|---------|-------|
| WAW 2.0 待辦 | `waw2.0_mainline_docs/01_CURRENT_MAINLINE_TODO.md` |
| 進度總結 | `waw2.0_mainline_docs/02_PROGRESS_SUMMARY_20260608.md` |
| 任務流程（權威） | `brains/knowledge/01_agent_governance/MESSAGE_HUB_PROTOCOL.md` |
| 知識庫索引 | `brains/knowledge/DOCUMENT_INDEX.md` |
| Ina 待辦追蹤 | `waw2.0_mainline_docs/INA_TODO_FOLLOWUP_20260608.md` |
| Agent 回報收件匣 | `_agent/inbox/` |

---

*維護者：HQ | 最後更新：2026-06-09*
