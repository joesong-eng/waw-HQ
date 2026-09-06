# iHub APK 打包工具說明

## 📍 位置

`/Users/ilawusong/Documents/sysWawIot/HQ/tools/ihubApp`

## 🎯 用途

使用 Apache Cordova 將 iHub WebView 應用打包成 Android APK。

## 🏗️ 三階段工作流程

### 階段 1：Web 內容開發 (Hubie)
- **專案路徑**: `/Users/ilawusong/Documents/sysWawIot/iHub`
- **負責 Agent**: Hubie
- **部署目標**: `ihub.tg25.win` (VPS: yd47)
- **內容**: Node.js Web 應用 (WebView 內容)

### 階段 2：APK 打包 (HQ Tools)
- **工具路徑**: `/Users/ilawusong/Documents/sysWawIot/HQ/tools/ihubApp`
- **技術**: Apache Cordova
- **輸出**: Android APK 檔案
- **特性**: WebView Wrapper，指向遠端 URL

### 階段 3：APK 發布 (Ina)
- **發布路徑**: `/Users/ilawusong/Documents/sysWawIot/tg25-infra/web/downloads/apk/`
- **負責 Agent**: Ina
- **下載 URL**: `https://api.tg25.win/downloads/apk/ihub-v1.0.x.apk`
- **版本管理**: `manifest.json`

## 📦 APK 配置

```xml
<widget id="com.tg25.ihub" version="1.0.6">
    <name>兌幣機-WaWI</name>
    <content src="https://ihub.tg25.win" />
</widget>
```

- **App ID**: `com.tg25.ihub`
- **當前版本**: v1.0.6
- **內容源**: 遠端 URL (不包含本地 HTML/JS)

## 🔄 版本更新策略

### 更新 Web 內容（無需重新打包）
1. Hubie 在 `iHub/` 專案中修改程式碼
2. 部署到 `ihub.tg25.win`
3. 使用者打開 APP 時自動載入新版本

### 更新 APK（需要重新打包）
只有以下情況才需要重新打包：
- 修改 App 配置（名稱、圖標、啟動畫面）
- 修改權限設定
- 修改 Cordova 插件
- 修改 WebView 指向的 URL

## 📝 打包步驟（簡要）

```bash
cd /Users/ilawusong/Documents/sysWawIot/HQ/tools/ihubApp
cordova build android --release
```

詳細步驟請參考：`HQ/tools/ihubApp/README.md`

## 🗂️ 歷史記錄

- **原始位置**: `/Users/ilawusong/AIPP/b202HOME/HQcenter/ihubApp`
- **遷移日期**: 2026-06-08
- **遷移原因**: HQ 是 wawIoT 協調中心，適合放置業務工具

## 🔗 相關文件

- **工具 README**: `HQ/tools/ihubApp/README.md`
- **iHub 專案**: `iHub/README.md`

---

**建立日期**: 2026-06-08  
**維護者**: HQ
