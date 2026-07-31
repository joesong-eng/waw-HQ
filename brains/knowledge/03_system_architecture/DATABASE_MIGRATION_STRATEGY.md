# WAW 2.0 數據過渡與雙寫策略

- **狀態**: 已實施 (2026-06-12)
- **實施者**: Ina (Infra) & Sophie (Owner)

## 1. 雙表同步機制 (Dual-Write)
為了確保從 `devices` (舊) 遷移到 `machines` (新) 的過程中業務不中斷，目前採用 MQTT Listener 雙寫模式：

- **監聽端**: `tg25-infra/mqtt/scripts/listener.py`
- **行為**: 當收到 `device/+/status` 消息時，同時執行：
  1. `UPDATE devices SET last_seen_at = NOW() WHERE chip_id = ...`
  2. `UPDATE machines SET last_seen_at = NOW() WHERE chip_id = ...`

## 2. 狀態保護原則 (Status Protection)
根據「坑 #17」規範，硬體連線狀態（Online/Offline）**嚴禁**覆蓋業務狀態（Active/Maintenance）：
- **規則**: 僅更新 `last_seen_at` 欄位，不得在 MQTT 監聽器中修改 `status` 欄位。
- **維護者**: `status` 欄位僅由 `waw-business` (Sophie) 進行人工或商務邏輯變更。

## 3. 專案領地劃分
- **waw-iot**: 負責硬體數據的「採集」與「初級快取」(Redis)。
- **waw-business**: 負責數據的「呈現」與「商務處理」。

