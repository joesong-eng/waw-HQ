---
priority: CRITICAL
auto_load: true
---

# 🧠 HQ 記憶管理協議

## 問題

Boss 說要記錄某件事時，如果隨便找個目錄、隨便取個文件名記錄，那這個記錄就像大海裡的針，下次根本不會被讀取，等於沒記錄。

**記錄歸記錄，跟下次不再犯錯一點關係都沒有。**

## 解決方案：分類記錄系統

### 📁 記錄位置的唯一標準

| 記錄類型 | 存放位置 | 用途 | 是否自動載入 |
|---------|---------|------|------------|
| **核心規則** | `.kiro/steering/*.md` (frontmatter: `auto_load: true`) | 每次執行時自動載入 | ✅ 是 |
| **操作手冊** | `brains/knowledge/*.md` | 需要時手動查閱 | ❌ 否 |
| **歷史事件** | `brains/history/*.md` | 事件記錄、事故報告 | ❌ 否 |
| **懲罰記錄** | `brains/history/punishment.log` | 違規記錄 | ❌ 否 |

### ⚠️ Token 管理原則

**問題**: 如果 `.kiro/steering/` 有太多文件，每次都全部載入會消耗大量 token。

**解決方案**: 
1. **只有最核心的規則放在 `.kiro/steering/`** (frontmatter 標記 `auto_load: true`)
2. **詳細的操作手冊放在 `brains/knowledge/`**，需要時手動讀取
3. **使用 frontmatter 控制是否自動載入**

### 🎯 記錄決策樹

```
Boss 說「記住這件事」
    ↓
問：這是「絕對不能再犯的核心錯誤」嗎？
    ↓
是 → 寫入 .kiro/steering/*.md（自動載入，簡短精煉）
    ↓
否 → 問：這是「詳細操作手冊」還是「歷史事件」？
    ↓
    ├─ 詳細操作手冊 → brains/knowledge/*.md（需要時查閱）
    └─ 歷史事件 → brains/history/*.md
```

### 📏 .kiro/steering/ 的內容原則

**只放最核心、最簡短的規則**：
- ✅ 「永遠不要說無法讀取 XXX 文件」
- ✅ 「記錄必須放在正確位置」
- ✅ 「收到任務必須回覆」
- ❌ 詳細的操作步驟（太長，放 brains/knowledge/）
- ❌ 完整的案例分析（太長，放 brains/history/）

**目標**: 每個文件 < 3KB，總共 < 30KB

## 📋 .kiro/steering/ 的文件命名規範

**這個目錄的文件會自動載入到每次執行的 context 中**

### 現有文件（標準）

| 文件名 | 用途 |
|--------|------|
| `identity.md` | HQ 的角色定位 |
| `product.md` | 專案概述 |
| `HQ_CROSS_WORKSPACE_ACCESS.md` | 跨 workspace 存取規則 |
| `MEMORY_MANAGEMENT_PROTOCOL.md` | 本文件 |

### 命名規則

```
{主題}_{類型}.md

主題：
- HQ_* : HQ 專屬規則
- AGENT_* : Agent 協作規則
- CODE_* : 代碼規範
- DEPLOY_* : 部署規範

類型：
- RULES : 操作規則
- PROTOCOL : 協議
- STANDARD : 標準
- FORBIDDEN : 禁止事項
```

### 範例

- `HQ_CROSS_WORKSPACE_ACCESS.md` ✅
- `AGENT_COMMUNICATION_RULES.md` ✅
- `CODE_REVIEW_PROTOCOL.md` ✅
- `DEPLOY_SAFETY_CHECKLIST.md` ✅
- `random_notes.md` ❌（太模糊）
- `temp.md` ❌（臨時文件不該放這裡）

## 🧠 brains/knowledge/ 的文件命名規範

**長期知識，需要時查閱**

### 命名規則

```
{領域}_{主題}.md

領域：
- MQTT_* : MQTT 相關
- kiosk_* : Kiosk 相關
- agent_* : Agent 相關
- hardware_* : 硬體相關
- deployment_* : 部署相關
```

