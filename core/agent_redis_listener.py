#!/usr/bin/env python3
"""
Agent Redis 監聽腳本
用途：監聽 HQ 發布的任務通知
使用方式：python agent_redis_listener.py <agent_name>
"""
import sys
import json
import datetime
import signal
import os
import subprocess
from pathlib import Path

# Redis 支援
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("❌ Redis 套件未安裝")
    print("   安裝方式: pip install redis")
    sys.exit(1)

class AgentRedisListener:
    """Agent Redis 訂閱監聽器"""
    
    def __init__(self, agent_name: str, redis_host: str = 'localhost', redis_port: int = 6379):
        self.agent_name = agent_name.lower()
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client = None
        self.pubsub = None
        self.running = False
        self.codex_bin = os.environ.get('CODEX_BIN', '/opt/homebrew/bin/codex')
        self.exec_timeout = int(os.environ.get('AGENT_EXEC_TIMEOUT', '900'))
        self.hq_path = Path(os.environ.get('HQ_PATH', str(Path.cwd().parent / 'HQ')))
        
        # 訂閱頻道
        self.channels = [
            f'agent/{self.agent_name}/*',  # agent/sophie/*
            f'hq/events/agent/{self.agent_name}/*'  # hq/events/agent/sophie/*
        ]
    
    def start(self):
        """啟動監聽"""
        print(f"🎧 {self.agent_name.upper()} Redis 監聽器啟動中...")
        print(f"   Redis: {self.redis_host}:{self.redis_port}")
        print()
        
        try:
            # 連接 Redis
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True
            )
            
            # 測試連線
            self.redis_client.ping()
            print(f"✅ Redis 連線成功")
            
            # 建立 Pub/Sub
            self.pubsub = self.redis_client.pubsub()
            
            # 訂閱頻道
            self.pubsub.psubscribe(*self.channels)
            
            # 等待訂閱確認
            for message in self.pubsub.listen():
                if message["type"] == "psubscribe":
                    break
            
            print(f"✅ 訂閱頻道:")
            for channel in self.channels:
                print(f"   - {channel}")
            print()
            print("🎧 開始監聽...")
            print("   按 Ctrl+C 停止")
            print()
            
            self.running = True
            
            # 監聽迴圈
            for message in self.pubsub.listen():
                if not self.running:
                    break
                
                if message['type'] == 'pmessage':
                    self._handle_message(message)
        
        except redis.ConnectionError:
            print(f"❌ 無法連接 Redis ({self.redis_host}:{self.redis_port})")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n\n👋 停止監聽...")
            self.stop()
        except Exception as e:
            print(f"❌ 監聽失敗: {e}")
            sys.exit(1)
    
    def _handle_message(self, message: dict):
        """處理收到的訊息"""
        channel = message['channel']
        data = message['data']
        
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"[{timestamp}] 📬 收到訊息")
        print(f"   頻道: {channel}")
        
        # 解析 JSON
        try:
            task = json.loads(data) if isinstance(data, str) else data
            print(f"   任務ID: {task.get('task_id', 'N/A')}")
            print(f"   描述: {task.get('description', 'N/A')}")
            
            # 儲存到本地
            task_file = self._save_task(task)
            self._execute_task(task, task_file)
            
        except json.JSONDecodeError:
            print(f"   內容: {data}")
        
        print()
    
    def _save_task(self, task: dict) -> Path:
        """儲存任務到本地"""
        inbox_dir = Path('_agent')
        inbox_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        task_id = task.get('task_id', 'UNKNOWN')
        filename = f'REDIS_{timestamp}_{task_id}.json'
        
        filepath = inbox_dir / filename
        filepath.write_text(json.dumps(task, indent=2, ensure_ascii=False))
        
        print(f"   ✅ 已存入: {filepath}")
        return filepath

    def _execute_task(self, task: dict, task_file: Path):
        """自動執行任務並回報 HQ"""
        if task.get('auto_execute') is False:
            print("   ⏸️ 任務標記 auto_execute=false，略過自動執行")
            return

        task_id = task.get('task_id') or task.get('consult_id') or 'UNKNOWN'
        description = task.get('description') or task.get('supplemental_info') or task.get('reason') or ''
        task_type = task.get('type', 'task')

        report_dir = Path('_agent')
        report_dir.mkdir(exist_ok=True)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f'REPORT_{timestamp}_{task_id}.md'

        prompt = f"""
你是 {self.agent_name} Agent。這是 HQ Message Hub 自動派發任務，請完整自動執行並產生可驗收回報。

任務類型: {task_type}
任務 ID: {task_id}
任務檔案: {task_file}
任務描述:
{description}

要求：
1. 先讀取任務檔案內容。
2. 依本 Agent 職責範圍執行；若超出職責，明確回報 blocked 與原因。
3. 需要修改/部署/查證時，提供實際證明，例如 log、API 回傳、DB 查詢、grep 結果或檔案路徑。
4. 完成後建立回報檔：{report_file}
5. 回報檔必須包含：任務 ID、狀態 completed/blocked/needs_review、執行摘要、證明、後續風險。
6. 不要只口頭說完成；沒有證明就標 needs_review 或 blocked。
""".strip()

        print(f"   🤖 自動執行 Codex: {task_id}")
        try:
            result = subprocess.run(
                [
                    self.codex_bin,
                    'exec',
                    '--skip-git-repo-check',
                    prompt,
                ],
                cwd=Path.cwd(),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=self.exec_timeout,
            )
            output = result.stdout or ''
            exit_code = result.returncode
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or '') + f"\n\nTIMEOUT: exceeded {self.exec_timeout}s"
            exit_code = 124
        except Exception as exc:
            output = f"自動執行失敗: {exc}"
            exit_code = 1

        if not report_file.exists():
            status = 'completed' if exit_code == 0 else 'needs_review'
            report_file.write_text(
                f"# {self.agent_name} 自動任務回報\n\n"
                f"> 任務 ID: {task_id}\n"
                f"> 狀態: {status}\n"
                f"> Exit code: {exit_code}\n"
                f"> 回報時間: {datetime.datetime.now().isoformat()}\n\n"
                f"## Codex 輸出\n\n```\n{output[-12000:]}\n```\n",
                encoding='utf-8'
            )

        print(f"   📄 回報檔: {report_file}")
        self._report_to_hq(report_file)

    def _report_to_hq(self, report_file: Path):
        """使用 HQ v2 回報腳本回報"""
        report_script = self.hq_path / 'scripts' / 'agent_report_to_hq_v2.sh'
        if not report_script.exists():
            print(f"   ❌ 找不到 HQ 回報腳本: {report_script}")
            return

        print("   📤 自動回報 HQ")
        result = subprocess.run(
            ['bash', str(report_script), self.agent_name, str(report_file), str(self.hq_path)],
            cwd=Path.cwd(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60,
        )
        print(result.stdout)
    
    def stop(self):
        """停止監聽"""
        self.running = False
        
        if self.pubsub:
            try:
                self.pubsub.unsubscribe()
                self.pubsub.close()
            except:
                pass
        
        if self.redis_client:
            try:
                self.redis_client.close()
            except:
                pass
        
        print("✅ 監聽已停止")

def main():
    """主程式"""
    if len(sys.argv) < 2:
        print("❌ 缺少 Agent 名稱")
        print("使用方式: python agent_redis_listener.py <agent_name>")
        print("範例: python agent_redis_listener.py sophie")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    
    # 建立監聽器
    listener = AgentRedisListener(agent_name)
    
    # 啟動
    listener.start()

if __name__ == '__main__':
    main()
