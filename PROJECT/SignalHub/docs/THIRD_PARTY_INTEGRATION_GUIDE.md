# WAW SignalHub 第三方 API 與 Webhook 接入指南

- **版本編號**：v1.0
- **適用對象**：第三方平台商、獨立開發者、自建 SaaS 系統之營運商
- **標準守護**：WAW 標準局（SignalHub / Sidney）
- **基礎端點**：https://signal.tg25.win/api/v9/signal-hub

---

## 1. 架構概念與接入方式

WAW SignalHub 提供兩種主要數據對接方式：
1. **Webhook 實時推送 (主動推)**：當硬體設備產生脈衝事件或電位變更時，WAW 伺服器即時向第三方 HTTP(S) Endpoint 推送 JSON Payload。
2. **REST API 查詢 (被動拉)**：第三方系統定時或按需向 WAW 查詢歷史事件流水、當前里程表讀數、統計報表。

---

## 2. Webhook 實時推送規範

### 2.1 HTTP 請求規格
- **Method**：POST
- **Content-Type**：application/json
- **User-Agent**：WAW-SignalHub-Webhook/1.0
- **自訂 Header**：
  - X-WAW-Signature：請求內容之 HMAC-SHA256 簽名 Hex 字串。
  - X-WAW-Timestamp：事件發送的 Unix 毫秒時間戳。
  - X-WAW-Event-Type：事件類型（如 signal.pulse, signal.status）。

### 2.2 Payload 格式範例
```json
{
  "event_id": 89412,
  "event_type": "signal.pulse",
  "chip_id": "C8F09E1A2B3C",
  "device_id": 1024,
  "machine_id": 55,
  "profile_id": 12,
  "pin_code": "UI1",
  "label": "投幣累計",
  "stat_group": "revenue",
  "raw_value": 15280,
  "delta_value": 1,
  "converted_value": 10.0,
  "unit_label": "元",
  "event_at": "2026-08-31 09:55:00.123",
  "timestamp": 1725088500123
}
```

---

## 3. HMAC-SHA256 簽名與安全驗簽

為防止偽造請求與中間人攻擊，每個 Webhook 均使用店主/第三方在後台設定的 secret_key 進行 HMAC-SHA256 簽名。

### 3.1 簽名計算規則
簽名密文字串（Signature String）之構成：
```
Signature = HMAC_SHA256(secret_key, raw_request_body)
```
將計算結果轉為小寫十六進位 (Hex String) 即為 X-WAW-Signature。

---

## 4. 驗簽程式碼範例 (Code Examples)

### 4.1 Python 3 (Flask 範例)

```python
import hmac
import hashlib
import json
from flask import Flask, request, jsonify

app = Flask(__name__)
WEBHOOK_SECRET = "your_webhook_secret_key_here"

def verify_signature(raw_body: bytes, signature_header: str, secret: str) -> bool:
    if not signature_header or not secret:
        return False
    computed = hmac.new(
        key=secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed, signature_header)

@app.route("/webhook/waw-signal", methods=["POST"])
def handle_waw_signal():
    signature = request.headers.get("X-WAW-Signature")
    raw_body = request.get_data()

    if not verify_signature(raw_body, signature, WEBHOOK_SECRET):
        return jsonify({"error": "Invalid signature"}), 401

    payload = json.loads(raw_body.decode("utf-8"))
    print(f"收到來自晶片 {payload.get('chip_id')} 腳位 {payload.get('pin_code')} 的增量: {payload.get('delta_value')}")

    # 處理商業邏輯...

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(port=8080)
```

### 4.2 Node.js (Express 範例)

```javascript
const express = require('express');
const crypto = require('crypto');

const app = express();
const WEBHOOK_SECRET = 'your_webhook_secret_key_here';

// 必須取得 Raw Buffer 以確保簽名計算精準
app.use(express.json({
  verify: (req, res, buf) => {
    req.rawBody = buf;
  }
}));

function verifySignature(rawBody, signatureHeader, secret) {
  if (!signatureHeader || !secret || !rawBody) return false;
  const computed = crypto
    .createHmac('sha256', secret)
    .update(rawBody)
    .digest('hex');
  
  return crypto.timingSafeEqual(
    Buffer.from(computed, 'utf8'),
    Buffer.from(signatureHeader, 'utf8')
  );
}

app.post('/webhook/waw-signal', (req, res) => {
  const signature = req.headers['x-waw-signature'];

  if (!verifySignature(req.rawBody, signature, WEBHOOK_SECRET)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const payload = req.body;
  console.log(`收到信號事件: ${payload.pin_code} 累計值: ${payload.raw_value}, 增量: ${payload.delta_value}`);

  // 執行業務邏輯...

  res.status(200).json({ status: 'ok' });
});

app.listen(8080, () => {
  console.log('Webhook receiver running on port 8080');
});
```

---

## 5. 重試與故障處理機制
1. **超時限制**：第三方接收伺服器須在 5 秒內回應 HTTP 2xx 狀態碼。
2. **重試策略**：若連線逾時或回傳 5xx 錯誤，系統將依照指數退避策略重試（1m, 5m, 15m, 30m），連續失敗 10 次將暫時掛起該 Webhook 並標記 failure_count。
3. **等冪保證 (Idempotency)**：第三方應利用 event_id 或 msg_id 做去重防護，確保重複投遞不影響帳務統計。