### 範例

- `MQTT_TOPIC_STANDARD.md` ✅
- `kiosk_bill_acceptor_interaction_flow.md` ✅
- `agent_execution_rules.md` ✅
- `notes.md` ❌（太模糊）

## 📜 brains/history/ 的文件命名規範

**歷史事件、事故報告、任務記錄**

### 命名規則

```
{類型}_{日期}_{主題}.md

類型：
- INCIDENT : 事故報告
- TASK : 任務記錄
- LESSON : 教訓記錄
- CLEANUP : 清理記錄

日期：YYYYMMDD
```

### 範例

- `INCIDENT_20260508_IHUB_QRCODE_500.md` ✅
- `TASK_20260508_QUICK_REFERENCE_VERIFICATION.md` ✅
- `LESSON_20260501_PHASE5_TIMEOUT.md` ✅
- `punishment.log` ✅（特殊文件）
- `notes.md` ❌（太模糊）

## 🚨 違規範例

### ❌ 錯誤做法

```
Boss: 記住，HQ 可以跨 workspace 讀取文件

HQ: 好的，我記錄在 notes.md 了
     ↓
     下次執行時不會自動載入
     ↓
     再次犯同樣的錯誤
```

### ✅ 正確做法

```
Boss: 記住，HQ 可以跨 workspace 讀取文件

HQ: 這是操作規則，我寫入 .kiro/steering/HQ_CROSS_WORKSPACE_ACCESS.md
     ↓
     每次執行時自動載入
     ↓
     不會再犯錯
```

## 📊 記錄檢查清單

每次 Boss 說「記住」時：

- [ ] 我確定了這是哪種類型的記錄？
- [ ] 我使用了正確的目錄？
- [ ] 我使用了符合規範的文件名？
- [ ] 如果是規則，我放在 `.kiro/steering/` 了嗎？
- [ ] 我確認這個文件會在下次執行時被讀取嗎？

## 🔥 違規懲罰

**如果再次隨便亂放記錄**：
- 記錄到 `brains/history/punishment.log`
- 標記為嚴重違規
- 必須重新整理所有記錄

## 📊 當前記憶系統狀態

### .kiro/steering/ （自動載入，總計 ~36KB）
- ✅ `identity.md` (2.5KB) - HQ 角色定位
- ✅ `product.md` (1.4KB) - 專案概述
- ✅ `structure.md` (5.4KB) - 專案結構
- ✅ `tech.md` (3.1KB) - 技術棧
- ✅ `HQ_CROSS_WORKSPACE_ACCESS.md` (5.2KB) - 跨 workspace 規則
- ✅ `MEMORY_MANAGEMENT_PROTOCOL.md` (5.6KB) - 本文件

### brains/knowledge/ （需要時查閱）
- ✅ `agent_execution_rules.md` (4.8KB) - Agent 執行詳細規則
- ✅ `task_routing_rules.md` (6.9KB) - 任務路由詳細規則
- ✅ `task_completion_standard.md` (5.5KB) - 任務完成標準
- ✅ `interaction_protocol_common_sense.md` (2.9KB) - 溝通協議
- ✅ 其他 25+ 個知識文件

### brains/history/ （歷史記錄）
- ✅ INCIDENT_* 系列
- ✅ TASK_* 系列
- ✅ LESSON_* 系列
- ✅ `punishment.log`

## 🎯 核心原則

1. **核心規則自動載入**: 放在 `.kiro/steering/`，簡短精煉（< 3KB）
2. **詳細手冊需要時查**: 放在 `brains/knowledge/`，詳細完整
3. **文件名必須有意義**: 不用 notes.md、temp.md
4. **分類必須明確**: 核心規則/操作手冊/歷史事件
5. **Token 管理**: steering 總大小 < 50KB，避免每次載入過多

---

**建立日期**: 2026-05-08  
**最後更新**: 2026-05-08（優化 token 管理）  
**優先級**: 🚨 CRITICAL  
**目的**: 確保記錄有效，下次不再犯錯，同時控制 token 消耗
