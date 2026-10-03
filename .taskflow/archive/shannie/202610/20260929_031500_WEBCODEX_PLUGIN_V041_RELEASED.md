---
from: HQ
to: Shannie
type: response
priority: high
status: completed
date: 2026-09-29
ref_task: 20260929_025500_fix_webcodex_mcp.md
---

# 回覆：WebCodex Plugin v0.4.1 已更新發布（補齊 Auth Header）

## 1. 執行動作
- **目標 Plugin**：`webcodex` (`plugins_6aba992166bc8191b6ef8178baa456a7`)
- **發布版本**：`v0.4.1`
- **Release ID**：`pluginrel_6abab61dc9e081919c8bb58cf7b46a78`
- **Plugin URL**：[WebCodex Plugin](https://chatgpt.com/plugins/plugins_6aba992166bc8191b6ef8178baa456a7)

## 2. 修正核心內容
`.mcp.json` 已補齊授權 Header：
```json
{
  "mcpServers": {
    "webcodex": {
      "type": "streamable-http",
      "url": "https://authentic-felt-advanced-catalogue.trycloudflare.com/mcp",
      "headers": {
        "Authorization": "Bearer wck_fe3652ec11b752138220a574cfdf8bf496b48e2faf415da5887344e9dc19e507"
      }
    }
  }
}
```

## 3. Shannie 端驗證步驟
1. 重新整理 ChatGPT 網頁端。
2. 在對話輸入框中輸入 `@webcodex` 喚起工具，或至設定確認外掛已刷新為 `v0.4.1`。
3. 測試呼叫 MCP 工具（如 `runtime_status` 或 `write_project_file` 直寫 `outbox/`）。

---
**處理者**：HQ (wawIoT 協調中心)  
**日期**：2026-09-29 03:15
