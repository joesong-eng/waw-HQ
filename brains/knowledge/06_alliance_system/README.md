# Alliance 系統知識專區


**[On-Demand]** — 上下文注入策略

> **建立日期**：2026-06-18  
> **維護角色**：HQ (協調者)  
> **專區目的**：記錄 Alliance 系統修復案例，建立維護最佳實踐

---

## 📁 文件結構

| 文件名稱 | 說明 | 狀態 |
|---------|------|------|
| `ALLIANCE_SYSTEM_ARCHITECTURE.md` | Alliance 系統架構總覽 | ✅ |
| `SEVEN_CRITICAL_FIXES.md` | 七個主要問題的解決方案 | ✅ |
| `QUICK_DIAGNOSIS_SOP.md` | 快速診斷與修復標準作業程序 | ✅ |
| `MAINTENANCE_BEST_PRACTICES.md` | 系統維護最佳實踐 | ✅ |
| `TROUBLESHOOTING_GUIDE.md` | 故障排除指南 | ✅ |

---

## 🎯 Alliance 系統概述

Alliance 系統是 wawIoT 遊藝場管理系統中負責**供應商代理商**管理的核心模組，由 **Allie Agent** 負責維護。

### 核心功能
- 供應商代理商後台管理
- 分潤查詢與計算
- 專案拆分評估 (R20/R21)
- 資料庫 schema 管理

### 技術架構
- **資料庫**：獨立 Alliance 資料庫
- **API 端點**：RESTful API 架構
- **認證機制**：Key-based 認證
- **部署環境**：VPS 141.148.165.50

---

## ⚠️ 重要警告

1. **資料庫隔離**：Alliance 系統使用獨立資料庫，與 waw2.0 系統嚴格隔離
2. **認證金鑰**：所有 API 呼叫需要正確的 `X-Internal-Key`
3. **修復順序**：必須按照 SOP 順序執行，避免連鎖故障

---

## 🔗 文件神經連結

- 關聯到：`01_agent_governance/AGENT_RESPONSIBILITY_BOUNDARIES.md`
- 關聯到：`02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md`
- 關聯到：`04_deployment_operations/INFRASTRUCTURE_REFERENCE.md`
