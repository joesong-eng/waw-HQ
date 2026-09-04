import json

with open('/Users/ilawusong/AIPP/b202HOME/HQcenter/DevBy3d/iot_system_contract.json', 'r') as f:
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

# 檢查是否已存在，不存在則加入
existing_ids = [n["id"] for n in data["nodes"]]
if "node_allie" not in existing_ids:
    data["nodes"].append(node_allie)
if "node_sophie" not in existing_ids:
    data["nodes"].append(node_sophie)

# 新增 iHub 與 Sophie 的連線 (Owner 後台讀取 iHub 資料或下指令)
link_ihub_sophie = {
    "id": "link_ihub_sophie",
    "from": "node_ihub",
    "to": "node_sophie",
    "template_type": "http_api",
    "fields_contract": [
        { "endpoint": "/api/v1/audit/report", "method": "POST", "location": "Header", "field_name": "Authorization", "data_type": "Bearer {ihub_token}" },
        { "endpoint": "/api/v1/audit/report", "method": "POST", "location": "Body", "field_name": "device_id", "data_type": "string" },
        { "endpoint": "/api/v1/audit/report", "method": "POST", "location": "Body", "field_name": "total_revenue", "data_type": "integer" }
    ]
}

# 新增 Sophie 與 Allie 的連線 (Owner 給代理商的分潤報表等)
link_sophie_allie = {
    "id": "link_sophie_allie",
    "from": "node_sophie",
    "to": "node_allie",
    "template_type": "http_api",
    "fields_contract": [
        { "endpoint": "/api/agent/revenue", "method": "GET", "location": "Query", "field_name": "agent_id", "data_type": "string" },
        { "endpoint": "/api/agent/revenue", "method": "GET", "location": "Query", "field_name": "month", "data_type": "string (YYYY-MM)" }
    ]
}

existing_links = [l["id"] for l in data["links"]]
if "link_ihub_sophie" not in existing_links:
    data["links"].append(link_ihub_sophie)
if "link_sophie_allie" not in existing_links:
    data["links"].append(link_sophie_allie)

with open('/Users/ilawusong/AIPP/b202HOME/HQcenter/DevBy3d/iot_system_contract.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

