# 任務回報：TASK_20260915_SIDNEY_REPORT_DEVICE_OWNER_ISOLATION

**完成時間**：2026-09-15 23:00  
**執行者**：Sidney

## 執行結果

已完成並部署 commit `af52d47`：

1. `findProfileByChipId()` 現在以 `device_id + device.owner_id + is_active` 尋找 Profile。相同實體卡不會再因 `first()` 取到其他帳號的 Profile。
2. `storeProfile()` 綁定設備前驗證 `devices.owner_id === profile owner_id`；不一致回應 HTTP 403。
3. `updateProfile()` 更新 `device_id` 前同樣驗證 owner 一致；不一致回應 HTTP 403。
4. 已推送 `origin/main` 並透過 `waw_ops.sh deploy sidney` 部署。部署流程已執行 view cache clear、config cache、application cache clear。
5. 遠端複驗：`/www/wwwroot/signal.tg25.win` HEAD 為 `af52d47`；`findProfileByChipId()` 第 828 行具 `->where('owner_id', $device->owner_id)`。

## 注意事項

此修正保護新信號路由與跨帳號綁定；設備退貨／轉售的歷史歸屬、封存與 assignment-first 查詢改造，已另提 `TASK_20260915_HQ_REVIEW_DEVICE_RETURN_REASSIGNMENT` 等待 HQ 審核。

## 結論
✅ 完成

---
**回報者**：Sidney  
**回報時間**：2026-09-15 23:00
