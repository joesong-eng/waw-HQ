# 任務：TASK_20260918_SOPHIE_FIX_DEVICES_BLADE_SYNTAX

**派發時間**：2026-09-18 12:44  
**優先級**：high  
**負責人**：sophie

---

## 📋 任務內容

P0 緊急修復：devices.blade.php JS 語法錯誤導致設備管理頁面全壞，Alpine 無法初始化。修復 commit da14472 引入的重複屬性和 HTML 錯位。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260918_SOPHIE_FIX_DEVICES_BLADE_SYNTAX

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：sophie

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：sophie  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-09-18 12:44
# 🔴 緊急修復：TASK_20260918_SOPHIE_FIX_DEVICES_BLADE_SYNTAX

**優先級**：P0 - 線上頁面全壞
**來源**：HQ 瀏覽器驗收 TASK_20260917_SOPHIE_LIVE_PIN_UI 時發現
**問題**：devices.blade.php 有 JS 語法錯誤，Alpine 整個 deviceManagement() 無法初始化，設備管理頁面完全空白

---

## 🐛 問題描述

Commit `da14472` (feat(owner): add Live Pin UI and backend support) 引入了兩個語法錯誤：

### 錯誤 1：第 583-586 行 - editForm 重複屬性

`loadDeviceDetails()` 函式中，`share_device_owner` 和 `share_venue_owner` 被貼了兩次，且缺少逗號/括號配對：

```diff
  placement_type: device.placement_type || 'self_operated',
  share_device_owner: device.share_device_owner || 100,
  share_venue_owner: device.share_venue_owner || 0
-                share_device_owner: device.share_device_owner || 100,    // ← 重複！刪除
-                share_venue_owner: device.share_venue_owner || 0,        // ← 重複！刪除
-                live_pin: device.live_pin ?? 0,                          // ← 留著但修正縮排
-                live_timeout_sec: device.live_timeout_sec ?? 120         // ← 留著但修正縮排
+                    live_pin: device.live_pin ?? 0,
+                    live_timeout_sec: device.live_timeout_sec ?? 120
```

### 錯誤 2：第 1917 行附近 - Tab 按鈕 HTML 錯位

Live Pin `</button>` 結束標籤和原本分潤管理的 `</button>` 重疊，導致 HTML 結構錯誤：

```
                        分潤管理
+                    <button ...>💓 存活感測</button>   ← 新按鈕
                        </button>                        ← 這是分潤管理的結束標籤，但位置錯了
```

應確認分潤管理的 `</button>` 在 Live Pin 按鈕之前正確關閉。

---

## ✅ 驗收標準

1. 修復後 `https://iot.tg25.win/devices` 頁面正常載入，設備列表正確顯示
2. 瀏覽器 Console 無 Alpine ReferenceError
3. 點擊任一設備 → 編輯 Modal → 所有 Tab（含 💓 存活感測）可正常切換
4. Live Pin 選項（停用/UI3/UI4）和離場逾時（30-600秒）可正常讀取/儲存
5. Commit + Deploy 到 yd174

---

## 📎 參考

- 問題 Commit: `da14472`
- 檔案: `resources/views/iot/modules/m3/devices.blade.php`
- Console 錯誤截圖：20+ 個 Alpine ReferenceError (claimErrors, selectedDevice, showDeviceModal 等全部 not defined)

