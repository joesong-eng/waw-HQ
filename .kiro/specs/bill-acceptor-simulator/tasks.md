# Implementation Plan: Bill Acceptor Simulator

## Overview

將 sim-bill 改為直連 MQTT 鏈路，與真實韌體行為完全一致。

**架構版本**：v4（MQTT 直連）  
**負責人**：Hubie (iHub)  
**變更範圍**：`iHub/server/index.js`、`iHub/public/sim-bill/index.html`

---

## 變更摘要

| 項目 | 舊（v3） | 新（v4） |
|------|---------|---------|
| 收 stack/reject 指令 | ❌ WebSocket `infra.cmd` | ✅ MQTT `kiosk/{chip_id}/cmd` via SSE |
| iHub Server MQTT | 無 | 持久連線，訂閱 `kiosk/{chip_id}/cmd` |
| WebSocket 用途 | bind + infra.cmd | 只剩 bind（`.MemberBoundToKiosk`） |

---

## Tasks

### Task 1: iHub Server — 建立 MQTT 持久連線並訂閱 cmd

**檔案**：`iHub/server/index.js`

**實作內容**：

Server 啟動時建立 MQTT client，訂閱 `kiosk/{chip_id}/cmd`（chip_id 從環境變數或預設 `test-esp32` 讀取）。收到訊息後，透過 SSE 推給所有已連線的前端。

```javascript
const mqtt = require('mqtt');

const MQTT_BROKER = process.env.MQTT_BROKER || 'mqtts://mqtt.tg25.win:8883';
const SIM_CHIP_ID = process.env.SIM_CHIP_ID || 'test-esp32';
const CMD_TOPIC = `kiosk/${SIM_CHIP_ID}/cmd`;

// SSE 客戶端列表
const sseClients = [];

// MQTT 持久連線
const mqttClient = mqtt.connect(MQTT_BROKER, {
  clientId: `sim-bill-server-${Date.now()}`,
  // TLS 憑證設定（若需要）
});

mqttClient.on('connect', () => {
  console.log(`[MQTT] Connected, subscribing to ${CMD_TOPIC}`);
  mqttClient.subscribe(CMD_TOPIC, { qos: 2 });
});

mqttClient.on('message', (topic, message) => {
  if (topic !== CMD_TOPIC) return;
  try {
    const payload = JSON.parse(message.toString());
    console.log(`[MQTT] Received cmd:`, payload);
    // 推給所有 SSE 客戶端
    const data = JSON.stringify({ action: payload.action, chip_id: SIM_CHIP_ID });
    sseClients.forEach(res => res.write(`event: mqtt_cmd\ndata: ${data}\n\n`));
  } catch (e) {
    console.error('[MQTT] Parse error:', e.message);
  }
});
```

**驗收標準**：
- [ ] Server 啟動時自動連線 MQTT broker
- [ ] 成功訂閱 `kiosk/{chip_id}/cmd`（QoS 2）
- [ ] 收到訊息後推給所有 SSE 客戶端
- [ ] MQTT 斷線時自動重連（mqtt.js 預設行為）

---

### Task 2: iHub Server — 新增 SSE 端點

**檔案**：`iHub/server/index.js`

**實作內容**：

新增 `GET /api/simulator/events` 端點，前端連線後加入 `sseClients`，斷線時移除。

```javascript
app.get('/api/simulator/events', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  sseClients.push(res);
  console.log(`[SSE] Client connected, total: ${sseClients.length}`);

  req.on('close', () => {
    const idx = sseClients.indexOf(res);
    if (idx !== -1) sseClients.splice(idx, 1);
    console.log(`[SSE] Client disconnected, total: ${sseClients.length}`);
  });
});
```

**驗收標準**：
- [ ] `GET /api/simulator/events` 回傳 `text/event-stream`
- [ ] 前端連線後，收到 MQTT cmd 時會收到 SSE 事件
- [ ] 前端斷線後，從 sseClients 移除

---

### Task 3: iHub Server — `/api/simulator/bill` 保持不變

**確認**：此端點不需修改，只處理投幣（escrow 事件）和狀態上報，與 v3 相同。

**驗收標準**：
- [ ] 確認現有 `/api/simulator/bill` 邏輯未被破壞

---

### Task 4: 前端 — 移除 WebSocket `infra.cmd` 監聽

**檔案**：`iHub/public/sim-bill/index.html`

**實作內容**：

