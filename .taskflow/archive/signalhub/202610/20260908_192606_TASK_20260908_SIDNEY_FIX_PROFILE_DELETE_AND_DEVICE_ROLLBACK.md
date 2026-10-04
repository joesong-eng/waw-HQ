# 任務：TASK_20260908_SIDNEY_FIX_PROFILE_DELETE_AND_DEVICE_ROLLBACK

**派發時間**：2026-09-08 17:55  
**優先級**：HIGH  
**負責人**：Sidney (SignalHub Lead)

---

## 📋 任務核心問題

目前在信號配置中心（`/signal-hub/profiles`）發現兩個嚴重影響業務閉環的缺陷：

1. **前端點擊刪除無反應**：
   - 模板 `resources/views/signal-hub/profiles.blade.php` 的刪除按鈕綁定了 `@click="deleteProfile(p.id, p.profile_name)"`。
   - 但底層 Alpine.js `signalHubProfiles()` 實例中完全遺漏了 `deleteProfile()` 方法，導致點擊時 JavaScript 毫無動作。

2. **後端缺乏防呆與設備狀態回退（嚴重孤兒數據風險）**：
   - `SignalHubController::destroyProfile($id)` 僅執行 `$profile->delete()`。
   - **嚴重漏洞**：刪除設定檔後，原本綁定該設定檔的設備（`$profile->device_id`）其 `status` 仍然留在 `'active'` 或其他狀態，導致老李刪除設定檔後，實體採集卡永遠不會重新出現在頂部橘色「⚠️ 待設置採集卡」清單中，淪為系統孤兒卡！

---

## 🛠️ 執行要求

### 1. 後端修復：設備狀態安全回退 (`SignalHubController::destroyProfile`)
- 在刪除 `SignalProfile` 前，先檢查其關聯的 `$profile->device_id`。
- 若存在 `device_id`，安全更新該設備狀態為 `'pending_setup'`：
  ```php
  if ($profile->device_id) {
      \App\Models\Device::where('id', $profile->device_id)
          ->where('owner_id', auth()->id())
          ->update(['status' => 'pending_setup']);
  }
  ```
- 同時確保刪除該 profile 下的所有子項目（`pinMappings`、`statRules`）。
- 回傳 JSON 包含成功訊息。

### 2. 前端修復：實作 `deleteProfile` 方法 (`profiles.blade.php`)
- 在 Alpine.js 加入 `async deleteProfile(profileId, profileName)` 方法：
  - 彈出確認視窗（如：`confirm('確定要刪除「' + profileName + '」機台設定檔嗎？\n刪除後該採集卡將重新回到上方「待設置採集卡」清單。')`）。
  - 發送 `DELETE /api/v9/signal-hub/profiles/${profileId}`（帶 CSRF-Token）。
  - 成功後提示已刪除，並同時呼叫 `this.loadProfiles()` 與 `this.loadPendingDevices()`。

### 3. Git 提交與遠端部署驗證
- 本機完成修改，執行 Git commit/push。
- 執行 `./dev_tools/waw_ops.sh deploy signalhub` 部署至遠端 VPS。
- 驗證點擊刪除後，該機台設定檔消失，且該採集卡立即回到上方橘色「⚠️ 待設置的採集卡」清單中。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260908_SIDNEY_FIX_PROFILE_DELETE_AND_DEVICE_ROLLBACK

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：Sidney (SignalHub Lead)

## 實作內容
（說明前後端修復細節）

## Git 提交資訊
（Commit Hash 與異動檔案）

## 驗收確認
- [ ] 點擊刪除彈出確認對話框
- [ ] 設定檔成功刪除
- [ ] 採集卡 status 成功回退為 pending_setup 並即時回到頂部待設置區塊

---
**回報者**：Sidney  
**回報時間**：YYYY-MM-DD HH:MM
```

---
**派發者**：HQ  
**派發時間**：2026-09-08 17:55
