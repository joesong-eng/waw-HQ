"""
Message Hub v2.0 - 事件路由模組
"""
import json
from .config import AGENT_ROUTING

def route_event_to_agent(event):
    """
    根據事件內容路由到對應 Agent
    
    Args:
        event: 事件物件 {'source': 'redis', 'channel': '...', 'data': {...}}
    
    Returns:
        list: 匹配的 Agent 名稱列表
    """
    matched_agents = []
    
    source = event.get('source', '')
    channel = event.get('channel', '')
    data = event.get('data', {})
    
    # 將整個事件轉成字串用於關鍵字匹配
    event_text = json.dumps(event).lower()
    
    for agent_name, rules in AGENT_ROUTING.items():
        # 1. 檢查 Redis 頻道匹配
        if source == 'redis':
            for pattern in rules['redis_channels']:
                if _match_channel(channel, pattern):
                    if agent_name not in matched_agents:
                        matched_agents.append(agent_name)
                    break
        
        # 2. 檢查 MQTT 主題匹配 (未來擴充)
        if source == 'mqtt':
            mqtt_topic = data.get('topic', '')
            for pattern in rules['mqtt_topics']:
                if _match_mqtt_topic(mqtt_topic, pattern):
                    if agent_name not in matched_agents:
                        matched_agents.append(agent_name)
                    break
        
        # 3. 檢查關鍵字匹配（作為後備方案）
        if agent_name not in matched_agents:
            for keyword in rules['keywords']:
                if keyword.lower() in event_text:
                    matched_agents.append(agent_name)
                    break
    
    return matched_agents

def _match_channel(channel, pattern):
    """
    匹配 Redis 頻道模式
    
    支援：
    - hq/events/device/* (萬用字元)
    - hq/events/device/exact (精確匹配)
    """
    if pattern.endswith('/*'):
        prefix = pattern[:-2]
        return channel.startswith(prefix)
    else:
        return channel == pattern

def _match_mqtt_topic(topic, pattern):
    """
    匹配 MQTT 主題模式
    
    支援：
    - device/+/status (單層萬用)
    - device/# (多層萬用)
    """
    if '+' in pattern or '#' in pattern:
        # 簡化版 MQTT 主題匹配
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')
        
        if '#' in pattern:
            # # 必須是最後一個
            hash_index = pattern_parts.index('#')
            if hash_index != len(pattern_parts) - 1:
                return False
            pattern_parts = pattern_parts[:hash_index]
            topic_parts = topic_parts[:hash_index]
        
        if len(pattern_parts) != len(topic_parts):
            return False
        
        for p, t in zip(pattern_parts, topic_parts):
            if p != '+' and p != t:
                return False
        
        return True
    else:
        return topic == pattern
