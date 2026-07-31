# Skill: 部署到 ait.tg25.win

## 觸發關鍵字
- 部署
- deploy
- 上線
- 發布

## 執行流程

### 1. 確認文件路徑
- 本地：`/Users/ilawusong/Documents/sysWawIot/ait.tg25.win/`
- 遠端：`/www/wwwroot/ait.tg25.win/`（VPS yd47）

### 2. Git 操作
```bash
cd /Users/ilawusong/Documents/sysWawIot/ait.tg25.win
git add .
git commit -m "feat: [任務描述]"
git push origin main
```

### 3. 遠端部署
```bash
ssh yd47 "cd /www/wwwroot/ait.tg25.win && git pull origin main"
```

### 4. 回報結果
```
✅ 部署完成
- 提交：[commit hash]
- 網址：https://ait.tg25.win
- 時間：[timestamp]
```

## 錯誤處理
- Git 衝突 → 回報需要手動處理
- SSH 失敗 → 檢查 VPS 連線
- 文件不存在 → 先創建文件
