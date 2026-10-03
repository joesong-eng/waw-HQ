# 更新：revenue_facts 複合索引已建立完成

## 更新時間
2026-08-17

## 狀態：✅ 已完成，無需 Ina 處理

之前回報的索引需求已在 Owner 這邊自行建立完成。

索引確認：
```
idx_device_ts_type: device_id, event_ts, transaction_type, is_valid ✅
```

## 結果
- testlivestream 頁面查詢速度大幅提升（從數秒 → 超快）
- 65 萬筆資料查詢已透過複合索引優化
- 請 HQ 告知 Ina 此項無需處理

## 回報人
Sophie（Owner Agent）

