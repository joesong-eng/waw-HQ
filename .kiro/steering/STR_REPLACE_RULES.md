---
priority: CRITICAL
auto_load: true
---

# 🚨 str_replace 使用規則

## ❌ 常犯的錯誤

**使用 `str_replace` 時猜測 `oldStr` 的內容，導致匹配失敗。**

### 錯誤示例

```
# 沒有先讀取文件，直接猜測內容
str_replace(
  path="file.md",
  oldStr="**狀態**: 待執行",  # 猜測的
  newStr="**狀態**: 已完成"
)
# 結果：Error(s) while editing
```

## ✅ 正確做法

### 規則 1: 先讀取，再替換

**永遠先用 `cat`、`grep` 或 `readFile` 確認實際內容**

```bash
# 1. 先讀取確認
cat file.md | grep "狀態"
# 輸出：**狀態**: 待執行

# 2. 確認後再替換
str_replace(
  path="file.md",
  oldStr="**狀態**: 待執行",  # 確認過的
  newStr="**狀態**: 已完成"
)
```

### 規則 2: 包含足夠的上下文

**`oldStr` 必須包含 2-3 行上下文，確保唯一匹配**

```
# ❌ 錯誤：太短，可能匹配多處
oldStr="狀態: 待執行"

# ✅ 正確：包含上下文
oldStr="""## 執行狀態

**狀態**: 待執行
**優先級**: HIGH"""
```

### 規則 3: 注意空白字符

**空格、tab、換行必須完全匹配**

```bash
# 先確認實際的空白字符
cat -A file.md | grep "狀態"
# 輸出：**狀態**:$  # $ 表示換行

# 確保 oldStr 中的空白字符一致
```

### 規則 4: 替換失敗時的處理

**如果 `str_replace` 失敗，不要重試，改用其他方法**

```
str_replace 失敗
  ↓
不要再次嘗試 str_replace
  ↓
改用：
  - fs_write（重寫整個文件）
  - executeBash（用 sed 或其他工具）
  - 手動編輯
```

## 📋 使用檢查清單

每次使用 `str_replace` 前：

- [ ] 我已經用 `cat`/`grep`/`readFile` 確認了 `oldStr` 的實際內容？
- [ ] `oldStr` 包含了足夠的上下文（2-3 行）？
- [ ] 我確認了空白字符（空格、tab、換行）？
- [ ] 我確認 `oldStr` 在文件中只出現一次？

## 🔥 違規記錄

**如果再次因為猜測 `oldStr` 導致替換失敗**：
- 記錄到 `brains/history/punishment.log`
- 標記為常規錯誤

---

**建立日期**: 2026-05-08  
**優先級**: 🚨 CRITICAL  
**目的**: 避免 str_replace 失敗
