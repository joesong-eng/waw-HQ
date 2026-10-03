# TASK: Alliance 站點首波安全與體驗優化 (Phase 1 + Quick UX Wins)

- **任務 ID**: TASK_20260920_ALLIE_SECURITY_AND_QUICK_UX_FIXES
- **指派給**: Allie (Alliance 專案負責人)
- **優先級**: High
- **來源參考**: `PROJECT/Alliance/docs/ALLIANCE_SITE_IMPROVEMENT_PLAN.md`

---

## 任務背景與範疇

HQ 審查站點改善計畫書，本次僅核准執行 **高收益、低風險、非破壞性** 的第一波修復。
**嚴格禁止** 執行大型架構重構（如 `burning.blade.php` 拆分）與全站 CSS 樣式大一統。

請依序完成以下具體項目：

### 1. 登入安全修復（原計畫 1.1, 1.2, 1.3）
- `resources/views/auth/login.blade.php`:
  - 移除登入頁底部測試帳密展示區塊（`<div class="test-accounts">`）。
  - 移除或妥善處理無效之「忘記密碼？」`href="#"` 連結（改為提示聯絡管理員或暫時隱藏）。
- `routes/web.php`:
  - `POST /login` 路由加上 `throttle:5,1` 中間件防止暴力破解。

### 2. 訂單號與 Dashboard UX 修正（原計畫 3.1, 3.3）
- `resources/views/orders/index.blade.php`:
  - 列表訂單編號改為優先顯示真實訂單號：`{{ $order->order_no ?? 'ORD-'.$order->id }}`。
- `resources/views/dashboard/index.blade.php`:
  - 移除「收益趨勢」與「最新訂單」區塊的 `collapsed` 預設折疊 class，改為預設展開；爭議區塊保持折疊。

### 3. 清理與細節修飾（原計畫 4.1, 4.2）
- `resources/views/layouts/app.blade.php`:
  - 側邊欄導航圖示去重（「出貨整理」圖示改為 🚚，避免與「產品管理」📦 重複）。
- 刪除無路由引用之孤立檔 `resources/views/welcome.blade.php`。

---

## 驗證與交付要求

1. **Git 控管**: 在 `PROJECT/Alliance` 分支以清晰 commit 提交變更並推送。
2. **遠端部署**: 執行遠端部署並清除 Laravel view/cache 快取：
   - 部署：`./dev_tools/waw_ops.sh deploy alliance`
   - 清除快取：`./dev_tools/waw_ops.sh remote alliance "php artisan view:clear && php artisan cache:clear && php artisan route:clear"`
3. **驗證憑證**:
   - curl 或登入測試確認 `/login` 5 次錯誤後觸發 429 Throttle。
   - 瀏覽器檢查登入頁面確認測試帳密已移除。
   - 檢查訂單列表確認已顯示 `ALI-xxxx` 正式單號。
4. **回報方式**: 完成後將成果回報寫入 `.taskflow/alliance/outbox/REPORT_20260920_ALLIE_SECURITY_AND_QUICK_UX_FIXES.md`。

