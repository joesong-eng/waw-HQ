#!/usr/bin/env python3
"""
HQ Gateway — 統一的任務流程決策中心
取代 agents_supervisor 的 HQReportThread，成為單一進程監聽所有 Agent 頻道、
呼叫 LLM 決策、寫入 context store。

三個 class：ContextStore、DecisionEngine、GatewayListener
"""

import sys, json, threading, datetime, signal, os, subprocess, tomllib, shutil
import fcntl, atexit

def ensure_singleton(lock_file_path):
    """確保只有一個 hq_gateway 實例運行"""
    try:
        lock_file = open(lock_file_path, "w")
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_file.write(str(os.getpid()))
        lock_file.flush()
        def cleanup():
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                os.unlink(lock_file_path)
            except: pass
        atexit.register(cleanup)
        return True
    except (OSError, IOError):
        if os.path.exists(lock_file_path):
            try:
                with open(lock_file_path, "r") as f:
                    existing_pid = f.read().strip()
                print(f"❌ hq_gateway 已在運行 (PID: {existing_pid})", flush=True)
            except:
                print("❌ hq_gateway 已在運行", flush=True)
        else:
            print("❌ 無法創建鎖定文件", flush=True)
        sys.exit(1)

from pathlib import Path

try:
    import redis, requests
except ImportError:
    print("❌ pip install redis requests", flush=True); sys.exit(1)


# ── 讀取 9router 配置 ────────────────────────────────────────────────────────
def _load_9router_config():
    """從 config.toml 讀取 9router 設定（統一配置點）"""
    # Fallback 預設值（從環境變數或硬編碼）
    fallback = {
        'base_url': os.environ.get('GATEWAY_URL', 'http://localhost:8000/v1'),
        'model': os.environ.get('GATEWAY_MODEL', 'kr/claude-sonnet-4.5'),
        'api_key': os.environ.get('GATEWAY_API_KEY', 'sk-Q4LOajzkGEoKqHYogFTUK7_qLZmSC8_Zi7F3r5wNyDw')
    }
    
    config_path = Path("/Users/ilawusong/AIPP/b202HOME/HQcenter/docs/9router/config/config.toml")
    
    if not config_path.exists():
        print(f"⚠️  config.toml 不存在，使用 fallback 設定: {fallback['model']}", flush=True)
        return fallback
    
    try:
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        
        provider_config = config.get('model_providers', {}).get('custom', {})
        
        return {
            'base_url': provider_config.get('base_url', fallback['base_url']),
            'model': config.get('model', fallback['model']),
            'api_key': provider_config.get('api_key', fallback['api_key'])
        }
    except Exception as e:
        print(f"⚠️  讀取 config.toml 失敗: {e}，使用 fallback 設定", flush=True)
        return fallback

_9R_CONFIG = _load_9router_config()

# ── 共用常數（內嵌自 agents_supervisor.py）─────────────────────────────────────
HQ_PATH = Path(os.environ.get('HQ_PATH', '/Users/ilawusong/Documents/sysWawIot/HQ'))
CODEX_BIN = os.environ.get('CODEX_BIN') or shutil.which('codex') or '/Users/ilawusong/.local/bin/codex'
EXEC_TIMEOUT = int(os.environ.get('AGENT_EXEC_TIMEOUT', '900'))
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
SKILL_FILE = HQ_PATH / 'skills' / 'hq_ops' / 'analyse_agent_report.md'

