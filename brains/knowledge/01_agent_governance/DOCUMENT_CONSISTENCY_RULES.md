# 文件一致性驗證規則

> **建立日期**: 2026-05-08  
> **目的**: 確保所有文件同步到最新的設計決策，避免混淆

---

## 🎯 核心原則

**單一真理來源 (Single Source of Truth)**

每個主題只有一個權威文件，其他文件必須與之保持一致。

---

## 📋 權威文件清單

### 1. API 認證規範

**權威文件**: `pubdocs/01_system/GLOBAL_STANDARDS.md`

**核心決策**:
- ✅ 統一使用 `X-Internal-Key` header
- ✅ 值為 `v9-internal-key-2026`
- ✅ 認證失敗回傳 **401**（不是 403）
- ❌ 不再使用 `X-API-Key`、`X-Api-Key`

**必須同步的文件**:
- `.kiro/quick_reference.yaml`
- `brains/knowledge/05_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md`
- 所有 `.kiro/specs/*/requirements.md`
- 所有 `.kiro/specs/*/design.md`

**驗證方式**:
```bash
# 檢查是否有過時的命名
grep -r "X-API-Key\|X-Api-Key" /Users/ilawusong/Documents/sysWawIot/HQ --include="*.md" --include="*.yaml"

# 應該回傳空（沒有結果）
```

---

### 2. MQTT 主題規範

**權威文件**: `brains/knowledge/02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md`

**核心決策**:
- ✅ Kiosk: `kiosk/{chip_id}/*`
- ✅ Device: `device/{chip_id}/*`
- ❌ 不再使用 `v9/kiosk/`、`waw/kiosk/`、`up/`、`down/` 前綴

**必須同步的文件**:
- `brains/knowledge/05_business_flows/kiosk_v0_exchange/KIOSK_EXCHANGE_FLOW.md`
- `brains/knowledge/hardware_pulse_mapping.md`
- 所有 `.kiro/specs/*/requirements.md`

**驗證方式**:
```bash
# 檢查是否有過時的主題格式
grep -r "v9/kiosk/\|waw/kiosk/\|up/kiosk/\|down/kiosk/" /Users/ilawusong/Documents/sysWawIot/HQ --include="*.md"

# 應該只在 archive/ 或 history/ 中出現
```

---

### 3. HTTP 狀態碼

**權威文件**: `pubdocs/01_system/GLOBAL_STANDARDS.md`

**核心決策**:
- ✅ 200: 成功
- ✅ 401: 認證失敗（X-Internal-Key 或 Bearer token 無效）
- ✅ 404: 資源不存在
- ✅ 409: 衝突（如 Kiosk 忙碌）
- ✅ 422: 驗證失敗
- ✅ 500: 伺服器錯誤
- ❌ 不使用 403（系統中未使用）

**必須同步的文件**:
- `.kiro/quick_reference.yaml`
- 所有 API 設計文件

**驗證來源**:
- Member/CallbackController.php:31
- Member/KioskController.php:357
- Infra/hardware/api/upload.py

---

### 4. 識別碼格式

**權威文件**: `pubdocs/01_system/GLOBAL_STANDARDS.md`

**核心決策**:
- ✅ 所有識別碼必須全小寫
- ✅ `node_id`: `kiosk_001`
- ✅ `esp32_mac`: `e072a1f73a78`
- ✅ `chip_id`: `e072a1f73a78`
- ⚠️ `screen_mac`: 保持原始格式（例外）

**必須同步的文件**:
- 所有涉及 Kiosk 識別的文件

---

### 5. 資料庫連線

**權威文件**: `pubdocs/01_system/02_protocols/DATABASE_PROTOCOL.md`

**核心決策**:
- ✅ 所有 DB 操作必須使用 SSH tunnel
- ✅ 本地 port: 3308
- ✅ 遠端 server: 141.148.165.50
- ✅ 遠端 port: 3306
- ❌ 禁止使用 localhost:3306

**必須同步的文件**:
- `.kiro/quick_reference.yaml`
- 部署相關文件

---

### 6. SSH 連線資訊

**權威文件**: `brains/knowledge/nginx_quick_view.md`

