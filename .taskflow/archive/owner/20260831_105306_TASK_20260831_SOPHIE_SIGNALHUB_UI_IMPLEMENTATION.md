# 任務：TASK_20260831_SOPHIE_SIGNALHUB_UI_IMPLEMENTATION

**派發時間**：2026-08-31 10:53  
**優先級**：1  
**負責人**：owner

---

## 📋 任務內容

請依據 PROJECT/SignalHub/ui-spec/BACKEND_UI_SPEC.md 規格，實作 SignalHub 信號設定模組與獨立域名綁定：

1. 獨立域名綁定 (signal.tg25.win)：
   - 透過 Route::domain('signal.tg25.win') 獨立域名直通 SignalHub 模組。
   - 進入 signal.tg25.win 根目錄直接導向信號設定首頁。
   - 同時保留 iot.tg25.win/signal-hub/* 子路由相容。

2. 四大核心頁面實作（Laravel Blade + Tailwind + Alpine.js）：
   - /signal-hub/profiles (設定檔列表、搜尋、模板化、新增/編輯 Modal)
   - /signal-hub/profiles/{id}/pins (8 通道 UI1~UI4 / UO1~UO4 腳位映射自訂卡片)
   - /signal-hub/profiles/{id}/stats (統計規則配置)
   - /signal-hub/webhooks (第三方 Webhook 推送與 HMAC-SHA256 密鑰設定)

3. 遵循 UI 與後端規範：
   - 大字清晰、高對比、緊湊排版。
   - 完整對接資料庫表：signal_profiles, signal_pin_mappings, signal_stat_rules, signal_webhooks。

4. 開發完成後回報成果。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260831_SOPHIE_SIGNALHUB_UI_IMPLEMENTATION

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：owner

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：owner  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-08-31 10:53
