#!/usr/bin/env python3
"""
Taskflow Redis 接收器 (VPS 單軌純事件驅動版 v3.2)
- 純單軌事件驅動：100% 依賴 Redis Pub/Sub 事件即時喚醒，堅決不使用輪詢！
- 動態探測 SQLite state_5.sqlite 最新活躍 Session (依 CWD 自適應感測)
- 徹底解決開新對話串 Session UUID 變更導致失聯的問題
- 自動熱更新 taskflow_sessions.json
- 去重: 用 SETNX 原子認領 task_id，防重複喚醒
"""
import json
import os
import subprocess
import sys
import time
import argparse
import signal
import sqlite3
import redis
from pathlib import Path

TASKFLOW_ROOT = Path(os.path.expanduser("~/WaW/.taskflow"))
SESSIONS_FILE = TASKFLOW_ROOT / "taskflow_sessions.json"
CODEX_STATE_DB = Path(os.path.expanduser("~/.codex/state_5.sqlite"))

AGENT_CWD_MAP = {
    "hq": ["/home/ubuntu/WaW"],
    "nana": ["/home/ubuntu"],
    "owner": [
        "/home/ubuntu/WaW/PROJECT/Sophie",
        "/home/ubuntu/WaW/PROJECT/Owner",
        "/home/ubuntu/wawOwner"
    ],
    "member": [
        "/home/ubuntu/WaW/PROJECT/Member",
        "/home/ubuntu/WaW/PROJECT/Mina",
        "/home/ubuntu/Member"
    ],
    "infra": [
        "/home/ubuntu/WaW/PROJECT/Infra",
        "/home/ubuntu/WaW/PROJECT/Ina",
        "/home/ubuntu/tg25-infra"
    ],
    "alliance": [
        "/home/ubuntu/WaW/PROJECT/Alliance",
        "/home/ubuntu/WaW/PROJECT/Allie",
        "/home/ubuntu/Alliance"
    ],
    "ihub": [
        "/home/ubuntu/WaW/PROJECT/iHub",
        "/home/ubuntu/WaW/PROJECT/Hubie",
        "/home/ubuntu/iHub"
    ],
    "signalhub": [
        "/home/ubuntu/WaW/PROJECT/SignalHub",
        "/home/ubuntu/WaW/PROJECT/Sidney",
        "/home/ubuntu/SignalHub"
    ],
    "fio": [
        "/home/ubuntu/WaW/PROJECT/IOTkiosk_v0",
        "/home/ubuntu/WaW/PROJECT/Fio"
    ],
    "coli": [
        "/home/ubuntu/WaW/PROJECT/IOTwawS3",
        "/home/ubuntu/WaW/PROJECT/Coli"
    ],
    "shannie": [
        "/home/ubuntu/WaW/shannie",
        "/home/ubuntu/shannie"
    ]
}

ALIAS_MAP = {
    "sophie": "owner",
    "mina": "member",
    "ina": "infra",
    "allie": "alliance",
    "hubie": "ihub",
    "sidney": "signalhub",
    "kiosk": "fio",
    "iotkiosk_v0": "fio",
    "waws3": "coli",
    "iotwaws3": "coli"
}

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{os.getpid()}] {msg}", flush=True)

def normalize_agent(agent_name):
    if not agent_name:
        return "hq"
    low = agent_name.lower()
    return ALIAS_MAP.get(low, low)

def load_sessions():
    if not SESSIONS_FILE.exists():
        return {}
    try:
        with open(SESSIONS_FILE, "r") as f:
            data = json.load(f)
        data.pop("_comment", None)
        data.pop("_config_path", None)
        return data
    except Exception as e:
        log(f"WARN: load_sessions failed: {e}")
        return {}

