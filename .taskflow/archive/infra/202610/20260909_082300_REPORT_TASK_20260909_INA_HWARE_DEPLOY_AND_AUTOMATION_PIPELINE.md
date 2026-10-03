# 任務回報：TASK_20260909_INA_HWARE_DEPLOY_AND_AUTOMATION_PIPELINE

**完成時間**：2026-09-09 08:23  
**執行者**：Ina (Infra Lead)

---

## 1. 線上部署與驗證結果

### 部署狀態
✅ IOTwawS3 v2.0.0 已成功部署至 `hware.tg25.win`

### URL 檢驗狀態

| URL | HTTP 狀態 | 說明 |
|-----|-----------|------|
| `https://hware.tg25.win/api/version.json` | **200 OK** | 全域版本 API，版本已更新為 2.0.0 |
| `https://hware.tg25.win/firmware/IOTwawS3/version.json` | **200 OK** | IOTwawS3 專屬版本資訊 |
| `https://hware.tg25.win/firmware/IOTwawS3/firmware-v2.0.0.bin` | **200 OK** | OTA 韌體（純 App） |
| `https://hware.tg25.win/firmware/IOTwawS3/firmware-v2.0.0-merged.bin` | **200 OK** | 完整開機映像（含 Bootloader + Partitions + App） |

### 檔案 SHA256 驗證

| 檔案 | 本地 SHA256 | 遠端 SHA256 | 狀態 |
|------|-------------|-------------|------|
| `firmware-v2.0.0.bin` | `1d9a60e0cc6385c3...` | `1d9a60e0cc6385c3...` | ✅ 一致 |
| `firmware-v2.0.0-merged.bin` | `810b6b308007daf9...` | `810b6b308007daf9...` | ✅ 一致 |

**結論**：本地產物與線上檔案完全一致，部署成功且無損壞。

### 版本資訊內容
```json
{
  "stable": {
    "version": "2.0.0",
    "url": "https://hware.tg25.win/firmware/IOTwawS3/firmware-v2.0.0.bin",
    "merged_url": "https://hware.tg25.win/firmware/IOTwawS3/firmware-v2.0.0-merged.bin",
    "changelog": "WAW-USS v1.0 全域信號標準對齊與 64-bit 脈衝計數",
    "released_at": "2026-08-31T00:00:00"
  }
}
```

---

## 2. 自動化發布通道交付成果

### 腳本位置
- **主腳本**：`PROJECT/Infra/hardware/scripts/publish-iotwaws3.sh`
- **使用文件**：`PROJECT/Infra/hardware/scripts/README-publish.md`
- **Git Commit**：`2909e2f`

### 用法
```bash
cd /Users/ilawusong/Documents/WaW/PROJECT/Infra
./hardware/scripts/publish-iotwaws3.sh <版本號>
```

**範例**：
```bash
./hardware/scripts/publish-iotwaws3.sh 2.0.1  # 發布 v2.0.1
```

### 腳本功能
1. ✅ **版本驗證**：自動檢查本地產物完整性與版本號一致性
2. ✅ **SHA256 計算**：計算本地檔案雜湊值
3. ✅ **遠端上傳**：使用 `scp` 上傳韌體和版本資訊
4. ✅ **完整性驗證**：比對遠端檔案 SHA256，確保傳輸無誤
5. ✅ **線上測試**：自動測試所有 URL 可用性（HTTP 200）
6. ✅ **彩色輸出**：友善的執行進度顯示

### 權限機制
- 使用 SSH 金鑰免密登入（`ssh infra`）
- 僅上傳至 `/var/www/hware.tg25.win/firmware/IOTwawS3/` 和 `/api/`
- 所有操作均有驗證步驟，確保安全性

### 適用角色
- **Coli**：可自行執行腳本發布韌體，無需請求 Ina
- **Ina**：維護腳本與基礎設施
- **HQ**：全域監督與架構決策

---

## 3. 部署過程記錄

### 執行步驟
1. 檢查本地產物（`IOTwawS3/firmware/` 和 `IOTwawS3/api/version.json`）
2. 計算本地檔案 SHA256
3. 使用 `scp` 上傳韌體至遠端 `/var/www/hware.tg25.win/firmware/IOTwawS3/`
4. 上傳 `version.json` 至 `/firmware/IOTwawS3/` 和 `/api/`
5. 驗證遠端檔案 SHA256
6. 測試線上 URL 可用性（全部 HTTP 200）

### 遠端目錄結構
```
/var/www/hware.tg25.win/
├── api/
│   └── version.json                          (全域版本 API)
└── firmware/
    └── IOTwawS3/
        ├── version.json                      (IOTwawS3 專屬版本資訊)
        ├── firmware-v2.0.0.bin               (OTA 韌體)
        ├── firmware-v2.0.0-merged.bin        (完整開機映像)
        └── [舊版本保留...]
```

---

## 結論

✅ **v2.0.0 線上部署完成**
- 所有 URL 可正常訪問（HTTP 200）
- SHA256 驗證通過，檔案完整無損
- 版本資訊已更新至 2.0.0

✅ **自動化發布通道已就緒**
- Coli 可使用 `publish-iotwaws3.sh` 自行發布未來版本（2.0.1+）
- 腳本包含完整驗證流程，確保發布安全性
- 使用說明文件已提供，含範例與常見問題

---

**任務狀態**：✅ 完成  
**Git Commit**：`2909e2f` (feat: 新增 IOTwawS3 韌體自動發布腳本)  
**下一步**：通知 Coli 自動化通道已就緒，可自行發布未來版本

