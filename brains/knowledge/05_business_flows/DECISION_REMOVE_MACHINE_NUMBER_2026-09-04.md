# 設計決策：移除 machine_number/machine_name 概念

**日期**：2026-09-04  
**決策者**：HQ + Joe  
**影響範圍**：SignalHub (Sidney) + IOTwawS3 (Coli)

---

## 決策內容

完全移除 `machine_number` 和 `machine_name` 欄位及相關功能。

---

## 背景

最初設計時，考慮在 SignalHub 後台和採集卡韌體中加入 `machine_number`（機台編號）和 `machine_name`（機台名稱）欄位，目的是：
- 讓運維人員在後台能識別每台設備對應的實體機台
- 在 Webhook 和 Serial 消息中攜帶機台編號，方便消費端處理

**實作狀態**：
- SignalHub 已新增 `devices.machine_number` 和 `signal_profiles.machine_number` 欄位
- Coli 韌體在 Serial JSON 中從 `device_id` 格式化出 "machine" 欄位（例：device_id=42 → "M042"）
- Webhook payload 包含這兩個欄位

---

## 問題分析

### 問題 1：兩套編號系統混淆
- SignalHub 的 `machine_number` 是業主自訂（例："A區-老虎機-01"）
- Coli Serial 的 `"machine"` 是從 `device_id` 自動格式化（例："M042"）
- 兩個 "machine" 概念完全不同，容易混淆

### 問題 2：Serial 路徑無法同步配置
- 數據流向：ESP32 → USB Cable → 小猴收銀系統
- 這條路徑**不經過 SignalHub 後台**
- Coli 韌體無法從雲端取得 `machine_number` 配置

### 問題 3：韌體通用性受損
- 不可能為每台機器燒錄不同的 `machine_number`
- 如果要支援，需要：
  - 配網時額外設定（複雜度高）
  - 新增 NVS 儲存（維護成本高）
  - 修改多處代碼（風險高）

### 問題 4：責任混亂
- **硬體層**應該只負責：我是誰（chip_id/device_id）+ 發生什麼（signals）
- **業務層**才應該負責：這是哪台機器（machine_number）
- 混在一起違反了責任分離原則

---

## 決策理由

### ✅ 架構清晰度
- 硬體層專注於設備識別和數據採集
- 業務邏輯層（小猴/客戶）自行維護映射表
- 清楚的邊界和職責劃分

### ✅ 降低系統複雜度
- 不需要在韌體中維護業務編號
- 不需要配置同步機制
- 減少出錯機會

### ✅ 提高靈活性
- 每個客戶可以自行定義編號規則
- 不受我們系統限制
- 更容易適應不同場景

### ✅ 韌體通用性
- 同一個韌體適用所有客戶
- 不需要定制化燒錄
- 降低維護成本

---

## 實施方案

### SignalHub (Sidney)
1. ✅ 移除 `devices.machine_number` 和 `devices.machine_name` 欄位
2. ✅ 移除 `signal_profiles.machine_number` 和 `signal_profiles.machine_name` 欄位
3. ✅ 保留 `signal_profiles.serial_enabled` 和 `signal_webhook_deliveries.cleared_points`
4. ✅ Webhook payload 不再包含 machine 欄位
5. ✅ 通知服務改用 `profile_name` 代替

### Coli 韌體 (IOTwawS3)
1. ✅ Serial JSON 移除 `"machine"` 欄位
2. ✅ 只保留：`chip_id`, `device_id`, `event`, `pin`, `raw`, `delta`, `ts`
3. ✅ 更新文檔說明新格式
4. ✅ 發布 v1.0.28

---

## 影響範圍

### 對內部系統
- SignalHub 後台：移除相關 UI 和功能
- 資料庫：執行 migration 移除欄位
- Coli 韌體：需要重新編譯和發布

### 對客戶（小猴等）
- 需要自行維護 `chip_id/device_id ↔ 業務編號` 映射表
- Serial JSON 解析邏輯需要調整（移除對 "machine" 欄位的依賴）
- MQTT 消息格式不受影響

---

## 替代方案（已否決）

### 方案 A：在韌體中維護 machine_number
**問題**：
- 配網時需要額外設定
- Serial 路徑無法從雲端同步
- 韌體通用性受損

### 方案 B：SignalHub Webhook 補充 machine_number
**問題**：
- 只解決了 Webhook 路徑，Serial 路徑仍然無解
- 增加 SignalHub 處理負擔
- 不如讓客戶端自己維護來得靈活

---

## 後續行動

1. ✅ 回滾相關代碼
2. ✅ 更新文檔
3. ⏳ 執行 SignalHub migration
4. ⏳ 編譯並發布 Coli v1.0.28
5. ⏳ 通知小猴團隊變更

---

## 經驗教訓

1. **在實作前充分討論架構設計**
   - 這次是在實作後才發現問題
   - 應該在設計階段就考慮責任分離和數據流向

2. **考慮所有數據路徑**
   - 不只是 MQTT（雲端路徑）
   - 還有 Serial（地端路徑）
   - 兩條路徑的配置同步是個挑戰

3. **硬體層保持簡單**
   - 韌體應該專注於核心功能
   - 業務邏輯盡量放在後端或客戶端
   - 降低韌體複雜度 = 降低出錯機率

---

**結論**：這是一個正確的決策，雖然需要回滾代碼，但長期來看簡化了架構並降低了維護成本。

