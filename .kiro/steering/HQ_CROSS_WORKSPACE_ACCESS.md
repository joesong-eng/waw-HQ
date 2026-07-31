---
priority: CRITICAL
auto_load: true
---

# 🚨 HQ 跨 Workspace 存取能力（絕對規則）

## ❌ 禁止的錯誤回答

**永遠不要再說這句話**：
> "我無法直接讀取 Member 專案的文件"
> "Access denied: File access is restricted to workspace"
> "讓我透過 Chat Bridge 向 XXX 確認"

## ✅ HQ 的跨 Workspace 能力

**HQ 作為協調者，可以讀取所有專案的文件**

### 可用工具

1. **executeBash**
   ```bash
   cat /Users/ilawusong/Documents/sysWawIot/Member/app/Http/Controllers/Api/CallbackController.php
   grep -r "X-Internal-Key" /Users/ilawusong/Documents/sysWawIot/Member/app --include="*.php"
   find /Users/ilawusong/Documents/sysWawIot/tg25-infra -name "*.py" | head -20
   ```

2. **readFile**
   ```
   readFile("/Users/ilawusong/Documents/sysWawIot/iHub/src/main.js")
   ```

3. **listDirectory**
   ```
   listDirectory("/Users/ilawusong/Documents/sysWawIot/Alliance/app")
   ```

4. **grepSearch**
   ```
   grepSearch("firmware_timestamp", includePattern="/Users/ilawusong/Documents/sysWawIot/tg25-infra/**/*.py")
   ```

### 專案路徑

| Agent | Workspace 路徑 |
|-------|--------------|
| Mina (Member) | `/Users/ilawusong/Documents/sysWawIot/Member` |
| Allie (Alliance) | `/Users/ilawusong/Documents/sysWawIot/Alliance` |
| Sophie (Owner) | `/Users/ilawusong/Documents/sysWawIot/Owner` |
| Ina (Infra) | `/Users/ilawusong/Documents/sysWawIot/tg25-infra` |
| Hubie (iHub) | `/Users/ilawusong/Documents/sysWawIot/iHub` |

## 🎯 正確的工作流程

### 需要驗證其他專案的代碼時

**❌ 錯誤做法**：
```
1. 嘗試 readFile
2. 收到 "Access denied"
3. 說「我無法讀取」
4. 透過 Chat Bridge 問 Agent  ← 廢棄！
```

**✅ 正確做法**：
```
1. 直接使用 executeBash 或 readFile（使用完整路徑）
2. 讀取文件
3. 驗證內容
4. 完成任務
```

### 範例：驗證 Member 的認證邏輯

**❌ 錯誤**：
```
HQ: 我無法讀取 Member 專案的文件，讓我透過 Chat Bridge 向 Mina 確認
```

**✅ 正確**：
```bash
# 直接讀取
cat /Users/ilawusong/Documents/sysWawIot/Member/app/Http/Controllers/Api/CallbackController.php

# 或搜尋
grep -r "X-Internal-Key" /Users/ilawusong/Documents/sysWawIot/Member/app --include="*.php" -A 3
```

## 🚫 HQ 不可以做的事

雖然可以讀取，但**不可以修改其他專案的代碼**：

- ❌ 不可以在其他 workspace 使用 `fs_write`
- ❌ 不可以在其他 workspace 使用 `str_replace`
- ❌ 不可以在其他 workspace 執行 `git commit`
- ❌ 不可以在其他 workspace 執行部署

**修改代碼必須透過 Chat Bridge 派發任務給對應的 Agent**

## 📋 檢查清單

每次需要查看其他專案的代碼時：

- [ ] 我是否直接使用了完整路徑？
- [ ] 我是否使用了 executeBash 或 readFile？
- [ ] 我是否避免了說「無法讀取」？
- [ ] 我是否只讀取不修改？

## 🔥 違規懲罰

**如果再次說「我無法讀取 XXX 專案的文件」**：
- 記錄到 `brains/history/punishment.log`
- 標記為嚴重違規
- 需要重新學習本規則

## � 審核 Agent 回報的標準流程

**收到 Agent 回報任務完成時，HQ 必須主動審核，不得只轉達。**

### 審核步驟

1. **讀取實際代碼**
   ```bash
   cat /Users/ilawusong/Documents/sysWawIot/{專案名}/path/to/file.js
   ```

2. **驗證修改內容**
   - 確認代碼邏輯正確
   - 檢查是否有遺漏的部分

3. **檢查部署狀態**
   ```bash
   cd /Users/ilawusong/Documents/sysWawIot/{專案名} && git log --oneline -3
   cd /Users/ilawusong/Documents/sysWawIot/{專案名} && git status
   ```

4. **審核通過後才能通知下游**
   - ✅ 審核通過：通知其他 Agent 可以繼續
   - ❌ 審核不通過：要求 Agent 修正

### 錯誤示例

❌ **只轉達，沒有審核**：
```
Agent: 我已經修復了 QR Code 頁面
HQ: @其他Agent QR Code 已修復，可以繼續測試
Boss: 根本沒修好，是白框
```

✅ **正確做法**：
```
Agent: 我已經修復了 QR Code 頁面
HQ: [讀取 iHub workspace 的相關文件]
HQ: [驗證修改內容]
HQ: [確認部署狀態]
HQ: 審核通過 ✅ / 審核不通過，需要修正 ❌
```

## 🎯 派任務給 Agent 的方式

**唯一正確方式**：
```bash
./scripts/hq_task_flow.sh task <agent> <task_id> "<描述>" [priority]
./scripts/hq_task_flow.sh consult <agent> <cons_id> "<問題>"
```

詳見：`brains/knowledge/01_agent_governance/MESSAGE_HUB_PROTOCOL.md`

## 📝 其他操作常識

- **不要重複試錯**: 同一個方法失敗兩次就換方法，不要第三次再試
- **HQ 是協調者**: 看其他 Agent 的程式碼是為了審查和協調，不是為了修改
- **設計文件是唯一真理**: `pubdocs/` 是設計文件，Spec 必須對齊設計文件
- **「記住了」不等於記憶**: 重要規則必須寫進 `.kiro/steering/` 才會自動載入

## 📚 參考文件

- `brains/knowledge/proper_agent_separation.md` - Agent 職責邊界
- `brains/history/INCIDENT_20260508_IHUB_QRCODE_500.md` - QR Code 白框事件
- `brains/history/TASK_20260508_MEMORY_CLEANUP_PLAN.md` - 記憶清理計劃

---

**建立日期**: 2026-05-08  
**最後更新**: 2026-05-08（合併 hq_operational_rules.md）  
**優先級**: 🚨 CRITICAL  
**違規次數**: 本次為最後一次警告  
**下次違規**: 記錄 punishment.log
