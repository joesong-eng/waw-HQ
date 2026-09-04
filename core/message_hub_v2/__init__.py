"""
HQ Message Hub v2.0 - 事件驅動架構
支援 HTTP + Redis Pub/Sub + WebSocket 監聽
"""

__version__ = '2.0.0'
__author__ = 'HQ (Hera)'

from .config import AGENT_ROUTING, REDIS_HOST, REDIS_PORT
from .router import route_event_to_agent
from .task_manager import TaskManager
from .redis_listener import RedisListener
from .http_server import create_http_server

__all__ = [
    'AGENT_ROUTING',
    'REDIS_HOST',
    'REDIS_PORT',
    'route_event_to_agent',
    'TaskManager',
    'RedisListener',
    'create_http_server',
]
