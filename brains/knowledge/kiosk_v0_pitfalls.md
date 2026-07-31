# 🚨 IOTkiosk 防坑手冊 (PITFALLS)

> 這份文件記錄了所有曾經踩過的坑。每一條都是真實代價換來的教訓。
> **新功能上線前、Debug 開始前，必讀此文件。**

---

## 坑 #1：MQTT Keepalive 與心跳間隔對不上 → 斷線盲區

**發生日期**：2026-05-04
**症狀**：Serial Log 明確顯示 `MQTT: 📤 Kiosk Event` 有執行，但 Broker 永遠收不到。
**根本原因**：
```
mqtt_service.c: keepalive = 30 秒
config.h:       BA_STATUS_INTERVAL_MS = 60000 (60 秒)
```
心跳 60 秒才發一次，但 Broker 30 秒沒收到封包就踢掉連線。機台在斷線盲區投幣，封包直接丟失。
**修復**：`BA_STATUS_INTERVAL_MS` 改為 `25000`（必須 < Keepalive）。

---

## 坑 #2：憑證 CN 與 Chip ID 不一致 → Broker Log 搜尋失靈

**發生日期**：2026-05-04
**症狀**：HQ 在 Broker Log 搜尋 `e072a1f73a78` 的記錄完全找不到。
**根本原因**：憑證 **CN (Common Name)** 為 `local-joesong`，Mosquitto 以此作為識別。
**正確做法**：在 Broker Log 中搜尋 `local-joesong`，而不是 chip_id。

---

## 坑 #3：本地 Python 腳本的憑證 ACL 限制 → 指令無效

**發生日期**：2026-05-04
**症狀**：用本地 Python 腳本發 `enable` 指令，機台無反應。
**根本原因**：`local-joesong` 憑證在 Broker ACL 中通常沒有 `kiosk/+/cmd` 的寫入權限。
**正確做法**：測試指令必須走 **Internal API** (`api.tg25.win/api/internal/mqtt/publish`)。

---

## 坑 #4：紙鈔機預設 DISABLED，測試前忘記先 Enable

**發生日期**：2026-05-04
**症狀**：投幣後直接吐鈔，無 `escrow` 事件。
**根本原因**：韌體 Fail-Safe 模式下開機預設為 `BA_STATE_DISABLED`。
`ba_state`: `IDLE`, `ESCROW`, `STACKING`, `REJECTING`, `DISABLED`, `FAULT`
**修復**：測試前必須確認收到 `BA Online (0x3E)` 訊號。

---

## 坑 #5：Serial Monitor 佔用 COM Port → 無法刷機

**操作規則**：刷機 (Upload) 前必須先按 `Ctrl + C` 關掉 Monitor，兩者互斥。

---

## 坑 #6：OTA 指令發出過早 → 下載 404

**根本原因**：GitHub Actions 編譯與上傳需要 3~5 分鐘。若 .bin 尚未上傳完成就發指令，機台會下載失敗。
**正確流程**：先確認 `https://hware.tg25.win/.../vX.Y.Z.bin` 返回 HTTP 200 後再發指令。

---

## 坑 #7：OTA 完成後不自動重啟

**設計說明**：為了安全，下載成功後會廣播 `pending_reboot: true`，需人工下發 `reboot` 指令才生效。

---

## 坑 #8：紙鈔機初始化狀態卡死

**發生日期**：2026-05-03 (v1.5.3 修復)
**原因**：部分紙鈔機在 POWER_UP 階段會噴 `0x3E`，舊版韌體未處理導致卡死。

---

## 坑 #9：使用了過時的主題前綴 (v9/ 或 waw/)

**發生日期**：2026-05-09
**症狀**：後台訂閱不到資料，或裝置收不到指令。
**根本原因**：舊版規格文件誤導使用 `v9/kiosk/...` 或 `waw/kiosk/...`。
**修復**：根據 **V9 體系標準**，已全面移除前綴。
**正確主題**：`kiosk/{id}/event`, `kiosk/{id}/cmd`, `kiosk/{id}/status`。

---

## 坑 #10：JSON 結構不一致 (Nested vs Flat)

**發生日期**：2026-05-09
**症狀**：後台解析 JSON 報錯（Field not found）。
**根本原因**：誤以為事件採 `{"type":"event","data":{...}}` 結構。
**實作事實**：韌體採用 **扁平化 JSON**：`{"event":"escrow","amount":100,...}`。

---

## 🛠️ 快速 Debug Checklist

- [ ] **1. 機台在線？** → `device/{chip_id}/status` 應為 `online`
- [ ] **2. 排除舊主題？** → 檢查是否還在用 `v9/` 或 `waw/` 前綴
- [ ] **3. JSON 格式？** → 確認後台採用扁平化 (Flat) 解析邏輯
- [ ] **4. 紙鈔機已 Enable？** → 確認 Serial Log 有 `BA Online` (`0x3E`)
- [ ] **5. 心跳間隔？** → 確認 `BA_STATUS_INTERVAL_MS` < Keepalive (30s)
- [ ] **6. 搜尋 Broker Log？** → 關鍵字使用 `local-joesong` (憑證 CN)

---
*最後更新：2026-05-09 | 維護人：Fio (Firmware Specialist)*
