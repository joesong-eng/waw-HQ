# 任務：TASK_20260819_OWNER_CLEANUP_AND_DOCS

**派發時間**：2026-08-19 17:53  
**優先級**：high  
**負責人**：Sophie

---

## 📋 任務內容

### 1. 專案清理與 .gitignore 更新
- 刪除 PROJECT/Owner 下所有臨時/備份檔案（包含 app/Models、app/Services、resources/views、routes 等目錄下的 .backup, .orig, .broken, .original, .temp_fix 等）。
- 於 PROJECT/Owner/.gitignore 中加入以上暫存副檔名過濾規則。

### 2. 專案 README.md 補齊
- 撰寫 PROJECT/Owner/README.md，內容包含：
  - 系統定位與職責 (wawOwner, iot.tg25.win)
  - 本地開發與常用指令 (composer dev 等)
  - 核心 API 端點與 WebSocket (Reverb) 說明
  - MQTT 主題訂閱 (device/+/status, device/+/credit)
  - 跨系統對接關係 (Mina, Ina, Hubie)
  - 部署指引

### 3. 測試骨架規劃
- 規劃核心業務邏輯（Device.php, Machine.php, 分潤計算）的單元測試架構，列出後續實作清單。

---

## 📝 回報格式

```markdown
# 任務回報：TASK_20260819_OWNER_CLEANUP_AND_DOCS

**完成時間**：YYYY-MM-DD HH:MM  
**執行者**：Sophie

## 執行結果
（寫在這裡）

## 結論
✅ 完成 / ❌ 遇到問題

---
**回報者**：Sophie  
**回報時間**：YYYY-MM-DD HH:MM
```

---

**派發者**：HQ  
**派發時間**：2026-08-19 17:53
