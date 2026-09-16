# QR Code 格式統一規範

> **版本**: 2.1.0
> **最後更新**: 2026-09-14
> **維護者**: HQ（唯一寫入權）
> **適用範圍**: iHub (Hubie)、Alliance (Allie)、Member (Mina)、Infra (Ina)

---

## ⚠️ 重要聲明

**本文件定義 WAW 系統 QR Code 格式規範與安全性標準。**

- ✅ 所有產線出廠、平板顯示與前端解析必須嚴格遵循本規範
- ❌ 任何 Agent 不得自行發明或修改 QR Code 格式
- ❌ 嚴禁將連續、具規律性的硬體實體 MAC / chip_id 明文印製在可公開接觸的機殼貼紙上（防止枚舉霸佔 DoS 攻擊）
- ❌ 嚴禁在出廠貼紙上生成 Raw JSON 字串

---

## 一、格式規範

### 1.1 兌幣機 QR Code（動態螢幕）

**標準格式**：
```
https://win.tg25.win/kiosk?id={node_id}&token={session_token}
```

**參數**：
- id：Kiosk 的 node_id（格式：kiosk_NNN）
- token：動態 Session Token（由 iHub 每 90 秒定期刷新）

**生成方**：iHub 平板螢幕
**讀取方**：Member 手機相機

---

### 1.2 遊戲機出廠實體貼紙 QR Code（老邱產線燒錄階段）

在工廠批量燒錄通訊卡階段，卡片尚未送達店家安裝，尚未綁定現場機台編號（無 node_id）。為防止客人拍下機殼 QR 後推算前後 MAC 遍歷霸佔機台（DoS 攻擊），出廠標籤一律採用「混淆 Public Token」，嚴禁印製 MAC 或 Raw JSON。

**標準出廠格式**：
```
https://win.tg25.win/m/play?t={public_token}
```

**參數**：
- t：32 字元不可逆隨機代號（UUID v4 去除連字號或高熵隨機字串，例如 c8f3b610a2d54e19b84a912e73f84c01）
- 儲存對應：由 Alliance 在建立設備燒錄綁定記錄時生成，並同步存於 public_token <-> chip_id 對應表

**生成方**：Alliance 燒錄工作站（印表機輸出貼紙）
**讀取方**：Member 手機相機

---

### 1.3 遊戲機現場營運標籤（已指定機台編號後）

若機台已由店長老李於後台完成裝機綁定，或在店內二次印製帶有名稱與編號的標籤：

**標準現場格式**：
```
https://win.tg25.win/m/play?node_id={node_id}
```

**參數**：
- node_id：機台在 WAW 系統中的唯一營運編號（由 Owner 後台裝機綁定時生成）

**生成方**：Owner 後台裝機綁定
**讀取方**：Member 手機相機

---

## 二、安全性標準

### 2.1 防枚舉與防暴力鎖定（Anti-DoS 機制）

1. **出廠貼紙**：一律使用 public_token（32 字元高熵隨機代號），不暴露 MAC / chip_id
2. **API 端點防護**：
   - /api/device/check-session：平板開機時驗證 session 有效性
   - /api/device/bind：平板配對綁定，需驗證 public_token 或 node_id 合法性
   - /api/device/by-token/{token}：以 public_token 查詢設備資訊
3. **IP 限流**：同一 IP 短時間內大量請求不同 token / node_id 時觸發封鎖

### 2.2 出廠貼紙內容規範

1. QR Code 內容：https://win.tg25.win/m/play?t={public_token}
2. 標籤底部可印 MAC / Chip ID 作為「老邱品檢辨識小字」（僅內部識別用，不作為 QR 掃描內容）
3. 嚴禁在 QR Code 中嵌入 Raw JSON 字串（如 {"type":"collector","chip_id":"...","mac":"..."}）

---

## 三、Member 端解析流程

| 場景 | URL 格式 | 解析入口 | 負責方 |
|------|----------|----------|--------|
| 出廠貼紙掃描 | /m/play?t={public_token} | welcome.blade.php → play.blade.php | DeviceController@bind |
| 現場標籤掃描 | /m/play?node_id={node_id} | welcome.blade.php → play.blade.php | DeviceController@bind |

**流程說明**：
1. 平板開機 → Member app 掃描機台 QR Code
2. 系統以 GET /api/device/by-token/{token} 或 node_id 查詢設備
3. welcome.blade.php 解析 QR → 跳轉 play.blade.php 進入遊戲畫面
4. DeviceController@bind 完成平板與機台綁定

---

**制定者**: HQ
**最後更新**: 2026-09-14
**版本**: 2.1.0
