---
inclusion: always
---

# Product Overview

## Project: HQ (Headquarters)

**HQ** is the coordination center for a multi-agent system managing IoT vending machine operations across multiple specialized projects.

### Core Purpose
- Central coordination hub for task distribution and workflow management
- Multi-agent orchestration for distributed development teams
- Knowledge management and inter-project communication

### Related Projects
- **Alliance** (`ali.tg25.win`) - Supplier and distributor management
- **Owner** (`iot.tg25.win`) - Operator backend (device, venue, reports)
- **Member** (`win.tg25.win`) - Player frontend (LINE SSO, payments, wallet)
- **Affiliate** (`affiliate.tg25.win`) - Affiliate platform
- **Infra** (`api.tg25.win`) - Infrastructure (database, MQTT, APIs)
- **iHub** (`ihub.tg25.win`) - Virtual hub integration (Android, device auth)
- **Firmware** - ESP32 firmware development (OTA, device flashing)

### Agent System
Multiple AI agents collaborate through:
- **HQ Message Hub (Redis Pub/Sub)** - 唯一正式通訊管道，走 `hq_task_flow.sh`
- **Specialized agents** - Allie (Alliance), Sophie (Owner), Mina (Member), Ina (Infra), Fio (Firmware), Coli (Firmware), Hubie (iHub)

### Business Domain
IoT vending machine ecosystem with:
- Device management and authentication
- Venue and operator management
- Player engagement and payments
- Supplier/distributor relationships
- Revenue sharing and settlements
