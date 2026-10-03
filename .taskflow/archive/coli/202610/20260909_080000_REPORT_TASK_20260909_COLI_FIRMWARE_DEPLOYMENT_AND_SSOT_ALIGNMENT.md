# 任務回報：REPORT_TASK_20260909_COLI_FIRMWARE_DEPLOYMENT_AND_SSOT_ALIGNMENT

**完成時間**：2026-09-09 08:00  
**執行者**：Coli (IOTwawS3 遊戲機訊號採集韌體負責人)  
**決策者**：Joe (Boss)  
**匯報對象**：HQ (Taskflow 總指揮)  
**協同對象**：Allie (Alliance 燒錄站)、Ina (Infra / hware 部署)  
**當前版本**：v2.0.0  
**Git 最新提交**：`692a04f` (`origin/main`)

---

## 🎯 執行成果與戰果摘要

### 1. 版本管理 SSOT (Single Source of Truth) 機制全面閉環
- **解決痛點**：過去每次版本更新需手動同步修改 5 處以上文件（`CHANGELOG.md`、`platformio.ini`、根目錄 `CMakeLists.txt`、`src/CMakeLists.txt`、`api/version.json`、`scripts/generate_web_firmware.py`），極易發生版本不一致或幽靈版本。
- **現在成果**：
  - **唯一真相來源**：確立 CHANGELOG.md 為全專案唯一手動修改來源。
  - **一鍵全自動同步**：執行 `python3 scripts/sync-version.py` 即自動更新所有檔案之版本號、OTA 下載 URL、網頁燒錄 URL、發布日期與更新摘要。
  - **防呆檢查機制**：支援 `python3 scripts/sync-version.py --check` 秒級檢查全庫版本一致性。
  - **韌體生成對齊**：`scripts/generate_web_firmware.py` 優先直接解析 `CHANGELOG.md`，杜絕任何預設舊版本 fallback 隱患。

### 2. SCons / IDE 語法檢查與動態執行期相容
- **解決痛點**：`scripts/generate_web_firmware.py` 在 IDE 靜態檢查（Pyright / Pylance）時因 SCons 動態注入 `env` 變數而持續報錯 `Could not find name 'env'`。
- **現在成果**：改以 `globals().get("env")` 安全宣告與解析，徹底消除 IDE 警告，同時完美兼顧 PlatformIO SCons post-action 構建與 CLI 獨立執行。

### 3. OTA 下載路徑與 Alliance 燒錄站深度審計（突破重大致命衝突）
- **審計發現**：
  - Alliance 網頁燒錄站（`burning.blade.php`）使用 WebSerial API，固定向 Flash `address: 0x0` 寫入二進位。
  - 若直接使用 OTA 用的純 App 韌體（`firmware-v2.0.0.bin`，起始位址 0x10000），全新板子燒入 0x0 會因缺少 Bootloader 與分區表而**直接變磚無法開機**。
- **架構方案落地**：
  - 升級 `api/version.json`，實現雙軌分離：
    - `stable.url`：指向 `firmware-v2.0.0.bin`（純 App 韌體，供 ESP32-S3 線上 OTA 安全寫入 OTA 分區）。
    - `stable.merged_url`：指向 `firmware-v2.0.0-merged.bin`（含 Bootloader@0x0 + Partitions@0x8000 + App@0x10000，供 Alliance 0x0 物理燒錄）。
  - `sync-version.py` 已同步自動化產生 `url` 與 `merged_url`。

### 4. 程式庫安全性與硬體訊號強化
- **敏感資訊隔離**：`.gitignore` 完整隔離 TLS 私鑰（`certs/*.key`）、環境變數（`.env*`）、本地工具鏈快取（`.cache/`、`.clangd`）。
- **訊號採集穩定**：修正 PCNT 計數邊沿極性映射邏輯，降低高頻輪詢日誌干擾。
- **WAW-USS 標準響應**：`simulate_pulse` 指令執行後發布標準 ACK 主題。

---

## 📋 協同任務請求（給 HQ 轉派）

為完成全域生產線閉環，請 HQ 協調下列 Agent 配合：

### 1. 請派工 Ina (Infra) — 部署韌體檔案至 `hware.tg25.win`
需將本地已驗證通過之 v2.0.0 韌體產物上傳至 `infra` 主機（`141.148.165.50`）之 `/var/www/hware.tg25.win/`：
- `/var/www/hware.tg25.win/api/version.json`（更新為 v2.0.0，包含 `url` 與 `merged_url`）
- `/var/www/hware.tg25.win/firmware/IOTwawS3/version.json`（專案專屬版本資訊）
- `/var/www/hware.tg25.win/firmware/IOTwawS3/firmware-v2.0.0.bin`（App 韌體，消除當前 404）
- `/var/www/hware.tg25.win/firmware/IOTwawS3/firmware-v2.0.0-merged.bin`（合併韌體）

### 2. 請派工 Allie (Alliance) — 確保燒錄代理優先取用 `merged_url`
建議審查 `Alliance/app/Http/Controllers/DeviceController.php`：
```php
$firmwareUrl = $manifest['stable']['merged_url'] ?? $manifest['stable']['url'] ?? null;
```
確保 Alliance 燒錄通訊卡時下載完整 Merged 包，杜絕燒錄後無法開機之客訴。

---

## 🏁 結論
Coli 職責範圍內之所有韌體修正、版本管理自動化閉環及部署準備已 100% 達成並推送到儲存庫。
