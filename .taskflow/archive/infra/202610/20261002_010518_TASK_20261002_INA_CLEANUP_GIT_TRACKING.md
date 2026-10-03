# 任務：清理 Infra 版控殘留與忽略運行時資料 (TASK_20261002_INA_CLEANUP_GIT_TRACKING)

**派發時間**：2026-10-02
**負責人**：Ina (Infra Master)
**優先級**：high
**背景**：
VPS 工作區出現：
- 11 個 modified: hardware/simulator/data/*_counters.json (模擬器運行狀態誤入版控)
- 8 個 untracked: 6 個新 counters.json + 2 個 backups 檔案

---

## 🎯 執行目標與規範

### 1. 更新 PROJECT/Infra/.gitignore
在 `.gitignore` 中增加忽略規則：
- 忽略模擬器運行數據：`hardware/simulator/data/*.json`（但保留 `!hardware/simulator/data/.gitkeep`）
- 忽略備份目錄：`backups/`

### 2. 移除 counters.json 版控追蹤（保留本機與 VPS 實體檔案）
- 執行 `git rm --cached hardware/simulator/data/*_counters.json`
- 確認目錄下保留 `.gitkeep`
- Commit: `chore(infra): untrack simulator counters and ignore runtime data/backups`
- Push 至 `origin/main`

### 3. VPS 同步與工作區驗證
- 在 VPS (/home/ubuntu/tg25-infra) 執行 `git pull origin main`
- 檢查 VPS 上實體檔案是否完好（模擬器運行資料與備份不可遺失）
- 驗證 VPS 上 `git status` 是否完全 clean

---

## 📝 驗收指標 (嚴禁口頭宣稱)
1. 提供本地 commit SHA 與 `git status` clean 證據
2. 提供 VPS 執行 `git pull` 輸出
3. 提供 VPS `git status` 乾淨 (working tree clean) 截圖/日誌輸出
4. 依標準產出回報至 `.taskflow/infra/outbox/`

