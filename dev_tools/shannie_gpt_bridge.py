#!/usr/bin/env python3
import os
import time
import re
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="Shannie WAW Bridge API",
    version="1.0.0",
    description="專為 ChatGPT Shannie GPT 打造的直寫 .taskflow/shannie/outbox API"
)

AUTH_TOKEN = "wck_fe3652ec11b752138220a574cfdf8bf496b48e2faf415da5887344e9dc19e507"
OUTBOX_DIR = "/Users/ilawusong/Documents/WaW/.taskflow/shannie/outbox"

class MessagePayload(BaseModel):
    title: str
    type: str = "task"
    priority: str = "normal"
    content: str

@app.get("/")
def read_root():
    return {"status": "online", "service": "Shannie WAW Bridge"}

@app.post("/api/outbox")
def write_outbox(msg: MessagePayload, authorization: str = Header(None)):
    if not authorization or authorization != f"Bearer {AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    clean_title = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', msg.title)[:30]
    filename = f"{timestamp}_{clean_title}.md"
    filepath = os.path.join(OUTBOX_DIR, filename)

    full_md = f"""---
from: Shannie
to: HQ
type: {msg.type}
priority: {msg.priority}
status: pending
date: {time.strftime('%Y-%m-%d')}
---

# 任務：{msg.title}

{msg.content}
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_md)
    
    # 觸發 Watcher 掃描
    os.system("/Users/ilawusong/Documents/WaW/dev_tools/shannie_watch.sh > /dev/null 2>&1 &")

    return {
        "status": "success",
        "file_created": filename,
        "message": f"任務已成功寫入本機 .taskflow/shannie/outbox/{filename}"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8089)
