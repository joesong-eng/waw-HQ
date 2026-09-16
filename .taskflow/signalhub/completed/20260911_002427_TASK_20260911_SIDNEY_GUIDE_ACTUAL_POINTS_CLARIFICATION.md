# 任務：TASK_20260911_SIDNEY_GUIDE_ACTUAL_POINTS_CLARIFICATION

**派發時間**：2026-09-11  
**優先級**：high  
**負責人**：Sidney (SignalHub)  
**主管單位**：HQ 協調中心  

---

## 📋 背景說明

Joe 在檢閱線上對接指南（https://signal.tg25.win/signal-hub/guide）時指出：
頁面文字說明過度側重洗分（UI2），而在開分（UI1）的說明文字上存在疏漏：
1. 第三章引腳對照表：UI2 洗分寫了「於回調接收 actual_points」，但 UI1 開分完全沒提到「回調需回報 actual_points」。
2. 第四章 4.1 開分通道文字：只寫「依預設比例配分（例：每次開分 100 點，3 次即派發 300 點）」，斷在這邊，完全漏掉「必須在回調回應中回傳實際派發點數 actual_points」的核心要求，容易讓第三方遊戲商誤以為開分不用回報點數。

---

## 🎯 任務目標與具體執行範圍

請立即修改 `PROJECT/SignalHub/resources/views/signal-hub/guide.blade.php`：

1. **第三章（引腳分配表）UI1 欄位說明強化**：
   - 在 UI1 的「功能說明與硬體接線建議」欄位中，除了 PCNT 連按計數外，明確補充：
     「通知遊戲商依比例開分，並於回調中接收實際配發點數 `actual_points`。」與 UI2 保持對稱嚴謹。

2. **第四章 4.1（開分通道）業務邏輯段落強化**：
   - 在配分後明確補充一句：
     「配分完成後，遊戲商**必須在 HTTP 回應（或 reply_url 回調）中回傳實際派發點數 `actual_points`**（例如 300 點），以供 WAW 後台精準記錄現場營業入金與拆帳對帳。若未回傳實際點數，後台將無法計入營業額。」

3. **遠端部署與驗證**：
   - 提交 Git Commit，並執行 `./dev_tools/waw_ops.sh deploy sidney` 部署至正式站。
   - 驗證 `https://signal.tg25.win/signal-hub/guide` 頁面渲染無誤。

---

## 📝 回報要求
完成後請產出詳細報告至 `.taskflow/signalhub/outbox/`。

