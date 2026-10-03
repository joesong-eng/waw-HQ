# Owner 專案分析報告

**報告時間**：2026-08-19 17:47  
**報告人**：Sophie (Owner Agent)  
**專案位置**：`/Users/ilawusong/Documents/WaW/PROJECT/Owner`

---

## 📊 專案概況

### 技術棧
- **後端**：Laravel 11.31 + PHP 8.2
- **前端**：Vite 6.0 + Tailwind CSS 3.4 + Alpine.js
- **即時通訊**：Laravel Reverb + Pusher
- **PDF生成**：Laravel DomPDF
- **開發工具**：Laravel Pail、Pint、Sail

### 專案角色定位
- **網域**：`iot.tg25.win`
- **職責**：營運商後台與設備管理
- **MQTT 主題**：管理 `device/{chip_id}/` 相關主題

---

## 🔴 高優先級問題

### 1. 測試覆蓋率嚴重不足 ⚠️

**現況**：
```
tests/Feature/
├── RevenueControllerRefactorTest.php
├── ProfitSharingAgreementTest.php
├── StatisticsControllerTest.php
├── DeviceOnlineStatusInitTest.php
└── M6/
    ├── ReportApiTest.php
    └── StatisticsControllerTest.php
```
僅 6 個業務測試，但專案涉及：
- IoT 設備管理（MQTT 通訊）
- 金流處理與分潤計算
- 即時監控與 WebSocket
- 多系統 API 對接

**風險評估**：
- WAW 2.0 雙資料庫遷移缺乏測試保護
- Migration 執行風險高
- API 變更可能影響其他 Agent（Mina、Ina、Hubie）

**建議**：
1. 為核心業務邏輯建立單元測試：
   - `app/Models/Device.php` (7.8KB，核心模型)
   - `app/Models/Machine.php` (4.7KB)
   - 分潤計算邏輯
2. 為 `/api/iot/*` 路由建立整合測試
3. MQTT 訊息處理建立模擬測試
4. 考慮引入 Pest PHP 提升測試可讀性

---

### 2. 程式碼備份檔案混亂 🗑️

**發現**：
```
app/Models/
├── Device.php
├── Device.php.backup
├── Device.php.orig
├── MachineExtensions.php
├── MachineExtensions.php.backup
├── MachineExtensions.php.broken
├── MachineExtensions.php.original
└── MachineExtensions.php.temp_fix
```

**問題分析**：
- 顯示對 Git 版本控制信心不足
- 增加專案混亂度
- 可能誤用錯誤版本

**建議**：
1. 立即清理所有 `.backup`、`.orig`、`.broken`、`.temp_fix` 檔案
2. 更新 `.gitignore` 排除：
   ```
   *.backup
   *.orig
   *.broken
   *.temp_fix
   ```
3. 建立 Git 使用規範：使用 feature branch 而非檔案備份

---

### 3. 專案文檔缺失 📄

**現況**：
- `README.md` 僅為 Laravel 預設範本
- 無 Owner 系統專屬說明
- 有 `deploy.sh` 但無部署文檔

**建議新增內容**：
```markdown
# Owner System (wawOwner)

## 系統職責
- 營運商後台管理
- 遊戲機設備管理 (device/{chip_id}/)
- 分潤協議與報表
- 即時監控 (/realtime)

## 本地開發
composer dev  # 啟動 server + queue + logs + vite

## 關鍵 API 端點
- POST /api/iot/devices          # 設備註冊
- GET  /api/iot/devices/{id}     # 設備狀態
- WebSocket: Reverb (Pusher協議)

## MQTT 主題訂閱
- device/+/status                # 設備狀態更新
- device/+/credit                # 信用點數變更

## 與其他系統對接
- Mina (Member): 玩家端開分請求
- Ina (Infra): 資料庫 Migration 申請
- Hubie (iHub): 平板端設備綁定

## 部署
bash deploy.sh  # 詳見知識庫 DEPLOYMENT_GUIDE.md
```

---

## 🟡 中優先級建議

### 4. TODO.md 階段一任務阻塞

**當前狀態**（來自 `/Users/ilawusong/Documents/WaW/TODO.md`）：

**已完成**：
- ✅ Sophie (Owner): 向 Ina 提交 devices 表 Schema 變更請求

**待執行**：
- ⏳ **Ina (Infra)**: 審核並執行 devices 表 Migration（阻塞中）
- ⏳ **Ina (Infra)**: 將 SQL 查詢的 `pulse_ratio` 改為 `pulse_to_token`（阻塞中）

