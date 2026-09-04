# 任務：TASK_20260831_SIDNEY_HOTFIX_CONTROLLER_CACHE

**派發時間**：2026-09-01 00:00  
**優先級**：1  
**負責人**：sidney

---

## 📋 任務內容

【緊急修復派工：Controller 與 Cache 錯誤】

致 Sidney：
遠端驗證發現兩個阻斷性錯誤，請立即修復：

1. Controller 命名空間錯誤：
   檢查 app/Http/Controllers/Web/SignalHubWebController.php
   確保：
   - namespace 正確為：namespace App\Http\Controllers\Web;
   - 正確繼承：use Illuminate\Routing\Controller;
   - class 聲明：class SignalHubWebController extends Controller

2. Cache 目錄權限與結構：
   執行以下指令：
   chmod -R 775 bootstrap/cache storage
   chown -R www:www bootstrap/cache storage
   mkdir -p bootstrap/cache/data bootstrap/cache/views
   
3. 清除並重建快取：
   php artisan config:clear
   php artisan cache:clear
   php artisan view:clear
   php artisan config:cache

修復後請回報並重新測試頁面訪問。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260831_SIDNEY_HOTFIX_CONTROLLER_CACHE

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
**派發時間**：2026-09-01 00:00
