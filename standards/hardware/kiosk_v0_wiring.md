# IOTkiosk_v0 硬體接線記錄

**主控板：** Dav-Master-ESP32-S3 Rev V1.0  
**更新日期：** 2026-05-09  
**狀態：** 已對齊 v1.5.4 韌體實作

---

## GPIO 腳位總表 (ESP32-S3)

### 輸入（光耦 UI1~UI4，採反邏輯：有信號時 GPIO 讀 0）

| GPIO | 功能 | 元件 | 說明 |
|------|------|------|------|
| **IO1** | PIN_IN1 / PIN_CREDIT_IN | UI1 | 入金計數 (脈衝信號) |
| **IO2** | PIN_IN2 / PIN_CREDIT_OUT | UI2 | 出金計數 (脈衝信號) |
| **IO13** | PIN_IN3 / PIN_FAULT | UI3 | 擺錘警報 / 系統故障監測 |
| **IO14** | PIN_IN4 | UI4 | 預留輸入 |

### 輸出（光耦 UO1~UO4，採正邏輯：GPIO 拉高觸發）

| GPIO | 功能 | 元件 | 說明 |
|------|------|------|------|
| **IO45** | PIN_OUT1 / PIN_CREDIT_ADD | UO1 | 開分 (模擬開分按鈕) |
| **IO46** | PIN_OUT2 / PIN_CREDIT_WASH | UO2 | 洗分 (模擬洗分按鈕) |
| **IO47** | PIN_OUT3 | UO3 | 預留輸出 |
| **IO48** | PIN_OUT4 | UO4 | 預留輸出 |

### 系統元件

| GPIO | 功能 | 說明 |
|------|------|------|
| **IO11** | PIN_LED_SYS | 系統狀態 LED（共陽極，拉低亮）|
| **IO21** | PIN_BUTTON_CONFIG | 配網按鈕 Fun1（外部 4k7 上拉，按下讀 0）|
| **IO15** | PIN_I2C_SDA | I2C 資料線 |
| **IO16** | PIN_I2C_SCL | I2C 時脈線 |

---

## RS232 紙鈔機通訊 (TP Series)

透過 MAX3232 轉壓晶片連接。紙鈔機端採用 ICT 104U 標準協議。

| GPIO | 功能 | 說明 |
|------|------|------|
| **IO17** | PIN_BA_TX | ESP32 TX → MAX3232 T1in → RS232 Pin2 (RXD) |
| **IO18** | PIN_BA_RX | ESP32 RX ← MAX3232 R1out ← RS232 Pin3 (TXD) |

### UART 104U 協議參數

| 項目 | 值 | 說明 |
|------|-----|-----|
| UART Port | UART1 | 核心 1 獨立任務處理 |
| Baud Rate | 9600 | |
| Data Bits | 8 | |
| **Parity** | **Even (偶校驗)** | 104U 協議標準 (8E1) |
| Stop Bits | 1 | |

---

## 硬體連接示意圖

```
ESP32-S3 (IO17/18)       MAX3232 (3.3V)           TP 紙鈔機 (RS232 12V)
──────────────────       ──────────────           ────────────────────
IO17 (TX) ─────────────> T1in   T1out ──────────> DB9 Pin 2 (RXD)
IO18 (RX) <───────────── R1out  R1in  <────────── DB9 Pin 3 (TXD)
GND       ─────────────> GND    GND   ──────────> DB9 Pin 5 (GND)
```

---

## 邏輯與電氣特性

1. **光耦輸入 (反邏輯)**：
   *   待機 (High)：GPIO 讀值為 1。
   *   觸發 (Low)：外部信號使光耦導通，GPIO 拉低，讀值為 0。
2. **光耦輸出 (正邏輯)**：
   *   待機 (Low)：GPIO 輸出 0。
   *   觸發 (High)：GPIO 輸出 1，使光耦導通，閉合外部迴路（模擬按鈕）。
3. **安全警示**：
   *   紙鈔機通訊必須經過 MAX3232 轉壓，嚴禁 12V 直接接入 ESP32。
   *   所有電路元件必須共地。

---
*文件更新於 2026-05-09，對齊 IOTkiosk_v0 (ESP32-S3) 實作配置。*
