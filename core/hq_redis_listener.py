#!/usr/bin/env python3
"""
HQ Redis 監聽腳本（HQ 分身）
職責：純觸發和搬運，不做任何分析決策
  1. 監聽 agent/*/report
  2. 存檔 inbox
  3. 更新 context store（機械性）
  4. 派子代理執行 skill: analyse_agent_report
"""
import sys
import json
import datetime
import signal
import os
import subprocess
from pathlib import Path

try:
    import redis
except ImportError:
    print("❌ Redis 套件未安裝，請執行 pip install redis")
    sys.exit(1)

HQ_PATH   = Path(os.environ.get('HQ_PATH', Path(__file__).parent.parent))
CODEX_BIN = os.environ.get('CODEX_BIN', '/opt/homebrew/bin/codex')
EXEC_TIMEOUT = int(os.environ.get('AGENT_EXEC_TIMEOUT', '900'))
SKILL_FILE = HQ_PATH / 'skills' / 'hq_ops' / 'analyse_agent_report.md'

SUBSCRIBE_PATTERNS = [
    'agent/*/report',
    'hq/events/agent/*/report',
]


class HQRedisListener:
    """HQ 分身：純監聽器，收到回報就存檔 + 派子代理"""

    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client = None
        self.pubsub = None
        self.running = False

    # ── 啟動 / 停止 ──────────────────────────────

    def start(self):
        print("🏠 HQ 分身啟動中...")
        print(f"   Redis: {self.redis_host}:{self.redis_port}")
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host, port=self.redis_port, decode_responses=True)
            self.redis_client.ping()
            print("✅ Redis 連線成功")

            self.pubsub = self.redis_client.pubsub()
            self.pubsub.psubscribe(*SUBSCRIBE_PATTERNS)
            for msg in self.pubsub.listen():
                if msg['type'] == 'psubscribe':
                    break

            print("✅ 訂閱頻道：")
            for ch in SUBSCRIBE_PATTERNS:
                print(f"   - {ch}")
            print("\n🎧 HQ 分身就緒，等待 Agent 回報...\n")

            self.running = True
            signal.signal(signal.SIGTERM, self._handle_signal)
            signal.signal(signal.SIGINT,  self._handle_signal)

            for msg in self.pubsub.listen():
                if not self.running:
                    break
                if msg['type'] == 'pmessage':
                    self._handle_report(msg)

        except redis.ConnectionError:
            print(f"❌ 無法連接 Redis ({self.redis_host}:{self.redis_port})")
            sys.exit(1)

    def stop(self):
        self.running = False
        try:
            self.pubsub and self.pubsub.close()
            self.redis_client and self.redis_client.close()
        except Exception:
            pass
        print("✅ HQ 分身已停止")

    def _handle_signal(self, signum, frame):
        print(f"\n收到信號 {signum}，停止...")
        self.stop()
        sys.exit(0)

    # ── 處理回報（純搬運）────────────────────────

    def _handle_report(self, msg: dict):
        channel = msg['channel']
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{ts}] 📬 收到回報  頻道: {channel}")

        # 解析來源 agent
        parts = channel.split('/')
        from_agent = parts[1] if len(parts) >= 3 else 'unknown'

        try:
            report = json.loads(msg['data'])
        except (json.JSONDecodeError, TypeError):
            report = {'raw': str(msg['data'])}

        task_id = (report.get('task_id')
                   or report.get('report_file', '')
                   or 'UNKNOWN')
        print(f"   來源: {from_agent}  任務: {task_id}")

        # 1. 存檔
        inbox_file = self._save_inbox(from_agent, report)

        # 2. context store：機械性更新輪次
        thread_key = f"hq:thread:{task_id}"
        self._tick_context(thread_key, from_agent, report)

        # 3. 派子代理執行 skill
        self._spawn_subagent(from_agent, task_id, inbox_file, thread_key)
        print()

    # ── 存檔 ─────────────────────────────────────

    def _save_inbox(self, from_agent: str, report: dict) -> Path:
        inbox_dir = HQ_PATH / '_agent' / 'inbox'
        inbox_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        fp = inbox_dir / f"{ts}_{from_agent}_auto.json"
        fp.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"   ✅ 存檔: {fp.name}")
        return fp

    # ── context store（機械性）───────────────────

    def _tick_context(self, thread_key: str, from_agent: str, report: dict):
        round_num = int(self.redis_client.get(f"{thread_key}:round") or 0) + 1
        self.redis_client.set(f"{thread_key}:round", round_num)
        self.redis_client.set(f"{thread_key}:last_from", from_agent)
        entry = {
            'round': round_num,
            'from': from_agent,
            'ts': datetime.datetime.utcnow().isoformat(),
            'summary': str(report)[:300],
        }
        self.redis_client.rpush(
            f"{thread_key}:history",
            json.dumps(entry, ensure_ascii=False)
        )
        print(f"   📝 context store round={round_num}")

    # ── 派子代理（只傳資訊，分析由 skill 負責）──

    def _spawn_subagent(self, from_agent: str, task_id: str,
                        inbox_file: Path, thread_key: str):
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        reply_file = HQ_PATH / '_agent' / f'HQ_REPLY_{ts}_{task_id}.md'

        skill_content = SKILL_FILE.read_text(encoding='utf-8') if SKILL_FILE.exists() else ''

        prompt = f"""
【HQ 子代理任務】
你是 HQ 子代理，負責分析 Agent 回報並決策。
請依照以下 skill 說明執行：

{skill_content}

【本次回報資訊】
- 來源 Agent：{from_agent}
- 任務 ID：{task_id}
- 回報檔案：{inbox_file}
- Context Store key：{thread_key}
- 回覆檔案請寫入：{reply_file}
- HQ 路徑：{HQ_PATH}
""".strip()

        print(f"   🤖 派子代理執行 skill: analyse_agent_report")
        try:
            result = subprocess.run(
                [CODEX_BIN, 'exec', '--skip-git-repo-check', prompt],
                cwd=str(HQ_PATH),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=EXEC_TIMEOUT,
            )
            exit_code = result.returncode
            output = result.stdout or ''
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or '') + f"\nTIMEOUT: {EXEC_TIMEOUT}s"
            exit_code = 124
        except Exception as exc:
            output = f"子代理失敗: {exc}"
            exit_code = 1

        print(f"   {'✅' if exit_code == 0 else '⚠️'} 子代理完成 (exit={exit_code})")

        if not reply_file.exists():
            reply_file.write_text(
                f"# HQ 子代理回覆\n\n"
                f"- 任務：{task_id}\n- 來源：{from_agent}\n"
                f"- exit：{exit_code}\n\n```\n{output[-3000:]}\n```\n",
                encoding='utf-8'
            )
        print(f"   📄 回覆檔：{reply_file.name}")


def main():
    HQRedisListener().start()


if __name__ == '__main__':
    main()
