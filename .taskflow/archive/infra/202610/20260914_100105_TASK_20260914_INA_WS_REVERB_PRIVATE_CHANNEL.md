# 任務：TASK_20260914_INA_WS_REVERB_PRIVATE_CHANNEL
**派發時間**：2026-09-14 11:00
**優先級**：CRITICAL
**負責人**：Ina (Infra)
**來源**：Member Code Audit P0-3 + 跨 Agent 協調需求

## 任務描述

Mina 正在將 Member 端 WebSocket 事件從 Public Channel 改為 PrivateChannel / PresenceChannel。需要你同步處理 Infra 端配合事項。

---

## 需處理項目

### 1. Reverb Server 設定確認
- 確認 Reverb server 已啟用 Private Channel 與 Presence Channel 支援
- 確認 Reverb 的 broadcasting 認證 endpoint 設定正確指向 Member 的 /broadcasting/auth
- 如有需要調整 config/reverb.php 或 .env 中的 Reverb 設定

### 2. MQTT Heartbeat Topic 確認（供 Member UX-P1-4 使用）
- Member 端超時邏輯需要改為看機台端活動
- 請確認目前 MQTT 中機台 heartbeat 的 topic 格式與 payload 欄位
- 回覆以下資訊給 HQ：
  - heartbeat topic pattern（例如：waw/kiosk/{kiosk_id}/heartbeat）
  - payload 欄位（例如：{ kiosk_id, session_id, timestamp, game_active: bool }）
  - Infra 端是否已有將 heartbeat 寫入 DB 或 Redis 的邏輯
- Member 端需要一個 API 或 WebSocket 事件來查詢機台是否活躍

### 3. SSL 憑證配合
- Mina 正在將 Member 對 Infra API 的 verify 從 false 改為 true
- 確認 Infra server（api.tg25.win）的 SSL 憑證為有效憑證（非自簽）
- 若為自簽，請提供 CA bundle 路徑或改用 Let's Encrypt

---

## 執行要求

1. 此任務與 Mina 的 TASK_20260914_MINA_P0_BACKEND_SECURITY 中的 P0-3 並行
2. 完成後回報至 outbox：修改的設定檔清單 + MQTT heartbeat topic 資訊 + SSL 憑證狀態
3. 不接受口頭報告

---

**派發者**：HQ
**派發時間**：2026-09-14 11:00
