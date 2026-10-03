#!/usr/bin/env python3
import subprocess, time, re, os, sys

outbox = "/Users/ilawusong/Documents/WaW/.taskflow/shannie/outbox"
os.makedirs(outbox, exist_ok=True)
last_paste = ""

print("[*] Shannie 剪貼簿自動接單服務啟動中...", flush=True)

while True:
    try:
        content = subprocess.check_output(["pbpaste"], text=True)
        if content and content != last_paste:
            last_paste = content
            # 判斷是否為 Shannie 任務：
            # 條件 1: 包含 from: Shannie
            # 條件 2: 包含 "請 HQ" 或 "HQ" 且字數大於 15
            is_shannie_task = False
            title = "TASK"
            msg_type = "task"
            priority = "normal"

            if "from: Shannie" in content:
                is_shannie_task = True
                m = re.search(r"#\s*任務[：:]?\s*(.*)", content)
                if m:
                    title = m.group(1).strip()
            elif ("請 HQ" in content or "HQ" in content) and len(content.strip()) > 15:
                is_shannie_task = True
                # 從第一行或前幾字當標題
                first_line = content.strip().split("\n")[0]
                title = first_line[:25].strip()
                # 自動包裝成標準 Frontmatter 格式
                content = f"""---
from: Shannie
to: HQ
type: task
priority: normal
status: pending
date: {time.strftime('%Y-%m-%d')}
---

# 任務：{title}

{content.strip()}
"""

            if is_shannie_task:
                clean_title = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', title)[:30]
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{clean_title}.md"
                filepath = os.path.join(outbox, filename)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                
                print(f"[+] 成功捕獲任務 -> {filename}", flush=True)
                # 執行 watcher 掃描
                subprocess.run(["/Users/ilawusong/Documents/WaW/dev_tools/shannie_watch.sh"])
    except Exception as e:
        print(f"[-] 錯誤: {e}", flush=True)
    time.sleep(1)
