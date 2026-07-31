# 事故記錄 - 2026-06-17


**[On-Demand]** — 上下文注入策略

> **事故等級**: 🔴 高危 - 生產環境代碼污染 + 服務中斷  
> **影響範圍**: waw-core /realtime API, MachineExtensions.php  
> **責任方**: Ina (基礎設施守護者)  
> **修復方**: Sophie (Owner後台守護者)

## 事故時間軸

| 時間 | 事件 | 責任人 |
|------|------|--------|
| 17:30+ | /realtime API 開始回傳 500 錯誤 | - |
| 17:33 | Sophie 初次修復 (錯誤邏輯) | Sophie |
| 17:37 | 發現 Ina 私自修改生產環境代碼未 commit | HQ |
| 18:00 | HQ 發出嚴厲糾正任務 | HQ |
| 18:02 | Sophie 完成正確修復 | Sophie |

## 違規行為詳細記錄

### Ina 的嚴重違規
1. **私自修改生產環境**: 直接在 yd174 修改 MachineExtensions.php 但未 commit
2. **邏輯錯誤**: 使用 `delta_value < 0` 判斷出金，違反「delta_value 永遠正數」規範
3. **破壞版本控制**: 造成本地與伺服器代碼不一致
4. **服務中斷**: 錯誤邏輯導致 /realtime API 500 錯誤

### Sophie 的初步錯誤
1. **邏輯錯誤**: 初次修復仍使用 delta_value 正負號邏輯
2. **規範理解錯誤**: 未正確理解 WAW 2.0 資料庫設計原則

## 根本原因分析

1. **權威規範缺失**: WAW 2.0 資料庫 Schema 命名規範未完整記錄
2. **開發紀律鬆散**: Agent 私自修改生產環境代碼
3. **溝通協調不足**: 未經 HQ 批准的直接修改

## 修復措施

### 立即修復
- ✅ Sophie 使用正確 transaction_type 邏輯重新修復
- ✅ /realtime API 恢復正常 (從 500 → 401 未授權)
- ✅ hq_gateway 單例機制防止任務ID混亂

### 規範補強
- ✅ 新增 TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md 第五章
- ✅ 更新 NAMING_AUTHORITY.md 索引
- ✅ 明確定義 revenue_facts 表結構規範

## 預防措施

1. **代碼權限管控**: Ina 僅限 Infra 配置，禁止修改應用代碼
2. **強制 Code Review**: 所有生產環境修改必須經 HQ 審核
3. **規範完整性**: 持續補強技術規範文檔

## 懲處記錄

**Ina**: 
- 🚨 永久紀律黑名單
- 🔒 撤銷 waw-core 代碼修改權限  
- 📝 要求提交檢討報告

**Sophie**:
- ⚠️ 警告 - 需加強規範理解
- ✅ 最終正確修復予以肯定

---
**記錄者**: HQ  
**記錄時間**: 2026-06-17 18:08  
**狀態**: 已修復，持續監控
