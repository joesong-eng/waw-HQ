"""
Message Hub v2.0 - HTTP 伺服器模組
提供 HTTP API，保持向下相容
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import datetime
from pathlib import Path
from typing import Optional

class MessageHandler(BaseHTTPRequestHandler):
    """HTTP 請求處理器"""
    
    # 類別變數：任務管理器（由主程式注入）
    task_manager = None
    event_queue = None
    
    def log_message(self, format, *args):
        """自定義日誌格式"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {format % args}")
    
    def do_POST(self):
        """處理 POST 請求 - Agent 回報"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            agent_name = data.get('from_agent', 'unknown')
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 寫入收件匣
            inbox_dir = Path('.taskbox/inbox')
            inbox_dir.mkdir(parents=True, exist_ok=True)
            inbox_file = inbox_dir / f'{timestamp}_{agent_name}.json'
            inbox_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            
            print(f"✅ 收到 {agent_name} 的回報")
            
            # 回應成功
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'received',
                'agent': agent_name,
                'timestamp': timestamp
            }).encode())
            
        except Exception as e:
            print(f"❌ 處理 POST 失敗: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'error',
                'message': str(e)
            }).encode())
    
    def do_GET(self):
        """處理 GET 請求 - 查詢任務、狀態"""
        try:
            path_parts = self.path.strip('/').split('/')
            
            # /tasks/<agent> - Agent 查詢任務
            if len(path_parts) == 2 and path_parts[0] == 'tasks':
                self._handle_get_tasks(path_parts[1])
            
            # /status - 系統狀態
            elif self.path == '/status':
                self._handle_get_status()
            
            # /agents - Agent 列表
            elif self.path == '/agents':
                self._handle_get_agents()
            
            # 404
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'not_found',
                    'message': 'Endpoint not found'
                }).encode())
        
        except Exception as e:
            print(f"❌ 處理 GET 失敗: {e}")
            self.send_response(500)
            self.end_headers()
    
    def _handle_get_tasks(self, agent_name: str):
        """處理 /tasks/<agent> 請求"""
        agent = agent_name.lower()
        
        if self.task_manager:
            tasks = self.task_manager.get_pending_tasks(agent)
            
            if tasks:
                print(f"📤 發送任務給 {agent} ({len(tasks)} 個)")
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(tasks, ensure_ascii=False).encode())
            else:
                print(f"📭 {agent} 目前無待辦任務")
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'no_tasks',
                    'message': f'No pending tasks for {agent}'
                }).encode())
        else:
            # 降級：直接讀檔案（v1.0 相容模式）
            self._handle_get_tasks_legacy(agent)
    
    def _handle_get_tasks_legacy(self, agent_name: str):
        """v1.0 相容模式：直接讀取 outbox 檔案"""
        outbox_file = Path(f'.taskbox/outbox/to_{agent_name}.json')
        
        if outbox_file.exists():
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(outbox_file.read_bytes())
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'no_tasks',
                'message': f'No pending tasks for {agent_name}'
            }).encode())
    
    def _handle_get_status(self):
        """處理 /status 請求"""
        inbox_count = len(list(Path('.taskbox/inbox').glob('*.json'))) if Path('.taskbox/inbox').exists() else 0
        outbox_count = len(list(Path('.taskbox/outbox').glob('*.json'))) if Path('.taskbox/outbox').exists() else 0
        
        status = {
            'status': 'running',
            'version': '2.0',
            'redis_enabled': self._is_redis_available(),
            'inbox_count': inbox_count,
            'outbox_count': outbox_count,
            'event_queue_size': self.event_queue.qsize() if self.event_queue else 0,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        if self.task_manager:
            status['agents_status'] = self.task_manager.get_all_agents_status()
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(status, indent=2).encode())
    
    def _handle_get_agents(self):
        """處理 /agents 請求 - 列出所有 Agent 狀態"""
        if self.task_manager:
            agents_status = self.task_manager.get_all_agents_status()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(agents_status, indent=2).encode())
        else:
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'unavailable',
                'message': 'Task manager not initialized'
            }).encode())
    
    def _is_redis_available(self) -> bool:
        """檢查 Redis 是否可用"""
        try:
            import redis
            return True
        except ImportError:
            return False

def create_http_server(host: str, port: int, task_manager=None, event_queue=None) -> HTTPServer:
    """
    建立 HTTP 伺服器
    
    Args:
        host: 主機位址
        port: 埠號
        task_manager: 任務管理器實例
        event_queue: 事件佇列
    
    Returns:
        HTTPServer 實例
    """
    # 注入依賴
    MessageHandler.task_manager = task_manager
    MessageHandler.event_queue = event_queue
    
    return HTTPServer((host, port), MessageHandler)
