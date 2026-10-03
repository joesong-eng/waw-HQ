# 回報：TASK_20260921_SIDNEY_TECHNICIAN_EFFECTIVE_OWNER

**回報時間**：2026-09-21
**執行者**：Sidney
**狀態**：碼審完成 + 本地 diff，未 deploy（依任務指示等 HQ 開燈）

---

## 改動檔案（5 檔，commit `35d4cee`）

| 檔案 | 改動 |
|---|---|
| `app/Models/User.php` | +`effectiveOwnerId()`：technician+root_id → 機台主 id；owner → 自身 id |
| `app/Http/Controllers/Api/V9/SignalHubController.php` | 全部 26 處 `auth()->id()` → `auth()->user()->effectiveOwnerId()` |
| `app/Http/Controllers/Api/SignalHubApiController.php` | 1 處同上替換 |
| `app/Http/Controllers/Api/V9/TestWebhookController.php` | 1 處同上替換 |
| `app/Http/Controllers/Signal/Authv9Controller.php` | login 加 `isExpired()` 檢查，過期 → logout + 錯誤「帳號已過期，請聯絡機台主重新開立。」 |

## auth()->id() 殘留 grep

```
grep -rn 'auth()->id()' app/Http/Controllers/ --include='*.php'
（零結果，Controller 內已無殘留）
```

## 關鍵邏輯

1. **effectiveOwnerId()** — 單一方法，全站共用，不複製 if 20 次
   - technician + root_id → `(int) root_id`
   - 其他 → `(int) id`

2. **登入流程**
   - Auth::attempt 成功後立即檢查 `isExpired()`
   - 過期 → logout + invalidate session + 回錯誤文案
   - technician → 允許登入（無 role gate）
   - 自行註冊仍 role=owner（未改）

3. **權限邊界**
   - technician 可讀寫 effective owner 名下 profile / pin / webhook / simulator
   - technician 寫入的 profile/webhook owner_id = 機台主 id（非技術帳 id）
   - 側邊欄無營收/分潤/訂閱入口（現況已滿足）

4. **未做（依指示）**
   - 未改 Owner 專案
   - 未新 migration、未改 ENUM
   - 未在本機跑 php artisan / 測 DB
   - **未 deploy**（等 HQ 核碼開燈）

## Deploy 狀態

❌ 未 deploy（依任務指示：「先不要 deploy，等 HQ 核碼再開燈」）

