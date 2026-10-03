# 任務回報：20260915_MINA_SERVICES_PHP_CLEANUP

**完成時間**：2026-09-15 10:55
**執行者**：mina

## 執行結果

### 問題
`config/services.php` 的 infra 區塊有 6 個鍵，其中多個重複：
- `url` + `base_url` → 都讀 `INFRA_BASE_URL` 但預設值不同（infra.tg25.win vs api.tg25.win）
- `key` + `infra_key` → 都讀 `INFRA_KEY`，完全重複

### 修改

**config/services.php** — 移除 3 個重複鍵，保留 3 個統一鍵：
| 移除 | 保留 |
|:---|:---|
| `url` (INFRA_BASE_URL, default infra.tg25.win) | `base_url` (INFRA_BASE_URL, default api.tg25.win) ✅ |
| `key` (INFRA_KEY) | `callback_key` (INFRA_CALLBACK_INTERNAL_KEY) ✅ |
| `infra_key` (INFRA_KEY) | `api_key` (INFRA_CREDIT_X_API_KEY) ✅ |

**呼叫端更新**：
| 檔案 | 原始 | 修改後 |
|:---|:---|:---|
| `app/Services/InfraApiService.php` L26 | `config('services.infra.url', 'https://infra.tg25.win')` | `config('services.infra.base_url', 'https://api.tg25.win')` |
| `app/Services/InfraApiService.php` L27 | `config('services.infra.key', env('INFRA_KEY', ''))` | `config('services.infra.callback_key', '')` |
| `app/Http/Controllers/Api/KioskController.php` L28 | `config('services.infra.infra_key')` | `config('services.infra.callback_key')` |

### 驗收
- **Commit**：`145c6b0` — `fix(config): deduplicate services.php infra keys (P3-2)`
- **Push**：`bd822d0..145c6b0 main -> main` ✅
- **部署**：`waw_ops.sh deploy mina` ✅ 成功
- **`php -l`**：services.php + InfraApiService.php + KioskController.php 全部通過 ✅
- **首頁**：`https://win.tg25.win/` → 200 ✅
- **全專案 grep 確認**：無殘留 `services.infra.url`、`services.infra.key'`、`services.infra.infra_key` 引用 ✅

## 結論
✅ 完成

---
**回報者**：mina
**回報時間**：2026-09-15 10:55
