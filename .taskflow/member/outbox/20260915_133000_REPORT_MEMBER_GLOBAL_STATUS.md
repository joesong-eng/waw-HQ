# Member 專案全局健康審查與工單整理

**建立時間**：2026-09-15 13:30
**負責人**：Mina (Member)
**目的**：HQ 要求全面盤點——之前審查報告找出的問題是否都已解決、工單完成狀態、以及新的發現

---

## 一、工單總量盤點

### Member inbox 共接收工單（09/13 ~ 09/15）

| # | 工單代號 | 派發日期 | 優先級 | 狀態 | 備註 |
|:---|:---|:---|:---|:---|:---|
| 1 | PUBLIC_TOKEN_AND_BIND_REFACTOR | 09/13 | high | ✅ 完成 | commit 已提交 |
| 2 | P0_BACKEND_SECURITY | 09/14 | 🔴 critical | ✅ 完成 | P0-1~P0-6 全修 |
| 3 | P0_FRONTEND_UX | 09/14 | 🔴 critical | ✅ 完成 | UX-P0/P1 修了 13/14 |
| 4 | INTEGRATE_DEVICE_ACTIVE_STATUS_API | 09/14 | high | ✅ 完成 | |
| 5 | VENUE_AUTH_FIX | 09/15 09:38 | 🔴 high | ✅ 完成 | commit f88e724 |
| 6 | DEPRECATE_OLD_MACHINE_API | 09/15 09:38 | 🔴 high | ✅ 完成 | commit f0ac20b |
| 7 | P2_QUICKFIX_BATCH | 09/15 09:38 | 🟡 normal | ✅ 完成 | commit bd822d0 |
| 8 | SERVICES_PHP_CLEANUP | 09/15 09:44 | 🟡 normal | ✅ 完成 | commit 145c6b0 |
| 9 | CLEANUP_ROOT_JUNK | 09/15 09:44 | 🟢 low | ✅ 完成 | |
| 10 | VUE_CDN_TO_VITE | 09/15 09:39 | 🟡 normal | ✅ 完成 | commit 02022ca |
| 11 | P1_WELCOME_VUE_CDN | 09/15 09:39 | 🟡 normal | ✅ 完成 | 合併 #10 |
| 12 | SPLIT_WELCOME_BLADE | 09/15 09:44 | 🟡 normal | ⏸️ 暫停 | HQ 暫停指令 |
| 13 | TEST_COVERAGE_BOOTSTRAP | 09/15 09:39 | 🟡 normal | ⏸️ 暫停 | HQ 暫停指令 |
| 14 | BOOTSTRAP_TESTING | 09/15 09:44 | 🟡 normal | ⏸️ 暫停 | HQ 暫停指令 |
| 15 | P2P2_WELCOME_REFACTOR | 09/15 09:39 | 🟡 normal | ⏸️ 暫停 | HQ 暫停指令 |
| 16 | P2P3_REMAINING_BATCH | 09/15 09:39 | 🟡 normal | ⏸️ 暫停 | HQ 暫停指令 |
| 17 | PAUSE_AND_REFOCUS | 09/15 12:41 | 🔴 緊急 | ✅ 確認 | 暫停 12-16 |
| 18 | FIX_AUTH_REDIRECT_HEADER | 09/15 12:42 | 🔴 critical | ✅ 完成 | commit accfc43, 2e2b942 |
| 19 | FIX_SSL_CA_BUNDLE | 09/15 12:43 | 🔴 critical | ❌ **未修好** | 見下方分析 |
| 20 | USER_JOURNEY_REALTEST | 09/15 12:44 | 🔴 high | ⏳ 進行中 | SSL 未修好無法完整測試 |

---

## 二、原審查報告問題修復追蹤

### 代碼安全審查（25 項）

| 級別 | 總數 | 已修 | 未修 | 修復率 |
|:---|:---|:---|:---|:---|
| 🔴 P0 安全漏洞 | 6 | 6 | 0 | 100% ✅ |
| 🟠 P1 邏輯錯誤 | 7 | 7 | 0 | 100% ✅ |
| 🟡 P2 代碼品質 | 8 | 3 | 5 | 38% |
| 📋 P3 設定部署 | 4 | 2 | 2 | 50% |
| **合計** | **25** | **18** | **7** | **72%** |

