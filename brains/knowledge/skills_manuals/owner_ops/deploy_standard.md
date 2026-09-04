# 🚀 技能：V9 標準部署流程 (Deploy Skill)

> 當 Agent 完成 PHP/View/JS 修改後，應參考此技能建議老闆進行部署。

## 1. 觸發情境
*   修改 `wawv9` 目錄下的任何代碼。
*   新增 Migration。
*   修改 `.env` (需額外說明)。

## 2. 標準指令集 (SOP)

### 情境 A：單純修改 PHP 或 Blade
```bash
# 1. 本地提交
git -C wawv9 add -A && git -C wawv9 commit -m "feat: [OwnerOps] 說明變更" && git -C wawv9 push

# 2. Server 拉取 (與主手冊一致的穩定流程)
ssh -i ~/.ssh/id_rsa -p 39022 ubuntu@129.153.116.174 "cd /www/wwwroot/iot.tg25.win/wawv9 && git fetch origin main && git reset --hard origin/main && php artisan optimize:clear"
```

### 情境 B：修改前端 (Tailwind/Alpine)
```bash
# 同上，但 Server 端需額外 build
ssh -i ~/.ssh/id_rsa -p 39022 ubuntu@129.153.116.174 "cd /www/wwwroot/iot.tg25.win/wawv9 && git fetch origin main && git reset --hard origin/main && pnpm install && pnpm run build && php artisan optimize:clear"
```

## 3. 注意事項
*   **不要** 在本地執行 `migrate`。
*   **不要** 直接在 Server 修改檔案。
