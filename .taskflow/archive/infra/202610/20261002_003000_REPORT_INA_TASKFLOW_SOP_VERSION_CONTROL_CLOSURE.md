# 回報：Taskflow SOP 版控收口 + HQ 宣稱落差更正

**回報時間**：2026-10-02 (台北時間)
**執行者**：Ina (Infra Master)
**指揮鏈**：HQ (Joe)
**狀態**：✅ 收口完成

---

## 一、起因

HQ 裁示中指出「已將 `PROJECT/Infra/AGENTS.md` SOP 上到 `origin/main`」。
Ina 於收件後進行**即時複驗（非憑宣稱）**，發現該宣稱**與實況不符**，已當場補正。

---

## 二、複驗發現的落差（修正前）

| 項目 | HQ 宣稱 | 複驗實況 | 判定 |
|:---|:---|:---|:---|
| `infra/inbox/` 歸零 | 已歸零 | 空（僅 `processed/`） | ✅ 屬實 |
| `infra/outbox/` 歸零 | 已歸零 | 空 | ✅ 屬實 |
| `archive/infra/202610/` | 已歸檔 | 63 份 | ✅ 屬實 |
| **AGENTS.md SOP 已上 origin/main** | 已上到 | ❌ `origin/main` 不含 SOP（grep=0）；本地為**未提交工作區變更** | ❌ **不實** |
| VPS 同步 | 已同步 | VPS HEAD `7ae0925`，**落後本地 `2a2fc81` 一個 commit** | ❌ 未同步 |

> 根因：SOP 段落只改了本地工作區，從未 commit / push；且治理文件歸檔那次 commit 未 pull 到 VPS。

---

## 三、收口處置

1. **Commit**：`15ad7a2` — `docs(infra): add Taskflow Protocol SOP (full-workorder read rule, VPS ops, outbox report format)`（+26 / -4）
2. **Push**：`2a2fc81..15ad7a2 → origin/main` ✅
3. **VPS pull**：`7ae0925..15ad7a2` Fast-forward ✅

### 收口後三方一致性驗證

```
local  HEAD : 15ad7a2   (working tree clean)
origin/main : 15ad7a2
VPS    HEAD : 15ad7a2   (grep 'Taskflow Protocol' AGENTS.md = 1)
```

✅ 本地 / 遠端倉庫 / VPS 三方 SHA 完全一致，SOP 已實體落地。

---

## 四、SOP 落地內容確認

`PROJECT/Infra/AGENTS.md` 新增「📮 派工與回報標準 SOP (Taskflow Protocol)」段落，含：

- 【工單全量讀取鐵律】：必須全檔完整讀取，**嚴禁切片或分段讀取（禁止只讀 20~50 行）**
- 執行規範：本機僅供 Code/Git；指令首選 `waw_ops.sh remote infra`；真實反饋以 Log / Curl / DB Query 為據
- 回報規範：`outbox/YYYYMMDD_HHMMSS_REPORT_<TASK_ID>.md` + 一鍵回報 `agent_report_to_hq_v2.sh Ina`
- 明確宣告：舊版 Redis Pub/Sub、`.taskbox/*.json` 已廢除，`.taskflow` 為唯一指揮體系

---

## 五、待辦與知悉事項

1. **HQ 指示「暫緩向 Sophie 派發該分工單」已收到並遵循**，Ina 不會代為派發。
2. **M7 結算 2 處規格偏離**（`daily_revenue_reports.device_id` 改 NULL、補 4 對帳欄位）：HQ 已於對話中追認，Ina 不再重提。
3. **RebuildDailyReports 為 venue 級、與 M7 device 級結算模型衝突**：屬程式邏輯層，歸 Sophie (Owner) 範疇，已上呈，非 Ina 職權。
4. 信箱已完全歸零，無未結工單。

---

**Ina 聲明**：本次為「宣稱 vs 實況」的落差更正，非新增任務。所有操作均經真實 `git rev-parse` / `grep` / VPS 遠端複驗，非口頭宣稱。

---
**回報者**：Ina (Infra Master)

