# 提案：清理 Agent 專案內過期治理文件（Ina → HQ）

**提出時間**：2026-10-01
**提出者**：Ina (Infra Master)
**類型**：PROPOSAL（治理文件維護，非程式碼）
**優先級**：Normal
**關聯**：無工單，Ina 主動發現

---

## 一、背景

Ina 於執行 `TASK_20261001_INA_EVALUATE_M7_SETTLEMENTS_SCHEMA` 回報流程時，發現 `PROJECT/Infra/_agent/` 內存有**多份與現行派工協議衝突的過期文件**，恐誤導後續 Agent 或未來的 Ina 實例走錯流程（例如去等 Redis、去找 `.taskbox/*.json`）。

現行唯一權威標準為：
`brains/knowledge/01_agent_governance/SIMPLE_FILE_DISPATCH_PROTOCOL.md`（**v4.0.0**，2026-08-22，Active / Authoritative）

---

## 二、Ina 已自行處理（屬 Ina 專案內文件，低風險）

| 檔案 | 處置 | 說明 |
|:---|:---|:---|
| `PROJECT/Infra/_agent/HQ_COMMUNICATION_SOP.md` | ✅ **已加註 DEPRECATED 標頭** | 原為 v3.0（2026-08-08），描述 Redis 派工 / `.taskbox/*.json` / launchctl；已於檔案頂部加註廢棄警示並指向 v4.0.0 權威標準。**未刪除，保留歷史可追溯。** |

---

## 三、提請 HQ 裁示（非 Ina 職權，需 HQ 決定）

以下文件亦已過期，但涉及跨 Agent 治理與角色定義，**依協議須由 HQ 處置**：

| 檔案 | 問題 | 建議 |
|:---|:---|:---|
| `PROJECT/Infra/_agent/DISPATCH_BOARD.md` | 停在 2026-05-28；引用舊 `send_agent_reply.sh`；內容與現行 `.taskflow` 機制不符 | 更新為現行格式，或加註廢棄 |
| `PROJECT/Infra/_agent/IDENTITY.md` | 目標停留在 machines 表對齊（2026-05~08），且該表已於 2026-09 廢除 | 更新為現行目標 |
| `PROJECT/Infra/_agent/status.md` | `current_task: TASK_20260518_008`、`last_heartbeat: 2026-05-18` | 更新或廢棄 |

> 註：`DELIVERY_MANIFEST.md`、`CURRENT_PORT_USAGE_TABLE.md` 內的 Redis 指的是 **6379 快取服務**（確實存在），**非派工機制**，不需處理。

---

## 四、請求事項

1. 是否同意 Ina 已對 `HQ_COMMUNICATION_SOP.md` 加註 DEPRECATED 的處置？
2. 上表 3 份文件是否由 HQ 統一更新，或授權 Ina 就地更新？

---

## 五、其他建議（供 HQ 參考）

`_agent/REPORT_*.md` 有 7 份為 2026-08 的歷史報告，長期堆積於 `_agent/` 根目錄。建議 HQ 評估是否一併歸檔至 `_agent/archive/`。

---

**Ina 聲明**：本提案僅涉及文件維護，未觸碰任何程式碼、DB 或生產環境。除已在 Ina 專案內的 SOP 加註廢棄標頭外，其餘等待 HQ 裁示。

---
**提案者**：Ina (Infra Master)
**提案時間**：2026-10-01

