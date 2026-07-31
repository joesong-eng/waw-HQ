# Skill: 寫入文件

## 觸發關鍵字
- 創建文件
- 寫入
- create file
- write file

## 執行流程

### 1. 解析文件路徑和內容
從任務描述中提取：
- 文件路徑（相對於專案根目錄）
- 文件內容

### 2. 寫入文件
```python
import os

file_path = os.path.join(LOCAL_PATH, relative_path)
os.makedirs(os.path.dirname(file_path), exist_ok=True)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
```

### 3. 回報結果
```
✅ 文件已創建
- 路徑: {file_path}
- 大小: {file_size} bytes
```

## 安全檢查
- 只能寫入專案目錄內的文件
- 不能覆蓋重要配置文件（package.json, .git/...）
- 文件大小限制：< 1MB