找到監聽 `infra.cmd` 的程式碼，**刪除**。WebSocket 只保留 `.MemberBoundToKiosk`。

```javascript
// 刪除這段（或類似的）：
// echo.channel(`kiosk.${nodeId}`).listen('infra.cmd', handleInfraCmd);

// 保留這段：
echo.channel(`kiosk.${nodeId}`).listen('.MemberBoundToKiosk', handleMemberBound);
```

**驗收標準**：
- [ ] 前端不再監聽 `infra.cmd`
- [ ] `.MemberBoundToKiosk` 監聽保留正常

---

### Task 5: 前端 — 建立 SSE 連線，處理 MQTT cmd

**檔案**：`iHub/public/sim-bill/index.html`

**實作內容**：

頁面初始化時建立 SSE 連線，收到 `mqtt_cmd` 事件後根據 `action` 執行狀態轉換。

```javascript
function connectSSE() {
  const evtSource = new EventSource('/api/simulator/events');

  evtSource.addEventListener('mqtt_cmd', (e) => {
    const { action } = JSON.parse(e.data);
    log(`[MQTT cmd] action=${action}`, 'info');

    if (action === 'stack' && currentState === 'ESCROW') {
      transitionTo('STACKING');
      setTimeout(() => {
        sendBillEvent('stacked');
        transitionTo('STACKED');
        setTimeout(() => transitionTo('IDLE'), 1500);
      }, 500);

    } else if (action === 'reject' && currentState === 'ESCROW') {
      transitionTo('RETURNING');
      setTimeout(() => {
        sendBillEvent('rejected');
        transitionTo('REJECTED');
        setTimeout(() => transitionTo('IDLE'), 1500);
      }, 500);

    } else if (action === 'enable') {
      transitionTo('IDLE');

    } else if (action === 'disable') {
      transitionTo('DISABLED');
    }
  });

  evtSource.onerror = () => {
    log('[SSE] 連線中斷，重連中...', 'warning');
  };
}
```

> `sendBillEvent('stacked')` 呼叫現有的 `/api/simulator/bill` proxy，發 MQTT stacked/rejected 事件。

**驗收標準**：
- [ ] 頁面載入時自動建立 SSE 連線
- [ ] 收到 `action=stack` → STACKING → 500ms → 發 stacked 事件 → STACKED → 1.5s → IDLE
- [ ] 收到 `action=reject` → RETURNING → 500ms → 發 rejected 事件 → REJECTED → 1.5s → IDLE
- [ ] 收到 `action=enable` → IDLE
- [ ] 收到 `action=disable` → DISABLED
- [ ] SSE 斷線時顯示警告（EventSource 會自動重連）

---

### Task 6: nginx 設定確認

**確認**：nginx 需要 proxy `GET /api/simulator/events` 到 iHub Server，且不能有 buffering（SSE 需要）。

```nginx
location /api/simulator/events {
    proxy_pass http://127.0.0.1:8083;
    proxy_buffering off;
    proxy_cache off;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding on;
}
```

**驗收標準**：
- [ ] nginx 設定已加入 `proxy_buffering off`
- [ ] SSE 事件能即時到達前端（無延遲）

---

### Task 7: 整合測試

**測試步驟**：
1. 開啟 sim-bill：`https://ihub.tg25.win/sim-bill/?key=dev`
2. 確認初始狀態：DISABLED
3. 用手機掃碼綁定 → 確認狀態變 IDLE（`.MemberBoundToKiosk` 觸發）
4. 點擊「100 元」→ 確認狀態變 ESCROW
5. iHub 平板點「確認入帳」→ Member 發 MQTT `stack` → SSE 推給前端
6. 確認狀態：STACKING → STACKED → IDLE
7. 重複步驟 4，iHub 點「拒絕」→ 確認：RETURNING → REJECTED → IDLE
8. 確認 WebSocket `infra.cmd` **不再**觸發任何行為

**驗收標準**：
- [ ] 完整 stack 流程正常
- [ ] 完整 reject 流程正常
- [ ] infra.cmd 移除後無副作用
- [ ] MQTT broker log 可見 `kiosk/test-esp32/cmd` 被訂閱

---

## 部署

```bash
# iHub 伺服器
cd /www/wwwroot/ihub.tg25.win
git pull origin main
pm2 restart ihub-server
# 確認 nginx 設定後 reload
sudo nginx -t && sudo nginx -s reload
```
