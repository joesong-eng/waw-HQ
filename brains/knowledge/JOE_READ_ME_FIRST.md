# 🎯 HQ 啟動備忘卡

> **最後更新**：2026-10-05
> **當前狀態**：舊派工系統（Redis / Message Hub / `.taskbox` / `hq_gateway.py`）已全面廢除；
> 現行唯一派工體系為 `.taskflow` 純檔案信箱。

---

## 📍 現在在哪

| 階段 | 內容 | 狀態 |
|------|------|------|
| 舊派工清除 | `.taskbox` / `_agent/` / Redis / launchd / hq_gateway.py | ✅ 已完成（2026-10-03） |
| ADR-001/002/003 | SignalHub 訂閱、Member device-session SSOT、訂閱表統一 | ✅ 已落地 |
| 文件對齊 | 治理文件、README、知識庫索引對齊 `.taskflow` | 🟡 進行中（HQ 收尾） |
| 對外開發者文件 | SignalHub OpenAPI / ESP32 / MQTT / MIT | ⏸️ 待辦 |

---

## 🚀 每次啟動 HQ Session 的第一步

### 1. 確認派工系統與站點
```bash
./dev_tools/waw_ops.sh status          # 檢視所有 Agent 信箱狀態
./dev_tools/waw_ops.sh log             # 最近派工日誌
```

### 2. 查看待辦
```bash
cat brains/knowledge/WAW_TODO.md                       # 跨專案中長期待辦
cat brains/knowledge/WAW_CLEANUP_AND_TASKS_SPEC_20261003.md  # 收斂 SPEC
```

### 3. 發任務（唯一正確方式）
```bash
# 短任務
./dev_tools/waw_ops.sh task <agent> <task_id> "<描述>" [priority]

# 長工單（強烈推薦，防截斷）
./dev_tools/waw_ops.sh task <agent> <task_id> --file <工單.md> [priority]
```

---

## ⚠️ 鐵律（不要再犯）

- ✅ 派工**只用** `.taskflow` 純檔案信箱（`inbox/` 收件、`outbox/` 回報）
- ❌ **禁止**再使用 Redis Pub/Sub、Message Hub、`.taskbox`、`hq_gateway.py`、`_agent/`
- ❌ 不接受口頭報告；回報必須附截圖、log 或 API 回傳結果
- ✅ 工單與回報（`inbox/*.md` / `outbox/*.md`）**必須整檔完整讀取**，禁止切片

---

## 📂 重要文件快速入口

| 想查什麼 | 去哪裡 |
|---------|-------|
| WAW 待辦總表 | `brains/knowledge/WAW_TODO.md` |
| 收斂 SPEC | `brains/knowledge/WAW_CLEANUP_AND_TASKS_SPEC_20261003.md` |
| 派工協議（權威） | `brains/knowledge/01_agent_governance/SIMPLE_FILE_DISPATCH_PROTOCOL.md` |
| 知識庫索引 | `brains/knowledge/DOCUMENT_INDEX.md` |
| Agent 回報收件匣 | `.taskflow/<agent>/outbox/` |
| 對外開發者文件 | `pubdocs/` |

---

*維護者：HQ | 最後更新：2026-10-05*