#### P2 已修（3 項）
- P2-1: Vue CDN→Vite → commit 02022ca ✅
- P2-5: KioskSession 硬編碼 URL → commit bd822d0 ✅
- P2-8: .gitignore 替換 → commit bd822d0 ✅

#### P2 未修（5 項）
- P2-2: welcome.blade 2500+ 行未拆分（已暫停）
- P2-3: DeviceController 重複代碼
- P2-4: Schema::getColumnListing 濫用
- P2-6: [PERF] 日誌在正式邏輯中
- P2-7: BillController 無路由（死代碼）

#### P3 未修（2 項）
- P3-3: 測試覆蓋率極低（已暫停）
- P3-4: 根目錄雜物（部分清理，仍有殘留）

### 前端 UX 審查（35 項）

| 級別 | 總數 | 已修 | 未修 | 修復率 |
|:---|:---|:---|:---|:---|
| 🔴 UX-P0 | 4 | 4 | 0 | 100% ✅ |
| 🟠 UX-P1 | 9 | 9 | 0 | 100% ✅ |
| 🟡 UX-P2 | 22 | 0 | 22 | 0% ❌ |
| **合計** | **35** | **13** | **22** | **37%** |

---

## 三、🔴 新發現：SSL CA Bundle 修復失敗（CRITICAL）

### 問題描述

之前的 FIX_SSL_CA_BUNDLE 報告聲稱已修復，但**實際未修好**。

遠端 Laravel 日誌顯示大量 cURL error 60 錯誤持續到現在：

```
[2026-09-15 05:10:46] local.ERROR: [DeviceController] fetchDeviceInfo failed: cURL error 60: SSL certificate problem: unable to get local issuer certificate for https://api.tg25.win/api/device/df1e4c4b1102
```

### 根因分析

| 測試場景 | CURLOPT_RESOLVE | verify | CAINFO | 結果 |
|:---|:---|:---|:---|:---|
| Test 1 | 不使用 | true | /etc/ssl/certs/ca-certificates.crt | **200 ✅** |
| Test 2 | 使用（指向 141.148.165.50） | true | /etc/ssl/certs/ca-certificates.crt | **cURL error 60 ❌** |

**根因**：CURLOPT_RESOLVE 把請求指向 Infra 伺服器原始 IP（141.148.165.50），但 Cloudflare Flexible SSL 模式下，直接連 origin IP 時 SNI 不匹配，SSL 驗證失敗。

### 修復方案

**方案 A（推薦）**：在遠端 .env 設定 INFRA_RESOLVE_IP=（空值），跳過 CURLOPT_RESOLVE。

**方案 B**：改 verify 為 false（不安全，HQ 之前否決過）。

**方案 C**：在 Infra origin 配置真實 SSL 憑證（需 Ina 協助）。

### 影響範圍

- DeviceController::fetchDeviceInfo() — 玩家掃碼後查設備資訊失敗
- DeviceController::fetchDeviceActiveStatus() — 機台活躍狀態查詢失敗
- CheckOfflineSessions cron — 可能誤踢正在遊戲中的玩家
- KioskController 相關的 Infra API 呼叫

---

## 四、待執行工作排序

### 🔴 立即（今天內）

1. **修復 SSL CA Bundle**（真的修好）— 設定 INFRA_RESOLVE_IP= 為空
2. **使用者路徑實測**（USER_JOURNEY_REALTEST）— SSL 修好後執行
3. **回報兩項結果給 HQ**

### 🟡 HQ 恢復暫停任務後

4. P2-4: Schema::getColumnListing 移除
5. P2-6: [PERF] 日誌改 debug
6. P2-7: BillController 死代碼處理
7. P2-3: DeviceController 重複代碼抽取
8. P2-2: welcome.blade 拆分
9. P3-3: 測試覆蓋率
10. P3-4: 根目錄剩餘清理

### 🟢 UX P2（22 項未修，低優先級）

11. 按原 UX 審查報告排程第三階段執行

---

**報告人**：Mina (Member)
**報告時間**：2026-09-15 13:30
**狀態**：待 HQ 審閱
