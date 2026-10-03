# Ina 回報：模擬設備 chip_id 更新評估報告

發報人：Ina (Infra Master)
發報時間：2026-09-30 11:05 CST
接收方：HQ
優先級：P2（計劃性維護）
狀態：待 HQ 核准與決策後執行

---

## 任務背景

hardware/simulator 7 台模擬設備的 device_uuid 為舊隨機字串格式，
用戶要求改為符合真實硬體規範的 MAC address 格式（小寫無冒號，12 位十六進位）。

---

## 新舊 ID 對照表

舊 chip_id              | 新 chip_id     | 設備名稱
------------------------|----------------|---------------------------
sr9adyxpdyt1tuf7        | a4c3f21b0e91   | 娃娃機 #1
chpw9fz16m6n391l        | b8d72e4a1f05   | 娃娃機 #2
w1ey33c1ta5sxtsr        | c1e84d3b2a67   | 娃娃機 #3
49tmby4z703wxqmp        | d5f96c4e3b18   | 娃娃機 #4
u19iy1yp17sm7o7h        | e2a07b5c4d29   | 博弈機台 #1
hxnz44vshjju0cjz        | f3b18c6d5e30   | 街機遊戲 #1
i767e3ieju7wncy2        | a6c29d7e4f41   | 娃娃機 #5（西門旗艦店，手動模式）

※ 金財神 #1~#5（df1e4c4b1101~1105）已是 MAC 格式，不在本次範圍。

---

## 影響範圍評估

### DB（iotv9 @ infra）

表                              | 台數 | 資料量        | 備註
--------------------------------|------|---------------|-------------------------------
devices                         | 5    | 5 rows        | chip_id 主識別欄；娃娃機#2、#3 不在 DB
device_snapshots                | 7    | ~9,380 rows   | 模擬器快照
revenue_facts                   | 6    | ~660,000 rows | 歷史流水，待 HQ 決策
revenue_facts_archive_20260804  | 6    | ~1,600,000    | 歸檔流水，待 HQ 決策

signal_events、device_data 無舊 ID，不受影響。

### 本機 Code（需 commit → push → deploy）

檔案                                              | 性質     | 說明
--------------------------------------------------|----------|------------------------
Infra/hardware/simulator/config/devices.json      | 執行配置 | 必改
Infra/mqtt/scripts/generate_mock_snapshots.py     | 測試腳本 | 5 個舊 ID 需更新
Owner/database/seeders/DeviceSeeder.php           | Seeder   | 5 個舊 ID，重跑會插舊 ID
Owner/app/...BroadcastController.php (x2)         | docblock | 僅注釋，不影響執行
Owner/app/Events/DeviceUpdated.php                | docblock | 僅注釋，不影響執行
Member/storage/framework/views/...php             | Blade 快取 | view:clear 後自動消失

---

## 待 HQ 決策

Q1：revenue_facts / revenue_facts_archive_20260804 歷史流水的舊 ID 是否一起更新？

選項 A（更新）：DB 完全統一，歷史圖表不再出現舊 ID（屬模擬資料，無財務意義）
選項 B（保留）：舊 ID 留在歷史表，新 ID 從更新後開始計算（歷史不斷裂）

---

## 預計執行步驟（HQ 核准後 Ina 執行）

1. 本機更新 devices.json、generate_mock_snapshots.py、DeviceSeeder.php
2. Git commit → push
3. waw_ops.sh deploy infra → 重啟 hardware-simulator service
4. DB UPDATE：devices.chip_id（5 rows）
5. DB UPDATE：device_snapshots.chip_id（~9,380 rows）
6. DB UPDATE：revenue_facts + archive（視 Q1 決策）
7. 驗證並回報完成

---

Ina / Infra Master
等待 HQ 核准與 Q1 決策後立即執行。
