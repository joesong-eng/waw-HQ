# 任務：TASK_20260831_SIDNEY_SIGNALHUB_STANDALONE_PROJECT

**派發時間**：2026-08-31 17:15  
**優先級**：1  
**負責人**：sidney

---

## 📋 任務內容

請開始進行 PROJECT/SignalHub 獨立站點專案建置與開發：
1. 站點定位：獨立 Web 站點 (signal.tg25.win)，對應 VPS 獨立目錄 /www/wwwroot/signal.tg25.win。
2. 搭建專案架構：
   - 建立 PROJECT/SignalHub 專案工程骨架（路由、控制器、View、配置）。
   - 對接 MySQL 資料庫 (iotv9) 與 5 張 SignalHub 表 (signal_profiles, signal_pin_mappings, signal_stat_rules, signal_webhooks, signal_events)。
3. 實作四大核心頁面 (Tailwind + Alpine.js，大字高對比緊湊排版)：
   - / (或 /profiles): 信號設定檔列表、搜尋、標記模板、新增/編輯 Modal
   - /profiles/{id}/pins: 8 通道 (UI1~UI4 / UO1~UO4) 映射設定卡片
   - /profiles/{id}/stats: 統計指標與分組規則配置
   - /webhooks: 第三方 Webhook 推送與 HMAC-SHA256 密鑰設定
4. 對外 API 端點：
   - /api/v9/signal-hub/*
5. 完成後透過 waw_ops 回報成果。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260831_SIDNEY_SIGNALHUB_STANDALONE_PROJECT

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：sidney

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：sidney  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-08-31 17:15