# ── Agent 設定表 ────────────────────────────────────────────────────────────────
AGENTS = {
    'hq': {
        'work_dir': '/Users/ilawusong/Documents/sysWawIot/HQ',
        'label': 'HQ',
        'context_files': ['_agent/AI_CONTEXT.md', 'AGENTS.md'],
        'db_check': None,
    },
    'ina': {
        'work_dir': '/Users/ilawusong/Documents/sysWawIot/tg25-infra',
        'label': 'Ina (Infra Master)',
        'context_files': ['_agent/AI_CONTEXT.md', '_agent/IDENTITY.md', '_agent/DB_MANIFEST.md'],
        'db_check': {
            'host': '127.0.0.1', 'port': 3306,
            'user': 'iot_user', 'password': 'IotUser2025Secure', 'db': 'iotv9',
            'keywords': ['資料表', '表格', 'table', 'schema', 'migration', 'migrate',
                         'DDL', '建表', '欄位', '資料庫', 'DB', '新表', '設計稿'],
        },
    },
    'sophie': {
        'work_dir': '/Users/ilawusong/Documents/sysWawIot/waw-core',
        'label': 'Sophie (Owner)',
        'context_files': ['_agent/IDENTITY.md', '_agent/DB_MANIFEST.md'],
        'db_check': {
            'host': '127.0.0.1', 'port': 3306,
            'user': 'iot_user', 'password': 'IotUser2025Secure', 'db': 'iotv9',
            'keywords': ['資料表', '表格', 'table', 'schema', 'migration', 'migrate',
                         'DDL', '建表', '欄位', '資料庫', 'DB', '新表', '設計稿'],
        },
    },
    'mina': {
        'work_dir': '/Users/ilawusong/Documents/sysWawIot/Member',
        'label': 'Mina (Member)',
        'context_files': ['_agent/IDENTITY.md'],
        'db_check': None,
    },
    'allie': {
        'work_dir': '/Users/ilawusong/Documents/sysWawIot/Alliance',
        'label': 'Allie (Alliance)',
        'context_files': ['_agent/IDENTITY.md'],
        'db_check': None,
    },
    'hubie': {
        'work_dir': '/Users/ilawusong/Documents/sysWawIot/iHub',
        'label': 'Hubie (iHub)',
        'context_files': ['_agent/IDENTITY.md'],
        'db_check': None,
    },
    'coli': {
        'work_dir': '/Users/ilawusong/Documents/sysWawIot/IOTwawS3',
        'label': 'Coli (IOTwawS3)',
        'context_files': ['_agent/IDENTITY.md'],
        'db_check': None,
    },
    'fio': {
        'work_dir': '/Users/ilawusong/Documents/sysWawIot/IOTkiosk_v0',
        'label': 'Fio (IOTkiosk_v0)',
        'context_files': ['_agent/IDENTITY.md'],
        'db_check': None,
    },
}

# ── 共用工具函式（內嵌自 agents_supervisor.py）──────────────────────────────────

def log(agent: str, msg: str):
    ts = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] [{agent.upper():8s}] {msg}", flush=True)

def save_task_file(agent: str, task: dict, work_dir: Path) -> Path:
    task_id = task.get('task_id') or task.get('consult_id') or 'UNKNOWN'
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    inbox = work_dir / '_agent'
    inbox.mkdir(parents=True, exist_ok=True)
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
            try: history.append(json.loads(h))
            except Exception: history.append({'raw': h})
        return {'status': status, 'round': round_num, 'history': history}
    except Exception:
        return {'status': 'unknown', 'round': 0, 'history': []}

def load_context_files(agent: str, work_dir: Path) -> str:
    """載入 Agent 的 context 文件（身份、DB 清單等）"""
    cfg = AGENTS.get(agent, {})
    context_files = cfg.get('context_files', [])
    sections = []
    for rel_path in context_files:
        fp = work_dir / rel_path
        if fp.exists():
            try:
                text = fp.read_text(encoding='utf-8')[:3000]  # 限制每份文件 3000 字
                sections.append(f"--- {rel_path} ---\n{text}")
            except Exception:
                pass
    return '\n\n'.join(sections)


