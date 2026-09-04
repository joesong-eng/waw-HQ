# 派工系統操作指南 (Agent 必讀)

> **適用對象**：所有 Agent (Sophie, Mina, Ina, Allie, Hubie, Fio, Coli)  
> **最後更新**：2026-08-16  
> **版本**：v4.0 純檔案系統

---

## 🎯 你需要知道的三件事

### 1️⃣ 如何接收任務

**任務位置**：
```
你的專案/.taskbox/inbox/<task_id>.json
```

**任務格式**：
```json
{
  "task_id": "TASK_20260816_001",
  "to_agent": "你的名字",
  "priority": "high",
  "description": "任務描述",
  "status": "pending",
  "created_at": "2026-08-16T05:00:00Z"
}
```

**啟動時自動檢查**：
- 你在 Codex 中啟動時，會自動檢查 `.taskbox/inbox/`
- 看到 JSON 任務文件，就開始處理

---

### 2️⃣ 如何處理任務

**步驟**：
1. 讀取 inbox 中的 JSON 任務文件
2. 理解 description 中的任務內容
3. 執行任務
4. 創建回報文檔（見下方）
5. 標記任務為已完成

---

### 3️⃣ 如何回報完成

**創建回報文件**：
```bash
# 在你的專案目錄下
cat > _agent/REPORT_$(date +%Y%m%d_%H%M%S)_<task_id>.md << 'EOF'
# 任務回報：<task_id>

## 任務資訊
- **任務 ID**：<task_id>
- **執行者**：你的名字
- **完成時間**：$(date -u +%Y-%m-%dT%H:%M:%SZ)

## 任務內容
（複製原任務描述）

## 執行結果
（寫下你做了什麼）

## 結論
（任務是否完成、有無問題）

---
**回報者**：你的名字  
**回報時間**：$(date -u +%Y-%m-%dT%H:%M:%SZ)
