# WaW 系統架構與 GitHub Repositories 對照表

**最後更新**: 2026-09-02
**狀態**: 正式規範

---

## 🗺️ 服務網域與對應 Repository 總表

| 服務網域 (URL) | 伺服器路徑 (VPS yd174) | 對應的 GitHub Repository | 真實定位 / 身份 | 狀態 |
| :--- | :--- | :--- | :--- | :--- |
| **`iot.tg25.win`** | `/www/wwwroot/iot.tg25.win` | `joesong-eng/waw-business.git` | **核心營運後台 (v9 Business Core)**。<br>處理商務、訂閱、計費、裝置、M0~M10 核心模組。 | ✅ 活躍運行中 (絕未退役) |
| **`signal.tg25.win`** | `/www/wwwroot/signal.tg25.win` | `joesong-eng/signal-hub-standalone.git` | **獨立信號標準站點 (SignalHub Standalone)**。<br>處理 Layer 0 信號採集、8通道映射、Webhook 推送。 | ✅ 統一並運行中 |
| **本機開發總控** | `~/Documents/WaW/` | `joesong-eng/waw-HQ.git` | **本機總控與知識庫 Monorepo**。<br>用於管理 Agent 派工、規格書、各子專案開發。 | ✅ 本機開發中 |

---

## 🚫 已廢棄 / 封存的 Repositories

| Repository | 原用途 | 處理方式 |
| :--- | :--- | :--- |
| `waw-signal-hub.git` | SignalHub 舊版 | ✅ 已合併至 `signal-hub-standalone.git`，建議在 GitHub 封存 (Archive)。 |

---

## 🤖 各 Agent 與部署規範

1. **Sophie (Owner) / waw-business**：
   - 部署網域：`iot.tg25.win`
   - 遠端倉庫：`waw-business.git`
   - 部署方式：透過 `waw_ops.sh deploy sophie` 觸發遠端拉取與快取清理。

2. **Sidney (SignalHub)**：
   - 部署網域：`signal.tg25.win`
   - 遠端倉庫：`signal-hub-standalone.git`
   - 部署方式：透過 `waw_ops.sh deploy signalhub` 觸發遠端拉取。

3. **Alliance (盟友系統)**：
   - 目前狀態：無獨立遠端 VPS 部署需求（或已整合），**不需要手動部署**。

