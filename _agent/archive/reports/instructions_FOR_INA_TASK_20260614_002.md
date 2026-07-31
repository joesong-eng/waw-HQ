# Ina - Phase 1：MQTT 監聽器割接 (TASK_20260614_002)

## 任務簡介
- **任務 ID**：TASK_20260614_002
- **優先級**：high
- **目標**：確認應用程式割接狀態，準備執行 Phase 1 割接

## 執行步驟

### Step 1：確認 waw-iot 應用程式狀態

#### 1.1 檢查 waw-iot 是否已切換至新表

**需確認**：
- [ ] `Machine` Model 是否使用 `machines` 表（而非 `devices`）
- [ ] `Store` Model 是否使用 `stores` 表（而非 `venues`）
- [ ] `MachineDeployment` Model 是否正常運作
- [ ] `RevenueService` 是否已實作分成固化邏輯

**檢查位置**：
```bash
# 在 waw-iot 專案目錄
grep -r "devices" app/Models/Machine.php app/Repositories/ || echo "No devices reference in Machine model"
grep -r "venues" app/Models/Store.php || echo "No venues reference in Store model"
```

#### 1.2 檢查 `profit_sharing_agreements` 初始化

**需確認**：
- [ ] 分潤邏輯是否有 fallback 預設比例（當 `profit_sharing_agreements` 為空）
- [ ] 預設比例是否為：機台主 100%，場地 0%

**檢查位置**：
```php
// app/Services/RevenueService.php
// 查看是否實作了 fallback 邏輯
```

### Step 2：部署 waw-iot 到 VPS（如果尚未部署）

**如果尚未部署**，執行以下步驟：

```bash
# SSH 到 infra VPS
ssh infra

# 部署 waw-iot
cd /var/www
sudo git clone <waw-iot-repo> waw-iot
sudo chown -R ubuntu:ubuntu waw-iot

# 配置 .env
cd /var/www/waw-iot
cp .env.example .env
# 編輯 .env：
# DB_HOST=127.0.0.1
# DB_PORT=3308
# DB_DATABASE=iotv9
# MQTT_HOST=mqtt.tg25.win
# MQTT_PORT=8883
# MQTT_USE_TLS=true

# 安裝依賴
composer install

# 執行遷移（如果需要）
php artisan migrate --force

# 啟動服務
sudo cp waw-iot-mqtt.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable waw-iot-mqtt
sudo systemctl start waw-iot-mqtt
```

### Step 3：測試 MQTT 監聽器

**測試心跳**：
```bash
# 發送測試心跳
mosquitto_pub -h mqtt.tg25.win -p 8883 \
  --cafile /etc/mosquitto/certs/ca.crt \
  --cert /etc/mosquitto/certs/client.crt \
  --key /etc/mosquitto/certs/client.key \
  -t 'device/test_chip_001/status' \
  -m 'online'

# 檢查 DB 更新
ssh infra "mysql -u root iotv9 -e \"SELECT chip_id, status, last_seen_at FROM machines WHERE chip_id='test_chip_001';\""
```

### Step 4：確認割接風險

**風險評估**：
- [ ] `devices` 與 `machines` 雙表是否仍被應用程式雙寫？
- [ ] `venues` 與 `stores` 雙表是否仍被應用程式雙寫？
- [ ] `profit_sharing_agreements` 為空時，分潤邏輯是否有 fallback？

## 回報格式

```markdown
# Ina - Phase 1 割接狀態報告 (TASK_20260614_002)

**任務 ID**：TASK_20260614_002  
**狀態**：✅ 可割接 / ⚠️ 需先完成 ______ / ❌ 不可割接

## waw-iot 應用程式狀態

| 項目 | 狀態 | 說明 |
|------|------|------|
| Machine Model 切換 | ✅ / ❌ | 使用 machines 表 |
| Store Model 切換 | ✅ / ❌ | 使用 stores 表 |
| 分潤 fallback 邏輯 | ✅ / ❌ | 當 profit_sharing_agreements 為空 |

## 部署狀態

| 項目 | 狀態 | 說明 |
|------|------|------|
| waw-iot 部署 | ✅ / ❌ | VPS 上是否有部署 |
| MQTT 服務狀態 | ✅ / ❌ | waw-iot-mqtt.service 是否運行 |

## 風險評估

| 風險 | 狀態 | 說明 |
|------|------|------|
| 雙表雙寫風險 | 低 / 中 / 高 | _________ |
| 分潤計算風險 | 低 / 中 / 高 | _________ |

## 建議行動

- **可割接項目**：___________
- **待完成項目**：___________

---

*報告人：Ina (Infra)*
```

## HQ 補充說明

根據 Ina 的評估報告 (CONS_20260614_001)：
- ✅ 資料庫 schema 已準備就緒
- ⚠️ `profit_sharing_agreements` 為空表
- ⚠️ 需確認應用程式是否已切換

**請 Ina 執行**：
1. 檢查 waw-iot 的 Model 和 Repository 實作
2. 確認分潤邏輯是否有 fallback 預設比例
3. 確認應用程式是否已停止寫入舊表 (`devices`, `venues`)

---

**HQ 指令**：請先確認割接狀態，不要直接執行割接。
