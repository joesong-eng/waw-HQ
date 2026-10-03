# 任務回報：清理 Infra 版控殘留與忽略運行時資料

**任務 ID**：TASK_20261002_INA_CLEANUP_GIT_TRACKING
**回報時間**：2026-10-02 (台北時間)
**執行者**：Ina (Infra Master)
**指揮鏈**：HQ
**狀態**：✅ 完成並通過三方驗證
**優先級**：high

---

## 一、執行摘要

| 項目 | 結果 |
|:---|:---|
| .gitignore 新增忽略規則 | ✅ 已提交 |
| counters.json 移除版控追蹤（保留實體檔） | ✅ 11 檔 untrack，實體檔全數保留 |
| .gitkeep 保留目錄結構 | ✅ 已加入版控 |
| 本地 / origin / VPS 三方同步 | ✅ 皆為 e559e52 |
| VPS 工作區乾淨度 | ✅ tracked 無修改、無 untracked |
| VPS 運行時資料保護 | ✅ 17 個 counters + 3 個 backups 實體檔完整保留 |

---

## 二、⚠️ 執行中發現的 3 個關鍵風險（已處置）

### 風險 1：VPS 有常駐模擬器程序持續寫入 counters（會阻斷 pull）
- **發現**：ps aux 顯示 /opt/hardware-simulator/simulator.py（PID 3644963）**常駐運行**，即時寫入 counters.json。
- **影響**：git pull 因「local changes would be overwritten」被**連續擋下 2 次**。
- **處置**：先將 17 個 runtime 檔**備份至 /tmp/ina_counters_backup_***，再以 git rm --cached（僅動 index、不動實體）搭配暫時移檔完成 pull，最後**還原全部實體檔**。

### 風險 2：工單未授權 untrack 的既有備份檔
- **發現**：backups/machine_transactions_20260916.sql 為**既有已追蹤檔**（工單僅要求忽略 backups/）。
- **處置**：**未動它**。gitignore 只作用於未追蹤檔，此檔仍安全保留於版控中（已驗證 exit=1 未被忽略）。

### 風險 3：首個 commit 漏加 .gitignore（已補正）
- **發現**：commit 8da4530 僅含 11 個 untrack + 1 個 .gitkeep，**漏掉 .gitignore**，導致 VPS pull 後規則未生效。
- **處置**：補 commit e559e52（.gitignore +7 行）並重新同步 VPS，規則已於 VPS 實測生效。

---

## 三、變更內容

### 1. .gitignore 新增規則

    # 模擬器運行時資料（runtime counters，不進版控；僅保留目錄結構）
    hardware/simulator/data/*.json
    !hardware/simulator/data/.gitkeep

    # 備份目錄（runtime 產物，不進版控）
    backups/

### 2. 移除追蹤（git rm --cached，實體檔保留）
- hardware/simulator/data/*_counters.json × 11 檔

### 3. 新增追蹤
- hardware/simulator/data/.gitkeep（保留空目錄結構；本地原存在但未追蹤，且被 .* 規則誤忽略）

---

## 四、驗證佐證（真實輸出）

### 4.1 忽略規則生效（本地 + VPS 一致）

    $ git check-ignore -q hardware/simulator/data/df1e4c4b1101_counters.json ; echo $?
    0        # 已忽略 ✅
    $ git check-ignore -q backups/m7_settlements_pre_drop_20261001_155533.json ; echo $?
    0        # 已忽略 ✅
    $ git check-ignore -q hardware/simulator/data/.gitkeep ; echo $?
    1        # 未被忽略（正確保留）✅

### 4.2 三方 SHA 一致

    local  HEAD : e559e52   (working tree clean)
    origin/main : e559e52
    VPS    HEAD : e559e52

### 4.3 VPS 工作區乾淨

    $ git status --porcelain --untracked-files=no
    (空)                              # 無 tracked 修改 ✅
    $ git status --porcelain | grep '^??'
    (無 untracked)                    # 無未追蹤檔 ✅

### 4.4 VPS 運行時資料保護

    counters 實體檔 : 17 個 ✅
    .gitkeep       : 1 個  ✅
    backups/ 實體檔 : 3 個（含 m7 重建前備份）✅
    data/ 追蹤檔    : hardware/simulator/data/.gitkeep （僅此 1 個）✅

---

## 五、Commit 紀錄

| Commit | 內容 |
|:---|:---|
| 8da4530 | chore(infra): untrack simulator counters, ignore runtime data/backups（11 untrack + .gitkeep）|
| e559e52 | chore(infra): add gitignore rules for simulator runtime data and backups/（.gitignore +7）|

均已 push 至 origin/main，VPS 已 pull 同步。

---

## 六、遺留提醒（非本工單範圍）

1. **VPS 常駐模擬器**（/opt/hardware-simulator/simulator.py，PID 3644963）持續寫 counters.json。本次已用 gitignore 妥善隔離，之後 VPS 不再因 runtime 資料顯示 dirty。
2. **VPS 上 3 個備份實體檔**（含 m7_settlements_pre_drop_20261001_155533.json）目前僅存在 VPS、不進版控。建議保留或另存，避免被 git clean -fdx 掃掉。
3. 本次為**唯讀 + 版控整理**，未執行任何 DB 變更。

---

**Ina 聲明**：本工單全程於 VPS 實機執行，關鍵步驟（pull 被擋、runtime 寫入）均有真實指令輸出佐證；所有 runtime 實體檔已備份後還原，無資料遺失。

---
**回報者**：Ina (Infra Master)
