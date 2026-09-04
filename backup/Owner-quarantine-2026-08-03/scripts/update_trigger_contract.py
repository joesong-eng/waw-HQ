import json

with open('/Users/ilawusong/AIPP/b202HOME/HQcenter/DevBy3d/trigger_pulse_contract.json', 'r') as f:
    data = json.load(f)

# 新增 Allie 節點
node_allie = {
    "id": "node_allie",
    "name": "Allie (代理商)",
    "type": "cloud",
    "pos": { "x": -20, "y": 6, "z": 20 }
}
# 新增 Sophie 節點
node_sophie = {
    "id": "node_sophie",
    "name": "Sophie (Owner 營運商後台)",
    "type": "cloud",
    "pos": { "x": 10, "y": 6, "z": 30 }
}
# 新增 iHub 節點 (trigger_pulse_contract 中尚未有 ihub)
node_ihub = {
    "id": "node_ihub",
    "name": "iHub (Android平板)",
    "type": "cloud",
    "pos": { "x": 30, "y": 6, "z": 20 }
}

existing_ids = [n["id"] for n in data["nodes"]]
if "node_allie" not in existing_ids:
    data["nodes"].append(node_allie)
if "node_sophie" not in existing_ids:
    data["nodes"].append(node_sophie)
if "node_ihub" not in existing_ids:
    data["nodes"].append(node_ihub)

# 依據任務說明: 補齊 Allie, Sophie 節點及通訊線路，並補齊 iHub 合約內容
# 這裡我們可以讓 iHub 也接收或傳送與脈衝相關的合約資料
# 例如 iHub 向 Sophie 發送設備事件
link_ihub_sophie_pulse = {
    "id": "link_ihub_sophie_pulse",
    "from": "node_ihub",
    "to": "node_sophie",
    "template_type": "http_api",
    "fields_contract": [
        { "endpoint": "/api/v1/event/pulse", "method": "POST", "location": "Header", "field_name": "Authorization", "data_type": "Bearer {ihub_token}" },
        { "endpoint": "/api/v1/event/pulse", "method": "POST", "location": "Body", "field_name": "chip_id", "data_type": "string" },
        { "endpoint": "/api/v1/event/pulse", "method": "POST", "location": "Body", "field_name": "pulse_count", "data_type": "integer" }
    ]
}

existing_links = [l["id"] for l in data["links"]]
if "link_ihub_sophie_pulse" not in existing_links:
    data["links"].append(link_ihub_sophie_pulse)

with open('/Users/ilawusong/AIPP/b202HOME/HQcenter/DevBy3d/trigger_pulse_contract.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

