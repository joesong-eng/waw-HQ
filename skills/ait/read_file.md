# Skill: 讀取文件

## 觸發關鍵字
- 讀取文件
- 查看
- read file
- show file
- cat

## 執行流程

### 1. 解析文件路徑
從任務描述中提取文件路徑

### 2. 讀取文件
```python
import os

file_path = os.path.join(LOCAL_PATH, relative_path)

if not os.path.exists(file_path):
    return f"❌ 文件不存在: {file_path}"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()
```

### 3. 回報結果
```
📄 文件內容: {relative_path}

{content}

---
大小: {file_size} bytes
修改時間: {mtime}
```

## 限制
- 只能讀取專案目錄內的文件
- 文件大小限制：< 100KB（超過則只顯示前 1000 行）
- 不顯示二進制文件
