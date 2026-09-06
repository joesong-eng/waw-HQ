# WAW 全域環境拓撲與連線權威常識卡 (SSOT)

> **版本**: 2.1.0  
> **更新日期**: 2026-09-06  
> **權威等級**: 🔴 最高指導規範 (MANDATORY & AUTHORITATIVE)  
> **維護者**: HQ (協調中心)  
> **適用對象**: 所有 Agent (Sophie, Mina, Ina, Allie, Hubie, Fio, Coli, Sidney) 與協調者

---

## 🛡️ 核心紅線禁令 (Zero-Tolerance Rules)

1. **嚴禁使用 raw IP 直連與猜測 Port 22**：
   - 本機（Mac）已配置好 `~/.ssh/config`，**必須一律使用 SSH 別名**（例如 `ssh yd174`、`ssh mina`）。
   - Oracle Cloud VPS 一律為 **Port 39022**、使用者 **ubuntu**、憑證 **~/.ssh/id_rsa**。
   - 嚴禁用 `root@<ip>`，嚴禁使用預設 Port 22 直連！
2. **嚴禁在 CLI 命令列洩漏明文密碼**：
   - 嚴禁執行 `mysql -u root -p<password>` 或任何包含密碼的 Shell 一行指令！此類動作會被系統日誌與行程監控捕獲。
3. **嚴禁混淆伺服器角色與資料庫拓撲**：
   - Web 伺服器（`yd174`, `yd177`, `yd16`）**並非資料庫本體**。
   - 所有業務資料庫（`iotv9` 等）集中託管在 **Infra DB 伺服器（`infra`, 141.148.165.50）**。
   - Web 專案是透過 Laravel `.env` 或 Port 3308 穿透連線。**在 Web 伺服器本機下 `mysql` 直連是無效且錯誤的行為**。
4. **本機代碼純淨原則**：
   - 本機環境僅供程式碼撰寫與 Git 版本控制。
   - 嚴禁在本機執行 `php artisan`（migrate, serve, tinker）、`npm/pnpm build`、本地 Web 伺服器或測試指令。

---

## 🗺️ 伺服器拓撲與別名對照表 (SSH Alias Mapping)

| 別名 (SSH Alias) | 實體 IP | SSH 端口 | 使用者 | 金鑰路徑 | 負責 Agent | 託管站點 / 服務 | 伺服器實體路徑 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`yd174`**<br>`v9`, `Owner`, `blc` | `129.153.116.174` | `39022` | `ubuntu` | `~/.ssh/id_rsa` | **Sophie**<br>**Sidney** | Owner 後台 (`iot.tg25.win`)<br>SignalHub (`signal.tg25.win`) | `/www/wwwroot/iot.tg25.win`<br>`/www/wwwroot/signal.tg25.win` |
| **`yd177`**<br>`mina`, `ihub`, `yd47` | `129.146.103.177` | `39022` | `ubuntu` | `~/.ssh/id_rsa` | **Mina**<br>**Hubie** | Member 前端 (`win.tg25.win`)<br>iHub API (`ihub.tg25.win`) | `/www/wwwroot/win.tg25.win`<br>`/www/wwwroot/ihub.tg25.win` |
| **`yd16`**<br>`alliance` | `137.131.50.16` | `39022` | `ubuntu` | `~/.ssh/id_rsa` | **Allie** | Alliance 代理/供應商 (`ali.tg25.win`) | `/www/wwwroot/ali.tg25.win` |
| **`infra`**<br>`db` | `141.148.165.50` | `39022` | `ubuntu` | `~/.ssh/id_rsa` | **Ina** | **Central MySQL (`iotv9`)**<br>MQTT Broker (`mosquitto`) | `/home/ubuntu/tg25-infra` |
| **`bessie202`**<br>`HQ`, `PM` | `132.226.87.202` | `39022` | `ubuntu` | `~/.ssh/id_rsa` | **HQ** | HQ 協調中樞 / Redis Taskflow | `/home/ubuntu` |

---

## 🗄️ 資料庫架構與查詢標準

1. **資料庫位置**：
   - 核心業務 DB `iotv9` 位於 `infra`（`141.148.165.50`）。
2. **Web 專案（Owner / SignalHub / Member / Alliance）如何查資料？**：
   - **標準方式 1**：透過 Laravel Tinker（由 Laravel 依據 `.env` 建立連線）：
     ```bash
     ssh yd174 "cd /www/wwwroot/signal.tg25.win && php artisan tinker --execute='echo json_encode(App\Models\Device::limit(3)->get());'"
     ```
   - **標準方式 2**：由 **Ina (Infra)** 負責直接在 `infra` 上執行資料庫檢查與維護，其他 Agent 不得跨權限操作 DB。
3. **嚴格禁止**：
   - ❌ 嚴禁在 `yd174` 或其他 Web 主機上執行 `mysql -u root ...`。

---

## 🛠️ 開發與遠端維運指令標準 (Dev Tools Priority)

所有遠端操作與部署，**第一優先使用 WAW 總控工具**：

```bash
# 1. 在遠端 VPS 執行指令 (自動帶入對應主機與路徑)
./dev_tools/waw_ops.sh remote <agent> "<指令>"
# 範例：檢查 Sidney 路由
./dev_tools/waw_ops.sh remote sidney "php artisan route:list"

# 2. 一鍵標準部署 (自動 pull, migrate, cache clear, build, 重啟服務)
./dev_tools/waw_ops.sh deploy <agent>
# 範例：部署 Sidney
./dev_tools/waw_ops.sh deploy sidney

# 3. 需手動連線時，直接使用別名
ssh yd174
ssh mina
ssh alliance
ssh infra
```
