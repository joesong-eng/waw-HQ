# HQ - wawIoT 遊藝場管理系統協調中心

HQ 是 wawIoT 遊藝場管理系統的多 Agent 協調樞紐，負責需求分析、任務規劃與分配，以及跨專案知識管理。

## 角色定位

**HQ 不是執行者，是協調者。**

- 分析需求，確認資料來源、通訊主題、系統邊界後，才發任務給對應 Agent
- 維護 `brains/knowledge/` 知識庫（唯一寫入權限）
- 透過 `.taskflow` 純檔案信箱機制派工給各 Agent（舊 Redis Pub/Sub、Chat Bridge、`hq_gateway.py` 已全面廢除）

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
| Sidney | SignalHub | `signal.tg25.win` | 信號中心與開放標準 |

## 兩種 ESP32 韌體（不可混淆）

| 韌體 | 專案 | MQTT Topic 前綴 | 用途 |
|------|------|----------------|------|
| `IOTwawS3` (game_v0) | Coli | `device/{chip_id}/` | 遊戲機採集卡 |
| `IOTkiosk_v0` (kiosk_v0) | Fio | `kiosk/{chip_id}/` | 紙鈔機收鈔卡 |

## 目錄結構

```
brains/
  knowledge/           # 知識庫（HQ 專屬寫入）
    01_agent_governance/      # Agent 協作與派工協議
    02_technical_standards/   # MQTT、WebSocket、命名標準
    03_system_architecture/   # 系統架構、ADR
    04_deployment_operations/ # 部署與運維
    05_business_flows/        # 業務流程
  history/             # 事件記錄、教訓

.taskflow/             # 純檔案派工信箱（唯一派工體系）
  <agent>/inbox/       # HQ 派工收件
  <agent>/outbox/      # Agent 完工回報
  archive/             # 結案歸檔

dev_tools/
  waw_ops.sh           # 全域總控（派工、部署、狀態、遠端指令）
  agent_report_to_hq_v2.sh

PROJECT/               # 各 Agent 專案
  Alliance/ Owner/ Member/ Infra/ iHub/ IOTkiosk_v0/ IOTwawS3/ SignalHub/
```

## 核心規範

1. **設計先行**：發任務前必須確認資料來源、通訊主題、系統邊界
2. **查文件優先**：MQTT 查 `02_technical_standards/MQTT_TOPIC_STANDARD.md`，WebSocket 查 `WEBSOCKET_CHANNEL_STANDARD.md`
3. **要求實際證明**：不接受口頭報告，需截圖、log 或 API 回傳結果
4. **知識庫唯一寫入**：其他 Agent 需透過 `.taskflow` 回報，由 HQ 審核後寫入

## 派工與回報

```bash
# 短任務
./dev_tools/waw_ops.sh task <agent> <task_id> "<desc>" [priority]

# 完整工單（強烈推薦，防截斷）
./dev_tools/waw_ops.sh task <agent> <task_id> --file <工單檔案路徑> [priority]

# 檢視狀態 / 讀取回報 / 結案
./dev_tools/waw_ops.sh status
./dev_tools/waw_ops.sh report <agent>
./dev_tools/waw_ops.sh close <agent> <key>
```

- 派工協議：`brains/knowledge/01_agent_governance/SIMPLE_FILE_DISPATCH_PROTOCOL.md`
- 對外文件（開發者/合作夥伴）：`pubdocs/`
