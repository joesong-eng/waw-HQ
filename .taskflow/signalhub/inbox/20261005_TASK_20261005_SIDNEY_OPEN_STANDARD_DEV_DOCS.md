# 任務：TASK_20261005_SIDNEY_OPEN_STANDARD_DEV_DOCS

**派發時間**：2026-10-05
**優先級**：medium
**負責人**：Sidney (SignalHub)
**性質**：對外開發者文件 / 開放標準（WAW 標準局）
**來源**：`WAW_TODO.md` → SignalHub 核心流程 → 「對外開發者文件」「API 接入規格」

---

## 背景

WAW 2.0「開放標準」是 `WAW_TODO.md` 中最大缺口。SignalHub 已獨立上線
（`signal.tg25.win`，repo: `signal-hub-standalone`），API 端點已就位（`routes/api.php` 共 51 條）。

現有素材（需整合，勿重造）：
- `PROJECT/SignalHub/docs/THIRD_PARTY_INTEGRATION_GUIDE.md`（v2.2，第三方接入）
- `brains/knowledge/02_technical_standards/WAW_SIGNAL_SEMANTIC_SPECIFICATION.md`（信號語意，HQ 正本）
- `brains/knowledge/02_technical_standards/MQTT_TOPIC_STANDARD.md`（MQTT 主題，HQ 正本）
- `brains/knowledge/03_system_architecture/SIGNALHUB_HARDWARE_WEBHOOK_INTEGRATION_SPEC_v2.md`

---

## 交付物（本單只做「對外文件」，不動業務邏輯）

### 交付 1：OpenAPI 3.0 規格
- 產出 `PROJECT/SignalHub/docs/openapi.yaml`（或 `.json`），涵蓋 `v9/signal-hub/*` 公開端點。
- 至少涵蓋：profiles（CRUD）、pins、stat-rules、webhooks、deliveries、events、subscription status。
- 標明**認證方式**、**請求/回應 schema**、**錯誤碼**。
- 內部管理端點（simulator、test-webhook）可標 `x-internal: true` 或排除。

### 交付 2：ESP32 韌體接入規格（對外版）
- 產出 `PROJECT/SignalHub/docs/ESP32_INTEGRATION_SPEC.md`。
- 內容：MQTT Topic 格式、Payload 欄位、QoS 等級、連線/重連、LWT。
- **必須引用 HQ 正本**（`MQTT_TOPIC_STANDARD.md`、`WAW_SIGNAL_SEMANTIC_SPECIFICATION.md`），
  不得另立規範；如發現正本有缺漏，於回報中列「提案」交 HQ。

### 交付 3：開發者快速上手（README）
- 產出 `PROJECT/SignalHub/docs/DEVELOPER_QUICKSTART.md`。
- 內容：取得 API Key → 建 profile → 設定 pin mapping → 設 webhook → 收 event → 對帳。

---

## 驗收指標（附實際佐證）

1. `openapi.yaml` 可被 OpenAPI 驗證器解析（附驗證指令與輸出，例如 `npx @redocly/cli lint` 或 python `openapi-spec-validator`）。
2. 文件中的端點與 `routes/api.php` **逐一對照**（列出對照表，確認無虛構端點）。
3. `ESP32_INTEGRATION_SPEC.md` 的 MQTT 內容與 `MQTT_TOPIC_STANDARD.md` **一致**（逐項對照）。
4. 三份文件 commit 至 SignalHub repo 並 push（附 commit hash）。

---

## 禁止

- 不改任何業務邏輯 / 路由 / migration
- 不在 SignalHub 文件另立規範正本（正本在 HQ `brains/knowledge/`）
- 不宣稱未實作的端點（必須對照 `routes/api.php`）

## 完成定義

3 份文件交付、4 項驗收有實際佐證、回報寫入 `.taskflow/signalhub/outbox/`。
若發現 HQ 正本規範有缺漏或矛盾，於回報中列「提案」供 HQ 裁定，不得自行修改正本。
