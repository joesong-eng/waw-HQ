# 任務回報：TASK_20260904_SIDNEY_BATCH_UPDATE_PROFILES (最終完成版)

**完成時間**：2026-09-04 21:00  
**執行者**：sidney

## 執行結果

已成功實作 SignalHub **真正的批量設置功能** — 一次設置多台採集卡。

## 任務理解歷程

1. **第一次誤解**：實作了 Deliveries 批量重試功能
2. **第二次誤解**：恢復了單台設置精靈
3. **最終正確**：實作真正的批量設置 — 勾選多台、一次配置、全部套用

## 完整實作內容

### 1. 後端 API

#### Device Model (新增)
```php
app/Models/Device.php
- 讀取 devices 表
- pendingSetup() scope 篩選未設置設備
- forOwner() scope 篩選當前用戶
```

#### SignalHubController 新方法
```php
indexPendingDevices()
- GET /api/v9/signal-hub/pending-devices
- 列出當前用戶的待設置採集卡

batchCreateProfiles()
- POST /api/v9/signal-hub/batch-create-profiles
- 接收 device_ids 陣列 (1-100台)
- 接收統一的 config 配置
- 批量建立 profiles + pin_mappings + webhooks
- 更新 devices.status = 'active'
- 使用 DB transaction 確保原子性
```

### 2. 前端 UI

#### 未設置設備區塊 (橘色卡片)
- 🟧 橘色背景 (`bg-orange-950/40`)
- 🟧 橘色邊框 (`border-orange-600/60`)
- ⚠️ 「待設置」標籤
- 顯示 chip_id、綁定時間、最後上線
- Checkbox 批量選擇
- 點擊整個卡片可切換選擇狀態

#### 批量操作工具列
- 選中設備時顯示「⚡ 批量設置 (N 台)」按鈕
- 橘色漸變按鈕 (`from-orange-600 to-orange-500`)
- 動態顯示選中台數

#### 批量設置精靈
- 標題動態顯示：
  - 未選設備：「3 步極速設置精靈」
  - 已選設備：「批量設置 N 台採集卡」
- 副標題顯示橘色提示
- submitWizard() 自動判斷批量/單個模式
- 批量模式呼叫 `/batch-create-profiles` API
- 完成後清空選擇並刷新列表

### 3. Alpine.js 狀態管理

新增 data 屬性：
- `pendingDevices: []` — 未設置的設備列表
- `selectedDeviceIds: []` — 選中的設備 ID

新增方法：
- `loadPendingDevices()` — 載入待設置設備
- `toggleDeviceSelection(deviceId)` — 切換單個選擇
- `hasSelectedDevices` — 計算屬性：是否有選中
- `selectedDeviceCount` — 計算屬性：選中數量
- `openBatchWizard()` — 開啟批量設置精靈

### 4. 批量設置流程

```
用戶登入
  ↓
顯示橘色未設置卡片 (pendingDevices)
  ↓
勾選多台設備 (Checkbox)
  ↓
點擊「⚡ 批量設置 (N 台)」
  ↓
開啟設置精靈
  ↓
Step 1: 行業標籤
Step 2: 8個腳位配置 (統一)
Step 3: Webhook URL + USB Serial
  ↓
提交 → POST /batch-create-profiles
  ↓
後端批量建立：
  - N 個 signal_profiles
  - N × 8 個 signal_pin_mappings
  - N 個 signal_webhooks (如有)
  - 更新 N 個 devices.status = 'active'
  ↓
前端刷新：
  - 清空 selectedDeviceIds
  - 重新載入 pendingDevices (橘色卡片消失)
  - 重新載入 profiles (新增已設置的卡片)
```

## 視覺設計

### 未設置卡片 (橘色)
- 背景：`bg-orange-950/40`
- 邊框：`border-2 border-orange-600/60`
- 懸停：`hover:border-orange-500`
- 文字：橘色系 (`text-orange-300/400`)
- 標籤：⚠️ 待設置

### 已設置卡片 (深色)
- 背景：`bg-slate-800`
- 邊框：`border-slate-700`
- 文字：白色/淺色系
- 標籤：✓ 啟用中 (綠色)

## Git 提交

- **Commit**: `21a1a72`
- **Message**: "Implement true batch setup for multiple collectors"
- **Files Changed**:
  - app/Models/Device.php (新增)
  - app/Http/Controllers/Api/V9/SignalHubController.php
  - routes/api.php
  - resources/views/iot/modules/m10/profiles.blade.php

## 部署狀態

- ✅ 已推送到 GitHub (main branch)
- ✅ 已部署到遠端伺服器 (signal.tg25.win)
- ✅ Laravel 快取已清除

## 線上驗證

**URL**: https://signal.tg25.win/signal-hub/profiles

**驗證步驟**：
1. 刷新頁面
2. 如有未設置設備，會顯示橘色卡片區塊
3. 勾選多台設備
4. 點擊「⚡ 批量設置 (N 台)」按鈕
5. 填寫配置
6. 完成後所有選中設備都套用相同配置
7. 橘色卡片消失，新增已設置卡片

## 結論

✅ **完成**

SignalHub 批量設置採集卡功能已完整實作並部署上線。

支援 1-100 台採集卡同時設置，大幅提升老李等大客戶的設置效率。

---
**回報者**：sidney  
**回報時間**：2026-09-04 21:00

