# Ina 詢問：waw-business 現況與去留決策

**時間**：2026-08-31 09:45
**詢問者**：ina

---

## 背景確認

Ina 已調查清楚，現況如下：

### waw-business 就是 PROJECT/Owner（Sophie 負責的商戶後台）
- Git remote：`https://github.com/joesong-eng/waw-business.git`
- 本地路徑：`/Users/ilawusong/Documents/WaW/PROJECT/Owner`
- 最新 commit：`8e33952` fix(m3/devices): responsive layout（2026-08-24）
- 負責 Agent：Sophie

### VPS 現況：waw-business **尚未部署**
- `iot.tg25.win` 的 nginx 目前指向 `/var/www/waw-iot/public`（waw-iot，IoT後端）
- VPS 上找不到 waw-business 的部署目錄
- 換句話說：商戶後台 `iot.tg25.win` 目前實際服務的是 `waw-iot`，不是商業邏輯層

### 架構文件說：兩者應**並存、分工**
根據 `V9_SYSTEM_SPLITTING_DESIGN.md`：
- `waw-iot`：物聯網採集、高頻寫入（繼續跑）
- `waw-business`：人與訂閱、商業邏輯（**應部署但未部署**）

---

## 請 HQ 裁決

**waw-business（商戶後台）的去留**：

| 選項 | 說明 | Ina 需要做什麼 |
|------|------|--------------|
| A. 繼續維持，要部署 | waw-business 仍是必要系統，需補上 VPS 部署 | Ina 協助環境建置（nginx、PHP-FPM、git clone、.env），Sophie 負責代碼 |
| B. 正式退役，清除 | waw-business 功能已整合進 waw-iot，不再需要獨立服務 | Ina 清除 GitHub repo 引用、更新文件，本地代碼保留或歸檔 |

請 HQ 明確裁決 A 或 B，Ina 收到後立即執行。

---
**詢問者**：ina
**時間**：2026-08-31 09:45

