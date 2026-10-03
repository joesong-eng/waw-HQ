# 任務回報：TASK_20260921_ALLIE_BATCH_ORDER_OPERATIONS

**完成時間**：2026-09-21 01:20
**執行者**：allie

## 執行結果

依工單要求，為訂單列表加入完整的批次操作功能，涵蓋前後端。

### 1. 後端（Controller + Route）

**routes/web.php**：新增兩條批次路由
- `POST /orders/batch/ship` → `orders.batch.ship`
- `POST /orders/batch/destroy` → `orders.batch.destroy`

**app/Http/Controllers/OrderController.php**：新增兩個方法
- `batchShip()`：批次出貨，篩選 `ready_to_ship` 狀態訂單，逐筆執行完整出貨流程（快照授權費、韌體出貨款記帳、生成分潤結算單、更新狀態為 completed、跨庫通知、業務日誌記錄）。
- `batchDestroy()`：批次刪除，僅限 `draft` 狀態訂單，安全刪除。

### 2. 前端（Blade + CSS + JS）

**resources/views/orders/index.blade.php**：
- **Checkbox 欄**：表頭全選/反選 checkbox + 每行 checkbox（帶 `data-status` 屬性）。
- **浮動批次工具列**：底部 fixed 定位，顯示已選數量，含三個按鈕：
  - 🚚 批次出貨（僅 `ready_to_ship` 可用）
  - 🗑️ 批次刪除（僅 `draft` 可用）
  - ✕ 取消選取
- **按鈕狀態联动**：依選取訂單的狀態自動啟用/停用對應按鈕。
- **全選/反選邏輯**：支援 indeterminate 半選狀態。
- **確認對話框**：批次操作前需二次確認，顯示確切數量。

### 3. 安全設計
- 批次出貨僅限 `ready_to_ship`，批次刪除僅限 `draft`，其他狀態被忽略。
- Controller 端二次篩選狀態，防止竄改。
- 每筆出貨記錄完整業務日誌（含 `batch: true` 標記）。

### Git 與部署

- **Commit**：`fc04e48`（`feat(orders): 訂單列表批次操作功能 — 全選/批次出貨/批次刪除草稿`）已推送 `origin/main`。
- **遠端**：`yd16`（`ali.tg25.win`）同步至 `fc04e48`，`view:clear`、`cache:clear`、`route:clear`、`view:cache`、`route:cache` 全數成功。
- **遠端驗證**：
  - `php artisan route:list --name=orders.batch` 確認兩條路由已註冊。
  - grep 確認 blade 含 21 處 checkbox/toolbar 相關元素。

未動 `burning.blade.php`，未執行任何資料庫遷移。

## 結論
✅ 完成

---
**回報者**：allie
**回報時間**：2026-09-21 01:20

