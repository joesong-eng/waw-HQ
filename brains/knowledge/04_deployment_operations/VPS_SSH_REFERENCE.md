# WAW VPS SSH 連線規範
# 
# 版本：v1.0 | 2026-08-31
# 維護者：HQ
# 所有 Agent 必讀，每次需要登入 VPS 時以本文件為準

## SSH 快速對照表

| 別名 | IP | Agent | 用途 | 指令 |
|------|----|-------|------|------|
| yd174 / v9 / Owner / blc | 129.153.116.174 | Sophie, Sidney | Owner後台 iot.tg25.win, signal.tg25.win | ssh yd174 |
| yd177 / mina / ihub | 129.146.103.177 | Mina, Hubie | Member win.tg25.win, iHub ihub.tg25.win | ssh mina |
| yd16 / alliance | 137.131.50.16 | Allie | Alliance ali.tg25.win | ssh alliance |
| infra / db | 141.148.165.50 | Ina | MySQL DB, MQTT Broker | ssh infra |
| bessie202 / HQ | 132.226.87.202 | HQ | HQ 控制台 | ssh HQ |
| ai105 | 158.101.23.105 | — | AI 伺服器 | ssh ai105 |
| tg180 / bot | 132.226.30.180 | — | syswaw, bot | ssh tg180 |

## 各 Agent 專屬 VPS

Sophie (Owner):
  ssh yd174
  路徑：/www/wwwroot/iot.tg25.win

Sidney (SignalHub):
  ssh yd174
  路徑：/www/wwwroot/signal.tg25.win（未來），現階段在 /www/wwwroot/iot.tg25.win

Mina (Member):
  ssh mina
  路徑：/www/wwwroot/win.tg25.win

Allie (Alliance):
  ssh alliance
  路徑：/www/wwwroot/ali.tg25.win

Ina (Infra):
  ssh infra
  路徑：/home/ubuntu/tg25-infra

Hubie (iHub):
  ssh mina
  路徑：/www/wwwroot/ihub.tg25.win

Coli / Fio (韌體):
  無直接 VPS，韌體燒錄在本地，OTA 透過 hware.tg25.win

## 鐵律：本機禁止執行以下任何操作

禁止在本機（Mac 本地）執行：
  - php artisan（包含 migrate, serve, tinker）
  - pnpm run build / npm run build
  - composer install / update
  - MySQL / Redis / MQTT 連線測試
  - HTTP 請求到任何 .tg25.win 域名
  - WebSocket 連線測試

所有測試、部署、DB 操作必須透過 SSH 連到對應 VPS 執行。

HQ 工具：
  部署：./dev_tools/waw_ops.sh deploy <agent>
  遠端指令：./dev_tools/waw_ops.sh remote <agent> "指令"
  直接 SSH：ssh yd174 / ssh mina / ssh alliance / ssh infra

## 全 Port 統一 39022（除 yd21 和 tg180）

所有主要 VPS 使用 Port 39022，User ubuntu，IdentityFile ~/.ssh/id_rsa
例外：
  yd21 (129.146.92.21)：Port 22
  tg180 (132.226.30.180)：Port 20220, User joesong
