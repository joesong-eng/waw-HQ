# 任務：20260915_MINA_TEST_COVERAGE_BOOTSTRAP

**派發時間**：2026-09-15 09:39  
**優先級**：normal  
**負責人**：mina

---

## 📋 任務內容

[P3-3] 建立測試基礎設施與首批案例

## 問題
tests/ 目錄仍只有 ExampleTest 空殼，無任何業務邏輯覆蓋。

## 執行項目
1. 確認 phpunit.xml 配置（Laravel 預設即可）
2. 建立 Unit/MemberWalletTest.php，覆蓋：
   - CURRENCY_COIN/TICKET 常數正確性
   - 餘額計算正確性（Credit/Debit）
3. 建立 Feature/Api/MemberAuthTest.php，覆蓋：
   - LINE callback 成功路徑
   - LINE callback 失敗路徑（無 code）
   - Auth middleware 阻擋未登入
4. 建立 Feature/Web/VenueAuthTest.php，覆蓋：
   - /devices、/billing、/subscriptions 未登入 → 302 redirect
   - 已登入 → 200
5. 跑 php artisan test，確保新案例全綠

## 驗收
1. 測試通過率 100%
2. coverage 報告（text 格式）貼在 outbox
3. Commit 訊息：test: bootstrap coverage with MemberWallet + Auth + Venue test suite (P3-3)
4. 推送 origin/main
5. 回報測試結果與覆蓋率至 outbox

工時預估：2 小時

---

## 📝 回報格式

```markdown
# 任務回報：20260915_MINA_TEST_COVERAGE_BOOTSTRAP

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：mina

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：mina  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-09-15 09:39
