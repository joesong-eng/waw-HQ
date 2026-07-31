# HQ - 本地開發協調中心

HQ 是 wawIoT 遊藝場管理系統的多 Agent 協調樞紐，負責需求分析、任務規劃與分配，以及跨專案知識管理。

## 角色定位

**HQ 不是執行者，是協調者。**

- 分析需求，確認資料來源、通訊主題、系統邊界後，才發任務給對應 Agent
- 維護 `brains/knowledge/` 知識庫（唯一寫入權限）
- 透過 Chat Bridge 協調各 Agent 的工作

## Agent 分工

| Agent | 專案 | 網域 | 職責 |
|-------|------|------|------|
| Allie | Alliance | `ali.tg25.win` | 供應商與代理商管理 |
| Sophie | Owner | `iot.tg25.win` | 營運商後台與設備管理 |
| Mina | Member | `win.tg25.win` | 玩家前端與支付系統 |
| Ina | Infra | `api.tg25.win` | 資料庫、MQTT、基礎設施 |
| Hubie | iHub | `ihub.tg25.win` | Android iHub APK |
| Fio | Firmware | IOTkiosk_v0 | 兌幣卡韌體（`kiosk/+/`） |
| Coli | Firmware | IOTwawS3 | 通訊卡韌體（`device/+/`） |

## 兩種 ESP32 韌體（不可混淆）

| 韌體 | 用途 | MQTT 前綴 | 管理方 |
|------|------|-----------|-------|
| `IOTwawS3` (game_v0) | 遊戲機採集卡 | `device/{chip_id}/` | Owner |
| `IOTkiosk_v0` (kiosk_v0) | 紙鈔機收鈔卡 | `kiosk/{chip_id}/` | Member/Infra |

## 目錄結構

```
brains/
  knowledge/           # 知識庫（HQ 專屬寫入）
    01_agent_governance/   # Agent 協作協議
    02_technical_standards/ # MQTT、WebSocket 標準
    03_system_architecture/ # 系統架構
    04_deployment_operations/ # 部署與運維
    05_business_flows/     # 業務流程
  history/             # 事件記錄、教訓

.kiro/
  steering/            # Workspace 規則
  specs/               # 功能規格（進行中）

archive/
  completed/           # 已完成任務報告
  obsolete/            # 廢棄文件
  reference/           # 參考文件
```

## 核心規範

1. **設計先行**：發任務前必須確認資料來源、通訊主題、系統邊界
2. **查文件優先**：MQTT 主題查 `02_technical_standards/MQTT_TOPIC_STANDARD.md`，WebSocket 查 `WEBSOCKET_CHANNEL_STANDARD.md`
3. **要求實際證明**：不接受口頭報告，需截圖、log 或 API 回傳結果
4. **知識庫唯一寫入**：其他 Agent 需透過 Chat Bridge 提交，由 HQ 審核後寫入

## 通訊方式

主要：Chat Bridge (MCP `ai-chat-bridge`)，格式：`@AgentName <訊息>`

---

## 📚 私有知識庫網站 (MkDocs)

本專案文件與知識庫已整合 MkDocs，並以安全隧道方式部署於 VPS (`bessie202` 的 `127.0.0.1:8088`），確保 100% 私密不對外公開。

### 🔑 存取步驟

1. **建立安全隧道**：在 Mac 本地終端機執行以下指令：
   ```bash
   ssh -N -L 8088:localhost:8088 bessie202
   ```
2. **打開網頁**：在瀏覽器打開 [http://localhost:8088](http://localhost:8088) 即可瀏覽美化的知識庫網頁。

### 💡 優雅免指令設定 (推薦)

修改 Mac 本地的 `~/.ssh/config`，在 `bessie202` 的伺服器區塊中加入以下這行：
```ssh
LocalForward 8088 localhost:8088
```
設定完成後，只要您平時用終端機連線伺服器（例如執行 `ssh bessie202`），即可直接在 Mac 上瀏覽 [http://localhost:8088](http://localhost:8088)，免去每次手動開隧道的步驟。

