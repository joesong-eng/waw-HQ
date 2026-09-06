# Agent 職責邊界 (Agent Responsibility Boundaries)

> **版本**: 3.0.0 (WAW 2.0)  
> **最後更新**: 2026-06-05  
> **適用對象**: 所有 Agent

---

## 📋 目錄

1. [核心理念](#核心理念)
2. [Agent 分離架構](#agent-分離架構)
3. [職責邊界定義](#職責邊界定義)
4. [代碼所有權保護](#代碼所有權保護)
5. [跨專案協作規範](#跨專案協作規範)
6. [違規案例與處理](#違規案例與處理)

---

## 核心理念

### 🎯 分門別類、各盡其職、記憶分離

每個專案的 Agent 應該:
1. **在自己的 workspace 運行**
2. **管理自己的記憶和 context**
3. **自己執行部署**
4. **只通過 HQ Message Hub 通訊**
5. **不跨專案修改代碼**

---

## Agent 分離架構

### ✅ 正確的架構

```
用戶 → HQ → 調用 HQ Message Hub
              ↓
            派發任務
              ↓
         Allie Agent (在 waw-cloud workspace)
              ↓
            修改 waw-cloud 文件
              ↓
            Allie 自己部署
              ↓
            回報到 HQ Message Hub
              ↓
            HQ 接收回報
              ↓
            通知用戶
```

**優點**:
- ✅ 完全分離的 context
- ✅ 記憶在正確的地方
- ✅ 可擴展到多個專案
- ✅ 真正的異步協作

---

## 職責邊界定義

### 📂 專案職責對照表 (WAW 2.0)

| 專案名稱 | 路徑 | 負責 Agent | 職責範圍 |
|------|------|--------|---------|
| **HQ** | `/Users/ilawusong/Documents/sysWawIot/HQ` | **Hera** (HQ) | 協調、維護知識庫（唯一寫入）、任務規劃與派發。 |
| **`waw-infra`** | 部署於雲端 (Ina) | **Ina** (Infra) | 資料庫、MQTT Server、Queue 管理與 Laravel 核心 API。**負責訂閱授權（防流浪機/流浪店）硬體攔截**。 |
| **`waw-wallet`** | 部署於雲端 (Mina) | **Mina** (Member) | 玩家端電子錢包、掃碼開分與洗分前端、第三方支付對接。 |
| **`waw-cloud`** | 部署於雲端 (Sophie/Allie) | **Sophie** (Owner) & **Allie** (Alliance) | 多租戶管理後台。負責「裝配商/經銷商/店主/機台主」權限、**機台部署關係建立**、**分潤協議設置**、**店面營運工具（交班、LINE警報）**。 |
| **`waw-exchange-console`** | 部署於 Android (Hubie) | **Hubie** (iHub) | 兌幣機終端顯示與物理收鈔/出硬幣操作之 Android UI。 |
| **`waw-firmware-exchange`** | IOTkiosk_v0 (Fio) | **Fio** (Firmware) | 兌幣機控制紙鈔與硬幣馬達韌體（Read+Write）。 |
| **`waw-firmware-arcade`** | IOTwawS3 (Coli) | **Coli** (Firmware) | 遊戲機/採集卡韌體（Read-Only），偵測脈衝回報。 |

---

### 🔐 資料庫操作權限 ⚠️ CRITICAL

**唯一執行者**：Ina (Infra)

**原因**：
- 所有 DB 實體由 `waw-infra` 統一管理
- 避免多個 Agent 同時操作 DB 導致衝突或鎖表

**其他 Agent 的正確流程**：

```
Mina/Sophie/Allie Agent 需要 DB 變更
  ↓
向 @Ina 發送 RFI（說明需求：哪個表、哪個欄位、要做什麼）
  ↓
Ina 評估並決定實作方式（migration 或 ALTER TABLE）
  ↓
Ina 在對應伺服器執行變更
  ↓
Ina 處理版本控制（如需要）
  ↓
Ina 回報執行結果（成功/失敗、錯誤訊息）
  ↓
Agent 繼續開發
```

**RFI 範本**：
```markdown
@Ina RFI: [專案名稱] DB Migration

**專案**: waw-wallet / waw-cloud
**變更需求**:
- 新增表：xxx (欄位: id, name, created_at...)
- 新增欄位：table_name.column_name (type: VARCHAR(255), nullable)
- 修改欄位：table_name.column_name (ENUM 加入新值 'xxx')
- 刪除欄位：table_name.column_name
- 新增索引：table_name (column1, column2)

**用途說明**: 為什麼需要這個變更 (例如支援 WAW 2.0 店面訂閱分潤)

**請求**: 請執行 DB 變更
```

**嚴禁的行為**：
- ❌ 其他 Agent 直接 SSH 到 VPS 執行 `php artisan migrate` 或 `ALTER TABLE`
- ❌ 直接在 VPS 上修改 DB schema
- ❌ 繞過 Ina 自行執行 DB 操作

---

## 跨專案協作規範

### ✅ 正確的跨專案協作流程

#### 場景 1: 需要其他專案的資訊

```
Mina 需要 Infra 的 DB schema
  ↓
Mina 透過 HQ Message Hub 問 @Ina
  ↓
Ina 在自己的 workspace 確認並回報
```

#### 場景 2: 需要其他專案修改代碼

```
Sophie 需要 Infra 新增訂閱攔截路由
  ↓
Sophie 透過 HQ Message Hub 向 @Ina 提交 RFI
  ↓
Ina 實作、測試並部署
  ↓
Ina 回報完成後，Sophie 繼續開發
```

---

**制定者**: HQ (Hera)  
**核心理念**: 你是誰，就只說你自己的事  
**執行**: IMMEDIATE_BLOCK
