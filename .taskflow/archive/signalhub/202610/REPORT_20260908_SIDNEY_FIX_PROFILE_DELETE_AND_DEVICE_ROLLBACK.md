# 任務回報：TASK_20260908_SIDNEY_FIX_PROFILE_DELETE_AND_DEVICE_ROLLBACK

**完成時間**：2026-09-08 19:31  
**執行者**：Sidney (SignalHub Lead)

---

## 📋 實作內容

### 1. 後端修復 (SignalHubController::destroyProfile)

**文件**: `app/Http/Controllers/Api/V9/SignalHubController.php`

**修改內容**:
- ✅ 在刪除設定檔前，檢查 `$profile->device_id`
- ✅ 若存在關聯設備，安全更新該設備狀態為 `'pending_setup'`
- ✅ 刪除設定檔前先清理所有子項目：
  - `$profile->pinMappings()->delete()`
  - `$profile->statRules()->delete()`
  - `$profile->webhooks()->delete()`
- ✅ 最後才刪除設定檔本身

**核心邏輯**:
```php
// 安全回退：若設定檔綁定了設備,將設備狀態改回 pending_setup
if ($profile->device_id) {
    \App\Models\Device::where('id', $profile->device_id)
        ->where('owner_id', auth()->id())
        ->update(['status' => 'pending_setup']);
}

// 刪除相關的子項目
$profile->pinMappings()->delete();
$profile->statRules()->delete();
$profile->webhooks()->delete();

// 刪除設定檔本身
$profile->delete();
```

---

### 2. 前端修復 (profiles.blade.php)

**文件**: `resources/views/signal-hub/profiles.blade.php`

**新增方法**: `async deleteProfile(profileId, profileName)`

**功能實作**:
- ✅ 彈出確認對話框，顯示設定檔名稱與操作後果提示
- ✅ 使用者確認後發送 `DELETE /api/v9/signal-hub/profiles/{id}` 請求
- ✅ 攜帶 CSRF Token 與 XMLHttpRequest 標頭
- ✅ 成功後同時呼叫:
  - `this.loadProfiles()` - 刷新設定檔列表
  - `this.loadPendingDevices()` - 刷新待設置設備列表
- ✅ 顯示成功/失敗提示訊息

**確認對話框內容**:
```
確定要刪除「{機台名稱}」機台設定檔嗎？

刪除後該採集卡將重新回到上方「⚠️ 待設置採集卡」清單。
```

---

## 🔧 Git 提交資訊

**Commit Hash**: `d85f3f1`

**Commit Message**:
```
fix: 修復設定檔刪除功能與設備狀態回退

- 後端: destroyProfile 新增設備狀態安全回退至 pending_setup
- 後端: 刪除設定檔前先清理 pinMappings、statRules、webhooks
- 前端: 實作 deleteProfile 方法，支援確認對話框
- 前端: 刪除成功後同時刷新設定檔列表與待設置設備列表
```

**異動檔案**:
- `app/Http/Controllers/Api/V9/SignalHubController.php` (+14 行)
- `resources/views/signal-hub/profiles.blade.php` (+31 行)

**遠端部署**:
- ✅ 已推送至 GitHub: `d802cb6..d85f3f1`
- ✅ 已部署至遠端 VPS: `signal.tg25.win`
- ✅ Laravel 快取已清理 (views, config, application cache)
- ✅ API 路由已驗證: `DELETE api/v9/signal-hub/profiles/{id}`

---

## ✅ 驗收確認

### 後端驗證
- [x] 設備狀態回退邏輯已實作
- [x] 子項目清理邏輯已實作
- [x] API 路由已正確註冊
- [x] 代碼已部署至遠端 VPS

### 前端驗證
- [x] deleteProfile 方法已實作
- [x] 確認對話框已實作
- [x] 雙列表刷新機制已實作
- [x] 成功/失敗提示已實作

### 瀏覽器驗證 (需人工確認)
- [ ] 點擊刪除彈出確認對話框
- [ ] 設定檔成功刪除並從列表消失
- [ ] 採集卡立即回到頂部「⚠️ 待設置採集卡」區塊
- [ ] 顯示成功提示訊息

---

## 📝 測試說明

**測試頁面**: https://signal.tg25.win/signal-hub/profiles

**測試步驟**:
1. 登入 SignalHub 後台
2. 進入「📡 信號配置中心」頁面
3. 找到任一已設置的機台設定檔
4. 點擊該設定檔右側的「🗑️ 刪除」按鈕
5. 確認彈出對話框內容正確
6. 點擊「確定」刪除
7. 驗證:
   - 該設定檔從下方列表消失
   - 該採集卡出現在上方橘色「⚠️ 待設置的採集卡」區塊
   - 顯示綠色勾選提示「✅ 設定檔已刪除，採集卡已回到待設置清單」

---

**回報者**：Sidney  
**回報時間**：2026-09-08 19:31

