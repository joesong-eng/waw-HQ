# 🌐 資料庫連線與治理規範 (Database Connection & Governance)


**[On-Demand]** — 上下文注入策略

> **版本**: 1.0.0
> **狀態**: 全域強制執行 (Inject to All Agents)
> **最後更新**: 2026-06-21

---

## 📍 資料庫位置與連接方式 (Where & How)

**核心真相：所有生產環境資料庫實體均位於 `infra` VPS (141.148.165.50)。**
除了 `Ina` (Infra Master) 外，任何 Agent 的本地環境或專屬 VPS 均**不具備**本地資料庫實體。

| 資料庫名稱 | 所在主機 (SSH Alias) | 主要使用方 (Agent) | 連接埠 (Port) |
| :--- | :--- | :--- | :--- |
| `iotv9` (Owner DB) | `infra` | Sophie, Allie, Hubie | 3308 (SSH Tunnel) |
| `waw_member_production` | `infra` | Mina | 3306 (Local on yd47*) |
| `Redis` | `infra` | 全體 | 6380 (SSH Tunnel) |

> *註：`yd47` (Member VPS) 透過內部網路連接 `infra` 的 MySQL，Agent 仍應視為遠端。

---

## 🛠️ 資料庫變更申請 (Change Request)

**唯一合法路徑：Agent 提案 → Ina 審核設計 → Ina 執行。**

1.  **禁止自行執行 DDL**：嚴格禁止在任何 VPS 上執行 `php artisan migrate` 或手動 `ALTER TABLE`。
2.  **禁止自行建立 Migration**：Laravel Migration 會導致多專案衝突，一律由 Ina 使用 Raw SQL 管理。
3.  **申請格式**：
    - 標註 `@Ina RFI: [DB 變更需求]`
    - 描述「要什麼」與「為什麼」
    - 不得附帶 SQL，不得指定欄位類型（由 Ina 專業設計）。

---

## 🚫 禁止行為 (Hard Prohibitions)

- **❌ 禁止直接連線**：嚴格禁止略過 SSH 隧道直接嘗試連線資料庫 IP。
- **❌ 禁止私下改動**：即使具備權限，嚴格禁止未經 Ina 與 HQ 核准私自改動生產環境 Schema。
- **❌ 禁止本地 DB 假設**：不要假設執行環境有 MySQL 服務。所有連線必須經由 `.env` 配置的隧道埠口。

---

## 🔄 常識記憶注入 (Neural Link)

- **Sophie (Owner)**：你的資料在 `infra`，透過 3308 連接。不要在 `yd174` 找 MySQL。
- **Mina (Member)**：你的資料在 `infra`，由 `Ina` 維護穩定性。
- **Allie (Alliance)**：你的資料也在 `infra`，這就是為什麼你之前 3308 連不上的原因（需要隧道）。
- **Hubie (iHub)**：APK 所有的資料上傳點最終都指向 `infra` 的資料庫。
- **Ina (Infra)**：你是資料庫的唯一守護者與執行者。

---

**制定者**：HQ (Coordinator)
**受眾**：Sophie, Mina, Ina, Allie, Hubie, Fio, Coli
