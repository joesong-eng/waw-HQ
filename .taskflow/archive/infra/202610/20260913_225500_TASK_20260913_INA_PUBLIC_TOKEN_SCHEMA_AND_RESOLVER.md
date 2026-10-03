# 任務：TASK_20260913_INA_PUBLIC_TOKEN_SCHEMA_AND_RESOLVER

**派發時間**：2026-09-13 22:55  
**優先級**：High  
**負責人**：Ina (Infra)
**指導規範**：`brains/knowledge/02_technical_standards/QRCODE_FORMAT_STANDARD.md` (v2.0.0)
**協調背景**：出廠標籤安全性防枚舉重構（Public Token 方案）

---

## 📋 任務核心要求（Ina 職責專屬）

### 1. 資料庫 Schema 變更與維護
- **Alliance 庫 (`ali_device_bindings`)**：
  - 新增欄位：`public_token VARCHAR(64) NULL`，並建立唯一索引 `UNIQUE KEY unq_public_token (public_token)`。
  - 對現有已有 `chip_id` 但 `public_token` 為 NULL 的舊資料，執行一次性補填 32 碼隨機字串。
- **Infra 設備總表 (`iotv9.devices`)**：
  - 同步建立 `public_token VARCHAR(64) NULL` 與唯一索引。

### 2. 提供 Token 設備反查介面（供 Member 玩家端使用）
- 在 Infra API（credit-relay 或設備路由）新增：
  - `GET /api/device/by-token/{token}`
  - 驗證 `X-API-Key` 或內部授權。
  - 依據 `public_token` 查出對應設備資訊（`chip_id`, `node_id`, `name`, `status`, `pulse_to_display`, `pulse_to_token` 等），格式與現有 `by-node/{node_id}` 對齊。
- 同步支援 Redis 緩存加速反查。

---

## 📝 驗收標準
1. [ ] 資料庫欄位與唯一索引就緒，無報錯。
2. [ ] 舊資料成功補填完整 `public_token`。
3. [ ] `GET /api/device/by-token/{token}` 通過驗證。
4. [ ] 產出執行報告至 `.taskflow/infra/outbox/`。
