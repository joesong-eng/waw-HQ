# Sophie - waw-business/waw-infra 割接狀態確認 (TASK_20260614_001)

## 任務簡介
- **任務 ID**：TASK_20260614_001
- **優先級**：high
- **目標**：確認應用程式割接狀態，確保可以安全割接 MQTT 監聽器

## 評估清單

### 1. waw-business 割接狀態

**需確認**：
- [ ] `VenueRepository` 是否已切換至 `stores` 表？
- [ ] `Venue` Model 是否已更新為 WAW 2.0 架構？
- [ ] `venues` 表是否進入只讀遷移模式？
- [ ] 是否有 API 仍在寫入 `venues` 表？

**檢查位置**：
- `waw-business/app/Models/Venue.php`
- `waw-business/app/Repositories/VenueRepository.php`
- `waw-business/database/migrations/`

### 2. waw-infra 割接狀態

**需確認**：
- [ ] `DeviceRepository` 是否已切換至 `machines` 表？
- [ ] `Device` Model 是否已更新為 WAW 2.0 架構？
- [ ] `devices` 表是否已停止寫入？
- [ ] 是否有 API 仍在寫入 `devices` 表？

**檢查位置**：
- `waw-infra/app/Models/Device.php` 或 `Machine.php`
- `waw-infra/app/Repositories/DeviceRepository.php`
- `waw-infra/database/migrations/`

### 3. 分潤協議初始化

**需確認**：
- [ ] `profit_sharing_agreements` 表是否有初始化邏輯？
- [ ] 是否有 seeder 從 `profit_sharing_proposals` 初始化協議？
- [ ] 若表為空，分潤邏輯是否有 fallback 預設比例？

## 報告格式

```markdown
# Sophie - waw-business/waw-infra 割接狀態報告 (TASK_20260614_001)

**任務 ID**：TASK_20260614_001  
**狀態**：✅ 可割接 / ⚠️ 需先完成 ______ / ❌ 不可割接

## waw-business 割接狀態

| 項目 | 狀態 | 說明 |
|------|------|------|
| VenueRepository 切換 | ✅ / ❌ | _________ |
| venues 表只讀模式 | ✅ / ❌ | _________ |
| API 雙寫風險 | ✅ 已排除 / ⚠️ 仍存在 |

## waw-infra 割接狀態

| 項目 | 狀態 | 說明 |
|------|------|------|
| MachineRepository 切換 | ✅ / ❌ | _________ |
| devices 表停止寫入 | ✅ / ❌ | _________ |
| API 雙寫風險 | ✅ 已排除 / ⚠️ 仍存在 |

## 分潤協議初始化

| 項目 | 狀態 | 說明 |
|------|------|------|
| profit_sharing_agreements 初始化 | ✅ / ❌ | _________ |
| fallback 預設比例 | ✅ 已實作 / ❌ 缺失 |

## 總結

- **可割接項目**：___________
- **待完成項目**：___________
- **風險等級**：低 / 中 / 高

---

*報告人：Sophie (Owner)*
```

## HQ 補充說明

根據 Ina 的評估報告 (CONS_20260614_001)，目前：
- ✅ 資料庫 schema 已準備就緒
- ⚠️ `profit_sharing_agreements` 為空表
- ⚠️ 需確認應用程式是否已切換

**請 Sophie 執行**：
1. 檢查 `waw-business` 和 `waw-infra` 的 Repository 實作
2. 確認舊表 (`devices`, `venues`) 是否已停止寫入
3. 確認分潤邏輯是否有 fallback 預設比例

---

**HQ 指令**：請先確認割接狀態，不要直接執行割接。
