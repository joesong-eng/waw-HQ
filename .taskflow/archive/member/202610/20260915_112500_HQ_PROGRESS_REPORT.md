# HQ 工單執行進度匯報

**匯報時間**：2026-09-15 11:25
**匯報人**：Mina (Member)
**工單總數**：12 張（9 項獨立任務）

---

## 已完成任務（5/9）

| # | 工單 | 優先級 | Commit | 狀態 |
|:---|:---|:---|:---|:---|
| ① | VENUE_AUTH_FIX | 🔴 high | `f88e724` | ✅ 完成 |
| ② | DEPRECATE_OLD_MACHINE_API | 🔴 high | `f0ac20b` | ✅ 完成 |
| ③ | P2_QUICKFIX_BATCH | 🟡 normal | `bd822d0` | ✅ 完成 |
| ④ | SERVICES_PHP_CLEANUP | 🟡 normal | `145c6b0` | ✅ 完成 |
| ⑤ | CLEANUP_ROOT_JUNK | 🟢 low | (無 git 變更) | ✅ 完成 |
| ⑦ | VUE_CDN_TO_VITE + P1_WELCOME_VUE_CDN | 🟡 normal | `02022ca`+`05c4357`+`df5a30e` | ✅ 完成 |

## 待執行任務（3/9）

| # | 工單 | 優先級 | 預估工時 | 說明 |
|:---|:---|:---|:---|:---|
| ⑧ | SPLIT_WELCOME_BLADE + P2P2_WELCOME_REFACTOR | 🟡 normal | 1.5h | 依賴 ⑦ 已完成，可開始 |
| ⑥ | TEST_COVERAGE_BOOTSTRAP + BOOTSTRAP_TESTING | 🟡 normal | 2-4h | 合併執行 |
| ⑨ | P2P3_REMAINING_BATCH | 🟡 normal | 2h | getColumnListing + PERF log + BillController 評估 |

## 已知問題
1. **SSL CA cert error**：P0-5 設 `verify => true` 但 VPS 缺少 CA bundle → `cURL error 60`。需另開任務修復 VPS CA bundle。
2. **Header injection 500**：`auth:sanctum` redirect 回應觸發 `Header may not contain more than a single header` 錯誤。根因疑似 session/response header 含換行符。影響所有未認證 redirect 回應。

## 下一步
Mina 將繼續執行 ⑧ SPLIT_WELCOME_BLADE（Vue 已打包，可安全拆分）。

---
**匯報人**：Mina
**匯報時間**：2026-09-15 11:25