**核心決策**:
- ✅ 所有 VPS 統一使用 port 39022
- ✅ yd16: 137.131.50.16:39022
- ✅ yd47: 129.146.103.177:39022
- ✅ infra: 141.148.165.50:39022
- ✅ yd174: 129.153.116.174:39022
- ❌ 不使用 port 22

**必須同步的文件**:
- `.kiro/quick_reference.yaml`
- 部署相關文件

---

## 🔍 驗證流程

### 階段 1: 自動檢查（每次重大變更後）

```bash
#!/bin/bash
# 文件一致性檢查腳本

echo "=== 檢查過時的 API 認證命名 ==="
grep -r "X-API-Key\|X-Api-Key" /Users/ilawusong/Documents/sysWawIot/HQ \
  --include="*.md" --include="*.yaml" \
  --exclude-dir=archive --exclude-dir=history

echo "=== 檢查過時的 MQTT 主題格式 ==="
grep -r "v9/kiosk/\|waw/kiosk/\|up/kiosk/\|down/kiosk/" \
  /Users/ilawusong/Documents/sysWawIot/HQ \
  --include="*.md" \
  --exclude-dir=archive --exclude-dir=history

echo "=== 檢查錯誤的 SSH port ==="
grep -r "port.*22[^0-9]\|:22[^0-9]" \
  /Users/ilawusong/Documents/sysWawIot/HQ \
  --include="*.md" --include="*.yaml" \
  --exclude-dir=archive --exclude-dir=history

echo "=== 檢查 HTTP 403 狀態碼（應該用 401）==="
grep -r "403.*Internal-Key\|Internal-Key.*403" \
  /Users/ilawusong/Documents/sysWawIot/HQ \
  --include="*.md" --include="*.yaml" \
  --exclude-dir=archive --exclude-dir=history
```

### 階段 2: 手動審核（定期）

**每週檢查清單**:
- [ ] 權威文件是否有更新？
- [ ] 所有相關文件是否已同步？
- [ ] 是否有新的設計決策需要記錄？
- [ ] 是否有文件需要標記為過時？

### 階段 3: 重大變更時的同步流程

```
設計決策變更
  ↓
1. 更新權威文件
  ↓
2. 列出所有需要同步的文件
  ↓
3. 逐一更新並驗證
  ↓
4. 執行自動檢查腳本
  ↓
5. 記錄到 brains/history/SYNC_*.md
  ↓
6. 通知所有 Agent
```

---

## 📝 同步記錄模板

每次重大同步後，建立記錄：

```markdown
# 文件同步記錄 - SYNC_YYYYMMDD_主題

## 變更內容
- 權威文件: XXX.md
- 變更: 從 AAA 改為 BBB

## 已同步的文件
- [x] file1.md (行 123)
- [x] file2.yaml (行 45)
- [x] file3.md (行 67, 89)

## 驗證結果
```bash
# 執行檢查腳本
./check_consistency.sh
# 結果: 無過時內容
```

## 通知記錄
- [x] 已透過 HQ Message Hub 通知所有 Agent
- [x] 已更新 DOCUMENT_INDEX.md
```

---

## 🚨 發現不一致時的處理

### 情況 1: 發現過時內容

```
發現文件 A 使用過時的 X-API-Key
  ↓
1. 確認權威文件的正確內容
  ↓
2. 更新文件 A
  ↓
3. 記錄到 punishment.log（如果是 Agent 造成的）
  ↓
4. 執行驗證確認修正
```

### 情況 2: 發現衝突定義

```
文件 A 說用 401，文件 B 說用 403
  ↓
1. 檢查實際代碼（真理來源）
  ↓
2. 更新權威文件
  ↓
3. 同步所有相關文件
  ↓
4. 記錄到 history/SYNC_*.md
```

---

## 🎯 目標

1. **零混淆**: 所有文件對同一主題的描述完全一致
2. **可追溯**: 每次變更都有記錄
3. **可驗證**: 有自動化腳本檢查一致性
4. **及時同步**: 設計決策變更後立即同步所有文件

---

## 📚 參考

- `DOCUMENT_INDEX.md` - 所有文件的索引
- `GLOBAL_STANDARDS.md` - 全域標準（權威）
- `02_technical_standards/TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - MQTT 規範（權威）
- `DATABASE_PROTOCOL.md` - 資料庫協議（權威）

---

**建立者**: HQ  
**最後更新**: 2026-05-08  
**狀態**: 執行中
