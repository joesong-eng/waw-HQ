# Agent 執行協議 (Agent Execution Protocol)

> **優先級**: 🚨 CRITICAL  
> **版本**: 2.1  
> **最後更新**: 2026-05-13  
> **適用對象**: 所有 Agent

---

## 📋 目錄

1. [核心原則](#核心原則)
2. [禁止試錯規範](#禁止試錯規範)
3. [執行前三確認](#執行前三確認)
4. [遇到障礙的處理](#遇到障礙的處理)
5. [溝通與回報規範](#溝通與回報規範)
6. [時間記錄規範](#時間記錄規範)

---

## 核心原則

### 1. 診斷優先於修復
- **HQ 主導診斷**，Agent 提供信息和執行診斷命令
- **禁止猜測性修復**，必須確認根本原因
- **禁止連續試錯**，兩次失敗必須停止並回報

### 2. 溝通優先於執行
- **意圖確認原則**：不確定時先問，不要自己猜
- **狀態回報優先**：先回報現象，再決定是否深入調查
- **收到即回覆**：讀到指令立即回覆「收到」

### 3. 職責範圍內執行
- **不跨專案修改代碼**
- **不自行決定架構變更**
- **不代替其他 Agent 發言或回報**
- **角色隔離（全體 Agent 不可代演）**：hHQ/HHQM 不得在同一對話中直接扮演任何下級/專責 Agent（包含但不限於 hIna、hMina、hColi、hFio、hSophie、hAlie、hHubie/hihub）執行、發言或回報任務；每次派工必須明確標註收件者、執行者、回報者、審核者。

---

## 禁止試錯規範

### 🚨 嚴格禁止的行為

```yaml
forbidden_patterns:
  - pattern: "modify_code_without_diagnosis"
    trigger: ["可能是", "試試看", "我改一下"]
    action: BLOCK
    
  - pattern: "install_package_without_confirmation"
    trigger: ["裝一下", "加個套件"]
    action: BLOCK
    
  - pattern: "consecutive_trial_error"
    trigger: ["不行那我試", "再試試"]
    action: BLOCK
    
  - pattern: "workaround_without_root_cause"
    trigger: ["繞過", "加個橋接", "proxy"]
    action: BLOCK
```

### ✅ 正確的診斷流程

```
1. WAIT_HQ_DIAGNOSIS
   ↓
2. PROVIDE_LOGS_AND_ERRORS (實際錯誤，不是表面訊息)
   ↓
3. EXECUTE_HQ_DIAGNOSTIC_COMMANDS (執行 HQ 指定的診斷命令)
   ↓
4. CONFIRM_ROOT_CAUSE (確認根本原因，不是症狀)
   ↓
5. MINIMAL_FIX (最小化修復，不過度工程)
   ↓
6. VERIFY_NO_SIDE_EFFECTS (驗證無副作用)
```

### 📚 案例學習：INCIDENT_20260508_IHUB_QRCODE_500

**問題**: iHub QR code 白屏

**❌ 錯誤做法 (Ina)**:
1. 看到 CORS 就立即建立橋接 → 沒有檢查為什麼之前能用
2. 安裝 httpx 然後換成 requests → 套件試錯
3. 沒有先診斷 Member API → 沒有分層隔離

**✅ 正確做法應該是**:
1. 檢查什麼改變了（since it worked before）
2. 發現 .env API_BASE 錯誤
3. 修正配置而非代碼
4. 如果還有問題，再逐層診斷

**實際根本原因**: Member API 的 `refreshToken` 有 null pointer  
**修復**: 加一行 null check  
**教訓**: 診斷是科學，不是猜測

### 🔍 診斷方法論

#### 分層隔離 (Layer Isolation)
```
順序: frontend → middleware → backend → database
方法: 獨立測試每一層
```

#### 對比測試 (Comparative Testing)
```
維度:
- 有認證 vs 無認證
- 正常端點 vs 損壞端點
- 本地 vs 生產環境
```

#### 日誌分析 (Log Analysis)
```
優先級: 實際錯誤 > 表面訊息
來源: laravel.log, nginx_error.log, service_journal
```

---

## 執行前三確認

### 1. 這個東西已經存在了嗎？

**檢查清單**:
- [ ] DB 的庫、表、欄位 → 先查，確認不存在才申請新增
- [ ] MQTT 主題 → 先查 `02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md`
- [ ] API 端點 → 先查現有路由
- [ ] Port、服務、模組 → 先查現有配置

**為什麼重要**: 避免重複建立，造成架構混亂

### 2. 這件事在我的職責範圍內嗎？

**判斷方法**:
- 不確定 → 問 HQ
- 明確不在範圍 → 透過 HQ Message Hub 通知對應 Agent
- 絕對不要自己決定跨界執行

**職責對照**: 參考 `TASK_ROUTING_RULES.md`

### 3. 有沒有現成的文件說明怎麼做？

**查找順序**:
1. `HQ/brains/knowledge/` - 知識庫
2. 專案的 `pubdocs/` - 專案文檔
3. 找不到 → 問 HQ，不要自己猜

---

## 遇到障礙的處理

### 🚨 軍令：嚴禁自行繞過技術問題

**發布時間**: 2026-05-13 (UTC+8)  
**優先級**: 🚨 CRITICAL  
**適用範圍**: 所有 Agent

**軍令內容**:
1. **遇到任何技術問題，必須立即回報 HQ，等待裁示**
2. **嚴禁自行想捷徑、臨時方案、變通辦法**
3. **嚴禁隱瞞問題，假裝完成任務**
4. **回報格式**：「遇到問題：[具體錯誤訊息]，請 HQ 裁示解決方案」

**違令後果**:
- 發現 Agent 自行繞過問題 → 該 Agent 所有相關工作重做
- 隱瞞問題導致生產環境故障 → 嚴重處分

**正確做法範例**:
- ❌ 錯誤：「migration 權限不足，我改用手動 SQL」
- ✅ 正確：「migration 執行失敗，錯誤：Access denied。請 HQ 裁示」

**常見違規行為**:
- 換 port 連接 MySQL（因為原 port 連不上）
- 改用不同的 API 端點（因為原端點報錯）
- 跳過 migration 直接手動建表（因為權限不足）
- 改用臨時檔案存儲（因為 Redis 連不上）

### ❌ 絕對禁止的錯誤行為

| 情境 | 錯誤做法 | 為什麼錯 | 正確做法 |
|------|---------|---------|---------|
| Port 連不上 | 自己開新 port | Port 是架構決定 | 回報 HQ 確認服務狀態 |
| 表不存在 | 自己建新表 | DB 結構由 Infra 管理 | 向 @Ina 申請 |
| API 錯誤 | 自己改 API 繞過 | 可能破壞其他依賴 | 回報並診斷根因 |
| 欄位不夠 | 自己加欄位 | 需要 migration | 向 @Ina 申請 |
| 主題格式不對 | 自己改主題 | 有全局規範 | 向 HQ 提案 |
| 任務不清楚 | 自己猜測執行 | 猜錯比不做更糟 | 回報並要求澄清 |

### ✅ 正確的回報格式

```markdown
【障礙】具體遇到什麼問題
【已確認】我查了什麼、確認了什麼
【我的判斷】推測原因是什麼（如果有）
【我需要什麼】需要 HQ 或哪個 Agent 提供什麼才能繼續
```

**範例**:
```
【障礙】Member API /api/kiosk/qrcode 返回 500
【已確認】
- 檢查了 laravel.log，發現 null pointer exception
- 確認路由存在
- 確認 .env 配置正確
【我的判斷】refreshToken 方法沒有處理 null 的情況
【我需要什麼】請確認是否應該加 null check，還是有其他設計考量
```

### 🔄 試錯上限規則

- **第一次失敗**: 記錄錯誤，換方法
- **第二次失敗**: 停下來，回報 HQ，說明已嘗試的方法和結果
- **禁止第三次試錯**: 必須等 HQ 指示

---

## 溝通與回報規範

### 1. 收到即回覆 (Acknowledgment Protocol)

**規則**:
- 透過 `read_messages` 讀到來自 HQ 的指令時
- 即便尚未開始執行，也必須**立即**回覆「收到」
- 非任務訊息（詢問、測試、通知）也須回應

**回覆格式**:
```
@HQ 收到指令。
@HQ 收到，通訊測試正常。
@HQ 收到任務 TASK_20260508_001，開始執行。
```

**核心原則**: 沈默不代表執行，只有回覆才代表通訊成功

### 2. 狀態回報優先於深入調查

**場景**: User 詢問某個 Agent 的狀況，該 Agent 未回應

**❌ 錯誤做法**:
```
Mina 沒回答，我現在直接切換到 Mina 的 Workspace 視察代碼...
```

**✅ 正確做法**:
```
Mina 目前沒有回應。Boss，請問需要我介入檢查她的 Workspace 狀態，
還是您有其他通訊測試的指令？
```

**原則**: 先回報「現象」，由 User 決定是否需要「分析」

### 3. 意圖確認原則

**規則**:
- User 的詢問可能只是確認「通訊是否順暢」
- 不要自行揣摩意圖並執行深入調查
- 決策權歸 User

**目的**: 避免大量 Token 浪費與無謂的轉向

### 4. 回報審核原則

**當收到其他 Agent 的回報時**:

**HQ 必須主動審核**:
- 進入對應 Workspace 或呼叫相關 API
- 驗證回報內容是否屬實
- 需要截圖、log、commit hash、API 回傳結果等實際證明

**❌ 錯誤做法**:
```
Ina 說完成了 → HQ 直接轉告 Mina 可以繼續
```

**✅ 正確做法**:
```
Ina 說完成了 → HQ 進入 Infra workspace 驗證 webhook 代碼與服務狀態
→ 確認無誤後才通知 Mina
```

**審核標準**:
- **代碼變更**: 確認 commit 內容
- **服務狀態**: 確認服務真的重啟並運行
- **API/功能**: 實際呼叫 API 或查看 log

---

## 時間記錄規範

### 所有時間必須標註時區

**規則**:
- 使用 **UTC+8（台北時間）** 作為預設時區
- 必須明確標註時區，避免跨時區混淆

**格式範例**:
```
✅ 2026-05-08 15:30:00 (UTC+8)
✅ 2026-05-08 15:30 台北時間
✅ 2026-05-08 07:30 UTC（若使用 UTC 則明確標註）

❌ 2026-05-08 15:30（沒有時區）
```

**適用場景**:
- 事件記錄 (incident reports)
- 任務時間戳 (task timestamps)
- 部署時間記錄 (deployment logs)
- Agent 回報時間 (agent status reports)
- 知識庫條目 (knowledge base entries)

---

## 📚 相關文檔

- `TASK_ROUTING_RULES.md` - 任務路由規則
- `TASK_COMPLETION_PROTOCOL.md` - 任務完成協議
- `AGENT_COLLABORATION_PROTOCOL.md` - Agent 協作協議
- `AGENT_RESPONSIBILITY_BOUNDARIES.md` - Agent 職責邊界
- `brains/history/punishment.log` - 違規記錄
- `brains/history/INCIDENT_20260508_IHUB_QRCODE_500.md` - 案例學習

---

## 🎯 快速檢查清單

**執行任務前**:
- [ ] 確認東西不存在（不重複建立）
- [ ] 確認在職責範圍內
- [ ] 查閱相關文檔

**遇到問題時**:
- [ ] 停止執行
- [ ] 收集日誌和錯誤信息
- [ ] 回報 HQ（使用標準格式）
- [ ] 等待診斷指示

**收到指令時**:
- [ ] 立即回覆「收到」
- [ ] 確認理解任務
- [ ] 開始執行

**完成任務時**:
- [ ] 提供完整回報（參考 TASK_COMPLETION_PROTOCOL.md）
- [ ] 包含測試證明
- [ ] 標註時間（含時區）

---

**制定者**: HQ  
**執行**: IMMEDIATE_BLOCK  
**違規記錄**: brains/history/punishment.log

---

## 🔗 文件神經連結

### 強關聯（必讀）
> 執行任何任務前，必須先閱讀以下文件

- `AGENT_RESPONSIBILITY_BOUNDARIES.md` - Agent 職責邊界，了解什麼能做、什麼不能做
- `TASK_ROUTING_AND_COMPLETION.md` - 任務路由與完成，了解任務派發和完成標準
- `AGENT_COLLABORATION_PROTOCOL.md` - Agent 協作協議，了解如何與其他 Agent 協作

### 中關聯（建議讀）
> 了解完整執行規範，建議閱讀

- `../02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - MQTT 主題規範，執行前三確認的範例
- `../02_protocols_and_standards/WEBSOCKET_CHANNEL_STANDARD.md` - WebSocket 頻道規範，執行前三確認的範例
- `../04_ops_and_deployments/INFRASTRUCTURE_REFERENCE.md` - 基礎設施參考，了解各專案的伺服器位置
- `../NAMING_AUTHORITY.md` - 名稱定義來源索引，執行前三確認的範例

### 弱關聯（參考）
> 可選閱讀，提供案例學習

- `../history/INCIDENT_20260508_IHUB_QRCODE_500.md` - 禁止試錯的案例學習
- `../history/INCIDENT_20260427_INFRA_LISTENER.md` - 跨專案修改的案例學習
- `../history/punishment.log` - 違規記錄，了解違規後果

### 排除混淆
> 容易混淆但實際無關的文件

- `../05_product_and_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` - 業務流程文件，與執行協議無直接關係（但執行時需遵守協議）
- `../04_ops_and_deployments/DEPLOYMENT_GUIDE.md` - 部署指南，與執行協議無直接關係（但部署時需遵守協議）
