# 任務：TASK_20260915_MINA_AUDIT_DEV_TOKEN_DEPENDENCY

**派發時間**：2026-09-15 14:30  
**優先級**：P0  
**負責人**：Mina (Member)

---

## 📋 任務內容

調查 `/api/dev/token` 端點依賴關係，確認改 `APP_ENV=production` 是否安全。

### 具體要求

1. **搜尋前端所有 JS/Vue/Blade 檔案**，查是否有呼叫 `/api/dev/token` 或 `dev/token`
2. **搜尋 `TEST_MODE_886937271782` 後門**在哪些地方被引用，前端是否依賴
3. **確認 LINE OAuth 登入流程**在 `APP_ENV=production` 下是否正常（不依賴 dev/token）
4. **列出所有會因 `APP_ENV=production` 而關閉的功能/端點**
5. **回報結論**：改 production 會不會斷掉任何線上功能

### ⚠️ 注意

- **只查不動** — 不要修改 `.env`，不要改任何代碼
- 查完回報給 HQ

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260915_MINA_AUDIT_DEV_TOKEN_DEPENDENCY

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：mina

## 調查結果

### 1. /api/dev/token 引用清單
（列出所有引用的檔案和行號）

### 2. TEST_MODE 後門引用清單
（列出所有引用的檔案和行號）

### 3. APP_ENV=production 影響評估
（會關閉哪些功能）

### 4. 結論
✅ 可安全切換 / ❌ 不可切換（原因）

---
**回報者**：mina  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-09-15 14:30

