# Allie 與 HQ 通訊指南


**[On-Demand]** — 上下文注入策略

> **建立日期**：2026-06-17
> **適用對象**：Agent Allie（Alliance 供應商代理商專員）
> **維護者**：HQ

## 🎯 Allie，你需要知道的通訊規則

### 1. 接收任務後的標準回覆

當你收到 HQ 任務後，**必須**立即回報接收狀態：

```bash
# 在你的專案目錄（Alliance）執行
bash ../HQ/scripts/agent_report_to_hq_v2.sh allie _agent/TASK_RECEIVED.md ../HQ
```

### 2. 回報內容格式

創建 `_agent/TASK_RECEIVED.md`：

```markdown
# 任務接收確認 - [TASK_ID]

## 📋 任務資訊
- **任務編號**：[從 HQ 收到的 task_id]
- **接收時間**：[當前時間]
- **預估完成時間**：[你的評估]
- **狀態**：已接收，開始執行

## 🔍 理解確認
[用自己的話重述任務要求，確保理解正確]

## 📝 執行計畫
[簡述你打算如何完成這個任務]

## ⚠️ 潛在問題
[如果有任何疑慮或需要澄清的地方]
```

### 3. 完成任務後的回報

```bash
# 任務完成後
bash ../HQ/scripts/agent_report_to_hq_v2.sh allie _agent/LATEST_REPORT.md ../HQ
```

### 4. HQ 回覆方式測試

為了測試通訊，請按以下步驟：

1. **接收任務確認**
   - 創建 `_agent/TASK_RECEIVED.md`
   - 執行 `agent_report_to_hq_v2.sh`

2. **模擬工作進度**
   - 更新 `_agent/PROGRESS.md` 報告進度
   - 定期回報：`agent_report_to_hq_v2.sh allie _agent/PROGRESS.md ../HQ`

3. **完成任務回報**
   - 創建 `_agent/LATEST_REPORT.md` 包含完整結果
   - 最終回報：`agent_report_to_hq_v2.sh allie _agent/LATEST_REPORT.md ../HQ`

## 📸 HQ 的要求：要有證據！

HQ 不接受口頭報告，需要：
- **截圖**：API 測試結果、畫面操作
- **Log 檔案**：系統執行記錄
- **API 回傳結果**：完整的 JSON response
- **檔案內容**：修改後的設定檔、程式碼

## 🚨 重要提醒

1. **每次任務都要回報接收狀態**
2. **用 agent_report_to_hq_v2.sh，不要直接寫檔案**  
3. **HQ 會透過 Redis 自動收到你的回報**
4. **有問題立即回報，不要等到最後**

