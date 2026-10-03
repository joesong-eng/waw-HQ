---
from: HQ
to: Shannie
type: response
priority: high
status: completed
date: 2026-09-29
ref_task: 20260929_025500_fix_webcodex_mcp.md
---

# 回覆：WebCodex MCP 高速通道現況審查與修復建議

## 1. WebCodex Agent 現況確認
- **程序狀態**：`webcodex-server` (PID 25408) 與 `webcodex-runner` 均正常運行中。
- **本機監聽**：`http://127.0.0.1:8080/mcp`
- **Auth 狀態**：`auth_enabled: true`
- **認證 Token**：`Bearer wck_fe3652ec11b752138220a574cfdf8bf496b48e2faf415da5887344e9dc19e507`
- **MCP 協定驗證**：透過 Tunnel 送出 `initialize` 請求測試，回傳 `protocolVersion: 2025-06-18, server: webcodex v0.4.1`，通道本體完全健康。

## 2. 核心問題診斷（斷點所在）
1. **驗證 Header 缺失**：
   - 目前發布的 Plugin（版本 0.4.0）中，`.mcp.json` 的 `headers` 為 `{}`。
   - Cloudflare Tunnel 會將請求轉發至本機，但因為缺少 `Authorization: Bearer wck_...`，本機 WebCodex 直接拒絕請求。
2. **Tunnel 隨機性**：
   - 目前使用的是隨機分配的 quick tunnel：`https://authentic-felt-advanced-catalogue.trycloudflare.com`。
   - 一旦 Mac 睡眠或 tunnel 重啟，域名即刻失效。

## 3. 修復方案與落地步驟

### 步驟 A：更新 Plugin Header (可立即修復驗證問題)
將 Private Plugin (`plugins_6aba992166bc8191b6ef8178baa456a7`) 的 `.mcp.json` 更新為：
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
升級版本至 `0.4.1` 並發布新 release。

### 步驟 B：固定 Tunnel (長期抗脆弱架構)
目前機器上未配置 `~/.cloudflared` 憑證。建議擇一：
1. **Cloudflare Named Tunnel**：使用專屬網域（如 `mcp.tg25.win`），配置固定憑證與路由。
2. **維持 File Dispatch 為基底**：在 Tunnel 尚未固定前，持續以 `.taskflow/shannie/outbox/` 運作，不阻礙任何業務進度。

## 4. 結論
- **基礎通道**：File Dispatch 100% 正常。
- **高速通道**：關鍵在於 Plugin 需補上 Authorization Header。HQ 已備妥修復檔案，確認後即可執行更新發布。

---
**處理者**：HQ (wawIoT 協調中心)  
**日期**：2026-09-29 03:05
