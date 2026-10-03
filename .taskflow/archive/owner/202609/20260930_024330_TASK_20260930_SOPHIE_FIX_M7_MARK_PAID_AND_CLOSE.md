# 任務工單：TASK_20260930_SOPHIE_FIX_M7_MARK_PAID_AND_CLOSE

**派發時間**：2026-09-30 02:50 (台北時間)  
**優先級**：P0 (打通 M7 對帳結算最後一哩路)  
**指派對象**：Sophie (Owner Agent)  
**驗收人**：HQ / Joe

---

## 🎯 任務目標

經 HQ 深入源碼稽核，確認 `SettlementService` 內部已有完整的 `markAsPaid()` (付款憑證與欠款扣除) 與 `closeSettlement()` (確認收訖結案) 核心業務邏輯，但 `SettlementController` 未包裝這兩個方法，導致前端按鈕噴 404。

本次任務目標：**在 Controller 與 Route 補齊這兩個端點，徹底打通 M7 結算付款與結案閉環**。

---

## 📋 具體實作要求

### 一、Controller 方法補齊 (`app/Http/Controllers/Api/V9/SettlementController.php`)

1. **`markPaid(Request $request, int $id): JsonResponse`**：
   - 驗證參數：`payment_proof_url` (可選，string/url)。
   - 呼叫 Service：`$this->settlementService->markAsPaid($id, $request->user()->id, $request->only('payment_proof_url'))`。
   - 權限/業務例外處理：捕捉 `InvalidArgumentException` 回傳 400，成功回傳 200 + 最新結算單資料與訊息。

2. **`close(Request $request, int $id): JsonResponse`**：
   - 呼叫 Service：`$this->settlementService->closeSettlement($id, $request->user()->id)`。
   - 捕捉例外：回傳對應錯誤，成功回傳 200 + 結案成功訊息。

### 二、路由補齊 (`routes/api.php`)
在 `Route::middleware(['web', 'auth'])->prefix('v9')` 的 settlements 分組中追加：
- `POST /api/v9/settlements/{id}/mark-paid` ➔ `SettlementController@markPaid`
- `POST /api/v9/settlements/{id}/close` ➔ `SettlementController@close`

---

## 📦 驗收標準 (Acceptance Criteria)

1. **路由檢查**：
   - 執行 `php artisan route:list --path=settlements`，確認新增的 `mark-paid` 與 `close` 兩條路由皆已正確註冊。
2. **Git 與遠端部署**：
   - Commit message 格式：`feat(m7): implement markPaid and close endpoints in SettlementController`
   - Push 至遠端 main 分支。
   - 執行 `./dev_tools/waw_ops.sh deploy owner` 部署至生產環境。
3. **回報格式**：
   - 依據 `SIMPLE_FILE_DISPATCH_PROTOCOL.md` 格式將回報送達 `.taskflow/owner/outbox/`。
   - 檢附遠端 `route:list` 包含 `mark-paid` 與 `close` 之實測輸出。

---
**派發者**：HQ  

