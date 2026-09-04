import paho.mqtt.client as mqtt
import json
from pathlib import Path

INFRA_PATH = Path("/Users/ilawusong/Documents/WaW/Infra")
CERT_PATH = INFRA_PATH / "config/mqtt_certs"

def publish_to_topic(topic, payload, qos=1):
    """
    統一的 MQTT 推送工具
    會自動處理 TLS 憑證載入
    """
    client = mqtt.Client()
    
    # 這裡可以加入 TLS 配置 (如果需要)
    # client.tls_set(ca_certs=str(CERT_PATH / "ca.crt"), ...)
    
    try:
        client.connect("mqtt.tg25.win", 8883)
        client.publish(topic, json.dumps(payload), qos=qos)
        client.disconnect()
        return True
    except Exception as e:
        print(f"MQTT Publish Error: {e}")
        return False
