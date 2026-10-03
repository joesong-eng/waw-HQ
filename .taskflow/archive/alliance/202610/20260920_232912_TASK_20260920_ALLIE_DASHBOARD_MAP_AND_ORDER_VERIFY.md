# 任務：TASK_20260920_ALLIE_DASHBOARD_MAP_AND_ORDER_VERIFY

**派發時間**：2026-09-20 23:29  
**優先級**：normal  
**負責人**：allie

---

## 📋 任務內容

【步驟5+6】3.5 驗證/確保 orders/show.blade.php 在已結案訂單（completed/shipped）無燒錄入口；3.2 修改 resources/views/dashboard/index.blade.php，將進度地圖由現行 4 步升級為 7 步真實狀態機（1.開單草稿 draft -> 2.已確認 confirmed -> 3.燒錄中 burning -> 4.已燒錄 burned -> 5.待出貨 ready_to_ship -> 6.已出貨 shipped -> 7.已完成 completed），每步點擊可連結至對應篩選頁面。注意：禁止動 burning.blade.php，禁止動資料庫遷移。完成後提交 Git、部署遠端並清快取。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260920_ALLIE_DASHBOARD_MAP_AND_ORDER_VERIFY

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：allie

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：allie  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-09-20 23:29
