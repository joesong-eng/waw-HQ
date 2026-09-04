#!/usr/bin/env python3
"""
wawIoT Agent Supervisor — 共用函式庫
此檔案僅提供共用常數與工具函式，由 hq_gateway.py 統一 import 使用。
不再有獨立 main()，所有監聽與觸發邏輯已整合至 hq_gateway.py。
"""

import sys
import json
import datetime
import signal
import os
import subprocess
import shutil
from pathlib import Path

try:
    import redis
except ImportError:
    print("❌ 請先安裝 redis：pip install redis")
    sys.exit(1)

HQ_PATH = Path(os.environ.get('HQ_PATH', '/Users/ilawusong/Documents/WaW'))
CODEX_BIN = os.environ.get('CODEX_BIN') or shutil.which('codex') or '/Users/ilawusong/.local/bin/codex'
EXEC_TIMEOUT = int(os.environ.get('AGENT_EXEC_TIMEOUT', '900'))
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
SKILL_FILE = HQ_PATH / 'skills' / 'hq_ops' / 'analyse_agent_report.md'

# ── Agent 設定表 ────────────────────────────────────────────────────────────────
AGENTS = {
    'hq': {
        'work_dir': '/Users/ilawusong/Documents/WaW',
        'label': 'HQ',
    },
    'ina': {
        'work_dir': '/Users/ilawusong/Documents/WaW/Infra',
        'label': 'Ina (Infra Master)',
    },
    'sophie': {
        'work_dir': '/Users/ilawusong/Documents/WaW/Owner',
        'label': 'Sophie (Owner)',
    },
    'mina': {
        'work_dir': '/Users/ilawusong/Documents/WaW/PROJECT/Member',
        'label': 'Mina (Member)',
    },
    'allie': {
        'work_dir': '/Users/ilawusong/Documents/WaW/PROJECT/Alliance',
        'label': 'Allie (Alliance)',
    },
    'hubie': {
        'work_dir': '/Users/ilawusong/Documents/WaW/PROJECT/iHub',
        'label': 'Hubie (iHub)',
    },
    'coli': {
        'work_dir': '/Users/ilawusong/Documents/WaW/PROJECT/IOTwawS3',
        'label': 'Coli (IOTwawS3)',
    },
    'fio': {
        'work_dir': '/Users/ilawusong/Documents/WaW/PROJECT/IOTkiosk_v0',
        'label': 'Fio (IOTkiosk_v0)',
    },
}

# ── 工具函式 ────────────────────────────────────────────────────────────────────

def log(agent: str, msg: str):
    ts = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] [{agent.upper():8s}] {msg}", flush=True)


def save_task_file(agent: str, task: dict, work_dir: Path) -> Path:
    task_id = task.get('task_id') or task.get('consult_id') or 'UNKNOWN'
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    inbox = work_dir / '_agent'
    inbox.mkdir(exist_ok=True)
    filepath = inbox / f'REDIS_{ts}_{task_id}.json'
    filepath.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding='utf-8')
    return filepath


def read_context_store(task_id: str) -> dict:
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        client.ping()
        key = f'hq:thread:{task_id}'
        status = client.get(f'{key}:status') or 'unknown'
        round_num = int(client.get(f'{key}:round') or 0)
        history_raw = client.lrange(f'{key}:history', -3, -1)
        client.close()
        history = []
        for h in history_raw:
            try:
                history.append(json.loads(h))
            except Exception:
                history.append({'raw': h})
        return {'status': status, 'round': round_num, 'history': history}
    except Exception:
        return {'status': 'unknown', 'round': 0, 'history': []}


def build_prompt(agent: str, label: str, task: dict, task_file: Path, report_file: Path) -> str:
    task_id = task.get('task_id') or task.get('consult_id') or 'UNKNOWN'
    description = task.get('description') or task.get('supplemental_info') or task.get('reason') or ''
    task_type = task.get('type', 'task')

    ctx = read_context_store(task_id)
    ctx_section = ''
    if ctx['round'] > 0:
        history_lines = '\n'.join(
            f"  round {h.get('round','?')}: [{h.get('from','?')}] {h.get('summary','')[:120]}"
            for h in ctx['history']
        )
        ctx_section = f"""
【Context Store（跨 Session 記憶）】
任務狀態: {ctx['status']}
目前輪次: {ctx['round']}
最近歷史:
{history_lines}
"""

    return f"""你是 {label}。這是 HQ 自動派發任務，請完整自動執行並產生可驗收回報。
{ctx_section}
任務類型: {task_type}
任務 ID: {task_id}
任務檔案: {task_file}
任務描述:
{description}

要求：
1. 先讀取任務檔案內容。
2. 若 Context Store 有歷史記錄，先理解前幾輪進度再繼續，不要重複已完成的步驟。
3. 依本 Agent 職責範圍執行；若超出職責，明確回報 blocked 與原因。
4. 需要修改/部署/查證時，提供實際證明，例如 log、API 回傳、DB 查詢、grep 結果或檔案路徑。
5. 完成後建立回報檔：{report_file}
6. 回報檔必須包含：任務 ID、狀態 completed/blocked/needs_review、執行摘要、證明、後續風險。
7. 不要只口頭說完成；沒有證明就標 needs_review 或 blocked。
8. 完成後執行：bash {HQ_PATH}/scripts/agent_report_to_hq_v2.sh {agent} {report_file} {HQ_PATH}
""".strip()


def execute_task(agent: str, label: str, work_dir: Path, task: dict, task_file: Path):
    if task.get('auto_execute') is False:
        log(agent, "⏸️  auto_execute=false，略過")
        return

    task_id = task.get('task_id') or 'UNKNOWN'
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = work_dir / '_agent'
    report_dir.mkdir(exist_ok=True)
    report_file = report_dir / f'REPORT_{ts}_{task_id}.md'

    prompt = build_prompt(agent, label, task, task_file, report_file)
    log(agent, f"🤖 codex exec → {task_id}")

    try:
        result = subprocess.run(
            [CODEX_BIN, 'exec', '--skip-git-repo-check', prompt],
            cwd=work_dir,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=EXEC_TIMEOUT,
        )
        output = result.stdout or ''
        exit_code = result.returncode
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or '') + f"\n\nTIMEOUT: exceeded {EXEC_TIMEOUT}s"
        exit_code = 124
    except Exception as exc:
        output = f"自動執行失敗: {exc}"
        exit_code = 1

    if not report_file.exists():
        status = 'completed' if exit_code == 0 else 'needs_review'
        report_file.write_text(
            f"# {label} 自動任務回報\n\n"
            f"> 任務 ID: {task_id}\n"
            f"> 狀態: {status}\n"
            f"> Exit code: {exit_code}\n"
            f"> 回報時間: {datetime.datetime.now().isoformat()}\n\n"
            f"## Codex 輸出\n\n```\n{output[-12000:]}\n```\n",
            encoding='utf-8'
        )

    log(agent, f"📄 {report_file}")
    report_script = HQ_PATH / 'scripts' / 'agent_report_to_hq_v2.sh'
    if report_script.exists():
        subprocess.run(
            ['bash', str(report_script), agent, str(report_file), str(HQ_PATH)],
            cwd=work_dir, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60,
        )
        log(agent, "📤 回報 HQ 完成")
