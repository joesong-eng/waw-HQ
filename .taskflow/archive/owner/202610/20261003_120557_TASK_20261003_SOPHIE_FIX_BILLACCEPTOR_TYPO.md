# 任務工單：修復 BillAcceptorService 第 43 行箭頭運算子筆誤

**工單編號**：TASK_20261003_SOPHIE_FIX_BILLACCEPTOR_TYPO  
**派發時間**：2026-10-03  
**負責人**：Sophie (Owner 後台守護者)  
**優先級**：P1 (High)  
**關聯模組**：Owner (iot.tg25.win / yd174)

---

## 🎯 任務內容

### 修復 BillAcceptorService.php 第 43 行筆誤

- **檔案**：`app/Services/BillAcceptorService.php`
- **問題**：第 43 行使用了 PHP 字串串接運算子 `.` 呼叫方法，應為箭頭運算子 `->`。
- **問題代碼**：
  ```php
  $this->mqttService.rejectBill($chipId, $reqId);  // ❌ 筆誤
  ```
- **修正代碼**：
  ```php
  $this->mqttService->rejectBill($chipId, $reqId);  // ✅
  ```
- **影響**：Kiosk Escrow 事件「設備不存在」降級路徑拋 500，應安全拒鈔卻崩潰。

---

## 🔍 驗收指標

1. 靜態確認：`grep -n 'mqttService.' app/Services/BillAcceptorService.php` 結果歸零。
2. 遠端部署：Commit + Push + `waw_ops.sh deploy owner`。
3. 站點存活：`curl -sI https://iot.tg25.win/login` 回傳 `HTTP/2 200`。
4. 回報至 `.taskflow/owner/outbox/`。

