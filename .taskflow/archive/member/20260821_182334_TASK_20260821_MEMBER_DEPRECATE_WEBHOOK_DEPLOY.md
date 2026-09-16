# 任務：TASK_20260821_MEMBER_DEPRECATE_WEBHOOK_DEPLOY

**派發時間**：2026-08-21 18:23  
**優先級**：high  
**負責人**：mina

---

## 📋 任務內容

【伺服器安全加固後續：廢棄 Webhook 部署 Controller 並完成安全評估】

1. 背景：
   - 伺服器 PHP 8.2 已在 disable_functions 禁用 shell_exec、proc_open、putenv，符合長期金融級資安標準。
   - CLI 與 FPM 獨立，Reverb (WebSocket) 與 Firebase Auth 經實測運行正常。
   - 舊有的 DeployController (/api/deploy/webhook) 依賴 shell_exec，現已不符安全架構，需正式廢棄。

2. 執行項目：
   - 將 Member 專案中的 DeployController.php 標記 deprecated 或移除對應 route (/api/deploy/webhook)。
   - 確認標準部署路徑統一採用 SSH / CLI 部署 SOP（參考 knowledge/04_ops_and_deployments/MEMBER_DEPLOYMENT_GUIDE.md）。
   - 回報確認。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260821_MEMBER_DEPRECATE_WEBHOOK_DEPLOY

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：mina

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：mina  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-08-21 18:23
