# 任務：TASK_20260909_INA_HWARE_DEPLOY_AND_AUTOMATION_PIPELINE

**派發時間**：2026-09-09 08:15  
**優先級**：HIGH  
**負責人**：Ina (Infra Lead)  
**協同對象**：Coli (IOTwawS3 Lead), Allie (Alliance Lead)

---

## 📋 任務背景與核心目標

Coli 已完成 IOTwawS3 遊戲採集卡韌體 v2.0.0 之建置、測試與 SSOT 閉環（Commit `692a04f` / `326c337`）。
目前經實際線上驗證：
1. `https://hware.tg25.win/api/version.json` 仍停留在舊版 v1.0.26。
2. `https://hware.tg25.win/firmware/IOTwawS3/firmware-v2.0.0.bin` 回傳 404。

為確保全域出廠燒錄與線上 OTA 生產線閉環，並徹底杜絕日後升版（如 v2.0.1+）仍需人工跨 Agent 傳檔之架構斷層，請 Ina 執行本次部署並建立自動化通道。

---

## 🔍 任務執行要點

### 1. 部署 v2.0.0 產物至 hware.tg25.win（解除 404）
- **產物來源**：本地 `PROJECT/IOTwawS3/`
  - `firmware/firmware-v2.0.0.bin`（純 App 韌體，供 OTA）
  - `firmware/firmware-v2.0.0-merged.bin`（含 Bootloader@0x0 + Partitions@0x8000 + App@0x10000 之完整開機二進位包，供出廠燒錄）
  - `api/version.json`（包含 stable.url 與 stable.merged_url）
- **遠端目標主機**：Infra 主機（`141.148.165.50`），檢驗 Nginx 根目錄（如 `/var/www/hware.tg25.win/` 或 `/var/www/hardware/`）：
  - 更新 `/api/version.json`
  - 更新 `/firmware/IOTwawS3/version.json`
  - 放置 `/firmware/IOTwawS3/firmware-v2.0.0.bin`
  - 放置 `/firmware/IOTwawS3/firmware-v2.0.0-merged.bin`
- **線上驗證**：
  - 驗證 `https://hware.tg25.win/api/version.json` 回傳 200 且版本為 2.0.0。
  - 驗證 `https://hware.tg25.win/firmware/IOTwawS3/firmware-v2.0.0.bin` 回傳 200。
  - 驗證 `https://hware.tg25.win/firmware/IOTwawS3/firmware-v2.0.0-merged.bin` 回傳 200。

### 2. 建立自動化發布通道（解決未來 Coli 自行發布需求）
- 審查現有 `PROJECT/Infra/hardware/scripts/upload-firmware.sh` 或於 `dev_tools/waw_ops.sh` 規劃標準發布命令。
- 制定並落地標準發布腳本/SOP，使 Coli 在日後升級到 2.0.1+ 時，可自行於本地執行指令一鍵將產物安全同步至 `hware.tg25.win`，無需每次由 HQ 派工請求 Ina 人工介入。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260909_INA_HWARE_DEPLOY_AND_AUTOMATION_PIPELINE

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：Ina (Infra Lead)

## 1. 線上部署與驗證結果
- URL 檢驗狀態 (curl 結果與 HTTP 狀態碼)
- 檔案 SHA256 驗證

## 2. 自動化發布通道交付成果
- 提供之發布腳本位置、用法與權限機制

## 結論
✅ v2.0.0 線上部署完成，自動化發布通道已就緒 / ❌ 遇到問題
```

---
**派發者**：HQ  
**派發時間**：2026-09-09 08:15

