"""
Message Hub v2.0 - 配置模組
"""
import os

# Redis 配置
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

# HTTP 配置
HTTP_PORT = 18899
HTTP_HOST = 'localhost'

# Agent 路由規則
# 與 AGENTS.md 保持一致：
#   - Sophie: 營運商後台與設備管理
#   - Ina: 資料庫、MQTT、基礎設施
#   - Mina: 玩家前端與支付系統
#   - Allie: 供應商與代理商管理
#   - Hubie: Android iHub APK
#   - Fio: IOTkiosk_v0 (kiosk/+) - 兌幣卡韌體
#   - Coli: IOTwawS3 (device/+) - 通訊卡韌體
AGENT_ROUTING = {
    'sophie': {
        'mqtt_topics': ['device/+/status', 'device/+/alarm', 'device/+/event'],
        'redis_channels': ['hq/events/device/*', 'hq/events/owner/*'],
        'keywords': ['device', 'owner', 'equipment', 'esp32']
    },
    'ina': {
        'mqtt_topics': ['system/+/alert', '$SYS/+', 'kiosk/+/status'],
        'redis_channels': ['hq/events/system/*', 'hq/events/infra/*'],
        'keywords': ['infrastructure', 'database', 'mqtt', 'redis', 'postgres']
    },
    'mina': {
        'mqtt_topics': ['kiosk/+/payment', 'kiosk/+/transaction', 'kiosk/+/coin'],
        'redis_channels': ['hq/events/member/*', 'hq/events/payment/*'],
        'keywords': ['payment', 'member', 'player', 'kiosk', 'redemption']
    },
    'allie': {
        'mqtt_topics': [],
        'redis_channels': ['hq/events/alliance/*'],
        'keywords': ['supplier', 'agent', 'alliance', 'partner']
    },
    'hubie': {
        'mqtt_topics': [],
        'redis_channels': ['hq/events/ihub/*'],
        'keywords': ['ihub', 'android', 'apk', 'tablet', 'qrcode']
    },
    'fio': {
        'mqtt_topics': ['kiosk/+/status', 'kiosk/+/error', 'kiosk/+/debug', 'kiosk/+/event'],
        'redis_channels': ['hq/events/firmware/kiosk/*'],
        'keywords': ['IOTkiosk_v0', 'kiosk_v0', 'bill acceptor', '紙鈔機', '兌幣機']
    },
    'coli': {
        'mqtt_topics': ['device/+/status', 'device/+/error', 'device/+/debug', 'device/+/event'],
        'redis_channels': ['hq/events/firmware/wawS3/*'],
        'keywords': ['IOTwawS3', 'game_v0', 'game device', '遊戲機', '採集卡']
    }
}

# Redis 訂閱頻道
REDIS_SUBSCRIBE_CHANNELS = [
    'hq/events/agent/*',
    'hq/events/system/*',
    'hq/events/device/*',
    'hq/events/member/*',
    'hq/events/owner/*',
    'hq/events/infra/*',
    'hq/events/firmware/*',
    'hq/events/mqtt/*'
]
