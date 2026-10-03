# 任務回報：TASK_20260920_ALLIE_DASHBOARD_MAP_AND_ORDER_VERIFY

**完成時間**：2026-09-20 23:45
**執行者**：allie

## 執行結果

### 3.2 Dashboard 進度地圖升級為 7 步真實狀態機

修改 `resources/views/dashboard/index.blade.php`，將原 4 步高層流程替換為 7 步真實訂單狀態機：

| 步驟 | 狀態 | 連結篩選 |
|---|---|---|
| 1 | 開單草案 | `?status=draft` |
| 2 | 已確認 | `?status=confirmed` |
| 3 | 燒錄中 | `?status=burning` |
| 4 | 已燒錄 | `?status=burned` |
| 5 | 待出貨 | `?status=ready_to_ship` |
| 6 | 已出貨 | `?status=shipped` |
| 7 | 已完成 | `?status=completed` |

每步點擊連結至 `orders.index` 帶對應 `status` 篩選參數，可直接查看該狀態之訂單清單。標題改為「🧭 訂單狀態流程」。

### 3.5 驗證已結案訂單無燒錄入口

確認 `resources/views/orders/show.blade.php` 第 333 行：

`@if(!in_array($order->status, ['completed', 'shipped']))`

此判斷確保 `completed` 和 `shipped` 狀態之訂單不會顯示「⚡ 前往燒錄」按鈕。第 594 行另有 `@if(in_array($order->status, ['shipped', 'completed']))` 控制已結案訂單的替代操作面板。邏輯正確，無需修改。

### Git 與部署

- **Commit**：`d3639d2`（`feat(ux): Dashboard 進度地圖升級為 7 步真實狀態機`）已推送 `origin/main`。
- **遠端**：`yd16`（`ali.tg25.win`）同步至 `d3639d2`，`view:clear`、`cache:clear`、`view:cache` 全數成功。
- **遠端驗證**：grep 確認 7 個 `step-name`（開單草案→已確認→燒錄中→已燒錄→待出貨→已出貨→已完成）順序正確；orders/show.blade.php 燒錄入口守衛存在於第 333 行。

未動 `burning.blade.php`，未執行任何資料庫遷移。

## 結論
✅ 完成

---
**回報者**：allie
**回報時間**：2026-09-20 23:45

