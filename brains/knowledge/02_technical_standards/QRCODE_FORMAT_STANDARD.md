# QR Code 格式統一規範

> **版本**: 1.1  
> **最後更新**: 2026-05-25  
> **狀態**: ✅ **已統一實作**  
> **適用範圍**: iHub (Hubie)、Alliance (Allie)、Member (Mina)

---

## ⚠️ 重要聲明

**本文件定義 V9 系統 QR Code 格式規範。**

- ✅ 所有新開發必須遵循本規範
- ❌ 任何 Agent 不得自行修改 QR Code 格式
- ❌ 發現不一致時，以本文件為準

**實作狀態**（2026-05-25 更新）：
- ✅ iHub：已統一為 `?id=` 參數（Commit: `000f41a`）
- ✅ Member：已支援 `?id=` 參數（Commit: `9a697fc`）
- ⏳ Alliance：待確認（遊戲機 QR Code）

**與韌體的關係**：
- ❌ 韌體（Fio/Coli）不處理 QR Code
- ✅ QR Code 由 iHub（兌幣機）和 Alliance（遊戲機）生成
- ✅ QR Code 由 Member 前端讀取

---

## 一、格式規範

### 1.1 兌幣機 QR Code

**標準格式**：
```
https://win.tg25.win/kiosk?id={node_id}&token={session_token}
```

**範例**：
```
https://win.tg25.win/kiosk?id=kiosk_001&token=mFbyvbYqQIhnC8hcw60LCctL7iKCpjIh
```

**參數**：
- `id`：Kiosk 的 `node_id`（格式：`kiosk_NNN`）
- `token`：Session token（90 秒有效期）

**生成方**：iHub  
**讀取方**：Member

---

### 1.2 遊戲機 QR Code

**標準格式**：
```
https://win.tg25.win/m/play?node_id={node_id}
```

**範例**：
```
https://win.tg25.win/m/play?node_id=device_001
```

**參數**：
- `node_id`：遊戲機的 `node_id`（格式：`device_NNN`）

**生成方**：Alliance  
**讀取方**：Member

---

## 二、實作規範

### 2.1 iHub 生成（檔案：`iHub/src/main.js`）

**正確**：
```javascript
await generateQR(`https://win.tg25.win/kiosk?id=${KIOSK_ID}&token=${data.token}`);
```

**錯誤**：
```javascript
// ❌ 參數名用 kiosk
await generateQR(`https://win.tg25.win/kiosk?kiosk=${KIOSK_ID}&token=${data.token}`);

// ❌ 舊格式
await generateQR(`KIOSK:${KIOSK_ID}:TOKEN:${data.token}`);
```

---

### 2.2 Alliance 生成（檔案：`Alliance/resources/views/devices/burning.blade.php`）

**正確**：
```php
$qrContent = "https://win.tg25.win/m/play?node_id={$device->node_id}";
```

**錯誤**：
```php
// ❌ 使用 chip_id
$qrContent = "https://win.tg25.win/m/play?node_id={$device->chip_id}";
```

---

### 2.3 Member 讀取（檔案：`Member/resources/views/welcome.blade.php`）

**正確**（向下相容）：
```javascript
const kioskId = urlObj.searchParams.get('id') || urlObj.searchParams.get('kiosk');
```

---

## 三、部署順序（強制）

```
1. 修改生成方（iHub 或 Alliance）
   ↓
2. 部署到生產環境
   ↓
3. HQ 驗證
   ↓
4. 修改讀取方（Member）
   ↓
5. 部署到生產環境
```

**嚴禁同時修改生成方和讀取方**

---

## 四、驗收標準

### 兌幣機
- [ ] iHub 生成格式：`?id={node_id}&token={token}`
- [ ] 手機相機掃描後跳轉正確
- [ ] 登入後進入兌幣流程

### 遊戲機
- [ ] Alliance 生成格式：`?node_id={node_id}`
- [ ] 手機相機掃描後跳轉正確
- [ ] 登入後進入開分流程

---

**制定者**: HQ  
**最後更新**: 2026-05-24  
**版本**: 1.0

---

## 🔗 文件神經連結

### 強關聯（必讀）
> 修改 QR Code 格式前，必須先閱讀

- `../NAMING_AUTHORITY.md` - 識別碼命名規則（node_id vs chip_id）
- `../04_deployment_operations/INFRASTRUCTURE_REFERENCE.md` - 部署位置（iHub 在 yd47）

### 中關聯（建議讀）
> 了解 QR Code 在業務流程中的使用

- `../05_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md` - 兌幣流程
- `WEBSOCKET_CHANNEL_STANDARD.md` - iHub 監聽 WebSocket
- `../04_deployment_operations/DEPLOYMENT_GUIDE.md` - 部署步驟

### 排除混淆
> 容易誤以為相關，但實際無關

- `02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - 韌體不處理 QR Code