**影響**：
- 第一階段未完成，無法進入第二階段（WAW 2.0 雙庫設計）
- `pulse_ratio` 命名不一致持續存在

**建議**：
- HQ 確認 Ina 任務狀態
- 若 Ina 阻塞，考慮 HQ 協調資源

---

### 5. 多 Agent 協作流程改善

**現行機制**（v4.0 純檔案系統）：
```
.taskflow/owner/
├── inbox/   # 接收 HQ 任務
└── outbox/  # 回報結果
```

**觀察**：
- 任務派發依賴手動執行 `hq_task_flow.sh`
- 回報格式可能不一致
- 缺乏任務狀態可視化

**建議**：
1. 標準化回報格式（本報告即為範例）
2. HQ 層級建立任務狀態儀表板（可選）
3. 為高頻任務建立範本：
   - 資料庫 Migration 申請範本
   - API 變更諮詢範本
   - 部署驗收報告範本

---

### 6. 環境變數管理

**現況**：
- 有 `.env` 和 `.env.example`
- Owner 系統連接多個外部服務（MQTT、Redis、其他 Agent API）

**建議**：
1. 在 `.env.example` 補充變數說明：
   ```ini
   # MQTT Broker (Infra 管理)
   MQTT_HOST=iot.tg25.win
   MQTT_PORT=1883
   
   # Redis (用於快取與 Queue)
   REDIS_HOST=127.0.0.1
   
   # Member API (Mina 提供)
   MEMBER_BILL_API_URL=https://win.tg25.win/api/bills
   
   # WebSocket (Reverb)
   REVERB_APP_ID=
   REVERB_APP_KEY=
   ```

2. 建立環境變數驗證（啟動時檢查）
3. 生產環境使用 `php artisan config:cache` 優化

---

## 🟢 低優先級建議

### 7. 前端測試

**現況**：
- 前端使用 Vite + Tailwind + Alpine.js
- 僅 1 個前端測試：`resources/js/darkMode.test.js`
- 即時監控頁面缺乏測試

**建議**：
- 考慮使用 Vitest 建立 JavaScript 單元測試
- 為互動元件建立測試（特別是 `/realtime` 監控頁）

---

### 8. 知識庫快速參考

**現況**：
- HQ 維護了完整 `brains/knowledge/`
- Agent 需查閱 `../../brains/knowledge/02_technical_standards/MQTT_TOPIC_STANDARD.md`

**建議**：
在 Owner 專案建立快速參考：
```
PROJECT/Owner/docs/
├── QUICK_REFERENCE.md       # 常用知識庫連結
├── MQTT_TOPICS.md           # MQTT 主題快速查詢
└── API_CONTRACTS.md         # 與其他系統的 API 契約
```

---

## 🚀 建議執行順序

### 立即可執行（本週）
1. **清理備份檔案**（低風險，30分鐘）
   - 刪除 `.backup`、`.orig`、`.broken`、`.temp_fix`
   - 更新 `.gitignore`

2. **補充 README.md**（1小時）
   - 參考上述範本撰寫

3. **追蹤 Ina 任務**（協調）
   - 確認 devices 表 Migration 狀態
   - 確認 `pulse_ratio` → `pulse_to_token` 進度

### 近期規劃（本月）
4. **建立測試框架**（3-5天）
   - 從核心業務邏輯開始
   - 優先覆蓋分潤計算、設備狀態管理

5. **環境變數文檔化**（2小時）
   - 更新 `.env.example` 加入說明

### 長期改善（下季度）
6. **提升測試覆蓋率至 60%+**
7. **建立 CI/CD 流程**（需 HQ 協調）

---

## 📋 需要 HQ 決策的事項

1. **Ina 任務阻塞**：devices 表 Migration 是否需要加速？
2. **測試策略**：是否要求所有 Agent 專案達到最低測試覆蓋率？
3. **多 Agent 協作**：是否需要建立統一的任務狀態追蹤系統？
4. **備份檔案清理**：是否需要其他 Agent 同步檢查並清理？

---

## 🔗 相關文檔

- 知識庫索引：`../../brains/knowledge/DOCUMENT_INDEX.md`
- 派工協議：`../../brains/knowledge/01_agent_governance/SIMPLE_FILE_DISPATCH_PROTOCOL.md`
- MQTT 規範：`../../brains/knowledge/02_technical_standards/MQTT_TOPIC_STANDARD.md`
- 部署指南：`../../brains/knowledge/04_ops_and_deployments/DEPLOYMENT_GUIDE.md`
- HQ TODO：`../../TODO.md`

---

**報告結束**

Sophie 已完成 Owner 專案分析，建議 HQ 審閱並決策優先執行項目。
