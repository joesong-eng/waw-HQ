---
description: 知識管理規範 - 如何查詢、更新、補充知識庫，避免試錯和編造
---

# 知識管理規範

## 核心原則

**先查文件，再行動。無文件時回報缺失，嚴禁編造。**

---

## 一、查詢順序（強制）

遇到任何技術問題時，必須按以下順序處理：

### 1. 查閱索引文件


| 情況 | 必查文件 |
|------|---------|
| 需要 SSH 到任何伺服器 | `brains/knowledge/04_deployment_operations/INFRASTRUCTURE_REFERENCE.md` |
| 需要部署任何專案 | `brains/knowledge/04_deployment_operations/DEPLOYMENT_GUIDE.md` |
| 需要確認任何名稱的正確寫法 | `brains/knowledge/NAMING_AUTHORITY.md` |
| 需要發 MQTT 指令或解讀 MQTT 訊息 | `brains/knowledge/02_technical_standards/MQTT_TOPIC_STANDARD.md` |
| 需要用 WebSocket 頻道或事件名稱 | `brains/knowledge/02_technical_standards/WEBSOCKET_CHANNEL_STANDARD.md` |
| 需要了解識別碼（chip_id / node_id） | `brains/knowledge/kiosk_identification_system.md` |
| 需要發任務給 Agent | `brains/knowledge/01_agent_governance/AGENT_RESPONSIBILITY_BOUNDARIES.md` |

### 2. 搜尋知識庫

如果索引表中沒有，使用 `file_search` 或 `grep_search` 搜尋：

```bash
# 搜尋檔案名稱
file_search: "MQTT"

# 搜尋內容
grep_search: "mqtt password" in brains/knowledge/
```

### 3. 明確回報結果

- ✅ **找到** → 引用文件路徑和行號
- ❌ **未找到** → 明確說「文件未找到」，不得編造

### 4. 提供後續選項

- 建議可能的文件位置
- 或建議詢問相關 Agent（Ina、Coli、Mina 等）
- 或建議詢問 Joe

---

## 二、禁止編造的內容

### 絕對不可編造

1. **技術參數**：GPIO 腳位、API 端點、資料表結構
2. **認證資訊**：MQTT 用戶名密碼、API Key、資料庫密碼
3. **配置路徑**：檔案位置、目錄結構、憑證路徑
4. **MQTT 主題**：主題格式、Payload 結構
5. **系統行為**：未經驗證的邏輯推測

### 正確做法範例

❌ **錯誤**：
```
MQTT 用戶名應該是 wawv8，密碼是 wawv8mqtt2024
```

✅ **正確**：
```
我在 INFRASTRUCTURE_REFERENCE.md 和 MQTT_TOPIC_STANDARD.md 中
都沒有找到 MQTT 認證資訊。

建議：
1. 詢問 @Ina（Infra 負責人）
2. 或查看 /home/ubuntu/tg25-infra/.env
```

---

## 三、詢問 Agent 的時機

### 何時詢問 Agent

需要 Agent 提供資訊或執行任務時，透過 Message Hub 發送：

```bash
./scripts/hq_task_flow.sh consult ina CONS_001 "問題描述"
```

| 情況 | 詢問對象 |
|------|---------|
| MQTT、資料庫、基礎設施問題 | `ina` |
| 韌體行為、設備通訊 | `coli` / `fio` |
| Member 前端、WebSocket | `mina` |
| Owner 後台、設備管理 | `sophie` |

---

## 四、補充知識到文件

### 何時補充

當發現以下情況時，應該補充到知識庫：

1. **文件缺失**：索引表中應該有但沒有的資訊
2. **新發現**：調查過程中發現的重要事實
3. **常用指令**：經常需要但文件中沒有的操作

### 補充位置

| 內容類型 | 補充位置 |
|---------|---------|
| SSH 指令、伺服器資訊 | `brains/knowledge/04_ops_and_deployments/INFRASTRUCTURE_REFERENCE.md` |
| MQTT 主題、Payload 格式 | `brains/knowledge/02_protocols_and_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` |
| 識別碼規則 | `brains/knowledge/NAMING_AUTHORITY.md` |
| 事件記錄、教訓 | `brains/history/INCIDENT_*.md` 或 `LESSON_*.md` |
| Agent 職責 | `brains/knowledge/01_agent_governance_rules/AGENT_RESPONSIBILITY_BOUNDARIES.md` |

### 補充格式

**必須包含**：
1. 資訊來源（誰提供的、從哪裡查到的）
2. 驗證時間
3. 完整的指令或參數（不可省略）

**範例**：
```markdown
### MQTT 測試指令

**來源**：Ina 提供（2026-05-26）

**訂閱主題**：
```bash
mosquitto_sub -h mqtt.tg25.win -p 8883 \
  --cafile /etc/mosquitto/certs/ca.crt \
  --cert /etc/mosquitto/certs/client.crt \
  --key /etc/mosquitto/certs/client.key \
  -t 'device/+/status' -v
```

**查看 Retained 訊息**：
```bash
# 加上 -C 1 參數，收到 1 條訊息後退出
mosquitto_sub ... -t 'device/{chip_id}/status' -v -C 1
```
```

---

## 五、試錯的代價

### 為什麼不能試錯

1. **浪費 Token**：每次錯誤的嘗試都消耗 Token
2. **浪費時間**：在錯誤方向上繞圈子
3. **破壞信任**：Joe 無法依賴 AI 提供的資訊
4. **可能造成損害**：錯誤的指令可能影響生產環境

### 本次 INCIDENT 的教訓

**浪費的 Token**：
- 試錯 MQTT 用戶名密碼：~2000 tokens
- 試錯憑證路徑：~1000 tokens
- 試錯連線方式：~1500 tokens
- **總計：~4500 tokens**

**正確做法**：
1. 查 `INFRASTRUCTURE_REFERENCE.md`（沒有 MQTT 測試指令）
2. 立刻詢問 @Ina
3. 等待回覆，不試錯
4. **只需：~500 tokens**

**節省：90% 的 Token**

---

## 六、檢查清單

在執行任何技術操作前，問自己：

- [ ] 我查過 `workspace-common-sense.md` 的索引表了嗎？
- [ ] 我查過相關的知識庫文件了嗎？
- [ ] 如果沒找到，我是否明確回報「文件未找到」？
- [ ] 我是否在試錯？（如果是，立刻停止）
- [ ] 我是否應該詢問相關 Agent？

---

## 七、文件更新流程

### HQ 的職責

**`brains/knowledge/` 只有 HQ 可以寫入**

1. 收到 Agent 提供的資訊
2. 驗證資訊正確性
3. 決定補充到哪個文件
4. 更新文件並記錄來源
5. 通知相關 Agent

### Agent 的職責

**Agent 不得直接修改 `brains/knowledge/`**

1. Agent 完成任務後透過 `agent_report_to_hq_v2.sh` 回報
2. HQ 審核後，若有需要更新知識庫，由 HQ 寫入

---

## 八、參考文件

- `no-fabrication-rule.md` - 嚴禁編造規範
- `workspace-common-sense.md` - 操作前必查索引
- `diagnostic-rules.md` - 診斷問題規則
- `identity.md` - HQ 角色定位

---

*制定者：HQ | 最後更新：2026-05-26 | 基於 INCIDENT_20260526 的教訓*
