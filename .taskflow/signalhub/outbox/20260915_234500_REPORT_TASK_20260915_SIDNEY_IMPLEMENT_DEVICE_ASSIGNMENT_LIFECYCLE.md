# 任務回報：TASK_20260915_SIDNEY_IMPLEMENT_DEVICE_ASSIGNMENT_LIFECYCLE

**完成時間**：2026-09-15 23:45  
**執行者**：Sidney

## 執行結果

已部署 commits f12e9a5、5cd3e3e、af0bcbc 至 signal.tg25.win。

1. 新增 device_assignments，保存 device、chip ID 快照、owner、Profile、指派與退貨時間、狀態、操作者、退貨原因。
2. signal_events 與 signal_webhook_deliveries 新增 owner_id、device_assignment_id，含 owner/時間與 assignment 索引；migration 已回填既有歸屬。
3. 新增 POST /api/v9/signal-hub/assignments/{id}/return。transaction 鎖定 assignment/device/profile，封存 Profile、停用 Webhook、結束 assignment、清空 Device owner、改 status=returned；不刪 Event、Delivery、Webhook、Profile 歷史。
4. DELETE profile 改封存。若有現役 assignment，強制同一退貨 transaction，避免 webhook cascade 刪掉 Delivery。
5. Profile 建立與批次建立會建立 assignment；device owner 不符、已有 active assignment、或已有其他 active Profile 時拒絕。更新 Profile 禁止直接換 device。
6. findProfileByChipId 現在要求 Device owner、active Profile、active assignment 一致；未知、退貨、未歸屬卡僅寫無 owner/profile 稽核 Event，回 HTTP 202，不發 Webhook。
7. 新 Delivery 寫 owner/assignment 快照。清單、詳情、統計改以 Delivery 自身 owner_id 授權，不依賴可刪除的 Webhook owner 關聯。

## 遠端驗證

- HEAD：af0bcbc。
- migration 2026_09_15_232500_create_device_assignments_and_snapshot_ownership：Batch 15，Ran。
- Device 43 / chip 3c0f02d42720：僅 assignment #5，owner=12、profile=35、status=assigned。
- events_owner_missing=0；deliveries_owner_missing=0。
- DeviceAssignment.php、DeviceAssignmentService.php PHP syntax 無誤。
- POST api/v9/signal-hub/assignments/{id}/return 已註冊。
- 已完成 view clear、config cache、application cache clear。

## 注意事項

本機未執行 Laravel 測試。遠端已完成 migration、syntax、route、資料回填驗證。建議下一步依 HQ 案例做實體卡端到端驗收：退貨前原 owner、退貨後 HTTP 202 無派送、新 owner 重綁後只送新 owner webhook。

## 結論
✅ 完成

---
**回報者**：Sidney  
**回報時間**：2026-09-15 23:45
