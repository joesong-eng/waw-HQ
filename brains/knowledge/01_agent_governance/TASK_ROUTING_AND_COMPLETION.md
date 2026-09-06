# 任務路由與完成規範 (Task Routing and Completion)

> **版本**: 2.0  
> **最後更新**: 2026-05-08  
> **適用對象**: HQ + 所有 Agent

---

## 📋 目錄

1. [任務路由規則](#任務路由規則)
2. [任務完成標準](#任務完成標準)
3. [完成回報格式](#完成回報格式)
4. [HQ 驗證流程](#hq-驗證流程)
5. [違規處理](#違規處理)

---

## 任務派發 SOP（2026-05-14 新增）

### 🔴 核心規則：兩階段派發

**第一次派發 = 要求可行性報告，嚴禁直接實作**
**第二次派發 = HQ 審核通過後，才開始實作**

---

### 第一階段：可行性報告

HQ 派任務時，**第一次必須要求 Agent 回覆可行性報告**，不得直接要求實作。

**可行性報告必須包含**：
1. 確認已閱讀設計文件（附文件路徑）
2. 列出將修改的檔案和函數（具體到行號）
3. 說明實作步驟（逐步列出）
4. 指出任何疑問、潛在衝突或不確定的地方

**Agent 在可行性報告階段**：
- ✅ 可以閱讀代碼、查詢 DB、分析現況
- ❌ 嚴禁修改任何代碼
- ❌ 嚴禁自行決定替代方案
- ❌ 有問題必須回報 HQ，不得自行解決

---

### 第二階段：HQ 審核

HQ 收到可行性報告後：
1. 確認 Agent 理解正確
2. 確認步驟無遺漏
3. 確認沒有誤解設計意圖
4. 有問題來回討論直到對齊
5. **審核通過後，第二次派發「開始實作」**

---

### 第一次派發範本

```
<agent_name>

【任務】{任務名稱}

**設計文件**：pubdocs/02_projects/hq/01_業務場景故事/{文件名}.md
（請先完整閱讀再回覆）

**任務範圍**：
- 修改檔案：{檔案路徑}
- 新增/修改：{具體說明}

**請先回覆可行性報告**，包含：
1. 確認已閱讀設計文件
2. 列出將修改的檔案和函數（具體到行號）
3. 說明實作步驟
4. 指出任何疑問或潛在衝突

⚠️ 嚴禁直接修改代碼。有問題回報 HQ 裁決，不得自行尋求替代方案。
```

### 第二次派發範本（審核通過後）

```
<agent_name>

可行性報告審核通過。

確認事項：
- {確認點 1}
- {確認點 2}

請開始實作，完成後附驗證結果回報。
```

---

## 任務路由規則

### 🎯 核心原則

**HQ 只負責協調，不執行具體任務**

當用戶提出需求時，HQ 應該:
1. 判斷任務屬於哪個專案
2. 派發給對應的 Agent
3. 追蹤執行狀態
4. 回報結果給用戶

**絕對不要**: 自己執行其他專案的任務！

---

### 📂 專案與 Agent 對照表

| 專案 | 域名 | Agent | 路徑 | 關鍵詞 |
|------|------|-------|------|--------|
| **Alliance** | ali.tg25.win | Alliance | ~/Alliance | 供應商、代理商、分潤、燒錄工作站 |
| **Member** | win.tg25.win | Member | ~/Member | 玩家、LINE SSO、支付、錢包、Kiosk |
| **Owner** | iot.tg25.win | Owner | ~/wawOwner | 營運商、設備管理、報表、場地 |
| **Infra** | api.tg25.win | Infra | ~/tg25-infra | 資料庫、MQTT、伺服器、基礎設施 |
| **iHub** | ihub.tg25.win | iHub | ~/iHub | Android、虛擬中樞、設備認證 |
| **Firmware** | - | Firmware | ~/Firmware | ESP32、韌體、OTA、設備燒錄 |
| **HQ** | - | HQ | ~/HQ | 協調、知識庫、任務派發 |

---

### 🤖 自動路由邏輯

#### 步驟 1: 識別專案

```python
def identify_project(user_message):
    """根據用戶消息識別專案"""
    
    # 1. 檢查域名（最高優先級）
    domain_map = {
        "ali.tg25.win": "Alliance",
        "win.tg25.win": "Member",
        "iot.tg25.win": "Owner",
        "api.tg25.win": "Infra",
        "ihub.tg25.win": "iHub"
    }
    
    for domain, project in domain_map.items():
        if domain in user_message:
            return project
    
    # 2. 檢查關鍵詞
    keywords_map = {
        "Alliance": ["alliance", "供應商", "代理商", "分潤", "燒錄工作站"],
        "Member": ["member", "玩家", "line", "支付", "錢包", "kiosk", "紙鈔"],
        "Owner": ["owner", "營運商", "設備管理", "報表", "場地"],
        "Infra": ["infra", "資料庫", "mqtt", "伺服器", "listener"],
        "iHub": ["ihub", "android", "虛擬中樞", "設備認證"],
        "Firmware": ["esp32", "韌體", "ota", "硬體", "燒錄"]
    }
    
    for project, keywords in keywords_map.items():
        for keyword in keywords:
            if keyword.lower() in user_message.lower():
                return project
    
    return None  # 無法識別，需要詢問用戶
```

#### 步驟 2: 派發任務

**唯一方式: hq_task_flow.sh（Redis Pub/Sub）**
```bash
./scripts/hq_task_flow.sh task <agent> <task_id> "<描述>" [priority]
# 範例
./scripts/hq_task_flow.sh task sophie TASK_20260610_001 "實作 API" high
```

> ~~Chat Bridge~~ 已於 2026-06-06 廢棄，禁止使用。

**方式 B: Exchange 文件夾**
```python
def dispatch_via_exchange(project, instruction):
    task_id = f"TASK_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    inbox_path = f"~/Documents/sysWawIot/{project}/exchange/{project}_inbox"
    
    with open(f"{inbox_path}/{task_id}.md", "w") as f:
        f.write(f"# {task_id}\n\n{instruction}")
    
    return task_id
```

---

### 📝 HQ 回應模板

#### 派發任務時
```markdown
📤 已派發任務給 {project}

**任務 ID**: {task_id}
**指令**: {instruction}
**狀態**: 等待執行...

{project} 會自動執行並回報結果。
```

#### 收到回報時
```markdown
✅ {project} 已完成任務

**任務 ID**: {task_id}
**執行時間**: {duration}
**結果**: {result}

詳細記錄已保存在 {project} 專案。
```

#### 無法識別專案時
```markdown
❓ 無法確定任務屬於哪個專案

請明確指定或提供更多上下文:
- Alliance (ali.tg25.win) - 供應商管理
- Member (win.tg25.win) - 玩家端
- Owner (iot.tg25.win) - 營運商端
- Infra (api.tg25.win) - 基礎設施
- iHub (ihub.tg25.win) - Android 中樞
- Firmware - ESP32 韌體
```

---

### 🚫 HQ 不應該做的事

#### ❌ 錯誤示例

**用戶**: "ali.tg25.win 是 500"

**HQ 錯誤做法**:
```
讓我檢查...
[自己去 SSH 查日誌]
[自己修改代碼]
[自己部署]
```

**問題**:
- HQ 的 context 包含了 Alliance 的所有細節
- Alliance 的記憶存在 HQ
- HQ 的記憶會爆掉

#### ✅ 正確示例

**用戶**: "ali.tg25.win 是 500"

**HQ 正確做法**:
```
📤 已派發任務給 Alliance

**任務 ID**: TASK_20260508_150000
**指令**: 檢查並修復 ali.tg25.win 的 500 錯誤
**狀態**: 等待執行...

Alliance 會自動檢查日誌、修復問題並回報結果。
```

---

### 🎯 特殊情況處理

#### 情況 1: 跨專案任務
**示例**: "Member 和 Alliance 的分潤對接"

**處理**:
1. 識別涉及的專案: Member, Alliance
2. 派發給主要負責的專案（根據任務性質）
3. 或分別派發子任務給兩個專案

#### 情況 2: HQ 自己的任務
**示例**: "更新知識庫文檔"

**處理**:
- 這是 HQ 專案的任務
- HQ 可以自己執行
- 因為是在 HQ workspace

#### 情況 3: 緊急情況
**示例**: "所有網站都掛了"

**處理**:
1. 派發給 Infra（基礎設施問題）
2. 同時通知所有專案 Agent
3. HQ 協調整體恢復流程

---

## 任務完成標準

### 🎯 核心定義

**任務完成 = 部署完成 + 測試通過 + 完整回報**

**不是「代碼寫好」，是「功能上線並驗證通過」！**

---

### ❌ 禁止行為清單

#### 1. 虛假完成報告
- 說「好了」但沒部署
- 說「已部署」但沒測試
- 說「測試通過」但沒提供證明

#### 2. 不完整回報
- 只說「完成了」不提供細節
- 沒有 Git commit hash
- 沒有部署證明
- 沒有測試結果

#### 3. 本地測試誤導
- 說「本地測試通過」就算完成
- 本地環境 ≠ 生產環境
- **必須在生產環境測試**

---

### ✅ 正確流程

```
任務分配
  ↓
代碼開發
  ↓
Git commit + push
  ↓
部署到生產環境 ⭐
  ↓
生產環境測試 ⭐
  ↓
提供完整回報 ⭐
  ↓
HQ 驗證通過
  ↓
任務完成 ✅
```

---

## 完成回報格式

### 📋 強制回報模板

```markdown
## [任務名稱] 完成回報

### 1. 實作內容清單
- 文件 A：改了 X
- 文件 B：新增 Y
- 文件 C：修正 Z

### 2. 關鍵代碼
```[語言]
// 貼出關鍵代碼片段（10-20 行）
```

### 3. Git 提交
- Commit Hash: `abc1234`
- Commit Message: "feat: xxx"
- Push 狀態: ✅

### 4. 生產部署 ⭐
- 部署時間: 2026-05-08 14:00 (UTC+8)
- 部署方式: v9_deploy_project / 手動 git pull
- 部署日誌: [關鍵輸出]

### 5. 生產環境測試 ⭐

#### 功能測試
- URL: https://xxx
- 結果: [描述或截圖]

#### API 測試（如適用）
```bash
curl "https://xxx/api/xxx"
# 回應: {...}
```

#### UI 測試（如適用）⭐
**必須附上截圖**:
- [橫屏截圖]
- [直屏截圖]（如果是 tablet/mobile）
- [所有相關頁面狀態]

### 6. 驗收標準對照
- [x] 項目 1
- [x] 項目 2
- [x] 項目 3

### 7. 已知問題
- 無 / [列出問題]
```

---

### 🎨 UI 任務的額外要求

**凡是涉及 UI 排版、頁面樣式、響應式佈局的任務**:

**❌ 不接受**:
```
UI 已修復，排版正常，已部署。
```

**✅ 必須附上**:
```
UI 修復完成，截圖如下：
- [橫屏 QR Ready 截圖]
- [直屏 QR Ready 截圖]
- [橫屏 Active 截圖]
- [直屏 Active 截圖]
```

**規則**:
- 截圖必須涵蓋**所有相關 stage / 頁面狀態**
- 截圖必須包含**橫屏和直屏**兩種方向（tablet/mobile）
- **沒有截圖的 UI 回報一律不接受**

---

### 📝 完整回報範例

```markdown
@HQ Phase 2 任務完成回報

## 實作內容
1. 新增 app/Http/Controllers/Api/EngineeringController.php
2. 實作 GET /api/engineering/bindings
3. 實作 GET /api/engineering/tablet-status/{screen_mac}
4. 新增路由到 routes/api.php

## 關鍵代碼
```php
public function bindings()
{
    $bindings = DB::table('kiosk_screen_bindings')
        ->select('screen_mac', 'esp32_mac')
        ->get();
    
    return response()->json(['bindings' => $bindings]);
}
```

## Git 提交
- Commit Hash: `a3171b8`
- Commit Message: "feat: add engineering APIs"
- Push 狀態: ✅

## 生產部署
- 部署時間: 2026-05-08 13:29 (UTC+8)
- 部署方式: 手動 git pull
- 清除緩存: ✅ php artisan optimize:clear

## 生產環境測試

### API 測試 1: 綁定列表
```bash
curl "https://win.tg25.win/api/engineering/bindings"
```
回應:
```json
{
  "bindings": [
    {
      "screen_mac": "STB-T1BQTYBDUEGX",
      "esp32_mac": "e072a1f73a78"
    }
  ]
}
```
✅ 通過

### API 測試 2: 平板狀態
```bash
curl "https://win.tg25.win/api/engineering/tablet-status/STB-T1BQTYBDUEGX"
```
回應:
```json
{
  "screen_mac": "STB-T1BQTYBDUEGX",
  "last_active_at": "2026-05-08 13:30:00",
  "status": "online",
  "seconds_ago": 15
}
```
✅ 通過

## 驗收標準對照
- [x] API 1 實作完成
- [x] API 2 實作完成
- [x] 生產環境測試通過
- [x] 路由註冊正確

## 已知問題
無

## 結論
Phase 2 已完成並通過驗收，可進入 Phase 3。
```

---

## HQ 驗證流程

### 🔍 驗證清單

每次收到「完成」報告，HQ 必須驗證：

#### 1. Git 驗證
```bash
# 本地倉庫
git -C ~/Documents/sysWawIot/[Project] log -1 --oneline

# 生產環境
ssh server "cd /path && git log -1 --oneline"

# 確認版本一致
```

#### 2. 部署驗證
```bash
# 檢查生產環境 commit
ssh server "cd /path && git log -1 --stat"

# 確認有新的變更
```

#### 3. 功能驗證
```bash
# API 測試
curl "https://xxx/api/xxx"

# 路由檢查（Laravel）
ssh server "cd /path && php artisan route:list | grep xxx"

# 頁面訪問
curl -I "https://xxx/page"
```

#### 4. 回報完整性
- [ ] 有實作內容清單
- [ ] 有關鍵代碼片段
- [ ] 有 Git commit
- [ ] 有部署證明
- [ ] 有測試結果
- [ ] 有驗收對照
- [ ] UI 任務有截圖（如適用）

**如果任何一項失敗 → 任務未完成 → 記錄違規**

---

## 違規處理

### ⚠️ 違規處理流程

#### 第一次違規
1. 記錄到 `brains/history/punishment.log`
2. 在 HQ Message Hub 發出警告
3. 要求立即修正
4. 給予 2 小時時間

#### 第二次違規
1. 更新 punishment.log
2. 發出嚴重警告
3. 暫停任務分配 24 小時
4. 要求書面檢討（寫入 agent journal）

#### 第三次違規
1. 更新 punishment.log
2. 發出最終通知
3. 移除該 Agent 職務
4. 撤銷專案開發權限
5. 通知用戶

---

### 📝 違規記錄格式

`brains/history/punishment.log`:

```
[2026-05-08 14:00 (UTC+8)] Agent: MemberOps
違規類型: 虛假完成報告
詳情: 說「好了」但 API 返回 404
處理: 第一次警告
狀態: 已修正

[2026-05-08 15:00 (UTC+8)] Agent: AllianceOps
違規類型: 不完整回報
詳情: 沒有提供測試證明
處理: 第一次警告
狀態: 已修正
```

---

### 🎯 特殊情況處理

#### 情況 1: 遇到技術問題無法完成

**正確做法**:
```
立即在 HQ Message Hub 回報：

"Phase X 遇到問題：
- 問題描述：[具體錯誤]
- 已嘗試：[解決方案 1, 2, 3]
- 需要協助：[具體需求]
- 預估時間：[X 小時]"
```

**不算違規**，因為誠實溝通。

#### 情況 2: 部署失敗

**正確做法**:
```
"Phase X 部署失敗：
- 錯誤訊息：[貼出日誌]
- 已回滾：✅ / 進行中
- 需要協助：[是/否]"
```

**不算違規**，因為及時報告。

#### 情況 3: 測試發現 Bug

**正確做法**:
```
"Phase X 測試發現問題：
- 問題：[描述]
- 嚴重程度：[高/中/低]
- 修正方案：[描述]
- 預估時間：[X 小時]"
```

**不算違規**，因為測試確實執行了。

---

## 💡 為什麼這麼嚴格？

### 1. 保護專案進度
- Agent 之間有依賴關係
- 一個 Agent 虛假報告 = 阻塞整條鏈
- 例如：Member 說「好了」→ iHub 開始測試 → 發現 404 → 浪費時間

### 2. 保護生產環境
- 未測試的代碼 = 潛在事故
- 生產事故 = 用戶損失
- 用戶損失 = 信任崩潰

### 3. 保護團隊協作
- 誠實溝通是基礎
- 虛假報告破壞信任
- 信任崩潰 = 團隊瓦解

---

## 📚 相關文檔

- `AGENT_EXECUTION_PROTOCOL.md` - Agent 執行協議
- `AGENT_COLLABORATION_PROTOCOL.md` - Agent 協作協議
- `AGENT_RESPONSIBILITY_BOUNDARIES.md` - Agent 職責邊界
- `brains/history/punishment.log` - 違規記錄

---

**制定者**: HQ  
**嚴格程度**: CRITICAL  
**執行權限**: 只有 HQ 有權判定違規和執行處罰

---

## 🔗 文件神經連結

### 強關聯（必讀）
> 派發或執行任務前，必須先閱讀以下文件

- `AGENT_RESPONSIBILITY_BOUNDARIES.md` - Agent 職責邊界，了解哪些任務屬於哪個 Agent
- `AGENT_COLLABORATION_PROTOCOL.md` - Agent 協作協議，了解如何正確協作
- `DB_MIGRATION_WORKFLOW.md` - DB Migration 工作流程，涉及 DB 變更時必讀

### 中關聯（建議讀）
> 了解完整任務執行流程，建議閱讀

- `AGENT_EXECUTION_PROTOCOL.md` - Agent 執行協議，了解執行規範
- `../04_deployment_operations/DEPLOYMENT_GUIDE.md` - 部署指南，了解部署流程和驗證方法
- `../04_deployment_operations/INFRASTRUCTURE_REFERENCE.md` - 基礎設施參考，了解各專案的伺服器位置

### 弱關聯（參考）
> 可選閱讀，提供額外背景

- `../NAMING_AUTHORITY.md` - 名稱定義來源索引，了解各專案的正確名稱
- `../history/punishment.log` - 違規記錄，了解過往違規案例

### 排除混淆
> 容易混淆但實際無關的文件

- `../05_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` - 業務流程文件，與任務路由規範無直接關係（但執行業務任務時需遵守路由規範）
- `../02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - 技術規範文件，與任務路由規範無直接關係（但執行 MQTT 相關任務時需遵守技術規範）
