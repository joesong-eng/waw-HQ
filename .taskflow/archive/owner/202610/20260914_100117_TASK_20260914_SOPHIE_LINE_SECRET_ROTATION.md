# 任務：TASK_20260914_SOPHIE_LINE_SECRET_ROTATION
**派發時間**：2026-09-14 11:00
**優先級**：CRITICAL
**負責人**：Sophie (Owner)
**來源**：Member Code Audit P0-2 跨 Agent 協調需求

## 任務描述

Mina 正在將 Member 端 LINE Login 憑證從硬編碼移至 .env。但 LINE Channel Secret 已進入 Git 歷史，必須在 LINE Developers Console rotate。

---

## 需處理項目

### 1. LINE Developers Console Secret Rotation
- 登入 LINE Developers Console
- 找到 Channel ID: 2009625522
- 重新發行 Channel Secret（舊 Secret: 20f443a0498bcdbfb1e24906f40704e3）
- 將新 Secret 提供給 HQ（透過安全管道，不要寫在任務檔裡）
- HQ 會更新 Member server 的 .env

### 2. 確認 LINE Login redirect URL 設定
- 確認 Console 中 redirect URL 是否已改為 Code Exchange 模式的 callback URL
- Mina 正在將 OAuth flow 從 implicit grant 改為 code exchange
- 確認 redirect URL 設為：https://win.tg25.win/api/auth/line/callback

### 3. 通知
- 完成後回報至 outbox：新 Secret 已 rotate（不需寫明 Secret 值）、redirect URL 已更新
- 不接受口頭報告

---

**派發者**：HQ
**派發時間**：2026-09-14 11:00
