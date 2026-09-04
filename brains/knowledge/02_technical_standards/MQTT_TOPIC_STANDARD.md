# MQTT Topic Standard (WAW IoT)

## Topic Structure
waw/v1/{site_id}/{device_type}/{device_id}/{action}

- site_id: 營運站點 ID
- device_type: 裝置類型 (e.g., kiosk, scanner)
- device_id: 裝置流水號
- action: 動作名稱 (e.g., status, event, command)

## QoS Levels
- 0: At most once
- 1: At least once (Default for command)
- 2: Exactly once
