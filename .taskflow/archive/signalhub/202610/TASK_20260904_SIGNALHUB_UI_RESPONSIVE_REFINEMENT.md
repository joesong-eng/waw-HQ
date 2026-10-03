---
task_id: TASK_20260904_SIGNALHUB_UI_RESPONSIVE_REFINEMENT
assignee: sidney
reporter: kiro
priority: normal
status: completed
created_at: 2026-09-04T18:41:00+08:00
completed_at: 2026-09-04T18:41:00+08:00
---

# SignalHub UI 響應式佈局與業務邏輯修正

## 📋 任務摘要

針對 SignalHub (https://signal.tg25.win/signal-hub/profiles) 進行完整的響應式佈局修正、主題統一、業務邏輯澄清與無效功能移除。

## 🎯 主要改動

### 1. 導航頁籤化改造 (`app.blade.php`)
**檔案**: `resources/views/layouts/app.blade.php`

- **原有問題**: 頂部導航使用傳統按鈕組，無明確視覺層級，域名標識 `● signal.tg25.win` 佔用空間
- **改進方案**:
  - 將導航改為清晰的頁籤 UI (Tabs)
  - 激活頁籤與 body 背景 (`bg-slate-900`) 無縫連接，頂部加青色高亮 (`border-t-2 border-cyan-400`)
  - 未激活頁籤保留細邊框 (`border-t border-x border-b border-slate-700`)，清晰區隔
  - 移除域名標識 pill `● signal.tg25.win`

**相關 Commit**: `e304bc4`, `4c72e07`, `72d6468`

---

### 2. 信號配置列表頁響應式重構 (`profiles.blade.php`)
**檔案**: `resources/views/iot/modules/m10/profiles.blade.php`

#### 2.1 佈局改造
- **原有問題**: 固定寬度表格欄位間距過寬，小螢幕直接破版，內容排列混亂
- **改進方案**:
  - 廢除傳統 table 佈局，改用響應式卡片流 (card stream)
  - 每張卡片包含:
    - **頂部**: 機台編號/名稱 + 行業標籤
    - **中部**: 三欄緊湊排列 — USB / Serial / Webhook 狀態
    - **底部**: 輸出通道數 / 已配腳位數 / 在線狀態
    - **操作**: 右側按鈕組 (管理腳位 / ⚡派送記錄 / 🔔Webhooks)
  - 卡片在小螢幕自動堆疊，大螢幕兩欄或三欄網格

#### 2.2 業務邏輯澄清與功能移除
- **移除副標題** `（實體卡由老邱出貨自動登錄至名下）`：資訊已內化至業務邏輯，無需前端重複提示
- **移除按鈕**:
  - `⚡ 3步極速設置精靈` (批量設置精靈)
  - `+ 新增機台配置` (單台手動新增)
  - `🎛️ 模擬器` 冗餘按鈕 (已有頂部頁籤)
- **原因**: 採集卡的新增與綁定嚴格由 **老邱出貨單** 觸發 (`collector_owner_id` 綁定購買人)，前端不應提供任意建立入口，避免產生無實體對應的虛擬記錄

#### 2.3 搜尋區塊優化
- **頂部控制列**: 標題右上角新增 `🔍` 按鈕，點擊切換搜尋欄可見性
- **預設狀態**: 搜尋欄隱藏
- **移除元素**:
  - `[收合搜尋 共 2 組]` 冗餘文字
  - 搜尋框保持簡潔，僅顯示必要欄位

**相關 Commit**: `2136f52`, `baf562b`, `d6ba636`, `34207e4`, `414290b`, `bc1e898`, `cd38267`, `4413056`, `fe8925e`

---

### 3. 腳位配置頁主題統一與邏輯簡化 (`pins.blade.php`)
**檔案**: `resources/views/iot/modules/m10/pins.blade.php`

#### 3.1 主題統一
- **原有問題**: 頁面混雜暗黑 (`bg-slate-900`) 與亮色 (`bg-white`, `bg-blue-50`) 元素，視覺不一致
- **改進方案**: 全頁統一為 Dark Slate 高對比主題 (`bg-slate-800 / 700 / 900` + 青色強調色)

#### 3.2 移除無效欄位
- **脈衝換算倍率 (點數/脈衝)**: 已移除
  - **原因**: 硬體脈衝與點數為 1:1 固定對應，換算邏輯已下沉至後端結算/webhook 層，前端無需配置
- **信號類型 (Signal Mode)**: 已移除
  - **原因**: UI 腳位預設為 `counter`，UO 腳位預設為 `level` (繼電器開關)，無需前端選擇

#### 3.3 預設啟用邏輯調整
- **新規則**:
  - `UI1` (開分)：預設 `● 啟用中`
  - `UI2` (洗分)：預設 `● 啟用中`
  - `UI3`, `UI4`, `UO1` ~ `UO4`：預設 `○ 停用` (需現場手動開啟)
- **資料庫驗證**:
  - 已於遠端 DB 檢查 M001 (profile_id=5) 與 M002 (profile_id=6)
  - 確認 `UI1`/`UI2` 為 `is_visible=true`，其餘為 `is_visible=false` (`ignored`)

**相關 Commit**: `e304bc4`, `4c72e07`, `72d6468`

---

## 🚀 部署與驗證

### Git 提交記錄
```
e304bc4 - SignalHub profiles responsive card layout + cleanup wizard/manual-add
4c72e07 - Remove ratio/mode fields from pins.blade.php, unify dark theme
72d6468 - Set default active pins UI1/UI2 for M001/M002 in remote DB
2136f52 - Refactor profiles filter bar + magnifying glass toggle
baf562b - Remove subtitle/wizard buttons from profiles page
d6ba636 - Clean up profiles card layout spacing
34207e4 - Final profiles search bar toggle refinement
414290b - Remove simulator redundant button from profiles
bc1e898 - Unify tab borders in app.blade.php
cd38267 - Remove domain pill from header
4413056 - Final pin defaults verification
fe8925e - Profiles responsive polish + inactive tab borders
```

### 遠端部署
- **目標伺服器**: `129.153.116.174` (`signal.tg25.win`)
- **部署路徑**: `/www/wwwroot/signal.tg25.win`
- **部署方式**: `waw_ops.sh remote sidney "php artisan view:clear && php artisan cache:clear && php artisan route:clear"`
- **推送狀態**: 已推送至 `origin/main` (`https://github.com/joesong-eng/signal-hub-standalone.git`)

### 線上驗證
- **URL**: https://signal.tg25.win/signal-hub/profiles
- **狀態**: ✅ 已於 2026-09-04 18:41 通過瀏覽器實測
- **確認項目**:
  - 頁籤導航正常切換，激活狀態視覺清晰
  - 信號配置卡片在窄/寬螢幕均正確顯示
  - 搜尋區塊預設隱藏，🔍 按鈕功能正常
  - 腳位配置頁主題統一，預設啟用邏輯符合業務需求

---

## 📊 影響範圍

- **前端視圖**: 3 個 Blade 模板
- **資料庫**: 遠端 `m10_signal_profiles` / `m10_signal_pins` 表 (僅驗證/調整既有記錄，無結構變更)
- **業務邏輯**: 移除無效手動建立入口，強化「實體卡出貨綁定」業務規則
- **用戶體驗**: 響應式佈局顯著改善，小螢幕不再破版，資訊層級清晰

---

## ✅ 完成標準

- [x] 導航頁籤化，視覺層級清晰
- [x] 信號配置頁響應式卡片佈局，小螢幕不破版
- [x] 移除所有無效業務入口 (手動新增/批量精靈)
- [x] 腳位配置頁主題統一 (Dark Slate)
- [x] 移除無效欄位 (脈衝倍率/信號類型)
- [x] 預設啟用邏輯符合業務需求 (UI1/UI2 預設啟用)
- [x] 遠端 DB 狀態驗證通過
- [x] 線上部署完成，瀏覽器實測通過

---

## 📎 附件

- 修改前截圖: (用戶提供)
- 修改後驗證: https://signal.tg25.win/signal-hub/profiles
- Git diff: 可於 `https://github.com/joesong-eng/signal-hub-standalone.git` 查看上述 commits

---

**報告人**: Kiro  
**執行 Agent**: sidney  
**報告時間**: 2026-09-04 18:41:00 +08:00  
**狀態**: ✅ 已完成

