# 回報：signal-hub/guide 補強（Webhook payload / 架構邊界 / Owner-SignalHub 分工表）

**回報者**：Sidney（SignalHub）
**日期**：2026-09-21
**狀態**：✅ 完成並上線

---

## 一、任務內容

補強公開頁面 `https://signal.tg25.win/signal-hub/guide`，新增四項內容：
1. Webhook payload：`points_per_pulse` / `amount` 語意
2. 電腦型：採集卡透明中繼，分數由遊戲商雲端決定
3. 傳統機板型：不走 SignalHub
4. Owner / SignalHub 分工表

---

## 二、實作變更（單檔）

`resources/views/signal-hub/guide.blade.php`（v2.2.0 → v2.3.0）

| # | 章節 | 變更 |
|---|------|------|
| 1 | 第一章 | 新增【架構邊界】雙卡：電腦型 (PC-Based) 適用 / 傳統機板型 (MCU/ROM Board) **不走 SignalHub** |
| 2 | 第一章 | 新增【現場兩類信號通道】：通道 A 服務員開洗分按鍵 (Event Trigger)、通道 B 實體入出幣計數表 (Counter Pulse) |
| 3 | 5.1 欄位說明 | `points_per_pulse` 標註為「機台後台參數、營運端設定值，非採集卡硬體換算」；`amount` 標註為「參考請求點數，最終以遊戲商回傳 `actual_points` 為準」 |
| 4 | 第七章（新增） | Owner / SignalHub 分工表（核心定位、帳號權限、機台場地、分潤計價、硬體設定、資料所有權）＋ 界線提醒 |
| 5 | 頁首/頁尾 | 版本 v2.3.0、發布日期 2026-09-21、認證代號 SPEC-20260921-V23 |

---

## 三、部署與驗證

**Git**：`955d00b docs(guide): v2.3 — webhook payload semantics, PC-based vs board boundary, Owner/SignalHub split`（已 push origin/main）

**部署**：`../../dev_tools/waw_ops.sh deploy sidney` → ✅ 完成（git pull Fast-forward、view:clear、config:cache）

**HTTP 驗證**：`GET https://signal.tg25.win/signal-hub/guide` → **HTTP 200**（48,419 bytes）

**瀏覽器目視驗證**（Codex In-app Browser）：
- 標題顯示「開洗分 API 介面規格書 (v2.3)」、版本 v2.3.0、日期 2026-09-21
- 第一章雙卡與兩類通道正常渲染
- 5.1 payload 的 `points_per_pulse` / `amount` 新語意正常
- 第七章分工表 6 列 + 界線提醒正常渲染
- 頁尾 SPEC-20260921-V23 正確

---

## 四、備註

- 本機未執行任何破壞性指令；僅編輯 → commit → push → 遠端標準部署。
- 舊有未追蹤檔（`profiles.blade.php.new_template` 等）非本單範圍，未納入本次 commit。
