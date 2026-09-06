# 基礎設施快速參考 (Infrastructure Reference)

> **版本**: 3.0
> **最後更新**: 2026-05-11
> **用途**: 快速查看伺服器別名、DB 架構、Nginx 配置、服務狀態

---

## 📋 目錄

1. [SSH 別名速查](#ssh-別名速查)
2. [資料庫架構](#資料庫架構)
3. [Nginx 配置查看](#nginx-配置查看)
4. [專案結構參考](#專案結構參考)
5. [環境配置](#環境配置)
6. [服務管理](#服務管理)

---

## SSH 別名速查

> **所有 SSH 指令必須使用別名，不得使用完整 IP**。別名定義在 `~/.ssh/config`。

| 別名 | IP | 用途 | 專案 |
|------|-----|------|------|
| `yd47` | `129.146.103.177` | Member + iHub VPS | `win.tg25.win`、`ihub.tg25.win` |
| `ihub` | `129.146.103.177` | iHub 專用別名（同 yd47） | `ihub.tg25.win` |
| `yd174` | `129.153.116.174` | Owner VPS | `iot.tg25.win` |
| `infra` | `141.148.165.50` | Infra VPS（DB + MQTT） | `api.tg25.win` |
| `db` | `141.148.165.50` | Infra DB 別名（同 infra） | MySQL、Redis |
| `yd16` | `137.131.50.16` | Alliance VPS | `ali.tg25.win` |
| `alliance` | `137.131.50.16` | Alliance 專用別名（同 yd16） | `ali.tg25.win` |
| `PM` | `132.226.87.202` | PM / bessie202 VPS | HQ 協調中心 |
| `bessie202` | `132.226.87.202` | PM 別名 | HQ 協調中心 |

**使用範例**：
```bash
# ✅ 正確
ssh yd47 "pm2 status"
ssh infra "sudo systemctl status mqtt-listener"

# ❌ 錯誤（不得使用完整 IP）
ssh yd47 "pm2 status"
```

---

## 資料庫架構

> **核心原則：所有 MySQL 資料庫實體都在 infra（`141.148.165.50`）。各專案透過隧道連接，不在本機。**

### DB 位置總覽

| 資料庫 | 所在主機 | 連接方式 | 使用方 |
|--------|---------|---------|--------|
| `iotv9`（Owner DB） | infra（`141.148.165.50`） | Port 3308 隧道 | Owner（yd174）、Infra |
| `waw_member_production`（Member DB） | infra（`141.148.165.50`） | Port 3306 本地（yd47 上有本地 MySQL） | Member（yd47） |
| Redis | infra（`141.148.165.50`） | Port 6380 隧道 | Owner、Member |

> ⚠️ `iotv9` 在 infra，Owner 專案（yd174）透過 Port 3308 遠端連接。直接在 yd174 上查 MySQL 查不到 iotv9，必須 SSH 到 infra 或透過 Laravel tinker。

### 查詢資料庫的正確方式

**查 iotv9（Owner DB）**：
```bash
# 方式 1：透過 Owner 的 Laravel tinker
ssh yd174 "php /www/wwwroot/iot.tg25.win/artisan tinker --execute=\"echo json_encode(DB::table('kiosks')->limit(5)->get());\""

# 方式 2：SSH 到 infra 直接查
ssh infra "mysql -u root iotv9 -e 'SELECT node_id FROM kiosks LIMIT 5;'"
```

**查 waw_member_production（Member DB）**：
```bash
# 透過 Member 的 Laravel tinker
ssh yd47 "php /www/wwwroot/win.tg25.win/artisan tinker --execute=\"echo json_encode(DB::table('kiosk_sessions')->select('kiosk_id')->limit(5)->get());\""
```

---

## Nginx 配置查看

> **原則**: 直接 SSH 查看，不存本機。需要時執行對應指令。

### Member VPS (win.tg25.win, yd47)

**查看 vhost 列表**:
```bash
ssh yd47 "sudo ls /www/server/panel/vhost/nginx/"
```

**查看 win.tg25.win 配置**:
```bash
ssh yd47 "sudo cat /www/server/panel/vhost/nginx/win.tg25.win.conf"
```

**查看 ihub.tg25.win 配置**:
```bash
ssh yd47 "sudo cat /www/server/panel/vhost/nginx/ihub.tg25.win.conf"
```

**檢查 Nginx 狀態**:
```bash
ssh yd47 "sudo nginx -t && sudo systemctl status nginx"
```

**重載 Nginx**:
```bash
ssh yd47 "sudo nginx -t && sudo systemctl reload nginx"
```

---

### Infra VPS (api.tg25.win, infra)

**查看 sites-enabled 列表**:
```bash
ssh infra "sudo ls /etc/nginx/sites-enabled/"
```

**查看 api.tg25.win 配置**:
```bash
ssh infra "sudo cat /etc/nginx/sites-enabled/api.tg25.win"
```

**查看 mqtt.tg25.win 配置**:
```bash
ssh infra "sudo cat /etc/nginx/sites-enabled/mqtt.tg25.win"
```

**檢查 Nginx 狀態**:
```bash
ssh infra "sudo nginx -t && sudo systemctl status nginx"
```

**重載 Nginx**:
```bash
ssh infra "sudo nginx -t && sudo systemctl reload nginx"
```

---

### Owner VPS (iot.tg25.win, yd174)

**查看 vhost 列表**:
```bash
ssh yd174 "sudo ls /www/server/panel/vhost/nginx/"
```

**查看 iot.tg25.win 配置**:
```bash
ssh yd174 "sudo cat /www/server/panel/vhost/nginx/iot.tg25.win.conf"
```

**檢查 Nginx 狀態**:
```bash
ssh yd174 "sudo nginx -t && sudo systemctl status nginx"
```

**重載 Nginx**:
```bash
ssh yd174 "sudo nginx -t && sudo systemctl reload nginx"
```

---

## 專案結構參考

### Member (win.tg25.win)

**專案路徑**: `/www/wwwroot/win.tg25.win`

**主要目錄**:
```
win.tg25.win/
├── app/
│   ├── Http/Controllers/
│   │   ├── Api/              # API 控制器
│   │   └── Web/              # Web 控制器
│   └── Models/               # 資料模型
├── resources/
│   └── views/                # Blade 模板
├── routes/
│   ├── web.php               # Web 路由
│   └── api.php               # API 路由
├── public/
│   └── build/                # 前端建置輸出
└── storage/                  # 儲存目錄
```

**關鍵服務**:
- Reverb WebSocket: `sudo systemctl status reverb`

---

### Owner (iot.tg25.win)

**專案路徑**: `/www/wwwroot/iot.tg25.win`

**主要目錄**:
```
iot.tg25.win/wawv9/
├── app/
│   ├── Http/Controllers/
│   │   ├── Iot/              # 後台控制器
│   │   └── Api/V9/           # API 控制器
│   └── Models/               # 資料模型
├── resources/
│   └── views/
│       └── iot/
│           ├── auth/         # 登入頁面
│           └── modules/      # M1~M9 模組
└── routes/
    └── web.php               # 主路由
```

**關鍵配置**:
- 資料庫: Infra VPS (Port 3308)
- Redis: Infra VPS (Port 6380)

---

### Infra (api.tg25.win)

**專案路徑**: `/home/ubuntu/tg25-infra`

**主要目錄**:
```
tg25-infra/
├── listener.py               # MQTT Listener 主程式
├── requirements.txt          # Python 依賴
├── config/                   # 配置文件
└── logs/                     # 日誌目錄
```

**關鍵服務**:
- MQTT Listener: `sudo systemctl status mqtt-listener`
- Mosquitto MQTT Broker: `sudo systemctl status mosquitto`

---

### Alliance (ali.tg25.win)

**專案路徑**: `/www/wwwroot/ali.tg25.win`

**主要目錄**:
```
ali.tg25.win/
├── app/
│   ├── Http/Controllers/     # 控制器
│   └── Models/               # 資料模型
├── resources/
│   └── views/                # Blade 模板
└── routes/
    └── web.php               # 路由
```

---

### iHub (ihub.tg25.win)

**專案路徑**: `/www/wwwroot/ihub.tg25.win`

**主要目錄**:
```
ihub.tg25.win/
├── src/                      # 前端源碼
├── public/                   # 靜態資源
└── dist/                     # 建置輸出
```

---

## 環境配置

### Member 環境

**資料庫**:
- Host: `localhost`
- Port: `3306`
- Database: `member_db`

**Redis**:
- Host: `localhost`
- Port: `6379`

**Reverb WebSocket**:
- Port: `8080`
- Protocol: `wss://`

---

### Owner 環境

**資料庫** (遠端 Infra):
- Host: `141.148.165.50`
- Port: `3308`
- Database: `iotv9`

**Redis** (遠端 Infra):
- Host: `141.148.165.50`
- Port: `6380`

**內部通訊**:
- 需帶 `X-Internal-Key` header

---

### Infra 環境

**MQTT Broker**:
- Host: `141.148.165.50`
- Port: `1883` (內部), `8883` (SSL)
- WebSocket: `8083`

**資料庫**:
- Port: `3308` (對外)
- Port: `3306` (本地)

**Redis**:
- Port: `6380` (對外)
- Port: `6379` (本地)

---

## 服務管理

### 常用服務指令

**查看服務狀態**:
```bash
sudo systemctl status <service-name>
```

**啟動服務**:
```bash
sudo systemctl start <service-name>
```

**停止服務**:
```bash
sudo systemctl stop <service-name>
```

**重啟服務**:
```bash
sudo systemctl restart <service-name>
```

**查看服務日誌**:
```bash
sudo journalctl -u <service-name> -f
```

---

### Member 服務

| 服務名稱 | 說明 | 管理指令 |
|---------|------|---------|
| `reverb` | WebSocket 服務 | `sudo systemctl restart reverb` |
| `nginx` | Web 伺服器 | `sudo systemctl reload nginx` |

---

### Infra 服務

| 服務名稱 | 說明 | 管理指令 |
|---------|------|---------|
| `mqtt-listener` | MQTT 監聽器（`mqtt/scripts/listener.py`）— V9 設備、統計 | `sudo systemctl restart mqtt-listener` |
| `kiosk_event_listener.py` | Kiosk_v0 事件監聽（獨立進程，非 systemd）— kiosk/+/event、kiosk/+/status | `ps aux \| grep kiosk_event_listener` |
| `mosquitto` | MQTT Broker | `sudo systemctl restart mosquitto` |
| `mysql` | 資料庫 | `sudo systemctl restart mysql` |
| `redis` | Redis 快取 | `sudo systemctl restart redis` |
| `nginx` | Web 伺服器 | `sudo systemctl reload nginx` |

---

### Owner 服務

| 服務名稱 | 說明 | 管理指令 |
|---------|------|---------|
| `nginx` | Web 伺服器 | `sudo systemctl reload nginx` |

---

## 快速診斷

### 檢查所有關鍵服務

**Member VPS**:
```bash
ssh yd47 "
sudo systemctl status reverb --no-pager && \
sudo systemctl status nginx --no-pager
"
```

**Infra VPS**:
```bash
ssh infra "
sudo systemctl status mqtt-listener --no-pager && \
sudo systemctl status mosquitto --no-pager && \
sudo systemctl status mysql --no-pager && \
sudo systemctl status redis --no-pager && \
sudo systemctl status nginx --no-pager
"
```

**Owner VPS**:
```bash
ssh yd174 "
sudo systemctl status nginx --no-pager
"
```

---

## MQTT 測試與除錯

> **來源**: Ina 提供（2026-05-26）  
> **用途**: 訂閱 MQTT 主題、查看 Retained 訊息、診斷設備通訊問題

### 訂閱 MQTT 主題

**基本訂閱指令**：
```bash
ssh infra "mosquitto_sub \
  -h mqtt.tg25.win \
  -p 8883 \
  --cafile /etc/mosquitto/certs/ca.crt \
  --cert /etc/mosquitto/certs/client.crt \
  --key /etc/mosquitto/certs/client.key \
  -t 'device/+/status' \
  -v"
```

**訂閱特定設備**：
```bash
ssh infra "mosquitto_sub \
  -h mqtt.tg25.win \
  -p 8883 \
  --cafile /etc/mosquitto/certs/ca.crt \
  --cert /etc/mosquitto/certs/client.crt \
  --key /etc/mosquitto/certs/client.key \
  -t 'device/{chip_id}/status' \
  -v"
```

**訂閱所有 Kiosk 事件**：
```bash
ssh infra "mosquitto_sub \
  -h mqtt.tg25.win \
  -p 8883 \
  --cafile /etc/mosquitto/certs/ca.crt \
  --cert /etc/mosquitto/certs/client.crt \
  --key /etc/mosquitto/certs/client.key \
  -t 'kiosk/+/event' \
  -v"
```

### 查看 Retained 訊息

**查看特定設備的 Retained 狀態**：
```bash
ssh infra "mosquitto_sub \
  -h mqtt.tg25.win \
  -p 8883 \
  --cafile /etc/mosquitto/certs/ca.crt \
  --cert /etc/mosquitto/certs/client.crt \
  --key /etc/mosquitto/certs/client.key \
  -t 'device/{chip_id}/status' \
  -v \
  -C 1"
```

**說明**：
- `-C 1`：收到 1 條訊息後自動退出
- 如果有 Retained 訊息，會立即顯示
- 如果沒有輸出（timeout），表示沒有 Retained 訊息

### 檢查 Listener 日誌

**查看 Listener 完整 log**：
```bash
ssh infra "sudo journalctl -u mqtt-listener -n 500 --no-pager"
```

**搜尋特定設備的訊息**：
```bash
ssh infra "sudo journalctl -u mqtt-listener --no-pager | grep '{chip_id}'"
```

**即時監控 Listener**：
```bash
ssh infra "sudo journalctl -u mqtt-listener -f"
```

**搜尋最近的狀態訊息**：
```bash
ssh infra "sudo journalctl -u mqtt-listener --since '1 hour ago' --no-pager | grep 'ESP32_STATUS'"
```

### 完整診斷流程

**步驟 1：確認設備當前的 Retained 狀態**
```bash
ssh infra "mosquitto_sub -h mqtt.tg25.win -p 8883 \
  --cafile /etc/mosquitto/certs/ca.crt \
  --cert /etc/mosquitto/certs/client.crt \
  --key /etc/mosquitto/certs/client.key \
  -t 'device/{chip_id}/status' -v -C 1"
```

**預期結果**：
- 顯示 `device/{chip_id}/status online`：設備在線 ✅
- 顯示 `device/{chip_id}/status offline`：設備離線 ❌
- 沒有輸出：沒有 Retained 訊息 ❌

**步驟 2：檢查 Listener 是否收到訊息**
```bash
ssh infra "sudo journalctl -u mqtt-listener --since '24 hours ago' --no-pager | grep '{chip_id}' | grep -i 'status'"
```

**預期結果**：
- 應該看到 `[ESP32_STATUS] {chip_id}: online` 或 `offline`

**步驟 3：檢查資料庫更新**
```bash
ssh infra "mysql -u iot_user -pIotUser2025Secure iotv9 -e \"SELECT chip_id, status, last_seen_at FROM devices WHERE chip_id='{chip_id}';\""
```

### 認證說明

**TLS 憑證認證**：
- Listener 使用 TLS 憑證認證，不使用用戶名密碼
- 憑證位置：`/etc/mosquitto/certs/`
  - `ca.crt` - CA 憑證
  - `client.crt` - 客戶端憑證
  - `client.key` - 客戶端私鑰

**Port 說明**：
- `8883`：TLS 加密（對外）
- `1883`：本地連接（僅 localhost）
- `9001`：WebSocket（僅 localhost）

---

## 📚 相關文檔

- `DEPLOYMENT_GUIDE.md` - 部署流程指南
- `V9_OPS_AUTOMATION.md` - V9 自動化運維工具
- `../02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - MQTT 主題規範

---

**制定者**: HQ  
**最後更新**: 2026-05-26  
**版本**: 3.1

---

## 🔗 文件神經連結

### 強關聯（必讀）
> 部署操作前，必須先閱讀以下文件

- `DEPLOYMENT_GUIDE.md` - 部署流程指南，包含完整的部署步驟和問題處理
- `../NAMING_AUTHORITY.md` - 名稱定義來源索引，確保使用正確的專案名稱和識別碼

### 中關聯（建議讀）
> 了解完整系統架構，建議閱讀

- `../02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - MQTT 主題規範，Infra 服務相關
- `../05_business_flows/kiosk_v0_exchange/KIOSK_IDENTIFICATION_SYSTEM.md` - 識別碼體系，理解 chip_id/node_id 對應關係
- `V9_OPS_AUTOMATION.md` - V9 自動化運維工具，快速部署指令

### 弱關聯（參考）
> 可選閱讀，提供額外背景

- `../02_technical_standards/WEBSOCKET_CHANNEL_STANDARD.md` - WebSocket 頻道規範，Member Reverb 服務相關
- `../01_agent_governance/AGENT_RESPONSIBILITY_BOUNDARIES.md` - Agent 職責邊界，了解各專案負責的 Agent

### 排除混淆
> 容易混淆但實際無關的文件

- `../05_business_flows/game_v0_arcade/GAME_V0_FLOW_AND_SESSION.md` - 遊戲機業務流程，與基礎設施無直接關係（但 Owner 專案部署在 yd174）
