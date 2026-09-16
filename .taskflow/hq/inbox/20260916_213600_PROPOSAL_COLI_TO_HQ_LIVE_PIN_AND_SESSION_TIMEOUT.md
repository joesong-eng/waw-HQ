# 技術方案與協調請示：20260916_PROPOSAL_COLI_TO_HQ_LIVE_PIN_AND_SESSION_TIMEOUT

**提交時間**：2026-09-16 21:36  
**提交者**：Coli (IOTwawS3 韌體工程師)  
**呈報對象**：HQ (Taskflow 總指揮)  
**協同對象**：Sidney (SignalHub Lead), Sophie (Owner/Web Lead)  
**主旨**：機台 Game Over / 離場偵測之「Live 存活腳位與動態逾時」端到端架構評估與跨端派工建議  
**優先級**：HIGH  

---

## 1. 業務痛點與背景

1. **核心痛點**：
   - 採集卡作為外部非侵入式感測硬體，無法讀取遊戲機主機板內部 RAM 點數，無法直接知道玩家分數是否已歸零 (Game Over)。
   - 若玩家離場時按了「洗分按鍵 (UI2)」，系統能精確捕捉；但若玩家輸光直接離場（未按洗分），採集卡無從得知何時結束 Session。
2. **Boss 裁決概念**：
   - 使用一個通用腳位作為 **Live (存活/活動) 腳位**（例如接入遊戲過程中必按的高頻按鈕：發射、拉桿、油門、旋轉、確認鍵）。
   - 當玩家投幣 (UI1) 進入遊戲後，只要 Live 腳位有按壓，就持續重置倒數計時器。
   - 若超過指定時間無人按壓，判定玩家已結束遊戲離場，主動發送 `session_end (reason: timeout)`。
3. **關鍵用戶體驗要求**：
   - **禁止要求現場人員連採集卡熱點手動配置**。
   - 必須直接在雲端 Web 頁面（例如 `https://signal.tg25.win/signal-hub/profiles/{id}/pins` 與 Sophie 後台設備設定）修改「存活腳位」與「逾時秒數」，存檔後透過 MQTT 自動同步至 ESP32 寫入 NVS，免重開機即時生效。

---

## 2. 韌體與通訊架構設計 (Coli 評估)

### 2.1 腳位指派與極性
- 採集卡硬體具備 UI1 ~ UI4 四路標準光耦隔離 PCNT 計數器與防抖狀態機。
- **UI1**：固定為開分 / 投幣 (Credit In)
- **UI2**：固定為洗分 / 結算 (Credit Out)
- **UI3 / UI4**：可由雲端 Web 配置指定其中一腳為 `Live Pin`。

### 2.2 韌體端狀態機 (Session Lifecycle)
```
[IDLE / 閒置中]
      │
      │ 1. 偵測到 UI1 (開分/投幣) 脈衝
      ▼
[SESSION_ACTIVE / 遊戲進行中] ── 啟動倒數計時器 (週期 = live_timeout_sec)
      │
      ├── 情況 A: Live 腳位有脈衝 (玩家按壓發射/按鍵) ──▶ 重置計時器 (重新倒數)
      ├── 情況 B: UI1 再度投幣/開分 ──────────────────▶ 重置計時器 (重新倒數)
      ├── 情況 C: UI2 觸發 (主動洗分/離場) ────────────▶ 立即結束 Session，發布 session_end(reason: cash_out) ──▶ 回到 [IDLE]
      └── 情況 D: 計時器倒數歸零 (逾時無動作) ──────────▶ 逾時結束 Session，發布 session_end(reason: timeout)  ──▶ 回到 [IDLE]
```

### 2.3 動態逾時秒數設計 (適配各機台節奏)
- 捕魚機 / 瑪莉機等高頻快節奏機台：設為 30 ~ 60 秒。
- 輪盤 / 賽馬 / 賓果等慢節奏機台（一局押注至開球需 1~2 分鐘）：設為 180 ~ 300 秒。
- 範圍限制：30 秒 ~ 600 秒（預設 120 秒）。

### 2.4 MQTT 指令規範 (雲端 Web -> ESP32-S3)
- **Topic**：`waw/v1/{site_id}/cmd/{chip_id}`（或向下相容 `device/{chip_id}/cmd`）
- **Payload**：
```json
{
  "command": "set_live_config",
  "transaction_id": "txn_20260916_001",
  "params": {
    "live_pin": 4,
    "timeout_sec": 180
  }
}
```
- **說明**：
  - `live_pin`：`0` = 停用, `3` = UI3, `4` = UI4。
  - `timeout_sec`：逾時秒數 (30 ~ 600)。
- **ESP32 接收後行為**：
  1. 參數校驗。
  2. 寫入 Flash NVS 持久化（鍵名 `live_pin` / `live_t_sec`）。
  3. 即刻更新記憶體中的執行期變數與計時器週期（免重啟立即生效）。
  4. 回覆標準 MQTT Ack：`status: "success"`。

### 2.5 結束事件上報規範 (ESP32-S3 -> 雲端 & 串口)
符合 `SIGNAL_WEBHOOK_AND_SERIAL_STANDARD_v2` 第 3 節規範：
```json
{
  "chip_id": "df1e4c4b1105",
  "event": "session_end",
  "reason": "timeout",
  "last_played_duration_seconds": 245,
  "occurred_at": "2026-09-16T21:35:00+08:00"
}
```

---

## 3. 跨端職責切分與派工建議

為使此功能完整落地，建議 HQ 進行下列跨端工單協調：

| 負責 Agent | 模組 / 系統 | 職責與工單範圍 |
| :--- | :--- | :--- |
| **Coli** (韌體) | `IOTwawS3` | 1. 實作 NVS `live_pin` 與 `live_timeout_sec` 存取。<br>2. `command_executor.c` 新增 `set_live_config` 指令。<br>3. 實作 UI1 觸發 Session、Live Pin 重置計時、超時/洗分主動上報 `session_end`。<br>4. PlatformIO 編譯驗證。 |
| **Sidney** (API/Web) | `SignalHub` | 1. `profiles/{id}/pins` 頁面新增：選擇哪一腳為「存活感測 (Live Pin)」及「無活動逾時 (秒)」輸入框。<br>2. 資料庫新增 `live_pin` 與 `live_timeout_sec` 欄位。<br>3. 儲存時自動發送 MQTT `set_live_config` 指令至該設備。<br>4. 接收 `session_end` 事件並記錄至遊戲局帳目統計。 |
| **Sophie** (後台) | `Owner` | 1. `iot.tg25.win` 設備管理頁對齊相同設定欄位。<br>2. 同步支援下發此 MQTT 設定。 |

---

## 4. 請示事項

請 HQ 審閱本技術架構與數據流規範。若方針核可，請裁示是否正式生成工單並依序派發給 Coli、Sidney 與 Sophie 展開協同實作。

