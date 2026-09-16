# 任務：TASK_20260908_SIDNEY_UPDATE_SIGNAL_SEMANTIC_DOCS

**派發時間**：2026-09-08 20:15  
**優先級**：high  
**負責人**：sidney

---

## 📋 任務內容

更新 SignalHub 文檔與介面，明確 UI2 信號語義

## 背景
HQ 已正式確認 WAW Signal 語義規範：
- UI2 = 洗分按鈕觸發（事件通知，delta: 1）
- 實際退分數量由遊戲商在 Webhook 回應的 actual_points 返回
- 如需監控退幣馬達，可使用 UI3 擴展配置

參考文檔：
- .taskflow/hq/outbox/ANSWER_20260908_HQ_SIGNAL_TYPE_AGGREGATION_BEHAVIOR.md
- brains/knowledge/02_technical_standards/WAW_SIGNAL_SEMANTIC_SPECIFICATION.md

## 任務清單

### 1. 更新第三方對接文檔（優先級：High）
文件：PROJECT/SignalHub/docs/THIRD_PARTY_INTEGRATION_GUIDE.md

新增「信號語義與責任邊界」章節：
- 明確說明 UI1/UI2 為「按鈕觸發事件」而非「實際金額」
- 強調 actual_points 由遊戲商決定
- 提供清晰的責任劃分說明

### 2. 更新 SignalHub 腳位設定介面（優先級：Medium）
文件：resources/views/signal-hub/pins.blade.php

調整 UI1/UI2 標籤與提示：
- UI1 標籤：「開分按鈕」
- UI2 標籤：「洗分按鈕」
- 增加 Tooltip 提示：「玩家請求觸發次數（實際點數由遊戲商決定）」
- UI3 標籤：「輔助輸入 3」，提示：「可選：退幣馬達計數、狀態感測、警報等」

### 3. 更新 WAW Signal Standard 文檔（優先級：Low）
文件：PROJECT/SignalHub/docs/WAW_SIGNAL_STANDARD_v1.0.md

在 UI2 定義處補充說明：
- UI2 為洗分按鈕觸發（事件通知）
- 如需監控退幣馬達實際數量，建議使用 UI3

## 驗收標準
- [ ] 文檔已更新並提交 Git
- [ ] 介面標籤已修改並部署至 signal.tg25.win
- [ ] 提交回報至 .taskflow/signalhub/outbox/ 或 .taskflow/sidney/outbox/

## 預計完成時間
2026-09-09 12:00

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260908_SIDNEY_UPDATE_SIGNAL_SEMANTIC_DOCS

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
**派發時間**：2026-09-08 20:15
