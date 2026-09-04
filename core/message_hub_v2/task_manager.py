"""
Message Hub v2.0 - 任務管理模組
負責產生任務並寫入 Agent 的 outbox
"""
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional

class TaskManager:
    """任務管理器"""
    
    def __init__(self, outbox_dir: str = '.taskbox/outbox', log_dir: str = '_agent/event_logs'):
        self.outbox_dir = Path(outbox_dir)
        self.log_dir = Path(log_dir)
        
        # 建立必要目錄
        self.outbox_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def create_task(self, agent_name: str, event: Dict) -> str:
        """
        為指定 Agent 建立任務
        
        Args:
            agent_name: Agent 名稱 (sophie, ina, mina...)
            event: 觸發事件 {'source': 'redis', 'channel': '...', 'data': {...}}
        
        Returns:
            task_id: 產生的任務 ID
        """
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        task_id = f"AUTO_{timestamp}_{agent_name.upper()}"
        
        # 解析事件內容
        source = event.get('source', 'unknown')
        channel = event.get('channel', 'N/A')
        data = event.get('data', {})
        event_timestamp = event.get('timestamp', datetime.datetime.now().isoformat())
        
        # 建立任務描述
        description = self._generate_description(source, channel, data)
        
        # 建立任務物件
        task = {
            'task_id': task_id,
            'to_agent': agent_name,
            'source': 'auto_event',
            'trigger': {
                'source': source,
                'channel': channel,
                'timestamp': event_timestamp
            },
            'priority': self._determine_priority(event),
            'description': description,
            'event_data': data,
            'published_at': datetime.datetime.now().isoformat(),
            'auto_generated': True
        }
        
        # 寫入 outbox
        self._write_to_outbox(agent_name, task)
        
        # 記錄日誌
        self._log_task_creation(task_id, agent_name, event)
        
        return task_id
    
    def _generate_description(self, source: str, channel: str, data: Dict) -> str:
        """產生任務描述"""
        if source == 'redis':
            return f'Redis 事件觸發 (頻道: {channel})'
        elif source == 'websocket':
            event_type = data.get('event_type', 'unknown')
            return f'WebSocket 事件觸發 (類型: {event_type})'
        elif source == 'mqtt':
            topic = data.get('topic', 'unknown')
            return f'MQTT 訊息觸發 (主題: {topic})'
        else:
            return f'自動觸發任務 (來源: {source})'
    
    def _determine_priority(self, event: Dict) -> str:
        """判斷任務優先級"""
        data = event.get('data', {})
        channel = event.get('channel', '')
        
        # 高優先級：錯誤、離線、警報
        high_keywords = ['error', 'offline', 'alarm', 'alert', 'critical']
        for keyword in high_keywords:
            if keyword in channel.lower() or keyword in str(data).lower():
                return 'high'
        
        # 中優先級：狀態變更、支付
        medium_keywords = ['status', 'payment', 'transaction']
        for keyword in medium_keywords:
            if keyword in channel.lower() or keyword in str(data).lower():
                return 'medium'
        
        # 低優先級：其他
        return 'low'
    
    def _write_to_outbox(self, agent_name: str, task: Dict):
        """寫入 Agent 的 outbox"""
        outbox_file = self.outbox_dir / f'to_{agent_name}.json'
        
        # 如果已有任務，合併成陣列
        if outbox_file.exists():
            try:
                existing_content = outbox_file.read_text()
                existing = json.loads(existing_content)
                
                # 處理單一任務或任務陣列
                if isinstance(existing, list):
                    tasks = existing
                else:
                    tasks = [existing]
                
                # 新增任務
                tasks.append(task)
                
            except (json.JSONDecodeError, Exception) as e:
                print(f"⚠️  讀取 {outbox_file.name} 失敗，覆寫為新任務: {e}")
                tasks = [task]
        else:
            tasks = [task]
        
        # 寫入檔案
        outbox_file.write_text(json.dumps(tasks, indent=2, ensure_ascii=False))
    
    def _log_task_creation(self, task_id: str, agent_name: str, event: Dict):
        """記錄任務建立日誌"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.log_dir / f'{timestamp}_task_{agent_name}.json'
        
        log_entry = {
            'task_id': task_id,
            'agent': agent_name,
            'event': event,
            'created_at': datetime.datetime.now().isoformat()
        }
        
        log_file.write_text(json.dumps(log_entry, indent=2, ensure_ascii=False))
    
    def get_pending_tasks(self, agent_name: str) -> Optional[List[Dict]]:
        """
        取得指定 Agent 的待辦任務
        
        Args:
            agent_name: Agent 名稱
        
        Returns:
            任務列表，無任務時返回 None
        """
        outbox_file = self.outbox_dir / f'to_{agent_name}.json'
        
        if not outbox_file.exists():
            return None
        
        try:
            content = outbox_file.read_text()
            tasks = json.loads(content)
            
            # 統一返回列表格式
            if isinstance(tasks, list):
                return tasks
            else:
                return [tasks]
        except Exception as e:
            print(f"❌ 讀取 {agent_name} 的任務失敗: {e}")
            return None
    
    def clear_tasks(self, agent_name: str):
        """清除指定 Agent 的任務"""
        outbox_file = self.outbox_dir / f'to_{agent_name}.json'
        
        if outbox_file.exists():
            outbox_file.unlink()
    
    def get_all_agents_status(self) -> Dict[str, int]:
        """取得所有 Agent 的待辦任務數量"""
        status = {}
        
        for outbox_file in self.outbox_dir.glob('to_*.json'):
            agent_name = outbox_file.stem.replace('to_', '')
            tasks = self.get_pending_tasks(agent_name)
            status[agent_name] = len(tasks) if tasks else 0
        
        return status
