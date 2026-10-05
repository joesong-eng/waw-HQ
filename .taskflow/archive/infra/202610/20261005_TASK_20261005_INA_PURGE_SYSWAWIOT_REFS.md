# 任務：TASK_20261005_INA_PURGE_SYSWAWIOT_REFS

**派發時間**：2026-10-05
**優先級**：medium
**負責人**：Ina (Infra)
**性質**：殘留清理（Joe 指示：`sysWawIot/` 都是舊的，更新或刪除）

---

## 背景

舊專案根目錄 `/Users/ilawusong/Documents/sysWawIot/` 已遷移為 `/Users/ilawusong/Documents/WaW/`。
Joe 指示：全系統凡引用 `sysWawIot/` 的**都是舊的**，一律更新為新路徑或刪除。

HQ 已清完 `brains/knowledge/`、`standards/`、`docs/`。專案內殘留由各 Agent 清理。

**新舊路徑對照**：
| 舊 | 新 |
|----|----|
| `/Users/ilawusong/Documents/sysWawIot/tg25-infra` | `/Users/ilawusong/Documents/WaW/PROJECT/Infra` |
| `/Users/ilawusong/Documents/sysWawIot/HQ` | `/Users/ilawusong/Documents/WaW` |
| `~/Documents/sysWawIot/tg25-infra` | `~/Documents/WaW/PROJECT/Infra` |

---

## 你專案內的殘留（HQ 已定位）

```
PROJECT/Infra/test_transaction_writer.py
PROJECT/Infra/mqtt/scripts/test_syntax_only.sh
PROJECT/Infra/api/credit-relay/TASK_20260520_002_IMPLEMENTATION_REPORT.md
PROJECT/Infra/waw-iot/README.md / CHANGELOG.md / MQTT_IMPLEMENTATION_SUMMARY.md / REVENUE_PROCESSING_IMPLEMENTATION.md
PROJECT/Infra/archive/legacy_202608/docs/deployment/README.md
PROJECT/Infra/archive/legacy_202608/test_transaction_writer.py
PROJECT/Infra/mqtt/scripts/kiosk_event_listener.py
PROJECT/Infra/.vscode/sftp.json  ← HQ 已修，請確認
```

## 任務

逐一判斷並處理：
1. **仍有效的檔案**（如 `sftp.json`、仍在用的腳本）→ 路徑改為新路徑。
2. **一次性/過時腳本**（`test_*.py`、`test_*.sh`、`archive/legacy_*` 內）→ 若已無用則刪除；不確定則改路徑保留並說明。
3. **歷史報告/文件**（如 `TASK_20260520_...md`）→ 路徑更新為新路徑（保留歷史）。

## 驗收指標

1. `grep -rn 'sysWawIot' PROJECT/Infra --include='*.py' --include='*.sh' --include='*.md' --include='*.json'` → 0 hits（或逐項說明保留原因）
2. 若有刪檔，列出清單
3. commit + push（附 hash）
4. 站點存活：`curl -sI https://api.tg25.win/` → 200

## 禁止

- 不刪除仍在使用的程式邏輯檔
- 不確定用途的檔案先保留並改路徑，於回報說明

## 完成定義

殘留處理完畢，驗收有輸出，回報寫入 `.taskflow/infra/outbox/`。
