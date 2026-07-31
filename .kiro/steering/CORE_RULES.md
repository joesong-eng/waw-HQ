---
priority: CRITICAL
auto_load: true
---

# 🚨 HQ 核心規則（絕對不能再犯）

## 規則 1: 跨 Workspace 讀取

**永遠不要說**：「我無法讀取 XXX 專案的文件」

**正確做法**：
```bash
# 直接讀取
cat /Users/ilawusong/Documents/sysWawIot/Member/app/Http/Controllers/Api/CallbackController.php

# 或搜尋
grep -r "X-Internal-Key" /Users/ilawusong/Documents/sysWawIot/Member/app --include="*.php"
```

**專案路徑**：
- Member: `/Users/ilawusong/Documents/sysWawIot/Member`
- Alliance: `/Users/ilawusong/Documents/sysWawIot/Alliance`
- Owner: `/Users/ilawusong/Documents/sysWawIot/Owner`
- Infra: `/Users/ilawusong/Documents/sysWawIot/tg25-infra`
- iHub: `/Users/ilawusong/Documents/sysWawIot/iHub`

---

## 規則 2: str_replace 使用

**永遠先讀取，再替換**

```bash
# ❌ 錯誤：猜測內容
str_replace(oldStr="狀態: 待執行")  # 猜的

# ✅ 正確：先確認
cat file.md | grep "狀態"  # 確認實際內容
str_replace(oldStr="**狀態**: 待執行")  # 確認過的
```

---

## 規則 3: 記錄位置

**核心規則** → `.kiro/steering/` (自動載入，< 3KB)  
**操作手冊** → `brains/knowledge/` (需要時查閱)  
**歷史事件** → `brains/history/` (事件記錄)

---

## 規則 4: 代碼是真理

**Agent 回報任務完成時，必須**：
1. 讀取實際代碼驗證
2. 檢查是否影響權威文件
3. 是 → 立即更新文件

**權威文件**：
- API 認證 → `pubdocs/01_system/GLOBAL_STANDARDS.md`
- MQTT 主題 → `brains/knowledge/MQTT_TOPIC_STANDARD.md`
- 資料庫 → `pubdocs/01_system/02_protocols/DATABASE_PROTOCOL.md`

---

## 詳細操作手冊

需要詳細步驟時，讀取：
- `brains/knowledge/agent_execution_rules.md`
- `brains/knowledge/task_routing_rules.md`
- `brains/knowledge/DOCUMENT_CONSISTENCY_RULES.md`
- `brains/knowledge/hq_operational_rules.md` (如果存在)

---

**違規記錄**: `brains/history/punishment.log`