def get_db_snapshot(agent: str, description: str) -> str:
    """偵測到 DB 相關任務時，取得 SHOW TABLES。
    優先嘗試本地 tunnel（127.0.0.1:3308），
    若 tunnel 未開則自動建立，失敗才 fallback 到 SSH 直連。
    """
    cfg = AGENTS.get(agent, {})
    db_check = cfg.get('db_check')
    if not db_check:
        return ''
    keywords = db_check.get('keywords', [])
    if not any(kw.lower() in description.lower() for kw in keywords):
        return ''

    u = db_check['user']
    p = db_check['password']
    d = db_check['db']
    tables = ''

    # 方法 1：本地 tunnel（127.0.0.1:3308）
    try:
        r = subprocess.run(
            ['mysql', '-h', '127.0.0.1', '-P', '3308',
             f'-u{u}', f'-p{p}', d, '-e', 'SHOW TABLES;'],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            tables = r.stdout.strip()
            log('gateway', '📊 DB 快照：tunnel 3308 成功')
    except Exception:
        pass

    # 方法 2：自動建立 tunnel 再試
    if not tables:
        try:
            subprocess.Popen(
                ['ssh', '-p', '39022', '-N', '-L', '3308:127.0.0.1:3306',
                 'ubuntu@141.148.165.50'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            import time; time.sleep(3)
            r = subprocess.run(
                ['mysql', '-h', '127.0.0.1', '-P', '3308',
                 f'-u{u}', f'-p{p}', d, '-e', 'SHOW TABLES;'],
                capture_output=True, text=True, timeout=5
            )
            if r.returncode == 0 and r.stdout.strip():
                tables = r.stdout.strip()
                log('gateway', '📊 DB 快照：自動建立 tunnel 後成功')
        except Exception:
            pass

    # 方法 3：SSH 直連 VPS 跑 mysql（fallback）
    if not tables:
        try:
            r = subprocess.run(
                ['ssh', '-p', '39022', 'ubuntu@141.148.165.50',
                 f'mysql -h 127.0.0.1 -u {u} -p{p} {d} -e "SHOW TABLES;" 2>/dev/null'],
                capture_output=True, text=True, timeout=15
            )
            if r.returncode == 0 and r.stdout.strip():
                tables = r.stdout.strip()
                log('gateway', '📊 DB 快照：SSH fallback 成功')
        except Exception as exc:
            return f"\n【DB 快照取得失敗: {exc}】"

    if not tables:
        return '\n【DB 快照：無法取得，請手動確認現有表結構】'

    return (
        f"\n【⚠️ 現有資料庫快照（執行前必讀）】\n"
        f"資料庫: {d}\n"
        f"現有表清單（SHOW TABLES）：\n{tables}\n\n"
        f"⚠️ 設計前必須核對現有表結構，避免重複建表。\n"
        f"需查看特定表結構請執行：DESCRIBE <table_name>;"
    )


def build_prompt(agent: str, label: str, task: dict, task_file: Path, report_file: Path) -> str:
    task_id = task.get('task_id') or task.get('consult_id') or 'UNKNOWN'
    description = task.get('description') or task.get('supplemental_info') or task.get('reason') or ''
    task_type = task.get('type', 'task')

    # Context store（跨 session 記憶）
    ctx = read_context_store(task_id)
    ctx_section = ''
    if ctx['round'] > 0:
        history_lines = '\n'.join(
            f"  round {h.get('round','?')}: [{h.get('from','?')}] {h.get('summary','')[:120]}"
            for h in ctx['history']
        )
        ctx_section = f"\n【Context Store（跨 Session 記憶）】\n任務狀態: {ctx['status']}\n目前輪次: {ctx['round']}\n最近歷史:\n{history_lines}\n"

    # DB 任務自動附上現有資料庫快照
    db_section = get_db_snapshot(agent, description)

    # 注意：身份/角色文件由 codex 自動讀取工作目錄的 AGENTS.md，不在此塞進 prompt
    return f"""這是 HQ 自動派發任務，請依照你在 AGENTS.md 中的身份與規範完整執行，並產生可驗收回報。
{ctx_section}{db_section}
任務類型: {task_type}
任務 ID: {task_id}
任務檔案: {task_file}
任務描述:
{description}

要求：
1. 先讀取 AGENTS.md 確認身份與本任務相關的規範（特別是 WAW 2.0 設計規範）。
2. 先讀取任務檔案內容（{task_file}）。
3. 若有【現有資料庫快照】，設計前必須核對，不可設計已存在的表或欄位。
4. 若 Context Store 有歷史記錄，先理解前幾輪進度再繼續，不要重複已完成的步驟。
5. 依 AGENTS.md 中的職責範圍執行；若超出職責，明確回報 blocked 與原因。
6. 需要修改/部署/查證時，提供實際證明（log、API 回傳、DB 查詢、grep 結果）。
7. 完成後建立回報檔：{report_file}
8. 回報檔須包含：任務 ID、狀態 completed/blocked/needs_review、執行摘要、證明、後續風險。
9. 不要只口頭說完成；沒有證明就標 needs_review 或 blocked。
10. 完成後不需要自行呼叫回報腳本，HQ Gateway 會自動收集回報。
""".strip()

def execute_task(agent: str, label: str, work_dir: Path, task: dict, task_file: Path):
    if task.get('auto_execute') is False:
        log(agent, "⏸️  auto_execute=false，略過"); return
    task_id = task.get('task_id') or 'UNKNOWN'
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = work_dir / '_agent'
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f'REPORT_{ts}_{task_id}.md'
    prompt = build_prompt(agent, label, task, task_file, report_file)
    log(agent, f"🤖 codex exec → {task_id}")
    try:
        result = subprocess.run(
            [CODEX_BIN, 'exec', '--skip-git-repo-check', prompt],
            cwd=work_dir, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=EXEC_TIMEOUT,
        )
        output = result.stdout or ''; exit_code = result.returncode
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or b'').decode('utf-8', errors='replace') + f"\n\nTIMEOUT: exceeded {EXEC_TIMEOUT}s"; exit_code = 124
    except Exception as exc:
        output = f"自動執行失敗: {exc}"; exit_code = 1
    if not report_file.exists():
        status = 'completed' if exit_code == 0 else 'needs_review'
        report_file.write_text(
            f"# {label} 自動任務回報\n\n"
            f"> 任務 ID: {task_id}\n> 狀態: {status}\n> Exit code: {exit_code}\n"
            f"> 回報時間: {datetime.datetime.now().isoformat()}\n\n## Codex 輸出\n\n```\n{output[-12000:]}\n```\n",
            encoding='utf-8'
        )
    log(agent, f"📄 {report_file}")
    report_script = HQ_PATH / 'scripts' / 'agent_report_to_hq_v2.sh'
    if report_script.exists():
        subprocess.run(
            ['bash', str(report_script), agent, str(report_file), str(HQ_PATH)],
            cwd=work_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60,
        )
        log(agent, "📤 回報 HQ 完成")

REDIS_HOST, REDIS_PORT = 'localhost', 6379

# ── 工具 ────────────────────────────────────────────────────────────────────────

def now_iso(): return datetime.datetime.now().isoformat()

# ══════════════════════════════════════════════════════════════════════════════
#  Class 1: ContextStore
# ══════════════════════════════════════════════════════════════════════════════

def safe_json_loads(s):
    if not isinstance(s, str):
        return {"raw": s}
    s_stripped = s.strip()
    if not (s_stripped.startswith("{") or s_stripped.startswith("[")):
        return {"raw": s}
    try:
        return json.loads(s_stripped)
    except Exception:
        return {"raw": s}

class ContextStore:
    def __init__(self, r: redis.Redis):
        self.r = r

    def read_thread(self, thread_id: str) -> dict:
        k = f'hq:thread:{thread_id}'
        raw = self.r.lrange(f'{k}:history', 0, -1)
        history_list = []
        for h in raw:
            if h:
                # 兼容處理
                if isinstance(h, bytes):
                    h = h.decode('utf-8')
                history_list.append(safe_json_loads(h))
        return {
            'status': self.r.get(f'{k}:status') or 'unknown',
            'round': int(self.r.get(f'{k}:round') or 0),
            'agent': self.r.get(f'{k}:agent') or '',
            'description': self.r.get(f'{k}:description') or '',
            'history': history_list,
        }

    def append_history(self, thread_id: str, entry: dict):
        k = f'hq:thread:{thread_id}'
        self.r.rpush(f'{k}:history', json.dumps(entry, ensure_ascii=False))
        for field in ('status', 'round'):
            if field in entry:
                self.r.set(f'{k}:{field}', str(entry[field]))
        for sfx in (':status', ':round', ':agent', ':description', ':history'):
            self.r.expire(f'{k}{sfx}', 604800)

# ══════════════════════════════════════════════════════════════════════════════
#  Class 2: DecisionEngine
# ══════════════════════════════════════════════════════════════════════════════

class DecisionEngine:
    LLM_URL = f"{_9R_CONFIG['base_url']}/chat/completions"
    LLM_MODEL = _9R_CONFIG['model']
    LLM_API_KEY = _9R_CONFIG['api_key']
    SYSTEM_PROMPT = (
        "你是 HQ，wawIoT 遊藝場管理系統的協調者。\n"
        "判斷 Agent 的回報是否達到要求，並決定下一步行動。\n"
        "判斷必須嚴格、客觀，不接受模糊口頭承諾，需實際證明（log、截圖、API 回傳）。"
    )
    STATUS_PROMPTS = {
        'consulting': (
            "目前處於諮詢階段。判斷 Agent 回覆是否：\n"
            "1. 諮詢問題已完整回答，不需要進一步實作 → DECISION: approved\n"
            "2. 確認可行且需要進一步實作，必須嚴格依照原始描述範圍 → DECISION: task:<具體任務描述>\n"
            "3. 不可行或有重大風險 → DECISION: escalate:<原因>\n"
            "4. 回覆不夠完整需補充 → DECISION: supplement:<需要補充的問題>\n"

            "注意：若諮詢本身只是查詢（非要求實作），請優先使用 approved 結案。\n"
            "注意：若諮詢標記為 requires_review=true（設計型諮詢），系統會自動 escalate，無需 LLM 判斷。"
        ),
        'pending': (
            "目前處於實作驗收階段。判斷 Agent 回報是否：\n"
            "1. 提供實際證明且符合任務要求 → DECISION: approved\n"
            "2. 部分問題或缺少證明 → DECISION: redo:<具體指出哪裡不對>\n"
            "3. 超出能力範圍 → DECISION: escalate:<原因>"
        ),
        'redo_requested': (
            "目前處於重做驗收階段。判斷 Agent 回覆是否：\n"
            "1. 已修正並提供證明 → DECISION: approved\n"
            "2. 仍有問題 → DECISION: redo:<具體指出哪裡不對>\n"
            "3. 需補充資訊 → DECISION: supplement:<需要補充的問題>\n"
            "4. 超出能力範圍 → DECISION: escalate:<原因>"
        ),
    }

    def __init__(self, hq_path: Path, cs: ContextStore):
        self.hq_path, self.cs = hq_path, cs

    def decide(self, thread_id: str, from_agent: str, inbox_file: Path) -> str:
        thread = self.cs.read_thread(thread_id)
        # 已結案則跳過，避免無限循環
        if thread['status'] in ('resolved', 'approved'):
            log('gateway', f"⏭ {thread_id} 已結案 ({thread['status']})，跳過")
            return 'skip'
        # 讀回報全文
        try:
            report = inbox_file.read_text(encoding='utf-8')
        except FileNotFoundError:
            self._escalate(thread_id, from_agent, f'回報檔案不存在: {inbox_file}', '')
            return 'escalate'
        # 呼叫 LLM
        try:
            llm_resp = self._call_llm(self._build_prompt(thread, report, thread['status']))
        except Exception as exc:
            log('gateway', f'❌ LLM 失敗: {exc}')
            self._escalate(thread_id, from_agent, f'LLM 失敗: {exc}', '')
            return 'escalate'
        dtype, content = self._parse(llm_resp)
        self.cs.append_history(thread_id, {
            'round': thread['round'] + 1, 'from': 'Gateway',
            'action': 'llm_decision', 'decision': dtype,
            'summary': f"LLM 決策: {dtype} - {content[:100]}", 'ts': now_iso(),
        })
        self._execute(dtype, content, from_agent, thread_id)
        return dtype

    def _build_prompt(self, thread: dict, report: str, status: str) -> str:
        hist = '\n'.join(
            f"Round {h.get('round','?')} [{h.get('from','?')}/{h.get('action','?')}]: "
            f"{h.get('summary','')}" + (f"  檔案：{h['file']}" if h.get('file') else '')
            for h in thread.get('history', [])
        ) or '（尚無歷史）'
        
        # 截斷過長的回報內容（保留前 2000 字 + 後 500 字）
        MAX_REPORT_LEN = 2000
        if len(report) > MAX_REPORT_LEN:
            report_preview = report[:2000] + f"\n\n[... 中間省略 {len(report) - 2500} 字 ...]\n\n" + report[-500:]
        else:
            report_preview = report
        return '\n\n'.join([
            f"【系統角色】\n{self.SYSTEM_PROMPT}",
            f"【任務背景】\n諮詢/任務 ID：{thread.get('description','（無描述）')[:20]}\nAgent：{thread.get('agent','?')}\n原始描述：{thread.get('description','（無）')}\n\n⚠️ 重要：若判斷為 task，任務描述必須嚴格限制在原始描述的範圍內，不可自行擴充。",
            f"【完整對話歷史】\n{hist}",
            f"【本次回報摘要】\n{report_preview}",
            f"【判斷指令】\n{self.STATUS_PROMPTS.get(status, self.STATUS_PROMPTS['consulting'])}\n\n請在回覆最後一行寫：DECISION: <決策>",
        ])

    def _call_llm(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.LLM_API_KEY}",
        }
        r = requests.post(self.LLM_URL, headers=headers,
                          json={"model": self.LLM_MODEL,
                                "messages": [{"role": "user", "content": prompt}],
                                "max_tokens": 2048, "stream": False},
                          timeout=(10, 300))
        r.raise_for_status()
        data = r.json()
        return data['choices'][0]['message']['content']

    def _parse(self, resp: str) -> tuple:
        for line in reversed(resp.strip().split('\n')):
            line = line.strip()
            if line.startswith('DECISION:'):
                d = line[len('DECISION:'):].strip()
                for p in ('task:', 'redo:', 'supplement:', 'escalate:'):
                    if d.startswith(p):
                        return p.rstrip(':'), d[len(p):].strip()
                return ('approved', '') if d == 'approved' else ('escalate', f'格式不符: {d}')
        return ('escalate', f'LLM 無 DECISION 標記: {resp[:200]}')

    def _execute(self, dtype: str, content: str, agent: str, tid: str):
        # 從 consult_id 衍生固定的 task_id，不疊加底線
        base_id = tid.split('_TASK')[0]  # 取 CONS_... 部分
        task_id = base_id.replace('CONS_', 'TASK_', 1) if base_id.startswith('CONS_') else f'{base_id}_TASK'

        flow = self.hq_path / 'scripts' / 'hq_task_flow.sh'
        cmds = {
            'approved':  ['bash', str(flow), 'approve', agent, tid],
            'task':      ['bash', str(flow), 'task', agent, task_id, content, 'high'],
            'redo':      ['bash', str(flow), 'redo', agent, tid, content],
            'supplement':['bash', str(flow), 'supplement', agent, tid, content],
        }
        if dtype in cmds:
            subprocess.run(cmds[dtype], cwd=str(self.hq_path), text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
            log('gateway', f"✅ {dtype} → hq_task_flow.sh {dtype} {agent} {tid}")
            # approved 結案，寫入 resolved 讓後續回報跳過
            if dtype == 'approved':
                rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
                rc.set(f'hq:thread:{tid}:status', 'resolved')
                rc.close()
                log('gateway', f"🔒 {tid} 已標記 resolved")
        elif dtype == 'escalate':
            self._escalate(tid, agent, content, '')

    def _escalate(self, tid: str, agent: str, reason: str, llm_resp: str):
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        fp = self.hq_path / '_agent' / f'HQ_ESCALATE_{tid}_{ts}.md'
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(f"# ⚠️ HQ Escalate\n\n- ID: {tid}\n- Agent: {agent}\n"
                      f"- 原因: {reason}\n- 時間: {now_iso()}\n\n"
                      f"## LLM 回覆\n```\n{llm_resp[:2000]}\n```\n", encoding='utf-8')
        log('gateway', f"🚨 escalate → {fp.name}")
        self._mac_notify(f"⚠️ HQ 需要審核", f"{agent} / {tid}\n{reason[:80]}")
        self._telegram_notify(f"⚠️ HQ 需要審核", f"Agent: {agent}\nID: {tid}\n{reason[:120]}")

    def _mac_notify(self, title: str, message: str):
        try:
            subprocess.run([
                'osascript', '-e',
                f'display notification "{message}" with title "{title}" sound name "Glass"'
            ], timeout=5)
            log('gateway', f"🔔 Mac 通知已發送: {title}")
        except Exception as exc:
            log('gateway', f"⚠️ Mac 通知失敗: {exc}")

    def _telegram_notify(self, title: str, message: str):
        BOT_TOKEN = "8669253700:AAGzsPKlawjhDSnamtHLUKAoblJ2Mg7R0G4"
        CHAT_ID   = "1367155154"
        text = f"⚠️ HQ Autoflow\n{title}\n{message}"
        try:
            # 用 curl 避免 .venv SSL 憑證問題
            subprocess.run([
                'curl', '-s', '-X', 'POST',
                f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
                '-d', f'chat_id={CHAT_ID}&text={text}'
            ], timeout=10)
            log('gateway', f"📱 Telegram 通知已發送: {title}")
        except Exception as exc:
            log('gateway', f"⚠️ Telegram 通知失敗: {exc}")

# ══════════════════════════════════════════════════════════════════════════════
#  Class 3: GatewayListener
# ══════════════════════════════════════════════════════════════════════════════

class GatewayListener:
    PATTERNS = ['agent/*/task', 'agent/*/consultation', 'agent/*/report',
                'agent/*/supplement', 'agent/*/redo', 'agent/*/approval']

    def __init__(self, hq_path, cs: ContextStore, de: DecisionEngine, stop: threading.Event):
        self.hq_path, self.cs, self.de, self.stop = hq_path, cs, de, stop

    def on_task(self, agent: str, payload: dict):
        cfg = AGENTS.get(agent)
        if not cfg:
            log('gateway', f"⚠️ 未知 Agent: {agent}"); return
        work_dir = Path(cfg['work_dir'])
        task_file = save_task_file(agent, payload, work_dir)
        threading.Thread(target=execute_task, args=(agent, cfg['label'], work_dir, payload, task_file), daemon=True).start()
        tid = payload.get('task_id') or payload.get('consult_id') or 'UNKNOWN'
        self.cs.append_history(tid, {'round': 0, 'from': 'Gateway', 'action': 'task_triggered',
                                     'summary': f"codex exec 已觸發: {agent}", 'ts': now_iso()})
        log(agent, f"📨 收到任務: {tid}")

    def on_consultation(self, agent: str, payload: dict):
        cfg = AGENTS.get(agent)
        if not cfg:
            log('gateway', f"⚠️ 未知 Agent: {agent}"); return
        work_dir = Path(cfg['work_dir'])
        task_file = save_task_file(agent, payload, work_dir)
        threading.Thread(target=execute_task, args=(agent, cfg['label'], work_dir, payload, task_file), daemon=True).start()
        cid = payload.get('consult_id') or 'UNKNOWN'
        self.cs.append_history(cid, {'round': 0, 'from': 'Gateway', 'action': 'consultation_dispatched',
                                     'summary': f"諮詢已觸發 {agent} 執行", 'ts': now_iso()})
        log(agent, f"📨 收到諮詢: {cid}")

    # 需要人工審核的關鍵詞（匹配到就走 escalate，不自動決策）


    def _needs_review(self, payload: dict, inbox_file) -> bool:
        """判斷這份諮詢是否需要人工審核（設計型 vs 查詢型）"""
        # 優先檢查 payload 中的 requires_review 旗標
        if "requires_review" in payload:
            return payload["requires_review"] is True or payload["requires_review"] == "true"
        # 向下相容：檢查 thread context（若從 Redis 讀出）
        tid = payload.get("task_id") or payload.get("consult_id")
        if tid:
            thread = self.cs.read_thread(tid)
            if thread.get("requires_review") is True:
                return True
        # 預設為查詢型，不需審核
        return False

    def on_report(self, agent: str, payload: dict, channel: str):
        tid = payload.get('task_id') or payload.get('consult_id') or payload.get('report_file', '') or 'UNKNOWN'
        # 存 inbox
        inbox_dir = self.hq_path / '_agent' / 'inbox'
        inbox_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        inbox_file = inbox_dir / f'{ts}_{agent}_auto.json'
        inbox_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
        log('gateway', f'✅ 存檔: {inbox_file.name}')
        # 更新 context store
        thread = self.cs.read_thread(tid)
        self.cs.append_history(tid, {'round': thread['round'] + 1, 'from': agent,
                                     'action': 'report', 'summary': str(payload)[:200],
                                     'file': str(inbox_file), 'ts': now_iso()})
        log('gateway', f'📬 收到 {agent} 回報  任務: {tid}')
        try:
            import hq_tg_notifier as tg
            tg.send_telegram("任務回報", f"Agent {agent} 已交卷！任務 ID: {tid}")
        except Exception:
            pass  # Telegram 通知失敗不影響主流程
        # 設計型諮詢（requires_review=true）→ 直接 escalate，不走 LLM 自動決策
        if self._needs_review(payload, inbox_file):
            log('gateway', f'📋 設計型諮詢（requires_review=true），直接通知 Joe')
            self.de._escalate(tid, agent, '設計型諮詢完成，等待 Joe 審核', '')
        else:
            try:
                self.de.decide(tid, agent, inbox_file)
            except Exception as e:
                log('gateway', f'❌ decide 執行失敗: {e}')
                try:
                    self.de._escalate(tid, agent, f'自動決策執行期異常: {e}', '')
                except Exception:
                    pass

    def on_supplement(self, agent: str, payload: dict):
        tid = payload.get('task_id') or payload.get('consult_id') or 'UNKNOWN'
        self.cs.append_history(tid, {'round': 0, 'from': 'Gateway', 'action': 'supplement_received',
                                     'summary': f"補充資訊已轉發給 {agent}", 'ts': now_iso()})
        log(agent, f"📨 收到 supplement: {tid}")

    def run(self):
        log('gateway', f'🎧 訂閱: {self.PATTERNS}')
        while not self.stop.is_set():
            try:
                client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
                client.ping()
                pubsub = client.pubsub()
                pubsub.psubscribe(*self.PATTERNS)
                log('gateway', '✅ Redis 已連線')
                for msg in pubsub.listen():
                    if self.stop.is_set(): break
                    if msg['type'] != 'pmessage': continue
                    parts = msg['channel'].split('/')
                    agent, mtype = (parts[1].lower(), parts[2].lower()) if len(parts) >= 3 else ("unknown", "unknown")
                    try:
                        payload = json.loads(msg['data'])
                    except (json.JSONDecodeError, TypeError):
                        payload = {'raw': str(msg['data'])}
                    handlers = {
                        'task': lambda: self.on_task(agent, payload),
                        'consultation': lambda: self.on_consultation(agent, payload),
                        'report': lambda: self.on_report(agent, payload, msg['channel']),
                        'supplement': lambda: self.on_supplement(agent, payload),
                        'redo': lambda: self.on_task(agent, payload),
                        'approval': lambda: log('gateway', f"✅ approval 通知已收到 ({agent})，不觸發執行"),
                    }
                    handler = handlers.get(mtype)
                    if handler:
                        threading.Thread(target=handler, daemon=True).start()
                    else:
                        log('gateway', f"⚠️ 未知類型: {mtype}")
                pubsub.close(); client.close()
            except redis.ConnectionError:
                log('gateway', '❌ Redis 斷線，5s 後重試...'); self.stop.wait(5)
            except Exception as exc:
                log('gateway', f'❌ 錯誤: {exc}，5s 後重試...'); self.stop.wait(5)

# ── 主程式 ──────────────────────────────────────────────────────────────────────

def main():
    stop = threading.Event()
    # 確保只有一個 hq_gateway 實例運行
    lock_file = os.path.join(os.path.dirname(__file__), "..", "logs", "hq_gateway.pid")
    ensure_singleton(lock_file)

    def _shutdown(sig, frame):
        print("\n\n👋 正在停止 Gateway...", flush=True); stop.set()
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    try:
        rc.ping()
    except redis.ConnectionError:
        print("❌ Redis 無法連線", flush=True); sys.exit(1)

    cs = ContextStore(rc)
    de = DecisionEngine(HQ_PATH, cs)
    gw = GatewayListener(HQ_PATH, cs, de, stop)

    print("=" * 55)
    print("  HQ Gateway")
    print(f"  Redis: {REDIS_HOST}:{REDIS_PORT}")
    print(f"  LLM:   {DecisionEngine.LLM_URL}")
    print(f"  Model: {DecisionEngine.LLM_MODEL}")
    print(f"  Agents: {', '.join(AGENTS.keys())}")
    print("=" * 55)
    gw.run()
    print("✅ Gateway 已停止", flush=True)

if __name__ == '__main__':
    main()
