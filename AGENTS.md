---

## 📂 重要目錄參考

**專案根目錄**: `/Users/ilawusong/Documents/WaW`

### 知識庫 (HQ 專屬寫入權限)

```
brains/knowledge/
├── 01_agent_governance/        # Agent 治理協議
│   ├── SIMPLE_FILE_DISPATCH_PROTOCOL.md  # 派工協議
│   └── AGENT_STARTUP_PROTOCOL.md         # 啟動協議
├── 02_technical_standards/     # 技術標準
│   └── MQTT_TOPIC_STANDARD.md            # MQTT 主題規範
├── 03_system_architecture/     # 系統架構文檔
├── 04_deployment_operations/   # 部署運維文檔
└── 05_business_flows/          # 業務流程文檔
```

**HQ 負責維護知識庫**，Agent 只能讀取。

### 派工系統

```
.taskflow/
├── owner/       # Sophie (Owner)
├── member/      # Mina (Member)
├── infra/       # Ina (Infra)
├── alliance/    # Allie (Alliance)
├── ihub/        # Hubie (iHub)
├── fio/         # Fio (IOTkiosk_v0)
├── coli/        # Coli (IOTwawS3)
├── archive/     # 封存區
└── task_flow.log # 派工日誌
```

**派發任務**：
```bash
./dev_tools/waw_ops.sh task <Agent名稱> <task_id> "<描述>" [priority]
```

**讀取回報**：
- 各 Agent outbox：`.taskflow/<agent>/outbox/`

### 開發與協作總控工具 (Dev & Ops Tools)

```
dev_tools/
├── waw_ops.sh               # 全域總控 (派工、部署、狀態、遠端指令)
├── hq_task_flow.sh          # 派工腳本
└── agent_report_to_hq_v2.sh # Agent 回報腳本
```

### Agent 專案目錄

```
PROJECT/
├── Owner/           # Sophie
├── Member/          # Mina
├── Infra/           # Ina
├── Alliance/        # Allie
├── iHub/            # Hubie
├── IOTkiosk_v0/     # Fio
└── IOTwawS3/        # Coli
```

---

---
### 檔案修改指引
- 當需要修改或建立檔案時，請優先使用 `exec_command` / bash 指令（例如 `cat << 'EOF' > ...`、`python3` 腳本或 `sed`）直接寫入檔案（**注意：定界符 `'EOF'` 必須加單引號**，以防止 PHP/Bash 等代碼中的 `$` 變數被本機 Shell 提前解析擴展）。
- 若必須使用 `apply_patch`，請嚴格遵守 Codex 專用格式：
  ```
  *** Begin Patch
  *** Update File: app/path/to/file.php
  @@
  - 舊代碼
  + 新代碼
  *** End Patch
  ```

