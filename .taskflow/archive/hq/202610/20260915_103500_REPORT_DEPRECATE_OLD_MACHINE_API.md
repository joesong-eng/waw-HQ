# 任務回報：20260915_MINA_DEPRECATE_OLD_MACHINE_API

**完成時間**：2026-09-15 10:35  
**執行者**：mina

## 執行結果

### 1. 確認前端已無引用
- `grep -rn '/api/machine'` 全專案搜索：前端 blade/JS 均無引用 `/api/machine/*`
- 僅 `MachineController.php` 內部使用 `url('/api/callback/credit')` 和 `url('/api/callback/settle')` 作為 callback_url（隨 Controller 一併移除）

### 2. 移除項目
| 項目 | 動作 |
|:---|:---|
| `routes/api.php` lines 53-56 | 移除 3 條 `/api/machine/*` 路由 |
| `app/Http/Controllers/Api/MachineController.php` (236 行) | `git rm` 刪除 |

### 3. 保留項目
- `app/Models/MachineSession.php` 保留，因 `CallbackController` 的 `credit()` 和 `settle()` 方法仍有引用（這些是舊版 callback 路由，屬於不同任務範圍）

### 4. 部署與驗證
- **Commit**：`f0ac20b` — `refactor(api): remove deprecated MachineController and /api/machine/* routes (P1-5)`
- **Push**：`f88e724..f0ac20b main -> main` ✅
- **部署**：`waw_ops.sh deploy mina` ✅
- **遠端 composer dump-autoload**：清除 autoload classmap 中對 MachineController 的引用 ✅
- **route:cache + config:cache**：重建路由快取 ✅

### 5. 驗證結果
- `php artisan route:list --path=machine` → "Your application doesn't have any routes matching the given criteria" ✅
- `curl /api/machine/machine_info/test` → **404** ✅
- `curl -X POST /api/machine/assign_credit` → **404** ✅
- `curl -X POST /api/machine/settle_credit` → **404** ✅
- `php -l routes/api.php` → No syntax errors ✅

## 結論
✅ 完成（舊版 MachineController 已刪除，/api/machine/* 路由已移除，遠端回傳 404）

---
**回報者**：mina  
**回報時間**：2026-09-15 10:35
