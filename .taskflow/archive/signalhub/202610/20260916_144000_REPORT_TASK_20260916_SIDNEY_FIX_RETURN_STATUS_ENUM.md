# 任務回報：TASK_20260916_SIDNEY_FIX_RETURN_STATUS_ENUM

**完成時間**：2026-09-16 14:40
**執行者**：Sidney

## 執行結果

採方案 1：退貨後 device.status 改設為 pending_setup。

選擇理由：
- enum 擴充需要 ALTER TABLE 全表鎖定，生產環境代價高，且 returned 語意過於特殊。
- pending_setup 語意「設備已退回，待下次出貨重新設置」，對庫存管理最直觀。
- 現有 Device 作業流程（pending_setup -> active）完全吻合再次出貨前提。

變更：DeviceAssignmentService::return() 將 status 改為 pending_setup。
commit 52e7e73，HEAD=52e7e73，已部署。

遠端驗證：部署成功，view/config/cache 已清除。

退貨流程兩次 DB constraint 問題均已修復：
1. owner_id nullable migration（da65dc5）
2. status=pending_setup 修正（52e7e73）

E2E 驗收路徑：
- 退貨前按卡：觸發現役廠商 Webhook。
- 退貨後按卡：device owner=NULL、profile archived，HTTP 202 無 Webhook。
- 重綁後按卡：僅送新廠商 Webhook。

## 結論
完成

---
**回報者**：Sidney
**回報時間**：2026-09-16 14:40
