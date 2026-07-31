---
inclusion: always
---

# 技術操作常識

> SSH 別名、DB 架構、部署流程 → 查 `workspace-common-sense.md` 的索引表

---

## 各專案常用指令

### Laravel 專案（Member / Owner / Alliance）
```bash
php artisan optimize:clear   # 改完代碼必跑，清除所有快取
php artisan migrate --force  # 執行 DB migration
php artisan tinker           # 互動式查詢 DB
sudo systemctl restart reverb  # Member 專案重啟 WebSocket
```

### iHub 專案
```bash
npm install && npm run build  # 改完 src/ 必跑，否則瀏覽器看不到變更
# 部署後驗證：ssh yd47 "ls -la /www/wwwroot/ihub.tg25.win/dist/assets/*.js"
# 確認 dist 時間戳是最新的，才算真正部署完成
```

### Infra 專案
```bash
pip install -r requirements.txt
sudo systemctl restart mqtt-listener
# 生產環境運行的是 /home/ubuntu/kiosk_event_listener.py
# 修改後必須同步這個檔案並重啟，不只是 git push
```

---

## 高風險操作規則

### 修改生產環境服役的代碼
凡是修改正在生產環境服役的 Controller / Service / Listener / 前端掃碼邏輯，必須先做影響分析：

1. 這個檔案目前負責哪些現有功能？
2. 我要加的代碼會影響哪些現有流程？
3. 最壞情況是什麼？

**HQ 審核影響分析後才能動手。修改後必須驗證所有現有功能仍然正常。**

### 多 Agent 協作改動：必須定義部署順序（強制）

凡是多個 Agent 的改動之間有依賴關係，**不可以「同時進行」**，必須：

1. 在任務計劃裡明確寫出部署順序
2. 前一個 Agent 完成並經 HQ 驗證後，才通知下一個 Agent 開始
3. 向下相容必須作為驗收條件（計劃裡寫了不算，HQ 要親自測試）

**教訓來源**：`brains/history/LESSON_20260513_QRCODE_BROKE_BILL_CHAIN.md`
（QR Code 格式更新，Mina 改了前端但 Hubie 未 build，導致 5/11 做完的鈔票鏈中斷，損失半天）

### Agent 驗證規範
- Agent 回報完成 → HQ 必須親自驗證（curl / log / 瀏覽器截圖）
- 不接受口頭回報，驗證通過才算完成

---

## 跨 Workspace 讀文件

- **同 workspace**：用 `read_file` 工具
- **跨 workspace**（iHub、Member、Owner 等）：用 `execute_bash` + `grep`/`sed`，不用 `read_file`
