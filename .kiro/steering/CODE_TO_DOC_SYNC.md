---
priority: CRITICAL
auto_load: true
---

# 🚨 代碼與文件強制同步規則

## 問題

**權威文件會過時**：寫完設計、實作完代碼後，權威文件就被冰起來，過兩天就跟實際代碼漸行漸遠。

## 核心原則

**代碼是唯一真理，文件必須跟隨代碼。**

---

## 📋 強制同步時機

### 時機 1: Agent 回報任務完成時

**HQ 必須做的事**：

1. **審核代碼變更**
   ```bash
   # 讀取實際代碼
   cat /Users/ilawusong/Documents/sysWawIot/Member/app/Http/Controllers/Api/CallbackController.php
   ```

2. **檢查是否影響權威文件**
   - 認證方式變更？ → 更新 `GLOBAL_STANDARDS.md`
   - MQTT 主題變更？ → 更新 `MQTT_TOPIC_STANDARD.md`
   - API 端點變更？ → 更新相關設計文件
   - 狀態碼變更？ → 更新 `GLOBAL_STANDARDS.md`

3. **立即同步文件**
   - 不要等「有空再更新」
   - 不要說「下次再同步」
   - **當下就更新**

4. **驗證一致性**
   ```bash
   # 執行一致性檢查
   grep -r "舊的定義" /Users/ilawusong/Documents/sysWawIot/HQ
   ```

### 時機 2: 發現代碼與文件不一致時

**立即處理流程**：

```
發現不一致
  ↓
1. 讀取實際代碼（真理來源）
  ↓
2. 更新權威文件
  ↓
3. 同步所有相關文件
  ↓
4. 記錄到 history/SYNC_*.md
  ↓
5. 通知所有 Agent
```

**不要**：
- ❌ 記下來「之後再處理」
- ❌ 假設文件是對的
- ❌ 等到「有時間」再同步

### 時機 3: 每週定期檢查

**每週五執行**：

1. **抽查關鍵 API**
   ```bash
   # 檢查認證邏輯
   grep -A 5 "X-Internal-Key" /Users/ilawusong/Documents/sysWawIot/Member/app/Http/Controllers/Api/*.php
   
   # 對比文件
   grep "X-Internal-Key" /Users/ilawusong/Documents/sysWawIot/HQ/pubdocs/01_system/GLOBAL_STANDARDS.md
   ```

2. **抽查 MQTT 主題**
   ```bash
   # 檢查 Infra listener
   grep "subscribe" /Users/ilawusong/Documents/sysWawIot/tg25-infra/mqtt/scripts/*.py
   
   # 對比文件
   cat /Users/ilawusong/Documents/sysWawIot/HQ/brains/knowledge/MQTT_TOPIC_STANDARD.md
   ```

3. **記錄檢查結果**
   - 建立 `history/WEEKLY_CHECK_YYYYMMDD.md`
   - 記錄發現的不一致
   - 記錄已修正的項目

---

## 🎯 權威文件的真正定義

**權威文件不是「設計文件」，而是「實際代碼的文字描述」。**

### 錯誤理解

```
設計階段：寫權威文件
  ↓
實作階段：寫代碼
  ↓
完成後：文件被冰起來
  ↓
代碼繼續演進
  ↓
文件過時
```

### 正確理解

```
設計階段：寫設計文件
  ↓
實作階段：寫代碼
  ↓
完成後：根據實際代碼更新權威文件
  ↓
代碼變更時：立即更新權威文件
  ↓
權威文件永遠反映實際代碼
```

---

## 📝 更新權威文件的檢查清單

每次 Agent 回報任務完成時，HQ 必須問自己：

- [ ] 這次變更是否影響 API 認證？
  - 是 → 更新 `GLOBAL_STANDARDS.md`
  
- [ ] 這次變更是否影響 MQTT 主題？
  - 是 → 更新 `MQTT_TOPIC_STANDARD.md`
  
- [ ] 這次變更是否影響 HTTP 狀態碼？
  - 是 → 更新 `GLOBAL_STANDARDS.md`
  
- [ ] 這次變更是否影響資料庫結構？
  - 是 → 更新 `DATABASE_PROTOCOL.md`
  
- [ ] 這次變更是否影響識別碼格式？
  - 是 → 更新 `GLOBAL_STANDARDS.md`

**如果任何一項是「是」，必須當下更新文件。**

---

## 🔍 如何確認代碼與文件一致

### 方法 1: 直接對比

```bash
# 1. 讀取代碼中的實際值
grep -A 3 "X-Internal-Key" /Users/ilawusong/Documents/sysWawIot/Member/app/Http/Controllers/Api/CallbackController.php

# 2. 讀取文件中的定義
grep "X-Internal-Key" /Users/ilawusong/Documents/sysWawIot/HQ/pubdocs/01_system/GLOBAL_STANDARDS.md

# 3. 對比是否一致
```

### 方法 2: 執行驗證腳本

```bash
# 執行一致性檢查
cd /Users/ilawusong/Documents/sysWawIot/HQ
./scripts/check_consistency.sh
```

### 方法 3: 實際測試

```bash
# 測試 API 是否按文件描述運作
curl -H "X-Internal-Key: v9-internal-key-2026" http://win.tg25.win/api/callback/credit

# 確認回應是否符合文件定義
```

---

## 🚨 違規處理

### 情況 1: Agent 回報完成，但文件未更新

```
Agent: 我已經修改了認證邏輯，改用新的 header
HQ: [審核代碼，發現確實變更了]
HQ: [檢查 GLOBAL_STANDARDS.md，發現未更新]
HQ: ❌ 違規！必須立即更新文件
```

**處理**：
1. 立即更新權威文件
2. 記錄到 `punishment.log`
3. 通知 Agent 下次必須同時更新文件

### 情況 2: HQ 審核時未檢查文件一致性

```
Agent: 任務完成
HQ: 審核通過 ✅
[一週後發現文件過時]
Boss: 文件跟代碼不一致！
```

**處理**：
1. HQ 記錄到 `punishment.log`
2. 立即修正文件
3. 加強審核流程

---

## 📊 文件生命週期

```
設計階段
  ↓
設計文件（初稿）
  ↓
實作階段
  ↓
代碼完成
  ↓
根據實際代碼更新權威文件 ← 這一步最容易被忽略
  ↓
權威文件（v1.0）
  ↓
代碼演進
  ↓
立即更新權威文件 ← 這一步最容易被忽略
  ↓
權威文件（v1.1, v1.2...）
```

---

## 🎯 核心規則

1. **代碼是真理** - 文件錯了就改文件，不是改代碼去符合文件
2. **立即同步** - 代碼變更時當下就更新文件，不要拖延
3. **定期驗證** - 每週檢查代碼與文件是否一致
4. **強制執行** - 違規記錄 punishment.log

---

## 📚 參考

- `DOCUMENT_CONSISTENCY_RULES.md` - 一致性驗證規則
- `HQ_CROSS_WORKSPACE_ACCESS.md` - 如何讀取其他專案代碼
- `GLOBAL_STANDARDS.md` - 權威文件範例

---

**建立日期**: 2026-05-08  
**優先級**: 🚨 CRITICAL  
**目的**: 確保文件永遠反映實際代碼，不會過時
