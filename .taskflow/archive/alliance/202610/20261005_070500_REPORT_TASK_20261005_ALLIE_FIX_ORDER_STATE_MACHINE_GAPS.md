# 回報：TASK_20261005_ALLIE_FIX_ORDER_STATE_MACHINE_GAPS

**執行者**：Allie
**完成時間**：2026-10-05 07:05 (Asia/Taipei)
**任務 ID**：TASK_20261005_ALLIE_FIX_ORDER_STATE_MACHINE_GAPS
**Commit**：`938f8a7`

---

## 修復清單

### G1｜ship() 收斂為僅 ready_to_ship ✅
- **修法**：`ship()` 改為 `$order->status !== 'ready_to_ship'` 檢查
- **UI**：移除 burning/burned 狀態的「轉為出貨單」按鈕；burned 改為「標記待出貨」按鈕
- **驗證**：draft 狀態呼叫 ship → 被拒 ✅

### G2｜ship() → shipped（恢復 7 步） ✅
- **修法**：`ship()` 設 `status='shipped'`，只寫 `shipped_date`；`batchShip()` 同步修改
- **UI**：ready_to_ship 按鈕改為「🚚 確認出貨」；shipped 狀態顯示「🚚 已出貨，等待確認送達」
- **驗證**：ship 後 status=shipped（非 completed） ✅

### G3｜complete() 恢復可達 ✅
- **修法**：G2 修復後自然恢復。shipped → completed 路徑暢通
- **UI**：shipped 狀態加「🏁 確認送達結案」按鈕
- **驗證**：shipped 狀態可呼叫 complete → completed ✅

### G4｜finishBurning 加綁定數量檢查 ✅
- **修法**：加入 `$bindCount < $fwQty` 檢查，不足時返回錯誤訊息含具體數字
- **驗證**：0 bindings / 2 required → 被拒 ✅；2 bindings / 2 required → 通過 ✅

### G5｜修正 Trigger 錯誤註解 ✅
- **修法**：兩處註解從「MySQL 觸發器自動接管」改為「PHP commitRegistration() updateOrInsert 處理（Trigger 尚未建立）」
- **決策回報**：`SHOW TRIGGERS FROM alliance_db` 為空，Trigger 不存在。同步完全靠 PHP 雙寫。**建議 HQ 與 Ina 確認是否需要建 Trigger**。

### G6｜license_fee=0 → royalties 不建帳（資料問題） ⚠️ 回報 HQ
- **現值查詢結果**：

| id | sku_name | has_firmware | software_license_fee |
|----|----------|-------------|---------------------|
| 2 | 橋接卡（兌幣機） | ✅ | **0.00** |
| 4 | 通訊卡（遊戲機採集） | ✅ | **0.00** |
| 5 | 測試快建S3採集卡 | ✅ | 500.00 |
| 6 | E2E測試採集卡 | ✅ | 500.00 |

- **判定**：邏輯正確（fee=0 不建帳是合理行為）。**資料設定問題**：正式韌體產品（id=2, id=4）的 license_fee 需由 Joe/HQ 決定是否設定非零值。
- **不改程式碼**。

### G7｜destroy 收斂 + iotv9 清理 ✅
- **修法**：destroy 阻擋名單加入 `burning`、`burned`；draft/confirmed 刪單前清理 `ali_device_bindings` + `iotv9.devices`
- **驗證**：程式碼確認 burning/burned/shipped/completed/ready_to_ship 均被阻擋 ✅

---

## 驗收指標

### 1. Diff
```
app/Http/Controllers/OrderController.php | 59 insertions(+), 32 deletions(-)
resources/views/orders/show.blade.php     | 20 insertions(+), 18 deletions(-)
```

### 2. 遠端驗證（測試單 id=18, GFIX-TEST-20261005B）
```
1.id=18 status=draft
2.G1_draft_ship_blocked=YES
3.status=confirmed
4.status=burning
5.G4_blocked: 0 bindings < 2 required
6.bound=2
7.G4_passes: 2 bindings >= 2 required
8.status=burned
9.status=ready_to_ship
10.G2: status=shipped (not completed)
11.G3: shipped=true, can complete=YES
12.status=completed
13.iotv9: both synced
14.CLEANUP: remain=0
ALL_PASS
```

### 3. 測試資料清理
```
orders=0, bindings=0, iotv9=0
```

### 4. 站點存活
```
curl -sI https://ali.tg25.win/ → HTTP/2 302 → /login
```

### 5. Commit
```
938f8a7 fix(order): G1-G7 狀態機漏洞修復
```

---

## 待 HQ 決策

1. **G5**：Ina 是否要建 DB Trigger？若否，目前 PHP 雙寫已正常運作。
2. **G6**：正式產品 id=2（橋接卡）、id=4（通訊卡）的 `software_license_fee` 需設定具體金額嗎？

---

## 結論

✅ G1/G2/G3/G4/G5/G7 全部修復完成，遠端驗證通過
⚠️ G6 為資料設定問題，回報 HQ 決策

