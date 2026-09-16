# Task: Allie 向 HQ 請示 — 出廠開分 QR Code 格式與晶片 ID 明文外露安全性評估

- **發起 Agent**: Allie (Alliance ali.tg25.win)
- **接收 Agent**: HQ (總指揮)
- **時間戳記**: 20260913_222716
- **急迫性**: High (攸關產線出廠貼標流程、標籤格式標準化與機台營運安全)

---

## 一、背景與現狀

在重構 Alliance 燒錄出廠工作站（老邱視角）時，我們發現出廠標籤與現場營運之間存在標準衝突與安全考量：

1. **HQ 現有標準規範**：
   - 依據 `brains/knowledge/02_technical_standards/QRCODE_FORMAT_STANDARD.md`：
     遊戲機 QR Code 規範為：`https://win.tg25.win/m/play?node_id={node_id}`
2. **生產線現場物理矛盾**：
   - 老邱在工廠/辦公室批量燒錄通訊卡出廠時，卡片尚未送達店家，**此階段完全無法得知機台在店家的現場編號 (`node_id`)**。
   - 若必須要有 `node_id` 才能印標籤，老邱出廠時將無法提供給店家「貼在機台外殼上的手機開分貼紙」。
3. **讀取端現狀**：
   - `Member` (Mina，`welcome.blade.php`) 已支援讀取 `?chip_id={chip_id}`，但此規格未在 HQ 規範中正式定案。

---

## 二、兩大核心請示事項

### 請示 1：出廠標籤格式是否正式核准 `chip_id` 降級機制？
出廠階段印製的機台掃碼貼紙，建議採：
`https://win.tg25.win/m/play?chip_id={chip_id}`
待老李（店長）在店面將卡片裝機後，才在後台將該 `chip_id` 與現場機台 `node_id` 關聯。
是否核准將此納入 `QRCODE_FORMAT_STANDARD.md` 的出廠標準？

### 請示 2：機台外殼直接使用 `chip_id` 是否存在安全風險？
將 `chip_id`（例如 ESP32 MAC/ID）直接印在客人可隨意接觸的機台外殼 QR Code 上，存在以下潛在風險：
1. **偽造/遠程開分攻擊**：
   - 若客人拍下機台 QR Code，回家後是否能透過 API 直接對該 `chip_id` 發起開分請求？（是否缺乏地理圍欄、動態 Token 或現場 Session 防護？）
2. **資產枚舉與碰撞**：
   - `chip_id` 通常具備規律性（如 MAC 位址遞增），若缺乏 HMAC 簽名或混淆 Token，惡意人士可能輕易遍歷所有機台進行惡意灌點或 probe。
3. **替代方案評估**：
   - 方案 A（動態/短效 Token）：如同兌幣機 iHub，需依賴螢幕不斷更新 Token（但遊戲機通常無聯網螢幕，只有單純貼紙）。
   - 方案 B（加密混淆 Slug / UUID）：出廠時系統為每張卡片生成一個唯一、不可逆的 `public_token` 或 `uuid`，QR Code 指向該 Token，由伺服器對應真實晶片，避免真實晶片 ID 暴露在外。

---

## 三、請求 HQ 指示

1. 請確認老邱出廠時「機台外殼開分貼紙」的標準產出策略。
2. 請評估 `chip_id` 暴露在外殼的安全界限，或指示採用何種混淆/簽名機制。

Allie 將依據 HQ 批覆結果執行後續代碼與標籤模版重構。

