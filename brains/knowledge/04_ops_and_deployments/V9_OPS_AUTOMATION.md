# V9 自動化運維工具 (V9 Ops Automation)

> **版本**: 2.0  
> **最後更新**: 2026-05-08  
> **用途**: V9 體系自動化運維工具 (MCP) 使用指南

---

## 📋 目錄

1. [工具概述](#工具概述)
2. [核心組件位置](#核心組件位置)
3. [工具清單](#工具清單)
4. [使用方式](#使用方式)
5. [常見誤區](#常見誤區)

---

## 工具概述

V9 自動化運維工具是基於 MCP (Model Context Protocol) 的自動化部署和運維工具集，提供一鍵部署、健康檢查、Agent 協調等功能。

**核心優勢**:
- ✅ 一鍵本地提交並同步至遠端
- ✅ 自動化建置和部署流程
- ✅ 統一的運維接口
- ✅ 跨專案協調能力

---

## 核心組件位置

### 實作腳本 (Python)
```
/Users/ilawusong/Documents/sysWawIot/pubdocs/01_system/00_common/tools/mcp/servers/v9_ops_server.py
```

### MCP 配置文件
```
/Users/ilawusong/Documents/sysWawIot/Alliance/.kiro/settings/mcp.json
```

**注意**: 其他專案也可能有自己的 `mcp.json` 配置。

---

## 工具清單

### 1. v9_deploy_project
**功能**: 一鍵本地 Git 提交並同步至遠端生產伺服器

**參數**:
- `project_name` (必填): 專案名稱
  - 可選值: `Alliance`, `Member`, `iHub`, `Infra`
- `commit_message` (必填): 提交說明訊息

**內部流程** (以 iHub 為例):
```
1. 本地操作
   ├─ git add .
   ├─ git commit -m "<commit_message>"
   └─ git push origin main

2. 遠端操作 (透過 SSH)
   ├─ 連線至 ihub 主機
   ├─ cd /www/wwwroot/ihub.tg25.win
   ├─ git pull origin main
   ├─ npm install
   └─ npm run build
```

**使用範例**:
```python
# 在支援 MCP 的環境中呼叫
mcp_v9_ops_v9_deploy_project(
    project_name="iHub",
    commit_message="feat: update QR code display"
)
```

---

### 2. v9_quick_deploy
**功能**: HQ 總部系統全量更新，重啟所有 V9 核心服務

**參數**:
- `commit_message` (必填): 提交說明訊息

**內部流程**:
```
1. 更新 HQ 專案
   ├─ git add .
   ├─ git commit -m "<commit_message>"
   └─ git push origin main

2. 重啟核心服務
   ├─ PA (Project Alliance)
   ├─ PM (Project Member)
   └─ Ops (Operations)
```

**使用範例**:
```python
mcp_v9_ops_v9_quick_deploy(
    commit_message="chore: update HQ configuration"
)
```

---

### 3. v9_check_health
**功能**: 檢查雲端基礎設施的運作狀態

**參數**: 無

**檢查項目**:
- PA (Project Alliance) 狀態
- PM (Project Member) 狀態
- Webhooks 連線狀態
- 關鍵服務運行狀態

**使用範例**:
```python
mcp_v9_ops_v9_check_health()
```

**輸出範例**:
```json
{
  "status": "healthy",
  "services": {
    "PA": "running",
    "PM": "running",
    "webhooks": "connected"
  },
  "timestamp": "2026-05-08 15:30:00 (UTC+8)"
}
```

---

### 4. v9_agent_summon
**功能**: 派發任務給指定 Agent

**參數**:
- `agent_name` (必填): Agent 名稱
  - 可選值: `Alliance`, `Member`, `Infra`, `iHub`, `Owner`
- `instruction` (必填): 任務指令

**內部流程**:
```
1. 生成任務 ID
2. 構造任務消息
3. 透過 HQ Message Hub 發送
4. 等待 Agent 回報
```

**使用範例**:
```python
mcp_v9_ops_v9_agent_summon(
    agent_name="Alliance",
    instruction="修改首頁標題"
)
```

---

## 使用方式

### 在 Kiro 中使用

**方式 1: 直接呼叫 MCP 工具**
```
# 在 Kiro 對話中
請使用 v9_deploy_project 部署 iHub 專案，commit message 為 "feat: update QR code"
```

**方式 2: 透過 Agent 呼叫**
```
# 在 Kiro 對話中
@alliance-dev 請部署 Alliance 專案
```

---

### 在 Python 腳本中使用

```python
# 需要在支援 MCP 的環境中
from mcp_client import MCPClient

client = MCPClient()

# 部署專案
result = client.call_tool(
    "v9_deploy_project",
    {
        "project_name": "Member",
        "commit_message": "fix: resolve payment issue"
    }
)

print(result)
```

---

### 在 Agent 中使用

Agent 可以在執行任務時自動呼叫這些工具：

```markdown
# Agent 定義文件中
當需要部署時：
1. 確認代碼已提交
2. 呼叫 v9_deploy_project
3. 驗證部署結果
4. 回報完成
```

---

## 常見誤區

### ❌ 誤區 1: 當作 Shell 指令使用

**錯誤做法**:
```bash
# 在終端機執行
which v9_deploy_project
v9_deploy_project Alliance "update"
```

**為什麼錯**:
- `v9_deploy_project` 是 MCP 工具，不是 Shell 指令
- 無法在終端機直接執行
- 無法用 `which` 找到

**正確做法**:
- 在支援 MCP 的環境中呼叫（如 Kiro）
- 或透過 MCP Client 呼叫

---

### ❌ 誤區 2: 不檢查環境依賴

**錯誤做法**:
```python
# 直接呼叫，不檢查 MCP 是否可用
mcp_v9_ops_v9_deploy_project(...)
```

**為什麼錯**:
- 必須在支援 MCP 的環境中
- 需要正確的 `mcp.json` 配置
- 需要 Python 環境和依賴

**正確做法**:
```python
# 檢查 MCP 是否可用
if mcp_available():
    mcp_v9_ops_v9_deploy_project(...)
else:
    print("MCP 不可用，請檢查配置")
```

---

### ❌ 誤區 3: 混淆專案名稱

**錯誤做法**:
```python
# 使用錯誤的專案名稱
mcp_v9_ops_v9_deploy_project(
    project_name="member",  # 小寫
    commit_message="update"
)
```

**為什麼錯**:
- 專案名稱大小寫敏感
- 必須使用正確的名稱

**正確做法**:
```python
# 使用正確的專案名稱（首字母大寫）
mcp_v9_ops_v9_deploy_project(
    project_name="Member",  # 正確
    commit_message="update"
)
```

**可用專案名稱**:
- `Alliance`
- `Member`
- `iHub`
- `Infra`

---

## 環境依賴

### 必要條件

1. **MCP 環境**
   - Kiro IDE
   - 或其他支援 MCP 的環境

2. **配置文件**
   - `mcp.json` 正確配置
   - 包含 `v9_ops_server` 定義

3. **Python 環境**
   - Python 3.8+
   - 必要的 Python 套件

4. **SSH 權限**
   - 對目標伺服器的 SSH 存取權限
   - SSH Key 已配置

---

## 檢查 MCP 配置

### 查看 mcp.json

```bash
cat /Users/ilawusong/Documents/sysWawIot/Alliance/.kiro/settings/mcp.json
```

**範例配置**:
```json
{
  "mcpServers": {
    "v9-ops": {
      "command": "python",
      "args": [
        "/Users/ilawusong/Documents/sysWawIot/pubdocs/01_system/00_common/tools/mcp/servers/v9_ops_server.py"
      ],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

---

### 驗證 MCP 工具可用性

在 Kiro 中執行：
```
請列出可用的 MCP 工具
```

應該看到：
- `v9_deploy_project`
- `v9_quick_deploy`
- `v9_check_health`
- `v9_agent_summon`

---

## 故障排除

### 問題 1: 工具不可用

**症狀**: 呼叫工具時提示「工具不存在」

**可能原因**:
1. `mcp.json` 配置錯誤
2. Python 腳本路徑錯誤
3. MCP 服務未啟動

**解決方案**:
1. 檢查 `mcp.json` 配置
2. 確認 Python 腳本存在
3. 重啟 Kiro 或 MCP 服務

---

### 問題 2: SSH 連線失敗

**症狀**: 部署時提示「SSH 連線失敗」

**可能原因**:
1. SSH Key 未配置
2. 伺服器無法連線
3. 權限不足

**解決方案**:
1. 檢查 SSH Key: `ssh yd47`（或對應別名）
2. 檢查網路連線
3. 確認 SSH 權限

---

### 問題 3: Git 操作失敗

**症狀**: 部署時提示「Git 操作失敗」

**可能原因**:
1. 本地有未提交的修改
2. 遠端有衝突
3. Git 配置錯誤

**解決方案**:
1. 檢查 Git 狀態: `git status`
2. 解決衝突
3. 參考 `DEPLOYMENT_GUIDE.md` 的「常見問題處理」

---

## 📚 相關文檔

- `DEPLOYMENT_GUIDE.md` - 部署流程指南
- `INFRASTRUCTURE_REFERENCE.md` - 基礎設施快速參考
- `../01_agent_governance_rules/AGENT_COLLABORATION_PROTOCOL.md` - Agent 協作協議

---

**制定者**: HQ  
**最後更新**: 2026-05-08  
**版本**: 2.0
