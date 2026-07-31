# WAW 2.0 核心待辦任務總結

## 一、架構設計已完成

✅ `WAW_2.0_ARCHITECTURE_SPEC.md` - 資料表設計
✅ `V9_SYSTEM_SPLITTING_DESIGN.md` - 系統拆分設計

## 二、Kiosk Exchange v2 實作狀態

### 已完成：43 個任務
### 待辦：39 個任務

## 三、關鍵待辦任務

### Member 專案 (Mina) - 進行中
- 3.1 驗證 LINE SSO 認證流程
- 3.3 更新 token 有效期為 300 秒
- 3.4 建立 heartbeat endpoint
- 5.1 更新 bind API 呼叫 Infra
- 5.2 實作多機台無縫切換
- 6.1-6.3 建立 escrow 相關 endpoints
- 7.1 實作 stacked endpoint 含冪等性

### 待驗證任務
- 17.3 驗證韌體 Hold 機制
- 多個測試檢查點

### 測試任務 (可選)
- 大量單元測試和整合測試

## 四、WAW 2.0 架構核心資料表

### 需要建立的表：
1. `stores` (場地/店面表)
2. `machines` (機器資產表)
3. `machine_deployments` (機台部署歷史表)
4. `profit_sharing_agreements` (分潤協議表)
5. `machine_transactions` (交易流水表)

### 職責分配：
- Ina (Infra)：負責 DB 變更
- Sophie (Owner)：負責管理後台 API
- Mina (Member)：負責玩家端 API

---

**問題：這次要修改/實作哪個部分？**
