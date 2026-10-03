# 路徑遷移報告 - _agent/inbox → .taskbox/inbox

**執行時間**: 2026-08-16 19:53
**執行者**: Coli (IOT 固件 Agent)

## 📋 遷移摘要

已完成 `_agent/inbox/` 到 `.taskbox/inbox/` 的全面遷移，確保無舊路徑殘留。

## ✅ 已完成項目

### 1. 目錄結構建立
- ✅ 建立 `.taskbox/inbox/` 目錄
- ✅ 建立 `.gitkeep` 佔位檔

### 2. 專案內腳本更新 (IOTwawS3)
- ✅ `scripts/agent_redis_listener.py` - inbox_dir 路徑更新為 `.taskbox/inbox`
- ✅ `scripts/agent_redis_listener.py` - report_dir 路徑更新為 `.taskbox`
- ✅ `_agent/TASK_NOTIFICATION_20260816.md` - inbox 路徑參考更新
- ✅ `_agent/TASK_NOTIFICATION_20260816.md` - 回報腳本範例更新
- ✅ `.gitignore` - 9 個 `_agent/*` 規則更新為 `.taskbox/*`
- ✅ `.codexignore` - 9 個 `_agent/*` 規則更新為 `.taskbox/*`

### 3. WaW 根目錄核心腳本更新
已確認以下腳本均已使用新路徑：
- ✅ `core/hq_archive_inbox.sh` - 使用 `.taskbox/inbox`
- ✅ `core/hq_inbox_summary.sh` - 使用 `.taskbox/inbox`
- ✅ `core/hq_status.sh` - 使用 `.taskbox/inbox`
- ✅ `core/hq_task_flow.sh` - 使用 `.taskbox/inbox`
- ✅ `core/hq_scaffold_agent.sh` - 新 Agent 建立時使用 `.taskbox/inbox`
- ✅ `core/message_hub_v2/http_server.py` - HTTP 伺服器使用 `.taskbox/inbox`
- ✅ `core/message_hub_v2/__main__.py` - 顯示訊息使用 `.taskbox/inbox`
- ✅ `scripts/agent_report_to_hq_v2.sh` - 使用 `.taskflow` (不受影響)

### 4. 舊目錄清理
已刪除以下專案中的空 `_agent/inbox/` 目錄：
- ✅ PROJECT/Alliance/_agent/inbox/
- ✅ PROJECT/IOTkiosk_v0/_agent/inbox/
- ✅ PROJECT/IOTwawS3/_agent/inbox/
- ✅ PROJECT/Infra/_agent/inbox/
- ✅ PROJECT/Member/_agent/inbox/
- ✅ PROJECT/Owner/_agent/inbox/

### 5. 驗證結果
- ✅ 活躍檔案中無 `_agent/inbox` 參考（不含 trash/backup/archive）
- ✅ 所有 PROJECT 子專案均已建立 `.taskbox/` 目錄
- ✅ 無殘留的舊 inbox 目錄

## 📝 保留項目（刻意保留）

### Archive 與 Backup
- `_agent/archive/inbox_legacy_20260816/` - 歷史任務檔案歸檔
- `scripts/*.backup_20260816` - 備份腳本保留舊路徑參考（僅供參考）
- `trash/` 目錄內容 - 已廢棄專案不做遷移

### 文檔參考
部分文檔檔案（知識庫、README）仍包含 `_agent/inbox` 歷史說明，屬於文檔性質，不影響實際運作。

## 🔍 遷移影響範圍

### 立即生效
- Redis listener 現在監聽後寫入 `.taskbox/inbox/`
- HQ 核心腳本查詢 `.taskbox/inbox/` 收件匣
- 新建立的 Agent 專案使用 `.taskbox/inbox/`

### 需要注意
- 舊的任務通知文件已更新路徑說明
- 回報腳本範例已更新為 `.taskbox/REPORT_*`

## ✅ 遷移完成確認

```bash
# 驗證新路徑存在
ls -la .taskbox/inbox/

# 驗證舊路徑已移除
find PROJECT -type d -name "inbox" | grep -v ".taskbox"
# (應無輸出)

# 驗證腳本無舊路徑參考
grep -r "_agent/inbox" PROJECT/IOTwawS3 --include="*.py" --include="*.sh" | grep -v "archive"
# (應無輸出)
```

---

**結論**: `_agent/inbox` → `.taskbox/inbox` 遷移已全面完成，系統現已使用新路徑結構。
