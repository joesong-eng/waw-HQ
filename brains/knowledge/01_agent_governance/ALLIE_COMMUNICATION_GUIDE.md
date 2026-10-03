# Allie 與 HQ 通訊指南

> **[On-Demand]** 上下文注入策略
> **建立日期**：2026-06-17
> **最後更新**：2026-10-03
> **適用對象**：Agent Allie（Alliance 供應商代理商專員）
> **維護者**：HQ

## 🎯 Allie，你需要知道的通訊規則

> ⛔ 舊版 `_agent/`、`../HQ/scripts/`、Redis 自動收訊已全面廢除。
> 現行唯一管道為 **`.taskflow` 純檔案信箱**。

### 1. 接收任務後的標準回覆

當你收到 HQ 任務後，**必須**立即回報接收狀態：

```bash
# 在你的專案目錄（Alliance）執行
cat > /tmp/TASK_RECEIVED.md << 'EOF'
# 任務接收確認 - [TASK_ID]

## 📋 任務資訊
- **任務編號**：[從 HQ 收到的 task_id]
- **接收時間**：[當前時間]
- **預估完成時間**：[你的評估]
- **狀態**：已接收，開始執行

## 🔍 理解確認
[用自己的話重述任務要求]

## 📝 執行計畫
[簡述你打算如何完成]

## ⚠️ 潛在問題
[如有疑慮或需澄清]
EOF

bash ../../dev_tools/agent_report_to_hq_v2.sh allie /tmp/TASK_RECEIVED.md
```

### 2. 完成任務後的回報

```bash
bash ../../dev_tools/agent_report_to_hq_v2.sh allie /tmp/LATEST_REPORT.md
```

回報會寫入 `.taskflow/alliance/outbox/`。

### 3. 進度更新

需要更新進度時，同樣產出 `.md` 後以 `agent_report_to_hq_v2.sh` 提交。

## 📸 HQ 的要求：要有證據！

HQ 不接受口頭報告，需要：
- **截圖**：API 測試結果、畫面操作
- **Log 檔案**：系統執行記錄
- **API 回傳結果**：完整的 JSON response
- **檔案內容**：修改後的設定檔、程式碼

## 🚨 重要提醒

1. **每次任務都要回報接收狀態**
2. **用 `agent_report_to_hq_v2.sh` 提交到 `.taskflow/alliance/outbox/`，不要直接散落檔案**
3. **有問題立即回報，不要等到最後**

---
**維護者**：HQ
**最後更新**：2026-10-03
