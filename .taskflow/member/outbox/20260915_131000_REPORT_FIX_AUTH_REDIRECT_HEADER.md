# 任務回報：20260915_MINA_FIX_AUTH_REDIRECT_HEADER

**完成時間**：2026-09-15 13:10
**執行者**：mina

## 執行結果

### 根因分析
1. **主因**：`php artisan route:cache` 在之前部署時快取了舊的 `auth:sanctum` middleware 設定，後續修改路由後未清除路由快取，導致 auth middleware 仍在執行
2. **次因**：PHP 的 `header()` 函數在 FastCGI 模式下，傳入 status code 參數時會將 HTTP 狀態行附加到 Location header，造成 `Header may not contain more than a single header, new line detected`

### 修復方案
1. **移除 auth:sanctum middleware**：Venue 路由改用 inline auth check（`if (!auth()->check()) return redirect('/')`），避免觸發 redirectGuestsTo 機制
2. **清除路由快取**：`php artisan route:clear` 清除了舊的 route:cache，讓新路由生效

### Commits
- `accfc43` — 初步嘗試：redirectGuestsTo 改為 redirect('/')
- `2e2b942` — 最終修復：移除 auth:sanctum，改用 inline auth check

### 驗收結果
| 路由 | HTTP Status | 結果 |
|:---|:---|:---|
| /venue/billing | 302 → / | ✅ |
| /venue/devices | 302 → / | ✅ |
| /venue/subscriptions | 302 → / | ✅ |
| / (homepage) | 200 | ✅ |
| /m/play | 200 | ✅ |
| /api/machine/* (deprecated) | 404 | ✅ |

## 結論
✅ 完成（Header injection 500 已修復，未登入使用者正確回傳 302 redirect）

---
**回報者**：mina
**回報時間**：2026-09-15 13:10