def sync_session_file(agent, uuid):
    try:
        if not SESSIONS_FILE.exists():
            data = {}
        else:
            with open(SESSIONS_FILE, "r") as f:
                data = json.load(f)
        if data.get(agent) != uuid:
            data[agent] = uuid
            with open(SESSIONS_FILE, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log(f"🔄 [SessionSync] 自動熱更新 Agent [{agent}] -> {uuid}")
    except Exception as e:
        log(f"WARN: sync_session_file failed: {e}")

def find_active_thread(agent):
    agent_key = normalize_agent(agent)
    targets = AGENT_CWD_MAP.get(agent_key, [])
    if not targets or not CODEX_STATE_DB.exists():
        return None

    try:
        conn = sqlite3.connect(f"file:{CODEX_STATE_DB}?mode=ro", uri=True, timeout=3.0)
        c = conn.cursor()
        c.execute("""
            SELECT id, cwd, updated_at, title
            FROM threads
            WHERE archived = 0
              AND source NOT LIKE '%subagent%'
              AND (title IS NULL OR title != 'Guardian review')
            ORDER BY updated_at DESC
        """)
        rows = c.fetchall()
        conn.close()
    except Exception as e:
        log(f"WARN: 查詢 state_5.sqlite 失敗: {e}")
        return None

    for tid, cwd, updated_at, title in rows:
        if not cwd:
            continue
        if agent_key == "nana":
            if cwd == "/home/ubuntu":
                return tid
        elif agent_key == "hq":
            if cwd == "/home/ubuntu/WaW":
                return tid
        else:
            for t in targets:
                if cwd == t or cwd.startswith(t + "/"):
                    return tid
    return None

def get_session_uuid(agent):
    agent_key = normalize_agent(agent)
    dynamic_tid = find_active_thread(agent_key)
    if dynamic_tid:
        sync_session_file(agent_key, dynamic_tid)
        return dynamic_tid

    sessions = load_sessions()
    uuid = sessions.get(agent_key)
    if uuid:
        return uuid

    return None

def claim_task_id(r, lock_key, ttl_seconds=600):
    result = r.set(f"taskflow:lock:{lock_key}", os.getpid(), nx=True, ex=ttl_seconds)
    if result:
        log(f"認領 {lock_key} 成功 (lock TTL={ttl_seconds}s)")
        return True
    else:
        return False

def wake_agent(agent, task_id, event_type):
    agent_key = normalize_agent(agent)
    uuid = get_session_uuid(agent_key)
    if not uuid:
        log(f"ℹ️ Agent [{agent_key}] 目前無在線活躍會話，工單已安全保存在 inbox/outbox 檔案信箱中 ({task_id})")
        return False

    if agent_key == "hq":
        msg = f"【Taskflow 通知】收到 {event_type} (工單/回報: {task_id})，請檢查 ~/WaW/.taskflow/ 並進行審核。"
    elif agent_key == "nana":
        msg = f"【Taskflow 派工】主機管家 Nana，收到新工單 {task_id}，請讀取 ~/WaW/.taskflow/nana/inbox/ 並執行維護。"
    else:
        msg = f"【Taskflow 派工】收到新工單 {task_id}，請完整讀取 ~/WaW/.taskflow/{agent_key}/inbox/ 檔案並執行。"

    cmd = ["codex", "queue", "--thread", uuid, "--message", msg]
    log(f"喚醒 {agent_key} ({uuid[:8]}...): {msg[:60]}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            log(f"✅ 喚醒成功: {result.stdout.strip()}")
            return True
        else:
            log(f"⚠️ 喚醒未完成 (exit={result.returncode}): {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        log("⚠️ 喚醒逾時 (15s)")
        return False

def on_dispatch(r, agent, task_id, event):
    agent_key = normalize_agent(agent)
    log(f"收到 dispatch: agent={agent_key} task={task_id}")
    if claim_task_id(r, f"dispatch_{agent_key}_{task_id}"):
        wake_agent(agent_key, task_id, "dispatch")

def on_response(r, task_id, responder):
    resp_key = normalize_agent(responder)
    log(f"收到 response: task={task_id} responder={resp_key}")
    if claim_task_id(r, f"response_{task_id}_{resp_key}", ttl_seconds=60):
        wake_agent("hq", task_id, f"response from {resp_key}")

def on_recovery(r, task_id):
    log(f"收到 recovery: task={task_id}")
    if claim_task_id(r, f"recovery_{task_id}", ttl_seconds=60):
        wake_agent("hq", task_id, "recovery")

def main():
    parser = argparse.ArgumentParser(description="Taskflow Redis 單軌智慧接收器 v3.2")
    parser.add_argument("--agent", default="all", help="Agent 名稱或 'all' 全域監聽")
    parser.add_argument("--redis-host", default="127.0.0.1")
    parser.add_argument("--redis-port", type=int, default=6379)
    args = parser.parse_args()

    agent_mode = args.agent.lower()
    log(f"🚀 啟動 Taskflow 單軌接收器 (Mode: {agent_mode}) redis={args.redis_host}:{args.redis_port}")

    r = redis.Redis(host=args.redis_host, port=args.redis_port, decode_responses=True)
    r.ping()
    log("🟢 Redis 連線成功 (純事件驅動，零輪詢)")

    if agent_mode == "all":
        channels = ["taskflow:dispatch:*", "taskflow:response:*", "taskflow:recovery"]
    elif agent_mode == "hq":
        channels = ["taskflow:response:*", "taskflow:recovery"]
    else:
        norm = normalize_agent(agent_mode)
        channels = [f"taskflow:dispatch:{norm}"]

    p = r.pubsub()
    p.psubscribe(*channels)
    log(f"📡 訂閱通道: {channels}")

    def graceful_shutdown(signum, frame):
        log(f"🛑 收到信號 {signum}，優雅關閉中...")
        p.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, graceful_shutdown)
    signal.signal(signal.SIGINT, graceful_shutdown)

    for message in p.listen():
        if message["type"] != "pmessage":
            continue
        try:
            channel = message.get("channel", "")
            data = json.loads(message["data"])
            task_id = data.get("task_id")
            event = data.get("event")
            
            if not task_id:
                log(f"WARN: 訊息缺少 task_id: {data}")
                continue

            if event == "new_task":
                target_agent = data.get("agent")
                if not target_agent and ":" in channel:
                    target_agent = channel.split(":")[-1]
                on_dispatch(r, target_agent, task_id, event)
            elif event == "response":
                responder = data.get("responder")
                if not responder and ":" in channel:
                    responder = channel.split(":")[-1]
                on_response(r, task_id, responder)
            elif event == "recovery":
                on_recovery(r, task_id)
            else:
                log(f"WARN: 未知事件類型: {event}")
        except json.JSONDecodeError:
            log(f"WARN: 無法解析 JSON: {message.get('data')}")
        except Exception as e:
            log(f"ERROR: {e}")

if __name__ == "__main__":
    main()
