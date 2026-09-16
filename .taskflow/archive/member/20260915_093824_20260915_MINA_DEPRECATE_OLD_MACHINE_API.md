# 任務：20260915_MINA_DEPRECATE_OLD_MACHINE_API

**派發時間**：2026-09-15 09:38  
**優先級**：high  
**負責人**：mina

---

## 📋 任務內容

[P1-5] 立即下線舊版 MachineController 與 /api/machine/* 路由。

## 問題
前端已切換到 /api/device/*，但舊版 MachineController.php (9.3KB)、MachineSession.php、routes/api.php 中 /api/machine/* 路由仍存活。
攻擊者可繞過新架構直接呼叫舊路由，觸發非預期行為。

## 執行項目
1. 全專案 grep -r '/api/machine' 確認已無前端引用
2. grep -r 'MachineController' Member/ 確認無其他依賴
3. 從 routes/api.php 移除 /api/machine/* 路由群組
4. 從 app/Http/Controllers/Api/ 移除 MachineController.php 與 MachineSession.php（若無引用）
5. 保留 git 歷史可追
6. php -l 語法檢查
7. Commit 訊息：refactor(api): remove deprecated MachineController and /api/machine/* routes (P1-5)
8. 推送 origin/main
9. 部署至 129.146.103.177
10. 部署後 curl 確認 /api/machine/* 回 404
11. 回報 Commit Hash、刪除檔案清單與驗證結果至 outbox

---

## 📝 回報格式

```markdown
# 任務回報：20260915_MINA_DEPRECATE_OLD_MACHINE_API

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
**派發時間**：2026-09-15 09:38
